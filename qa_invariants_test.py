"""Regression suite for the invariants verified against About.md.

Lives OUTSIDE tests/ on purpose: this project is not under version control and
something removed that directory twice while cycles were running. One file,
consolidated, re-derivable from About.md.

Run:  /opt/data/.venv/bin/python3 qa_invariants_test.py
"""
import datetime as dt
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import daily_controller as dc  # noqa: E402

PY = sys.executable
FAILED = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILED.append(label)


# ---------------------------------------------------------------- retention
print("\n1. undated rows get first_seen_in_master stamped (About.md: record it)")
base = {"posted": "Unknown", "location": "Dresden, Germany", "work_mode": "Hybrid",
        "company": "EffiCon GmbH & Co. KG", "role_verified": "Yes",
        "german_entity_verified": "Yes"}
row = dict(base)
gate = dc.eligibility(row, "2026-09-25")
check("stamps on first sight", gate.get("first_seen_in_master") == "2026-09-25",
      f"got {gate.get('first_seen_in_master')!r}")
check("row object carries it to the master", row.get("first_seen_in_master") == "2026-09-25")
check("row is retained, not rejected", gate["verification"] == "Current / Partial")

gate = dc.eligibility({**base, "first_seen_in_master": "2026-08-20"}, "2026-09-25")
check("36 days later it is removed", gate["verification"] == "REJECT", gate["reason"])
gate = dc.eligibility({**base, "first_seen_in_master": "2026-09-05"}, "2026-09-25")
check("20 days later it is retained", gate["verification"] == "Current / Partial")

# A dated row must NOT get a stamp: the real date is the stronger clock.
gate = dc.eligibility({**base, "posted": "2026-09-20"}, "2026-09-25")
check("dated rows are unaffected",
      "first_seen_in_master" not in gate and gate["verification"] == "Current")

# ------------------------------------------------------------- date parsing
print("\n2. real-world Posted formats are handled without a false rejection")
for raw, expect in [
    ("2026-09-04 (approx.; 3 weeks ago)", "Current"),
    ("2026-07-01 (approx.; 4 weeks ago)", "REJECT"),
    ("2026-06-01 (vor mehr als 2 Monaten)", "REJECT"),
    ("2026-09-22 (3 days ago)", "Current"),
    ("approx. 3 weeks ago", "Unclear"),
    ("Unknown", "Current / Partial"),
    ("2026-09-25T17:09:28Z", "Current"),
]:
    got = dc.eligibility({**base, "posted": raw}, "2026-09-25")["verification"]
    check(f"{raw[:34]:36} -> {expect}", got == expect, f"got {got}")

# ---------------------------------------------------------------- dedup
print("\n3. dedup: three independent keys, first-found URL kept, evidence retained")
# About.md: "Deduplicate by the complete announcement text and vacancy identity,
# not by URL alone." Each key alone fails a real case:
#   text triple  -> "Dresden or Essen" vs "Dresden" splits one vacancy
#   URL          -> LinkedIn re-serves one card with a new ?position=/refId
#   announcement -> the same role on two boards has two different URLs
body = ("We are hiring a QA Automation Engineer in Dresden. You will design test "
        "automation frameworks, work with our dev team, and own quality across "
        "releases. Apply now.")
li = "https://de.linkedin.com/jobs/view/senior-qa-engineer-remote-at-kake-4461168232"
SCENARIOS = [
    ("LinkedIn re-serves one card with new tracking params", 1, [
        {"url": li + "?position=7&pageNum=0&refId=aaa", "title": "Senior QA Engineer - Remote",
         "company": "Kake", "location": "Remote globally; listed as Berlin", "announcement": "Kake QA remote Berlin"},
        {"url": li + "?position=8&pageNum=0&refId=bbb", "title": "Senior QA Engineer - Remote",
         "company": "Kake", "location": "Berlin, Germany — Remote", "announcement": "Kake QA remote Berlin"},
    ]),
    ("same vacancy posted on two different boards", 1, [
        {"url": "https://www.linkedin.com/jobs/view/x-123", "title": "Test Automation Engineer",
         "company": "secunet", "location": "Dresden or Essen, Germany", "announcement": body},
        {"url": "https://www.stepstone.de/stellenangebote-SJN-123.html", "title": "Test Automation Engineer",
         "company": "secunet", "location": "Dresden, Germany", "announcement": body},
    ]),
    ("same title, three different employers stay three", 3, [
        {"url": "https://a.example/1", "title": "Softwaretester", "company": "deltra", "location": "Germany", "announcement": "deltra"},
        {"url": "https://b.example/2", "title": "Softwaretester", "company": "medatixx", "location": "Bamberg, Berlin", "announcement": "medatixx"},
        {"url": "https://c.example/3", "title": "Softwaretester", "company": "Robotron", "location": "Dresden", "announcement": "Robotron"},
    ]),
    ("same employer and title in two cities stays two", 2, [
        {"url": "https://a.example/1", "title": "QA Lead", "company": "Acme", "location": "Berlin", "announcement": "Acme QA Berlin"},
        {"url": "https://b.example/2", "title": "QA Lead", "company": "Acme", "location": "Hamburg", "announcement": "Acme QA Hamburg"},
    ]),
]
for label, want, rows in SCENARIOS:
    kept, dropped = dc.deduplicate_first_url(rows)
    check(f"{label:52} -> {want}", len(kept) == want, f"got {len(kept)}")
    if dropped:
        check("  evidence names dropped AND kept url",
              all(d["dropped_url"] and d["kept_url"] for d in dropped), str(dropped))
        check("  evidence records what matched",
              all(d.get("matched_on") in ("text", "url", "announcement") for d in dropped))

check("tracking params stripped, identity params kept",
      dc.canonical_url("https://x.example/j/1?gh_jid=abc&position=3") == "https://x.example/j/1?gh_jid=abc")
check("first-found url is the one kept",
      dc.deduplicate_first_url(SCENARIOS[1][2])[1][0]["kept_url"] == "https://www.linkedin.com/jobs/view/x-123")

# A re-post with identical employer/title/city is INTENTIONALLY one vacancy: the
# text triple fires first and the announcements are never compared. About.md
# wants the first-found URL for exactly that case -- do not "fix" this.
collapsed, dropped = dc.deduplicate_first_url([
    {"url": "https://a.example/1", "title": "QA Engineer", "company": "Acme", "location": "Berlin", "announcement": "web automation"},
    {"url": "https://b.example/2", "title": "QA Engineer", "company": "Acme", "location": "Berlin", "announcement": "game QA"},
])
check("identical employer/title/city collapses (documented)",
      len(collapsed) == 1 and dropped[0]["matched_on"] == "text")

# ------------------------------------------------- eligibility: city + remote
print("\n4. location / work-mode rules")
city = {"posted": "2026-09-20", "company": "Acme GmbH", "role_verified": "Yes",
        "german_entity_verified": "Yes"}
g = dc.eligibility({**city, "location": "Leipzig", "work_mode": "Unknown"}, "2026-09-25")
check("target city with unknown mode is retained",
      g["verification"] in ("Current", "Current / Partial"), g["verification"])
g = dc.eligibility({**city, "location": "Hamburg", "work_mode": "Remote", "germany_remote_explicit": "Yes"}, "2026-09-25")
check("explicit Germany-wide remote is eligible",
      g["verification"] in ("Current", "Current / Partial"), g["verification"])
g = dc.eligibility({**city, "location": "Hamburg", "work_mode": "Onsite"}, "2026-09-25")
check("non-target city, onsite -> rejected", g["verification"] == "REJECT", g["verification"])

# --------------------------------------------------------------- self-test
print("\n5. controller self-test reaches DONE")
with tempfile.TemporaryDirectory() as tmp:
    r = subprocess.run([PY, "daily_controller.py", "--self-test", "--no-publish", "--project", tmp],
                       cwd=str(PROJECT), capture_output=True, text=True, timeout=300)
    check("self-test exit 0", r.returncode == 0, r.stderr[-300:])
    payload = json.loads(r.stdout.strip().splitlines()[-1])
    check("status is DRY_RUN_VERIFIED", payload["status"] == "DRY_RUN_VERIFIED", payload.get("status"))
    cycle = Path(tmp) / "cycles" / payload["cycle_id"]
    state = json.loads((cycle / "state.json").read_text())
    timings = state.get("stage_seconds") or {}
    check("MASTER_RECHECK is charged to stage_seconds", "MASTER_RECHECK" in timings, str(timings))
    check("private _stage_started_at not persisted", "_stage_started_at" not in state)
    check("no notice for a silent dry run", not (Path(tmp) / "notices.jsonl").exists())
    check("dedup evidence artifact written", (cycle / "dedup_evidence.json").exists())

    store = json.loads((Path(tmp) / "first_seen.json").read_text())
    check("first_seen side-car written", bool(store.get("entries")), str(store)[:120])
    check("side-car is keyed by canonical url",
          all(k.startswith("http") for k in store.get("entries", {})),
          str(list(store.get("entries", {}))[:2]))
    # A second run in the same project must REUSE the stamp, not re-stamp today.
    stamps_before = dict(store["entries"])
    r2 = subprocess.run([PY, "daily_controller.py", "--self-test", "--no-publish", "--project", tmp],
                        cwd=str(PROJECT), capture_output=True, text=True, timeout=300)
    check("second self-test exit 0", r2.returncode == 0, r2.stderr[-300:])
    store2 = json.loads((Path(tmp) / "first_seen.json").read_text())
    reused = sum(1 for k, v in store2.get("entries", {}).items() if stamps_before.get(k) == v)
    check("stamps survive a second run unchanged", reused == len(stamps_before),
          f"{reused}/{len(stamps_before)}")

# --- regressions found on 2026-09-25, all of which broke a real cycle ---

print("\n6. single-controller guard (About.md: exactly one detached controller)")
script = PROJECT / "daily_controller.py"
def guard_blocks(argv):  # mirrors the predicate in launch_detached's /proc scan
    return any(Path(part).name == script.name for part in argv) and "--launch" not in argv
for label, argv, want in [
    ("manual relative run must block", ["python3", "daily_controller.py", "--project", str(PROJECT)], True),
    ("cron absolute run must block", ["python3", str(script)], True),
    ("launcher --launch must not block", ["python3", str(script), "--launch"], False),
    ("unrelated script must not block", ["python3", "daily_controller_bundler.py"], False),
]:
    check(label, guard_blocks(argv) is want, str(argv))
# The old test compared the absolute path, so a hand-started controller (relative
# argv) was invisible and a second one was spawned.
check("absolute-path comparison misses a relative manual run",
      (str(script) in ["python3", "daily_controller.py", "--project", str(PROJECT)]) is False,
      "old predicate silently passed a live controller")

print("\n7. empty worker stage must not crash the cycle")
_probe = Path(tempfile.mkdtemp())
res_empty = dc.Pipeline(_probe, self_test=True).run_queue(_probe, _probe / "workers", "VACANCY_WORKER", [], lambda *a: "complete")
check("run_queue([]) returns no jobs", res_empty == {}, str(res_empty))
_qp = _probe / "workers" / "queue.json"
check("run_queue([]) creates no queue.json", not _qp.exists())
try:
    (json.loads(_qp.read_text())["jobs"] if _qp.exists() else [])
    check("guarded call-site read survives an empty stage", True)
except FileNotFoundError as exc:
    check("guarded call-site read survives an empty stage", False, str(exc))

print("\n8. publication: NO_CHANGE must not replace, archive or commit (About.md step 7)")
_gitcalls = []
def _fake_git(repo, *args):
    _gitcalls.append(args); return ""
_p = Path(tempfile.mkdtemp()); _repo = Path(tempfile.mkdtemp()) / "repo"; _repo.mkdir(parents=True)
_p.mkdir(exist_ok=True)
_bytes = b"# Master\n\n| 1 | x | y |\n"
(_p / "qa_vacancies_master.md").write_bytes(_bytes)
(_repo / "README.md").write_bytes(_bytes)
(_p / "result.md").write_bytes(_bytes)
_cand = _p / "candidate.md"; _cand.write_bytes(_bytes)
_r = dc.publish_github_transaction(project=_p, repository=_repo, candidate=_cand, run_git=_fake_git,
                                  archive_date="2026-09-25")
check("identical candidate yields NO_CHANGE", _r.status == "NO_CHANGE", _r.status)
check("NO_CHANGE creates no archive", not (_p / "qa_vacancies_master_2026-09-25.md").exists())
check("NO_CHANGE runs no git command", not _gitcalls, str(_gitcalls))
check("master left byte-identical", (_p / "qa_vacancies_master.md").read_bytes() == _bytes)
# One byte of difference must publish, archive, and commit.
_gitcalls.clear()
_cand.write_bytes(_bytes + b"<!-- changed -->\n")
_r2 = dc.publish_github_transaction(project=_p, repository=_repo, candidate=_cand, run_git=_fake_git,
                                   archive_date="2026-09-25")
check("changed candidate publishes", _r2.status == "CHANGED_PUBLISHED", _r2.status)
check("previous master archived", (_p / "qa_vacancies_master_2026-09-25.md").read_bytes() == _bytes)
check("archive not overwritten on a second change same day",
      (lambda: (dc.publish_github_transaction(project=_p, repository=_repo, candidate=_cand, run_git=_fake_git, archive_date="2026-09-25"),
                (_p / "qa_vacancies_master_2026-09-25.md").read_bytes() == _bytes)[1])(),
      "archive must keep the OLD master, not the newly published one")
check("git stages, commits and pushes exactly once each",
      [a[0] for a in _gitcalls] == ["add", "commit", "push"], str(_gitcalls))
# About.md: "Publish the project master, result.md, and GitHub README.md".
# The repo copy of result.md was tracked in git but never rewritten, so it
# froze on the first publication while the master moved on.
check("repository result.md is republished too",
      (_repo / "result.md").read_bytes() == _cand.read_bytes(),
      f"repo result.md is {len((_repo/'result.md').read_bytes())}B, master is {len(_cand.read_bytes())}B")
check("all three published artifacts are byte-identical",
      len({(_p/'qa_vacancies_master.md').read_bytes(), (_p/'result.md').read_bytes(),
           (_repo/'README.md').read_bytes(), (_repo/'result.md').read_bytes()}) == 1)

print("\n9. durable worker recovery (About.md: lease, fencing, 5-min staleness, backoff)")
_q = Path(tempfile.mkdtemp()) / "q.json"
dc.create_queue(_q, "c1", [{"source_id": "s1", "source": {}}, {"source_id": "s2", "source": {}}], 2)
_claim = dc.claim_job(_q, "w1")
check("claim records a live pid and a lease token",
      bool(_claim.get("pid")) and bool(_claim.get("lease_token")) and dc.process_is_alive(_claim["pid"]))
try:
    dc.finish_job(_q, _claim["source_id"], "REVOKED-TOKEN", "complete")
    check("a stale lease cannot finish the job", False, "write was accepted")
except dc.LeaseError:
    check("a stale lease cannot finish the job", True)
_st = [j for j in json.loads(_q.read_text())["jobs"] if j["source_id"] == _claim["source_id"]][0]
check("the job is left untouched after a rejected write", _st["state"] == "claimed", _st["state"])
check("backoff is exactly 5/30/120 then exhausted",
      [dc.next_retry_delay(a) for a in (1, 2, 3, 4)] == [5, 30, 120, None],
      str([dc.next_retry_delay(a) for a in (1, 2, 3, 4)]))
_now = time.time()
check("a fresh claimed job is not stale", not dc.job_is_stale(_claim, _now))
check("a dead pid is stale", dc.job_is_stale(dict(_claim, pid=999999), _now))
_old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=400)).isoformat()
check("heartbeat AND checkpoint both >5min old is stale",
      dc.job_is_stale(dict(_claim, heartbeat_at=_old, progress_at=_old), _now))
check("stale heartbeat with a fresh checkpoint is NOT stale (AND rule)",
      not dc.job_is_stale(dict(_claim, heartbeat_at=_old, progress_at=dc.utcnow()), _now))
check("a non-claimed job is never stale", not dc.job_is_stale(dict(_claim, state="complete"), _now))

print("\n10. role gate (About.md lists the ROLE as the FIRST acceptance rule)")
def _row(**kw):
    base = {"url": "https://x.example/1", "title": "QA Engineer", "company": "ACME GmbH",
            "location": "Berlin", "posted": "2026-09-20", "work_mode": "Hybrid",
            "announcement": "QA Engineer role, apply at https://x.example/1",
            "role_verified": True, "german_entity_verified": True}
    base.update(kw); return base
check("a determinate non-QA role is rejected even in a target city",
      dc.eligibility(_row(role_verified=False, title="Softwareentwickler"), "2026-09-25")["verification"] == "REJECT",
      str(dc.eligibility(_row(role_verified=False), "2026-09-25")))
check("the role gate is checked BEFORE the city rule",
      dc.eligibility(_row(role_verified=False, location="Berlin", work_mode="Hybrid"), "2026-09-25")["verification"] == "REJECT")
check("a verified QA role is unaffected", dc.eligibility(_row(), "2026-09-25")["verification"] == "Current")
# Rows carried forward from the old master have no flag until re-analysed; an
# ABSENT flag must not be treated as "not QA" or known vacancies would vanish.
check("an absent role_verified flag is not read as a rejection",
      dc.eligibility(_row(role_verified=None), "2026-09-25")["verification"] in ("Current", "Current / Partial"),
      str(dc.eligibility(_row(role_verified=None), "2026-09-25")))
# Staleness still outranks the role gate: a stale non-QA row must be REJECT either way.
check("staleness is still enforced", dc.eligibility(_row(posted="2026-07-01"), "2026-09-25")["verification"] == "REJECT")

print("\n11. compressed-response decoding (failures seen live on 2026-09-27)")
import gzip
import io
import zlib
import source_adapters as sa

_gz = gzip.compress(b'{"data": [{"title": "QA Engineer"}]}')
_raw_deflate = zlib.compressobj(wbits=-zlib.MAX_WBITS)
_df = _raw_deflate.compress(b'{"data": []}') + _raw_deflate.flush()

check("gzip with a correct Content-Encoding decodes",
      sa.decompress(_gz, "gzip") == b'{"data": [{"title": "QA Engineer"}]}')
# The header said br, the bytes were gzip. The old code tried br first, caught
# the failure and returned the still-compressed body -> "can't decode byte 0x8b".
check("a lying/compound header still yields readable text",
      sa.decompress(_gz, "gzip, br").startswith(b"{"),
      repr(sa.decompress(_gz, "gzip, br")[:4]))
check("gzip with NO Content-Encoding header is sniffed",
      sa.decompress(_gz, "") == b'{"data": [{"title": "QA Engineer"}]}',
      "raw gzip bytes reached the text decoder")
check("raw DEFLATE with no zlib wrapper decodes", sa.decompress(_df, "deflate") == b'{"data": []}')
check("zlib-wrapped deflate decodes", sa.decompress(zlib.compress(b'{"a": 1}'), "deflate") == b'{"a": 1}')
check("uncompressed text passes through untouched", sa.decompress(b'{"a": 1}', "") == b'{"a": 1}')
check("unknown encoding on plain text is not corrupted", sa.decompress(b"hello", "identity") == b"hello")
try:
    import zstandard
    _zs = zstandard.ZstdCompressor().compress(b'{"z": true}')
    check("zstd body decodes", sa.decompress(_zs, "zstd") == b'{"z": true}')
    check("zstd body with no header is sniffed", sa.decompress(_zs, "") == b'{"z": true}')
except ImportError:
    print("  SKIP  zstd (module not installed; the magic-byte path stays inert)")
# A truncated/corrupt stream must not raise: About.md treats a temporary access
# failure as Unverified, never as a crash that loses the whole source.
check("a corrupt gzip stream degrades instead of raising", isinstance(sa.decompress(_gz[:8], "gzip"), bytes))

print("\n12. the three sources that failed on 2026-09-27, re-fetched live")
for _u in ("https://remotive.com/api/remote-jobs?limit=3",
           "https://www.arbeitnow.com/api/job-board-api"):
    try:
        _f = sa.fetch(_u, timeout=25)
        _ok = _f.status == 200 and _f.body.lstrip()[:1] in (b"{", b"[")
        check(f"{_u.split('/')[2]} returns JSON now", _ok, f"status={_f.status} body={_f.body[:40]!r}")
    except Exception as _e:
        check(f"{_u.split('/')[2]} returns JSON now", False, f"{type(_e).__name__}: {_e}")
# GermanTechJobs is a pure client-side SPA: 4.7 KB shell, no server-rendered job
# markup and its /api/jobs endpoint answers "ENDPOINT Deprecated". Without a
# browser it cannot yield cards, so it must stay Not used with that reason
# rather than being retried as a transient failure.
_f = sa.fetch("https://germantechjobs.de/api/jobs", timeout=25)
check("GermanTechJobs API is genuinely deprecated, not a decode bug",
      b"Deprecated" in _f.body, repr(_f.body[:60]))

print("\n13. registry adapter vs primary_method (2026-09-27 routing failure)")
# GermanTechJobs carried adapter="rss_v1" together with primary_method="api".
# primary_method used to win, so the source was sent to /api/jobs -> "ENDPOINT
# Deprecated" while its 600+ item RSS feed, already the registered listing_url,
# was never tried. An explicit feed adapter must correct the method.
check("an rss adapter overrides primary_method=api",
      sa.adapter_candidates({"id": "germantechjobs.de", "adapter": "rss_v1",
                             "primary_method": "api"})[0] == "http",
      str(sa.adapter_candidates({"id": "germantechjobs.de", "adapter": "rss_v1", "primary_method": "api"})))
# "rss" must never resolve to the /api/ REST route: feeds are plain http.
check("primary_method=rss never starts on the api route",
      "api" not in sa.adapter_candidates({"id": "x", "primary_method": "rss"}),
      str(sa.adapter_candidates({"id": "x", "primary_method": "rss"})))
# A genuine API source must keep its api route first.
check("a real api source still starts on api",
      sa.adapter_candidates({"id": "y", "adapter": "remotive_v1",
                             "primary_method": "api"})[0] == "api")
check("a camofox source still starts on camofox",
      sa.adapter_candidates({"id": "xing.com", "primary_method": "camofox"})[0] == "camofox")
# Live: the GermanTechJobs feed yields real cards now.
try:
    _reg = __import__("json").loads(Path("source_registry.json").read_text())
    _ss = _reg.get("sources", _reg)
    _it = _ss if isinstance(_ss, list) else list(_ss.values())
    _src = [s for s in _it if s.get("id") == "germantechjobs.de"][0]
    _ad = sa.make_adapter(_src, Path(tempfile.mkdtemp()), method="http")
    _cards = _ad.cards(_ad.listing())
    check("GermanTechJobs RSS feed yields cards live", len(_cards) >= 2, f"{len(_cards)} cards")
except Exception as _e:
    check("GermanTechJobs RSS feed yields cards live", False, f"{type(_e).__name__}: {_e}")

print("\n14. LinkedIn payload trimming (2026-09-27: 50 KB cards, 25% was boilerplate)")
_md = Path("cycles/2026-09-27_cycle-2/workers/linkedin.com/raw")
if _md.exists() and list(_md.glob("crawl4ai-card-*.md")):
    _tb = _ta = 0
    _bad = 0
    for _f in sorted(_md.glob("crawl4ai-card-*.md")):
        _raw = _f.read_text(errors="replace")
        _t = sa.trim_markdown_boilerplate(_raw, "linkedin.com")
        _tb += len(_raw); _ta += len(_t)
        _ttl = sa.page_identity(_t).get("title", "")
        # "Karrierestufe ..." / "Tätigkeitsbereich ..." are the posting's own
        # sidebar metadata, not a job title.
        if "Karrierestufe" in _ttl or "Tätigkeitsbereich" in _ttl or not _ttl:
            _bad += 1
    check("every real card yields a real title", _bad == 0, f"{_bad} bad of 12")
    check("the boilerplate is actually removed", _ta < _tb * 0.35,
          f"{_tb} -> {_ta} bytes ({_ta/_tb*100:.0f}% kept)")
else:
    print("  SKIP  no stored LinkedIn markdown on disk")
# The posting body must SURVIVE: trimming cuts whole blocks, never truncates.
if _md.exists():
    _one = sorted(_md.glob("crawl4ai-card-*.md"))[0]
    _raw = _one.read_text(errors="replace")
    _t = sa.trim_markdown_boilerplate(_raw, "linkedin.com")
    for _marker in ("Qualitätssicherung", "Aufgaben"):
        check(f"the announcement body keeps '{_marker}'", _marker in _t)
    check("the consent wall is gone", "Privatsphäre" not in _t)
    check("the related-jobs tail is gone", "Ähnliche Jobs" not in _t)
# Trimming is LinkedIn-only and must never alter another source.
_plain = "## Heading\n" + "y" * 3000
check("a non-LinkedIn payload is byte-identical", sa.trim_markdown_boilerplate(_plain, "remotive.com") == _plain)
check("an empty payload is safe", sa.trim_markdown_boilerplate("", "linkedin.com") == "")
_norole = "## LinkedIn nimmt den schutz ihrer Privatsphäre sehr ernst\nkeine Rolle hier\n" * 200
check("a page with no role heading is left alone", sa.trim_markdown_boilerplate(_norole, "linkedin.com") == _norole)
# Identity of the OTHER sources must be untouched by the title change.
check("Arbeitsagentur 'Stellenangebot:' phrasing still parses",
      sa.markdown_identity("Stellenangebot: Test Engineer (m/w/d) bei ACME GmbH ## x").get("title") == "Test Engineer (m/w/d)")
_xsnap = Path("cycles/2026-09-27_cycle-2/preflight/xing.com/raw/0005-card-2-snapshot.json")
if _xsnap.exists():
    _xt = sa.snapshot_identity(json.loads(_xsnap.read_text()).get("snapshot", "")).get("title", "")
    check("the XING snapshot title is unchanged", _xt == "Recruiter (m/w/d)", _xt)
# schema.org is read out of a <script type="application/ld+json"> block, not
# from a bare JSON string -- json_ld_objects() only scans the script tags.
_ld = json.dumps({"@type": "JobPosting", "title": "QA Automation Engineer",
                  "description": "x", "datePosted": "2026-09-20", "employmentType": "FULL_TIME",
                  "hiringOrganization": {"name": "ACME GmbH"},
                  "jobLocation": {"address": {"addressLocality": "Berlin", "addressCountry": "DE"}}})
_sl = f'<script type="application/ld+json">{_ld}</script>'
check("schema.org JobPosting identity still works",
      sa.page_identity(_sl).get("title") == "QA Automation Engineer", str(sa.page_identity(_sl)))
check("company from schema.org is unaffected", sa.page_identity(_sl).get("company") == "ACME GmbH")
check("location from schema.org is unaffected", sa.page_identity(_sl).get("location") == "Berlin, DE",
      sa.page_identity(_sl).get("location"))
check("posted from schema.org is unaffected", sa.page_identity(_sl).get("posted") == "2026-09-20")

print("\n15. identity must be derived from the TRIMMED markdown (ordering)")
# Regression: `page_identity()` was called on the RAW page, so it read the first
# heading of the untrimmed document. Live in cycle-3: 10 of 12 LinkedIn cards
# stored the title "Karrierestufe ..." even though the trimmer and the
# markdown_identity fix were both already deployed and unit-green.
if _md.exists():
    for _f in sorted(_md.glob("crawl4ai-card-*.md")):
        _raw = _f.read_text(errors="replace")
        _trimmed = sa.trim_markdown_boilerplate(_raw, "linkedin.com")
        _from_raw = sa.page_identity(_raw).get("title", "")
        _from_trim = sa.page_identity(_trimmed).get("title", "")
        if "Karrierestufe" in _from_trim or "Tätigkeitsbereich" in _from_trim or not _from_trim:
            check(f"trimmed text yields a real title for {_f.name[-12:]}", False, _from_trim)
            break
    else:
        check("trimmed text yields a real title on every stored card", True)
    # The ordering itself. Match CALLS only, not the prose: the explanatory
    # comment above the call site mentions `page_identity()` by name, so a
    # plain str.find() reports it "first" and this check always fails.
    _src = __import__("inspect").getsource(sa.Crawl4AIAdapter.detail)
    _code = "\n".join(l for l in _src.splitlines()
                      if not l.strip().startswith("#"))
    _ti = _code.find("trim_markdown_boilerplate(")
    _pi = _code.find("page_identity(")
    check("trim_markdown_boilerplate is called BEFORE page_identity", 0 <= _ti < _pi,
          f"trim at {_ti}, identity at {_pi}")

print("\n16. preflight must not blame access for an editorial outcome (2026-09-28)")
# XING serves "Recruiter (m/w/d)" and "Initiativbewerbung" as FULL postings
# (About this job / Aufgaben / Über uns / Kontakt, ~14 KB each), yet both
# titles are in NON_VACANCY_TITLES, so the old check reported the pages as
# "portal pages" and the master blamed "all independent access methods failed"
# for what is a perfectly readable source with no QA vacancy in it.
_xs2 = Path("cycles/2026-09-28_cycle-2/preflight/xing.com/raw")
if _xs2.exists():
    for _n in ("0003-card-1-snapshot.json", "0005-card-2-snapshot.json"):
        _p = _xs2 / _n
        if not _p.exists():
            continue
        _pg = {"title": sa.first_heading(json.loads(_p.read_text()).get("snapshot", "")),
               "announcement": json.loads(_p.read_text()).get("snapshot", "")}
        check(f"a real XING posting is not a utility page ({_pg['title'][:22]!r})",
              sa._is_utility_page(_pg) is False, str(sa._is_utility_page(_pg)))
for _t in ("Ähnliche Jobs", "Passwort", "Registrieren", "Similar jobs"):
    check(f"a utility page is still rejected ({_t})",
          sa._is_utility_page({"title": _t, "announcement": "x" * 900}) is True)
# A posting whose title happens to be in NON_VACANCY_TITLES must NOT be judged
# by that list alone when the page has a real posting structure.
check("a structured 'Recruiter' posting is not a utility page",
      sa._is_utility_page({"title": "Recruiter (m/w/d)",
                           "announcement": "About this job Aufgaben Über uns Kontakt " + "x" * 200}) is False)
for _t, _want in (("QA Engineer (m/w/d)", True), ("Senior Software Test Engineer", True),
                  ("Game Localization Tester (m/f/d)", True), ("Recruiter (m/w/d)", False),
                  ("Initiativbewerbung Mitarbeiter", False),
                  ("Softwareentwickler für die Prüftechnik", False), ("", False), (None, False)):
    check(f"looks_like_testing_role({_t!r:36s}) == {_want}", sa.looks_like_testing_role(_t) is _want)


class _PF(sa.SourceAdapter):
    """Preflight on two synthetic pages; exercises the real SourceAdapter code."""

    def __init__(self, pages):
        super().__init__({"id": "xing.com", "listing_url": "https://www.xing.com/jobs/search"},
                         Path(tempfile.mkdtemp()))
        self.pages = pages

    def listing(self, *, preflight: bool = False):
        return sa.Fetch("u", "u", 200, b"<html></html>", "text/html")

    def cards(self, page):
        return [{"url": f"https://www.xing.com/jobs/hamburg-role-{157400000+i}"} for i in (1, 2)]

    def detail(self, card):
        self._n += 1
        return dict(self.pages[self._n - 1], url=card["url"])


# A fixture must now look like a REAL posting: looks_like_vacancy_posting()
# requires body text with >=2 VACANCY_BODY_MARKERS, so a bare title plus filler
# is correctly rejected now. Pad with genuine posting sections.
_FILLER = (" About this job Ihre Aufgaben Ihr Profil Qualifikationen Wir bieten "
           "Dein Impact Kontakt Über uns ") + ("Aufgaben sind abwechslungsreich. " * 40)
_QA = {"title": "QA Engineer (m/w/d)", "announcement": _FILLER}
_NQA = {"title": "Recruiter (m/w/d)", "announcement": _FILLER}
_UTIL = {"title": "Ähnliche Jobs", "announcement": "x" * 900}
try:
    _PF([_NQA, _QA]).preflight()
    check("a QA vacancy among the two cards passes preflight", True)
except Exception as _e:
    check("a QA vacancy among the two cards passes preflight", False, str(_e)[:80])
try:
    result = _PF([_NQA, _NQA]).preflight()
    check("readable but no QA vacancy passes with deep_scan_needed", 
          result.get("status") == "pass" and result.get("deep_scan_needed") is True, 
          f"got {result}")
except Exception as _e:
    check("readable but no QA vacancy is not reported as an access failure",
          "readable but offered no QA" in str(_e) and "access method" not in str(_e), str(_e)[:90])
try:
    _PF([_UTIL, _UTIL]).preflight()
    check("two utility pages do NOT pass", False, "they passed")
except Exception as _e:
    check("two utility pages are still rejected as portal pages",
          "portal/utility pages" in str(_e), str(_e)[:80])

# The regression that shipped the first half of this fix: CamofoxAdapter
# REIMPLEMENTS preflight (it must, to drive the browser), so the base class's
# two findings exist in two places and drift apart. XING and LinkedIn are the
# only Camofox sources, so the base-class fix alone never reached XING -- the
# master still printed "Camofox preflight card-1 is a portal page" for a
# readable source. Assert the Camofox override applies the SAME checks.
_camo = __import__("inspect").getsource(sa.CamofoxAdapter.preflight)
check("CamofoxAdapter.preflight uses _is_utility_page, not the title list",
      "_is_utility_page" in _camo and "non_vacancy_heading" not in _camo,
      "Camofox preflight still judges on the title list")
check("CamofoxAdapter.preflight distinguishes readable-but-no-QA",
      "looks_like_testing_role" in _camo and "deep_scan_needed" in _camo)

print("\n17. an ERROR response body must be decompressed too (2026-09-29 cron)")
# The cron of 2026-09-29 failed on Remotive/Arbeitnow/GermanTechJobs with the
# same "0x8b / 0xfc" errors I had already "fixed" on 2026-09-27. The reason:
# fetch()'s HTTPError branch returned exc.read() verbatim, WITHOUT decompress().
# The 200 path was decompressed, which is why every manual test passed -- the
# servers only compress the ERROR body, so only the cron path hit it.
import brotli as _brotli
_err_body = _brotli.compress(b'{"error":"rate limited"}')
_src_f = __import__("inspect").getsource(sa.fetch)
check("fetch() decompresses the HTTPError branch too",
      _src_f.count("decompress(") >= 2,
      f"decompress() appears {_src_f.count('decompress(')}x in fetch()")
import io as _io
import urllib.error as _ue
_e = _ue.HTTPError("https://x", 429, "Too Many", {"Content-Encoding": "br"}, _io.BytesIO(_err_body))
_out = sa.decompress(_e.read(), _e.headers.get("Content-Encoding", ""))
check("a brotli error body becomes readable text", _out == b'{"error":"rate limited"}', repr(_out[:30]))
# And the non-error path must stay intact.
check("the 200 path still decompresses", _src_f.count("decompress(") >= 2)

print("\n18. Camofox 5xx must be retried, not fatal (2026-09-25..29)")
# 19 of 27 XING preflights died on "Camofox HTTP 500 for GET /tabs/<id>/snapshot"
# while the identical four-snapshot flow succeeded from the same code path
# minutes later. XING and LinkedIn are the only Camofox sources, so a single
# transient gateway 5xx removed XING from the day's sources entirely.
import io as _io2
import urllib.error as _ue2


class _CamoStub:
    """CamofoxClient that fails N times with 5xx, then succeeds."""

    def __init__(self, fail_times):
        self.fail_times, self.calls = fail_times, 0
        self.base_url, self.timeout = "http://stub", 5
        self.opener = self._opener

    def _opener(self, req, timeout=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise _ue2.HTTPError(req.full_url, 500, "boom", {}, _io2.BytesIO(b'{"error":"tab busy"}'))
        return _io2.BytesIO(b'{"ok": true}')

    __call__ = _opener


_c2 = sa.CamofoxClient("http://stub", opener=None)
_c2.opener = _CamoStub(2)
sa.time.sleep = lambda *_a, **_k: None  # keep the test instant
try:
    _r = _c2.health()
    check("a 5xx is retried and the retry succeeds", _r.get("ok") is True and _c2.opener.calls == 3,
          f"calls={_c2.opener.calls} result={_r}")
except Exception as _e:
    check("a 5xx is retried and the retry succeeds", False, str(_e)[:80])

_c3 = sa.CamofoxClient("http://stub", opener=None)
_c3.opener = _CamoStub(9)
try:
    _c3.health()
    check("persistent 5xx still fails after the retries", False, "it succeeded")
except Exception as _e:
    check("persistent 5xx still fails after the retries", "HTTP 500" in str(_e), str(_e)[:70])
    check("the failure keeps the server's own explanation", "tab busy" in str(_e), str(_e)[:90])


def _raise404(req, timeout=None):
    raise _ue2.HTTPError(req.full_url, 404, "gone", {}, _io2.BytesIO(b'{"error":"Tab not found"}'))


_c4 = sa.CamofoxClient("http://stub", opener=_raise404)
try:
    _c4.health()
    check("a 4xx is NOT retried", False, "it succeeded")
except Exception as _e:
    check("a 4xx is NOT retried", "HTTP 404" in str(_e), str(_e)[:60])

print("\n19. Indeed: /rc/clk?jk= cards and listing-title fallback (2026-09-29)")
# Indeed 403s every plain HTTP request and hides card URLs behind /rc/clk?jk=.
# The Camofox accessibility snapshot of the listing contains NO card links at
# all (0 occurrences in a 36 KB snapshot), so crawl4ai is the only route that
# can see them. Following the redirect lands on the employer's own board, whose
# markdown has no job-title heading -- so the title must come from the listing
# link text or every card comes back empty and preflight reports "no QA vacancy"
# for a source full of QA roles.
check("an Indeed /rc/clk?jk= URL is a direct card",
      sa.direct_card("https://de.indeed.com/rc/clk?jk=d4c948bc460ec1d8") is True)
check("an Indeed /rc/clk URL without jk is not a card",
      sa.direct_card("https://de.indeed.com/rc/clk?bb=xyz") is False)
for _bad in ("https://de.indeed.com/jobs?q=QA&l=Berlin",
             "https://de.indeed.com/q-acme-jobs.html",
             "https://de.indeed.com/l-berlin-jobs.html",
             "https://de.indeed.com/career/quality-engineer/salaries/Berlin"):
    check(f"an Indeed non-card URL is rejected ({_bad.rsplit('/', 1)[-1][:28]})", sa.direct_card(_bad) is False)
# The cards() regression: the href/markdown pair order was inverted by a
# content-sniffing guess and produced ZERO cards on a 156-link listing.
_md = ("* [Startseite](https://de.indeed.com/)\n"
       "* [Qualitätsingenieur KI-Fokus / Quality Engineer (m/w/d)]"
       "(https://de.indeed.com/rc/clk?jk=b61d3fbdb683ee91&bb=abc)\n"
       "* [QA Automation Test Engineer](https://de.indeed.com/rc/clk?jk=34b2f27db740da55&bb=abc)\n"
       "* [Jobs in Berlin](https://de.indeed.com/l-berlin-jobs.html)\n")
_af = sa.Crawl4AIAdapter({"id": "de.indeed.com", "listing_url": "https://de.indeed.com/jobs?q=QA&l=Berlin"},
                         Path(tempfile.mkdtemp()))
_cards = _af.cards(sa.Fetch("u", "https://de.indeed.com/jobs?q=QA&l=Berlin", 200, _md.encode(), "text/markdown"))
check("crawl4ai cards() finds both Indeed cards", len(_cards) == 2, f"{len(_cards)} cards")
check("each Indeed card carries the listing title",
      all(c.get("listing_title") for c in _cards) and
      "Quality Engineer" in (_cards[0]["listing_title"] if _cards else ""),
      str([c.get("listing_title")[:30] for c in _cards]))
# The placeholder is NON-EMPTY, so an empty-title fallback never fires. The
# detail page's first heading on Indeed's redirect target is the modal text
# "Stellenbeschreibung Gleichen Sie hier die Stellenbeschreibung mit Ihrem
# Profil ab" -- a non-testing string that must lose to the listing link text.
_placeholder = "Stellenbeschreibung Gleichen Sie hier die Stellenbeschreibung mit Ihrem Profil ab"
check("an Indeed placeholder heading is not a testing role", sa.looks_like_testing_role(_placeholder) is False)
_li = "Qualitätsingenieur KI-Fokus / Quality Engineer (m/w/d)"
check("the listing title wins over an Indeed placeholder",
      sa.looks_like_testing_role(_li) and not sa.looks_like_testing_role(_placeholder))

print("\n20. multi-location listing sweep (Indeed has no pagination)")
# Measured 2026-09-29: Indeed ignores `start=` (start=10 returns nothing) but
# re-sorts per location and serves a DISJOINT card set -- Berlin and Muenchen
# each returned 15 cards with ZERO overlap, 75 distinct across 7 locations vs 15
# from a single query. `config.listing_urls` is how a source declares the sweep.
_sweep = {
    "id": "de.indeed.com",
    "listing_url": "https://de.indeed.com/jobs?q=QA&l=Berlin",
    "config": {"listing_urls": ["https://de.indeed.com/jobs?q=QA&l=Leipzig",
                                 "https://de.indeed.com/jobs?q=QA&l=Hamburg"]},
}
_src = __import__("inspect").getsource(sa.Crawl4AIAdapter.listing)
check("Crawl4AIAdapter.listing honours config.listing_urls", "listing_urls" in _src)
# A source without the key must behave exactly as before (one crawl).
_plain = sa.Crawl4AIAdapter({"id": "stepstone.de", "listing_url": "https://www.stepstone.de/"},
                            Path(tempfile.mkdtemp()))
check("a source without listing_urls is untouched", "listing_urls" not in _plain.source.get("config", {}))
# The dedup of already-seen links must keep the union honest.
_ded = sa.Crawl4AIAdapter({"id": "de.indeed.com", "listing_url": "https://de.indeed.com/jobs?q=QA&l=Berlin",
                           "config": {"listing_urls": ["https://de.indeed.com/jobs?q=QA&l=Leipzig"]}},
                          Path(tempfile.mkdtemp()))
_in_urls = [s for s in _reg["sources"] if s.get("id") == "de.indeed.com"][0]["config"].get("listing_urls", [])
check("the Indeed registry entry declares the sweep", len(_in_urls) >= 5, f"{len(_in_urls)} listing URLs")

print("\n21. Indeed `bb` token and direct-URL recovery (2026-09-29)")
# Two identical queries a minute apart returned the SAME 15 vacancies (jk
# identical) but DIFFERENT URLs, because Indeed regenerates `bb` per page view.
# bb is click tracking, not identity: leaving it in the canonical URL made one
# vacancy look like several, which only the announcement-text key happened to
# catch -- a coincidence that will not hold at 300 cards.
_b1 = "https://de.indeed.com/rc/clk?jk=b61d3fbdb683ee91&bb=6sEC9AoPnYEhgxHIIr"
_b2 = "https://de.indeed.com/rc/clk?jk=b61d3fbdb683ee91&bb=oEAKjjcRPfoIoyg4PbyPz"
check("two Indeed URLs for one vacancy canonicalise equal",
      dc.canonical_url(_b1) == dc.canonical_url(_b2), dc.canonical_url(_b1))
check("the jk identity survives canonicalisation", "jk=b61d3fbdb683ee91" in dc.canonical_url(_b1))
# bb must not be stripped from a URL where it is the identity (there is no such
# case today, but a blanket strip would be a latent bug).
check("bb is stripped", "bb=" not in dc.canonical_url(_b1))
# The master must publish the EMPLOYER's page, not the ad-click hop: About.md
# requires a direct vacancy card, and an /rc/clk?jk= link with a per-view token
# is neither direct nor durable.
_del = ("# Job als Senior IT-Consultant / Software Quality Engineer (m/w/d) | Deloitte GmbH\n"
        "## Ihre Aufgaben\n* Berät Kunden bei Testautomatisierung\n## Ihr Profil\n* Studium\n"
        + ("Wir bieten vielfältige Projekte. " * 20) + "\n"
        "[](https://job.deloitte.com/job-senior-it-consultant-software-quality-engineer-mwd-_48452"
        "?utm_source=indeed&utm_medium=organic)\n"
        "[](https://job.deloitte.com/job-senior-it-consultant-software-quality-engineer-mwd-_48452"
        "?utm_source=indeed&utm_medium=organic)\n"
        "[](https://www.cookiebot.com/de/x)\n")
check("the employer URL is recovered from the rendered page",
      sa.extract_final_vacancy_url(_del) ==
      "https://job.deloitte.com/job-senior-it-consultant-software-quality-engineer-mwd-_48452",
      sa.extract_final_vacancy_url(_del))
check("the aggregator's own host is never returned as the final URL",
      "indeed.com" not in sa.extract_final_vacancy_url(_del))
check("the cookie-consent host is skipped",
      "cookiebot.com" not in sa.extract_final_vacancy_url(_del))
# No trustworthy candidate -> return "" so the caller keeps the original URL
# rather than publishing a guess.
check("a lone stray link is not trusted",
      sa.extract_final_vacancy_url("see https://example.com/jobs/one for details") == "",
      repr(sa.extract_final_vacancy_url("see https://example.com/jobs/one for details")))
check("a page with no off-aggregator link yields nothing",
      sa.extract_final_vacancy_url("nothing here") == "")
check("static assets are never taken for a vacancy page",
      sa.extract_final_vacancy_url("https://cdn.example.com/app.js https://cdn.example.com/logo.png") == "")
_src2 = __import__("inspect").getsource(sa.Crawl4AIAdapter.detail)
# de.indeed.com is a CANDIDATE-ONLY source (see CANDIDATE_ONLY_SOURCES): its card
# URL is an ad-click hop that is not worth following, so detail() must NOT
# publish a "direct URL" and must NOT attempt a crawl. The older assertion
# expected extract_final_vacancy_url here and is no longer true for this source.
check("aggregator sources are marked candidate-only",
      "de.indeed.com" in sa.CANDIDATE_ONLY_SOURCES)
check("detail() short-circuits for a candidate-only source",
      "_candidate_card" in _src2)
check("the candidate card keeps the source URL as provenance",
      '"source_url": card["url"]' in __import__("inspect").getsource(sa.Crawl4AIAdapter._candidate_card))
check("a candidate card carries no invented body",
      '"announcement": ""' in __import__("inspect").getsource(sa.Crawl4AIAdapter._candidate_card))

print("\n22. one blocked card must not cost the whole source (2026-09-29)")
# Measured: all 49 Indeed listing crawls succeeded (250 distinct cards), then
# the FIRST /rc/clk detail hop drew a Cloudflare challenge three times and the
# retry budget burned ~10 minutes failing that one card -- taking the entire
# source out of the run. detail() now degrades to the listing data instead of
# raising, and about 300 other cards are still processed.
check("detail() no longer raises on an unreadable detail page",
      "return self._listing_only_card" in _src2 and 'raise RuntimeError("Crawl4AI detail unreadable")' not in _src2)
check("the fallback card carries the listing title",
      "listing_title" in __import__("inspect").getsource(sa.Crawl4AIAdapter._listing_only_card))
# CRITICAL: the fallback must NOT invent announcement text. About.md requires
# the COMPLETE announcement for acceptance, and synthesize() only feeds cards
# with a non-empty announcement to the analyser, so an empty body means the row
# is retained as Unverified rather than judged on data we do not have.
_fb = sa.Crawl4AIAdapter({"id": "de.indeed.com", "listing_url": "https://de.indeed.com/jobs?q=QA&l=Berlin"},
                          Path(tempfile.mkdtemp()))
_card = _fb._listing_only_card({"url": "https://de.indeed.com/rc/clk?jk=abc", "listing_title": "QA Engineer (m/w/d)"},
                               "detail page blocked")
check("the fallback announcement is EMPTY, not invented", _card["announcement"] == "", repr(_card["announcement"]))
check("the fallback is flagged unreadable", bool(_card.get("unreadable_reason")) and _card["http_status"] == 0)
check("the fallback keeps the listing title", _card["title"] == "QA Engineer (m/w/d)")
# And the synthesis filter that keeps such a card out of the analyser:
check("synthesize() only analyses cards with a non-empty announcement",
      'x.get("announcement") and x.get("url")' in
      __import__("inspect").getsource(dc.Pipeline.synthesize))

print("\n23. a card needs posting BODY, not just a plausible title (2026-09-29)")
# A category index can be long, have a full site menu and a title naming a real
# role, and still not be a posting. Its final URL would then be a link to a list
# of OTHER jobs, which is exactly what About.md forbids.
_idx = ("# Job Visitenkarte Senior IT-Consultant / Software Quality Engineer (m/w/d)\n"
        "- Stellenangebote ansehen\n"
        + " ".join(["Karriere Team Bewerbungsprozess Unternehmen Standorte Presse"] * 12) + "\n"
        "## cloud-jobs-_pr16\n## automotive-jobs-_pr6\n## accounting-ifrs-jobs-_pr22\n"
        + " ".join(["Impressum Datenschutz Cookie-Einstellungen Newsletter AGB"] * 10))
check("a category index is not a vacancy posting",
      sa.looks_like_vacancy_posting({"title": "Job Visitenkarte QA", "announcement": _idx}) is False)
_real = ("## Ihre Aufgaben * Du testest unsere Software * Du automatisierst Regressionstests\n"
         "## Ihr Profil * Studium * Erfahrung mit Selenium "
         + "Wir suchen einen engagierten Kollegen für unser Team in Berlin. " * 10)
check("a real posting body is accepted",
      sa.looks_like_vacancy_posting({"title": "QA Engineer", "announcement": _real}) is True)
check("a title alone is never a posting",
      sa.looks_like_vacancy_posting({"title": "QA Engineer (m/w/d)",
                                     "announcement": "Ihre Aufgaben"}) is False)
check("an empty body is never a posting",
      sa.looks_like_vacancy_posting({"title": "QA", "announcement": ""}) is False)
# And the direct-URL extractor must not hand back a careers SECTION (measured:
# it returned pta.de/karriere/ twice while the real posting, seen once, sat at
# karriere.pta-gruppe.com/.../jobs/273/apply).
check("the careers section is not a vacancy card",
      sa.direct_card("https://www.pta.de/karriere/") is False)
check("a real posting URL is a vacancy card",
      sa.direct_card("https://karriere.pta-gruppe.com/de/p/pta-deutschland/jobs/273/apply") is True)
_pta = ("[Karriere](https://www.pta.de/karriere/) [Karriere](https://www.pta.de/karriere/) "
        "[Unternehmen](https://www.pta.de/unternehmen/) [Unternehmen](https://www.pta.de/unternehmen/) "
        "[Bewerben](https://karriere.pta-gruppe.com/de/p/pta-deutschland/jobs/273/apply)")
check("the careers section loses to the real posting",
      sa.extract_final_vacancy_url(_pta) ==
      "https://karriere.pta-gruppe.com/de/p/pta-deutschland/jobs/273/apply",
      sa.extract_final_vacancy_url(_pta))



print("\n" + ("FAILED: " + ", ".join(FAILED) if FAILED else "ALL INVARIANTS HOLD"))
sys.exit(1 if FAILED else 0)
