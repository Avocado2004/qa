"""Train step 3: follow the 302 and see what the CARD page actually serves.

/viewjob?jk= answered 302 for one key and 403 for another. Follow the redirect
(crawl4ai and a real browser both do) and record where it lands and whether the
landing page is a real posting or an ad/teaser.
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
from t1_viewjob import BROWSER

LISTING = "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = []


def get(url, referer=None, timeout=30):
    h = dict(BROWSER)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, sa.decompress(r.read(), r.headers.get("Content-Encoding", "")).decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        try:
            body = sa.decompress(e.read(), e.headers.get("Content-Encoding", "")).decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, body, (e.headers.get("Location") or url)
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}", url


st, body, _ = get(LISTING)
print("листинг HTTP", st, len(body) // 1024, "KB, cookies:", len(list(jar)))
jk = list(dict.fromkeys(re.findall(r"[?&]jk=([0-9a-f]{8,})", body)))
print("jk:", len(jk))

print()
print("=== /viewjob?jk= с переходами ===")
for key in jk[:5]:
    u = f"https://de.indeed.com/viewjob?jk={key}"
    time.sleep(random.uniform(3.0, 5.0))
    st2, t2, final = get(u, referer=LISTING)
    tt = sa.text(t2.encode())
    ident = sa.page_identity(tt)
    print(f"  jk={key[:12]} HTTP {st2:3d} текст {len(tt):6d}")
    print(f"     финал: {final[:100]}")
    if tt:
        print(f"     заголовок: {str(ident.get('title'))[:56]!r}")
        print(f"     работодатель: {str(ident.get('company'))[:34]!r}")
        low = tt[:3000].casefold()
        for flag in ("blocked", "captcha", "verify you are human", "unusual traffic"):
            if flag in low:
                print(f"     !! {flag}")
