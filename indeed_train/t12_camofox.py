"""Test: Camofox + stealth to access Indeed listing.

The listing page itself (not /viewjob) returned 200 with full posting data
before the IP got throttled. Camofox may pass the "Security Check - Indeed"
challenge that blocks curl.
"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/opt/data/qa-vacancy-project")
import source_adapters as sa

URL = "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"
ARTIFACT = Path(tempfile.mkdtemp())

print("=== Camofox adapter test ===")
src = {"id": "de.indeed.com", "listing_url": URL, "config": {}}
ad = sa.CamofoxAdapter(src, ARTIFACT)

# Try the listing
print("Fetching listing via Camofox...")
try:
    listing = ad.listing()
    print(f"HTTP {listing.status}  {len(listing.body)//1024}KB")
    if listing.status == 200:
        html = listing.body.decode("utf-8", "replace")
        # Check for the embedded posting
        for marker in ("autoOpenTwoPaneViewjobResponse", "sanitizedJobDescription", "jobKey"):
            print(f"  {marker}: {html.count(marker)}")
        if "autoOpenTwoPaneViewjobResponse" in html:
            i = html.find('"autoOpenTwoPaneViewjobResponse":')
            j = html.find("{", i)
            depth, in_str, esc = 0, False, False
            for k in range(j, len(html)):
                c = html[k]
                if in_str:
                    if esc: esc = False
                    elif c == "\\": esc = True
                    elif c == '"': in_str = False
                    continue
                if c == '"': in_str = True
                elif c == "{": depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        blob = json.loads(html[j:k+1])
                        b = blob.get("body") or {}
                        jim = ((b.get("jobInfoWrapperModel") or {}).get("jobInfoModel") or {})
                        head = jim.get("jobInfoHeaderModel") or {}
                        title = head.get("jobTitle") or b.get("jobTitle")
                        raw = jim.get("sanitizedJobDescription") or ""
                        text = sa.text(raw.encode()) if raw else ""
                        print(f"\n  SUCCESS: title={str(title)[:60]!r}")
                        print(f"  body length: {len(text)}")
                        break
except Exception as exc:
    print(f"Camofox error: {type(exc).__name__}: {exc}")

print("\n=== Also test with crawl4ai + stealth headers ===")
# Try the crawl4ai adapter with proper headers
try:
    src2 = {"id": "de.indeed.com", "listing_url": URL}
    ad2 = sa.Crawl4AIAdapter(src2, ARTIFACT)
    page = ad2.listing()
    print(f"crawl4ai HTTP {page.status}  {len(page.body)//1024}KB")
    if page.status == 200:
        html = page.body.decode("utf-8", "replace")
        for marker in ("autoOpenTwoPaneViewjobResponse", "sanitizedJobDescription", "jobKey"):
            print(f"  {marker}: {html.count(marker)}")
except Exception as exc:
    print(f"crawl4ai error: {type(exc).__name__}: {exc}")