"""Train step 5: a polite session, and does the listing carry the body?

Repeated hits from this IP have started getting 403 on the LISTING itself, so
the first question is durability: warm the session from the homepage the way a
person does, keep one cookie jar, pace the requests, and see how long the
listing stays readable. Only then does it make sense to ask what is inside it.
"""
import http.cookiejar
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
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = []


def get(url, referer=None, lo=2.5, hi=5.0, timeout=30):
    time.sleep(random.uniform(lo, hi))
    h = dict(BROWSER)
    if referer:
        h["Referer"] = referer
    try:
        with op.open(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.status, sa.decompress(r.read(), r.headers.get("Content-Encoding", "")).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, sa.decompress(e.read(), e.headers.get("Content-Encoding", "")).decode("utf-8", "replace")
        except Exception:
            return e.code, ""
    except Exception as e:
        return 0, str(e)


print("=== 1. разогрев: главная, как человек ===")
st, t = get("https://de.indeed.com/", lo=0.5, hi=1.0)
print("  главная HTTP", st, len(t) // 1024, "KB, cookies:", len(list(jar)))

print()
print("=== 2. листинг с прогревом, 4 попытки с паузами ===")
LISTING = "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"
body = ""
for attempt in range(1, 5):
    st, t = get(LISTING, referer="https://de.indeed.com/", lo=4, hi=7)
    jk = list(dict.fromkeys(re.findall(r"[?&]jk=([0-9a-f]{8,})", t)))
    print(f"  попытка {attempt}: HTTP {st} {len(t)//1024}KB jk={len(jk)} "
          f"cookies={len(list(jar))}")
    if st == 200 and jk:
        body = t
        break

if not body:
    print("  листинг недоступен — IP во временной блокировке")
    raise SystemExit(0)

print()
print("=== 3. что внутри листинга ===")
jk = list(dict.fromkeys(re.findall(r"[?&]jk=([0-9a-f]{8,})", body)))
first = jk[0]
for marker in ("window.mosaic", "providerJobcards", "__INITIAL_STATE__",
               "application/ld+json", '"jobTitle"', '"snippet"', '"jobDescription"',
               '"description"', "mosaic-provider-jobcards"):
    print(f"  {marker:28s} {body.count(marker)}")

i = body.find(first)
print()
print("=== 4. текст вокруг первой вакансии ===")
if i > 0:
    txt = re.sub(r"<[^>]+>", " ", body[i: i + 12000])
    print(re.sub(r"\s+", " ", txt)[:1100])
