"""Train step 10 (ready to run when access returns): the determinism test.

The task's completion criterion is: pull the SAME vacancies out of Indeed twice
in a row. This script does exactly that, twice, from a clean session each time,
and diffs the results.

It also settles the open question left by t8: does paginating the listing
(start=10, 20, ...) yield a DIFFERENT auto-open posting each time? If so, one
listing page yields one full posting and N keys, and N pages yield N postings
with zero /viewjob requests and zero 403s.

Every listing page is saved to disk so a throttle never costs us the evidence.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, "/opt/data/qa-vacancy-project")
import source_adapters as sa
from indeed_client import Indeed, job_keys

SAVE = Path("listings")
SAVE.mkdir(exist_ok=True)

QUERIES = [
    ("QA+Engineer", "Berlin"),
    ("QA+Engineer", "Leipzig"),
    ("QA+Engineer", "Dresden"),
    ("Softwaretester", "Berlin"),
    ("Softwaretester", "Leipzig"),
    ("Softwaretester", "Dresden"),
    ("Test+Automation", "Berlin"),
    ("Qualit%C3%A4tssicherung", "Dresden"),
    ("Testingenieur", "Leipzig"),
]


def posting_from(html):
    """(jobKey, title, body_text, company) from a listing page, or Nones."""
    i = html.find('"autoOpenTwoPaneViewjobResponse":')
    if i < 0:
        return None
    j = html.find("{", i)
    depth, in_str, esc = 0, False, False
    blob = None
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
    if not blob or blob.get("status") != "success":
        return None
    b = blob.get("body") or {}
    jim = ((b.get("jobInfoWrapperModel") or {}).get("jobInfoModel") or {})
    head = jim.get("jobInfoHeaderModel") or {}
    raw = jim.get("sanitizedJobDescription") or ""
    text = sa.text(raw.encode()) if raw else ""
    company = sa.page_identity(text or "") if text else {}
    return (b.get("jobKey") or head.get("jobKey"),
            head.get("jobTitle") or b.get("jobTitle"),
            re.sub(r"\s+", " ", text).strip(),
            b.get("trueJobLocation") or (head.get("companyName") or ""))


def run_pass(label, starts=(0, 10, 20)):
    cli = Indeed(lo=5.0, hi=9.0)
    print(f"\n=== ПРОХОД {label}: разогрев {cli.warm()} ===")
    found = {}
    for q, city in QUERIES:
        for start in starts:
            url = f"https://de.indeed.com/jobs?q={q}&l={city}&start={start}"
            st, html = cli.get(url, referer="https://de.indeed.com/")
            if st != 200:
                print(f"  {q[:22]:24s} {city:9s} start={start:3d} HTTP {st}")
                continue
            tag = f"{label}_{q}_{city}_{start}".replace("%", "_")
            (SAVE / f"{tag}.html").write_text(html, encoding="utf-8")
            keys = job_keys(html)
            p = posting_from(html)
            note = ""
            if p and p[2]:
                key, title, text, loc = p
                found[key] = {"title": title, "body": len(text), "city": city,
                              "q": q, "start": start}
                note = f"ТЕЛО {len(text):6d} jk={str(key)[:12]}"
            print(f"  {q[:22]:24s} {city:9s} start={start:3d} "
                  f"HTTP 200 ключей={len(keys):3d} {note}")
    return found


a = run_pass("A")
print(f"\nпрогон A: уникальных вакансий с телом = {len(a)}")
json.dump(a, open("pass_a.json", "w"), ensure_ascii=False, indent=1)

print("\nожидание перед вторым проходом (60с)...")
time.sleep(60)

b = run_pass("B")
print(f"\nпрогон B: уникальных вакансий с телом = {len(b)}")
json.dump(b, open("pass_b.json", "w"), ensure_ascii=False, indent=1)

print()
print("=" * 60)
ka, kb = set(a), set(b)
print("критерий задачи: два раза подряд одни и те же вакансии")
print(f"  A={len(ka)}  B={len(kb)}  пересечение={len(ka & kb)}")
print(f"  только в A: {len(ka - kb)}   только в B: {len(kb - ka)}")
print(f"  повторяемость: {len(ka & kb) / max(1, len(ka | kb)):.1%}")
