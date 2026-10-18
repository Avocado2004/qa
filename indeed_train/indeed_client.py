"""Polite, retrying Indeed client for training. Import this, do not re-probe.

Measured 2026-09-30 on this host:
  * listing GET  -> 200, ~1 MB, 8 cookies set, 15-16 job keys (jk)
  * /viewjob?jk= -> 403 "Security Check - Indeed" (Indeed's own gate; no cf-ray,
    so it is NOT Cloudflare). Unreliable by path alone.
  * The listing embeds "autoOpenTwoPaneViewjobResponse":{"status":"success",
    "body":{...}} = the FULL posting for the auto-opened card.
  * Burst probing gets the IP throttled: the listing itself started answering
    403 after ~15 quick requests. Pace requests and retry with backoff.
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

HOME = "https://de.indeed.com/"


class Indeed:
    def __init__(self, lo=4.0, hi=8.0):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self.op.addheaders = []
        self.lo, self.hi = lo, hi

    def _once(self, url, referer):
        h = dict(BROWSER)
        if referer:
            h["Referer"] = referer
        try:
            with self.op.open(urllib.request.Request(url, headers=h), timeout=30) as r:
                return r.status, sa.decompress(
                    r.read(), r.headers.get("Content-Encoding", "")).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            try:
                return e.code, sa.decompress(
                    e.read(), e.headers.get("Content-Encoding", "")).decode("utf-8", "replace")
            except Exception:
                return e.code, ""
        except Exception as e:
            return 0, str(e)

    def get(self, url, referer=None, attempts=4):
        """One paced GET with backoff. Returns (status, html)."""
        for i in range(attempts):
            time.sleep(random.uniform(self.lo, self.hi) * (1 + i))
            st, t = self._once(url, referer)
            if st == 200:
                return st, t
            if i == attempts - 1:
                return st, t
        return st, t

    def warm(self):
        """Visit the homepage first, as a person does. Failure is fine."""
        st, _ = self.get(HOME, attempts=2)
        return st

    def listing(self, q, city, start=0, radius=None, remote=False):
        """A results page. q is already URL-encoded-ish; city plain."""
        params = f"q={q}&l={city}&start={start}"
        if remote:
            params += "&sc=0kf%3Aattr(DSQF7)%3B"      # remote filter
        if radius is not None:
            params += f"&radius={radius}"
        return self.get(f"{HOME}jobs?{params}", referer=HOME)


def job_keys(html):
    """Job keys in document order, deduplicated."""
    found = re.findall(r'"(?:jk|jobKey|autoOpenTwoPaneJobKey)":"([0-9a-f]{8,})"', html)
    found += re.findall(r"data-jk=\"([0-9a-f]{8,})\"", html)
    found += re.findall(r"[?&]jk=([0-9a-f]{8,})", html)
    return list(dict.fromkeys(found))


def json_object_after(text, key):
    """Parse the JSON object that follows `"key":`, brace-matched."""
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


def embedded_posting(html):
    """The full posting Indeed ships inside a listing page, or None."""
    blob = json_object_after(html, "autoOpenTwoPaneViewjobResponse")
    if not blob or blob.get("status") != "success":
        return None
    return blob.get("body") or None


if __name__ == "__main__":
    cli = Indeed()
    print("разогрев:", cli.warm(), "cookies:", len(list(cli.jar)))
    st, html = cli.listing("QA+Engineer", "Berlin", start=0)
    print("листинг HTTP", st, len(html) // 1024, "KB")
    if st != 200:
        raise SystemExit(0)
    keys = job_keys(html)
    print("job keys:", len(keys))
    post = embedded_posting(html)
    print("встроенное объявление:", bool(post))
    if post:
        for k in ("jobKey", "title", "companyName", "location", "salary",
                  "datePublished", "workSchedule", "canonicalUrl", "applyUrl",
                  "jobDescription", "jobDescriptionText", "requisitionNumber",
                  "jobLocation", "hiringCompany", "jobTypes", "displayDate"):
            v = post.get(k)
            if v in (None, "", {}, []):
                continue
            s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            print(f"  {k:22s} = {s[:180]}")
