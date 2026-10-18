"""Train: get real vacancy CARDS out of Indeed, not ad hops.

Hypothesis 1: the listing carries a `jk` job key, and Indeed serves the full
posting server-side at /viewjob?jk=<key> WITHOUT the /rc/clk ad hop that
Cloudflare refused 684 times. Test the hypothesis first.
"""
import gzip
import random
import re
import sys
import time
import urllib.error
import urllib.request
import zlib

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
    "DNT": "1",
}


def get(url, referer=None, timeout=30):
    headers = dict(BROWSER)
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    op = urllib.request.build_opener()
    try:
        with op.open(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, sa.decompress(raw, r.headers.get("Content-Encoding", "")).decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, "", url
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}", url


LISTING = "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"

print("=== 1. листинг обычным HTTP ===")
status, body, final = get(LISTING)
print("HTTP", status, len(body) // 1024, "KB   final:", final[:80])
jk = list(dict.fromkeys(re.findall(r'"jk"\s*:\s*"([0-9a-f]{8,})"', body)))
print("jk в JSON-встройках:", len(jk))
jk += [k for k in re.findall(r"[?&]jk=([0-9a-f]{8,})", body) if k not in jk]
print("jk всего уникальных:", len(jk))
print("  примеры:", jk[:3])
if not jk:
    print("  viewjob в разметке:", len(re.findall(r"viewjob", body, re.I)))
    print("  mosaic:", "mosaic-provider-jobcards" in body)
    print("  первый текст:", re.sub(r"\s+", " ", sa.text(body.encode()))[:400])

print()
print("=== 2. /viewjob?jk= отдаёт полный текст? ===")
for key in jk[:3]:
    u = f"https://de.indeed.com/viewjob?jk={key}"
    st, txt, _ = get(u, referer=LISTING)
    t = sa.text(txt.encode())
    blocked = any(x in t[:4000].casefold() for x in
                  ("blocked", "captcha", "verify you are human", "unusual traffic",
                   "access denied", "security check"))
    ident = sa.page_identity(t)
    print(f"  jk={key[:14]} HTTP {st:3d} текст {len(t):6d} "
          f"блок={blocked} заголовок={str(ident.get('title'))[:44]!r}")
    time.sleep(random.uniform(2.5, 4.5))
