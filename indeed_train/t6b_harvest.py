"""Train step 6 (clean): harvest posting bodies straight out of the listing.

Key finding so far: the listing embeds
  "autoOpenTwoPaneViewjobResponse":{"status":"success","body":{...}}
which is the FULL posting for the card the two-pane view auto-opens. If a body
ships with the listing, there is no /rc/clk ad hop and no /viewjob 403 -- the
anti-bot surface shrinks to one request per listing page instead of one per
card.

This script is self-contained (no imports of the earlier probes, which executed
their own tests on import) and uses a brace matcher instead of a regex, because
the embedded JSON is ~50 KB deep and a non-greedy pattern cuts it mid-object.
"""
import http.cookiejar
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/data/qa-vacancy-project")
import source_adapters as sa

BROWSER = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
               "image/webp,*/*;q=0.8"),
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
jar = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
_op.addheaders = []


def get(url, referer=None, lo=4.0, hi=7.0, timeout=30):
    time.sleep(random.uniform(lo, hi))
    h = dict(BROWSER)
    if referer:
        h["Referer"] = referer
    try:
        with _op.open(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.status, sa.decompress(r.read(), r.headers.get("Content-Encoding", "")).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, sa.decompress(e.read(), e.headers.get("Content-Encoding", "")).decode("utf-8", "replace")
        except Exception:
            return e.code, ""
    except Exception as e:
        return 0, str(e)


def json_object_after(text, key):
    """Return the parsed JSON object that follows `"key":`, or None."""
    i = text.find(f'"{key}":')
    if i < 0:
        return None
    j = text.find("{", i)
    if j < 0:
        return None
    depth, in_str, esc = 0, False, False
    for k in range(j, len(text)):
        c = text[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[j:k + 1])
                except Exception:
                    return None
    return None


print("=== 1. листинг ===")
url = "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"
st, body = get(url, referer="https://de.indeed.com/")
print("HTTP", st, len(body) // 1024, "KB, cookies:", len(list(jar)))
if st != 200:
    raise SystemExit("листинг недоступен")

print()
print("=== 2. autoOpenTwoPaneViewjobResponse ===")
blob = json_object_after(body, "autoOpenTwoPaneViewjobResponse")
print("распарсился:", bool(blob))
if not blob:
    raise SystemExit("нет блока")
print("status:", blob.get("status"))
b = blob.get("body") or {}
print("полей в body:", len(b))
interesting = ("jobKey", "title", "companyName", "location", "jobDescription",
               "jobDescriptionText", "salary", "datePublished", "workSchedule",
               "jobLocation", "canonicalUrl", "indeedApplyUrl", "applyUrl",
               "jobUrl", "requisitionNumber", "requestAttribute", "company",
               "hiringCompany", "employer", "jobTypes", "displayDate",
               "createDate", "publishDate", "country", "city")
for k in interesting:
    v = b.get(k)
    if v in (None, "", {}, []):
        continue
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    print(f"  {k:24s} = {s[:200]}")

print()
print("=== 3. где ещё в листинге лежат описания ===")
for k in ("jobDescriptionText", "jobDescription", "\"description\"", "snippet",
          "jobCardDescriptionJson", "jobPosting"):
    print(f"  {k:26s} вхождений: {body.count(k)}")
