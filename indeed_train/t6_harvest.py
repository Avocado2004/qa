"""Train step 6: harvest the posting body straight out of the listing.

Found it. The listing carries `autoOpenTwoPaneViewjobResponse` with
`status:"success"` -- Indeed server-renders the FULL posting for the first card
because the two-pane view opens it automatically. The question now is how many
cards come with a body and how many need a second request.

If a body is in the listing, there is no ad hop, no /viewjob 403, and no
anti-bot problem for that card at all: one listing request serves N cards.
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
from t5_polite import BROWSER, get  # noqa: F401  (get warms the session)


def listing(q="QA+Engineer", city="Berlin", start=0):
    u = f"https://de.indeed.com/jobs?q={q}&l={city}&start={start}"
    st, body = get(u, referer="https://de.indeed.com/", lo=4, hi=7)
    return st, u, body


print("=== 1. листинг ===")
st, u, body = listing()
print("HTTP", st, len(body) // 1024, "KB")

# Every job key in the page, in document order.
keys = list(dict.fromkeys(re.findall(r'"(?:jk|jobKey|autoOpenTwoPaneJobKey)":"([0-9a-f]{8,})"',
                                     body)))
# The auto-open response holds the real body.
m = re.search(r'"autoOpenTwoPaneViewjobResponse":(\{.*?\})\s*,\s*"', body, re.S)
print("jk найдено:", len(keys))
print("autoOpenTwoPaneViewjobResponse:", bool(m))

if m:
    try:
        blob = json.loads(m.group(1))
    except Exception as exc:
        print("  JSON не распарсился:", exc)
        blob = {}
    b = blob.get("body") or {}
    print("  status:", blob.get("status"))
    print("  ключи в body:", sorted(b.keys())[:20])
    for k in ("jobKey", "title", "companyName", "location", "jobDescription",
              "jobDescriptionText", "salary", "datePublished", "workSchedule",
              "jobLocation", "companyRating", "applyUrl", "canonicalUrl",
              "indeedApplyUrl", "jobUrl", "requisitionNumber", "requestAttribute"):
        v = b.get(k)
        if v in (None, "", {}, []):
            continue
        s = json.dumps(v, ensure_ascii=False)[:220] if not isinstance(v, str) else v[:220]
        print(f"    {k:22s} = {s}")

print()
print("=== 2. сколько карточек в листинге и у скольких есть описание? ===")
# Job cards are <a ... jk=...> blocks; count them and look for inline text.
cards = re.findall(r'data-jk="([0-9a-f]{8,})"', body)
print("data-jk карточек:", len(set(cards)))
snips = re.findall(r'"snippet":\s*"([^"]{20,400})"', body)
print("snippet-полей:", len(snips))
for s in snips[:3]:
    print("   ", s[:150].replace("\\u002F", "/"))
