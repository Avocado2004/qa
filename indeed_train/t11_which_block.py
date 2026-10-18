"""Train step 11: is the block on the IP, or on the request fingerprint?

15 probes over 5.5 hours all answer 403 with 27 KB. Before accepting "Indeed has
banned us", separate the two causes:

  A. IP-level block  -> every route from this address is refused.
  B. Fingerprint     -> a different TLS/UA/session shape would be served.

A cheap discriminator: ask for the block page from two different entry points
and compare. If the body is byte-identical it is one canned page, which tells us
little; if a *different* path (e.g. a country domain, or an API host) serves
normally, the block is route-specific rather than global.

This is diagnosis only. It does not attempt to defeat anything: the goal is to
learn whether "reliably extract from Indeed" is achievable at all from here.
"""
import hashlib
import sys

sys.path.insert(0, "/opt/data/qa-vacancy-project")
from indeed_client import Indeed

TARGETS = [
    ("de listing", "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"),
    ("de home", "https://de.indeed.com/"),
    ("www listing", "https://www.indeed.com/jobs?q=QA+Engineer&l=Berlin"),
    ("at listing", "https://at.indeed.com/jobs?q=QA+Engineer&l=Wien"),
    ("uk listing", "https://uk.indeed.com/jobs?q=QA+Engineer&l=London"),
    ("ch listing", "https://ch.indeed.com/jobs?q=QA+Engineer&l=Z%C3%BCrich"),
]

cli = Indeed(lo=6.0, hi=10.0)
print("разогрев:", cli.warm())
for label, url in TARGETS:
    st, html = cli.get(url, referer="https://www.google.com/", attempts=1)
    h = hashlib.sha256(html.encode()).hexdigest()[:12] if html else "-"
    title = ""
    i = html.find("<title>")
    if i >= 0:
        j = html.find("</title>", i)
        title = html[i + 7: j].strip()[:52]
    print(f"  {label:12s} HTTP {st:3d} {len(html)//1024:5d}KB  sha={h}  {title!r}")
