"""Train step 8: harvest many cards per listing via the mobile viewjob API.

Confirmed: the listing's auto-open block carries
  jobInfoWrapperModel.jobInfoModel.jobInfoHeaderModel.jobTitle        (83 chars)
  jobInfoWrapperModel.jobInfoModel.sanitizedJobDescription          (6386 chars)
for the auto-opened card only -- one posting per listing page, and no
/viewjob request at all. 16 job keys per listing, so 1 body per ~16 cards.

Question: is there one URL that returns that same block for an ARBITRARY jk?
`appShareUrl` shows Indeed's own share link is /viewjob?jk=... , and that path
answers 403. Test the mobile/desktop variants of the same API and, separately,
whether paginating the listing (start=10,20,...) yields one full posting each.
"""
import json
import re
import sys
import time

sys.path.insert(0, "/opt/data/qa-vacancy-project")
from indeed_client import Indeed, job_keys

cli = Indeed()
print("разогрев:", cli.warm())


def title_and_body(html):
    """Pull (title, body) out of a page that carries the auto-open block."""
    i = html.find('"autoOpenTwoPaneViewjobResponse":')
    if i < 0:
        return None, None, None
    j = html.find("{", i)
    depth, in_str, esc = 0, False, False
    for k in range(j, len(html)):
        c = html[k]
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
                blob = json.loads(html[j:k + 1])
                break
    else:
        return None, None, None
    b = blob.get("body") or {}
    t = ((b.get("jobInfoWrapperModel") or {}).get("jobInfoModel") or {})
    head = t.get("jobInfoHeaderModel") or {}
    return (b.get("jobKey"), head.get("jobTitle") or b.get("jobTitle"),
            t.get("sanitizedJobDescription"))


print()
print("=== 1. один листинг: сколько вакансий и у скольких тело? ===")
st, html = cli.listing("QA+Engineer", "Berlin", start=0)
keys = job_keys(html)
jk, title, desc = title_and_body(html)
print("HTTP", st, "ключей:", len(keys))
print("тело пришло для jk:", jk, "в списке:", jk in keys if jk else None)
print("заголовок:", repr(str(title)[:70]))
print("длина тела:", len(desc or ""))

print()
print("=== 2. пагинация: даёт ли start=10 / 20 своё тело? ===")
for start in (10, 20):
    st, h = cli.listing("QA+Engineer", "Berlin", start=start)
    k2, t2, d2 = title_and_body(h)
    print(f"  start={start:3d} HTTP {st} ключей {len(job_keys(h))} "
          f"тело_для={str(k2)[:14]} длина={len(d2 or '')} "
          f"заголовок={str(t2)[:44]!r}")

print()
print("=== 3. прямой viewjob под разными вариантами пути ===")
target = keys[1] if len(keys) > 1 else keys[0]
for path in (f"https://de.indeed.com/viewjob?jk={target}",
             f"https://de.indeed.com/m/viewjob?jk={target}",
             f"https://de.indeed.com/viewjob?jk={target}&vjs=3",
             f"https://de.indeed.com/viewjob?jk={target}&vjk=1"):
    st, h = cli.get(path, referer="https://de.indeed.com/jobs?q=QA&l=Berlin")
    _, t3, d3 = title_and_body(h)
    print(f"  {path[:58]:58s} HTTP {st} тело={len(d3 or '')}")
    if st != 200:
        tt = re.search(r"<title>(.*?)</title>", h, re.S)
        print("      причина:", re.sub(r"\s+", " ", tt.group(1))[:60] if tt else h[:80])
