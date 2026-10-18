"""Train step 2: why does /viewjob return 403, and what DOES work?

Hypothesis 2: the 403 is not a hard Cloudflare block on the path but a missing
session cookie. A real user goes listing -> card in ONE session. Test: fetch the
listing, keep the Set-Cookie, then request /viewjob with the same cookie jar and
a matching Referer.
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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def opener():
    o = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),
                                   NoRedirect)
    o.addheaders = []
    return o


def get(url, referer=None, timeout=30):
    h = dict(BROWSER)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    try:
        with opener().open(req, timeout=timeout) as r:
            return r.status, sa.decompress(r.read(), r.headers.get("Content-Encoding", "")).decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", dict(e.headers)


print("=== 1. листинг с cookie jar ===")
st, body, hd = get(LISTING)
print("HTTP", st, len(body) // 1024, "KB")
print("Set-Cookie:", hd.get("Set-Cookie", "")[:120] or "(нет)")
print("cookies в jar:", [c.name for c in jar])
jk = list(dict.fromkeys(re.findall(r"[?&]jk=([0-9a-f]{8,})", body)))
print("jk:", len(jk))

print()
print("=== 2. /viewjob с той же сессией ===")
for key in jk[:2]:
    u = f"https://de.indeed.com/viewjob?jk={key}"
    time.sleep(random.uniform(3, 5))
    st2, t2, hd2 = get(u, referer=LISTING)
    low = t2[:3000].casefold()
    blocked = any(x in low for x in ("blocked", "captcha", "verify you are human",
                                     "unusual traffic", "access denied", "cloudflare"))
    print(f"  jk={key[:14]} HTTP {st2:3d} текст {len(t2):6d} блок={blocked}")
    if st2 != 200:
        print("     Server:", hd2.get("Server", "-"), "| cf-ray:",
              "да" if hd2.get("cf-ray") else "нет")
        print("     body[:200]:", t2[:200].replace("\n", " "))
    time.sleep(random.uniform(3, 5))

print()
print("=== 3. а /viewjob?jk= как ССЫЛКА из листинга? ===")
m = re.search(r'href="(/viewjob\?[^"]{10,120})"', body)
print("нашли ссылку в листинге:", bool(m), (m.group(1)[:80] if m else "-"))
