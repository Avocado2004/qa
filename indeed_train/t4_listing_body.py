"""Train step 4: does the LISTING already contain the posting text?

The card page is behind "Security Check - Indeed" (Indeed's own gate, not
Cloudflare -- the 403 carries no cf-ray). But the listing HTML is ~1 MB. A job
board rendering 15+ cards server-side often ships a snippet, and sometimes the
whole body, in the page. If the body is in the listing, no card request is
needed at all and the anti-bot problem disappears by construction.
"""
import re
import sys

sys.path.insert(0, "/opt/data/qa-vacancy-project")
import source_adapters as sa

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
LISTING = "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"

f = sa.fetch(LISTING, timeout=30)
body = f.body.decode("utf-8", "replace")
print("листинг HTTP", f.status, len(body) // 1024, "KB")

jk = list(dict.fromkeys(re.findall(r"[?&]jk=([0-9a-f]{8,})", body)))
print("jk:", len(jk))
first = jk[0]

print()
print("=== 1. структура JSON-встройки ===")
for marker in ("window.mosaic", "providerJobcards", "jobcards", "__INITIAL_STATE__",
               "window.__data", "application/ld+json", "\"jobTitle\"", "\"snippet\""):
    print(f"  {marker:26s} вхождений: {body.count(marker)}")

print()
print("=== 2. application/ld+json (JobPosting = полное описание) ===")
for m in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', body, re.S):
    raw = m.group(1).strip()
    if "JobPosting" in raw:
        print("  найден JobPosting, длина:", len(raw))
        print("  ", raw[:900])
        break
else:
    print("  JobPosting в ld+json нет")

print()
print("=== 3. что известно о первой вакансии из листинга ===")
i = body.find(first)
print("позиция в разметке:", i)
if i > 0:
    # window out the CSS noise: take the tag-stripped text after the key
    tail = body[i: i + 14000]
    txt = re.sub(r"<[^>]+>", " ", tail)
    txt = re.sub(r"\s+", " ", txt)
    print(txt[:1200])
