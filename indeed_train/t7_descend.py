"""Train step 7: find the title and body inside the embedded posting.

The auto-open block gave only `jobKey` and `jobLocation`. The title/description
live deeper -- Indeed splits the posting across `jobDescriptionText`,
`jobDescriptionHtml`, a `mapbox`/`section` model, or a separate
`mosaic.providerJobcards` array. Walk the object graph and report every key
that holds a long string, rather than guessing names.
"""
import json
import sys

sys.path.insert(0, "/opt/data/qa-vacancy-project")
from indeed_client import Indeed, embedded_posting, job_keys


def walk(node, path="", out=None, depth=0):
    if out is None:
        out = []
    if depth > 7:
        return out
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, f"{path}.{k}" if path else k, out, depth + 1)
    elif isinstance(node, list):
        for i, v in enumerate(node[:4]):
            walk(v, f"{path}[{i}]", out, depth + 1)
    elif isinstance(node, str) and len(node) >= 60:
        out.append((path, len(node), node))
    return out


cli = Indeed()
print("разогрев:", cli.warm())
st, html = cli.listing("QA+Engineer", "Berlin", start=0)
print("листинг HTTP", st, len(html) // 1024, "KB")
if st != 200:
    raise SystemExit(0)

post = embedded_posting(html)
print("блок:", bool(post))

print()
print("=== A. все длинные строки в autoOpen-блоке ===")
for path, n, val in walk(post):
    print(f"  {n:6d}  {path}")
    print(f"          {val[:150]!r}")

print()
print("=== B. ключи верхнего уровня body ===")
for k in sorted((post or {}).keys()):
    v = post[k]
    kind = type(v).__name__
    size = len(v) if isinstance(v, (str, list, dict)) else ""
    print(f"  {k:34s} {kind:6s} {size}")

print()
print("=== C. сколько job keys в листинге и есть ли тело у каждого ===")
keys = job_keys(html)
print("ключей:", len(keys), keys[:4])
# Look for a per-card array in the whole page.
for marker in ("mosaic.providerJobcards", "jobcards\",", "\"jobCards\"",
               "providerJobCards", "\"jobKey\":\"", "jobDescriptionText",
               "jobDescriptionHtml", "\"jobDescription\""):
    print(f"  {marker:28s} {html.count(marker)}")
