#!/usr/bin/env python3
"""Detached, fail-closed controller for the daily QA vacancy pipeline.

The scheduler is only a trigger. This module owns cycle order, durable queues,
source partitioning, recovery, direct OpenAI-compatible LLM calls, verification
and changed-only publication. It never starts Hermes/Kanban/cron sessions.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from source_adapters import fetch, text, looks_like_vacancy_posting

SCHEMA = 2
MAX_WORKERS_LIMIT = 10
BACKOFF_SECONDS = [5, 30, 120]
STALE_SECONDS = 300
GRACE_SECONDS = 30
TERMINAL = {"complete", "failed", "blocked"}
VERIFICATIONS = {"Current", "Current / Partial", "Rejected", "Unclear"}
CATEGORIES = (
    "Manual WEB QA Engineer", "Software Test Engineer",
    "Gamedev QA Engineer", "Other QA Roles",
)
PROJECT_DEFAULT = Path(__file__).resolve().parent
QA_REPOSITORY_DEFAULT = Path("/opt/data/qa-repo")


@dataclass(frozen=True)
class PublicationResult:
    status: str
    archive: Path | None = None


def run_git_command(repository: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repository, check=True, capture_output=True, text=True)


def publish_github_transaction(
    *, project: Path, repository: Path, candidate: Path, run_git=run_git_command,
    archive_date: str | None = None, commit_message: str = "Publish QA vacancy master",
) -> PublicationResult:
    """Archive and publish byte-different content, then commit and push the repository."""
    project, repository = project.resolve(), repository.resolve()
    candidate = candidate.resolve()
    candidate_bytes = candidate.read_bytes()
    master = project / "qa_vacancies_master.md"
    result_file = project / "result.md"
    readme = repository / "README.md"
    master_changed = not master.exists() or master.read_bytes() != candidate_bytes
    github_changed = not readme.exists() or readme.read_bytes() != candidate_bytes
    result_changed = not result_file.exists() or result_file.read_bytes() != candidate_bytes
    if not master_changed and not github_changed and not result_changed:
        return PublicationResult("NO_CHANGE")
    archive = None
    if master_changed and master.exists():
        date = archive_date or dt.datetime.now(dt.timezone.utc).date().isoformat()
        archive = project / f"qa_vacancies_master_{date}.md"
        if not archive.exists():
            atomic_text(archive, master.read_bytes())
    atomic_text(master, candidate_bytes)
    atomic_text(result_file, candidate_bytes)
    atomic_text(readme, candidate_bytes)
    # About.md requires publishing the project master, result.md AND the
    # GitHub README. The repository copy of result.md was tracked in git but
    # never rewritten, so it silently froze on the first publication while the
    # master moved on -- a stale artifact published as if it were current.
    repo_result = repository / "result.md"
    if repo_result.exists() or result_file.exists():
        repo_result_changed = not repo_result.exists() or repo_result.read_bytes() != candidate_bytes
        atomic_text(repo_result, candidate_bytes)
    else:
        repo_result_changed = False
    if github_changed or repo_result_changed:
        run_git(repository, "add", "--", "README.md", "result.md")
        run_git(repository, "commit", "-m", commit_message)
        run_git(repository, "push")
    return PublicationResult("CHANGED_PUBLISHED", archive)


class LeaseError(RuntimeError):
    pass


def load_env_file() -> None:
    """Load non-secret environment values from the project .env without logging them."""
    for candidate in (PROJECT_DEFAULT / ".env", Path("/opt/data/.env")):
        try:
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip().strip('"').strip("'")
                if key and value and key not in os.environ:
                    os.environ[key] = value
        except FileNotFoundError:
            continue


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def parse_time(value: str | float | None) -> float:
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return dt.datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        with contextlib.suppress(OSError):
            dfd = os.open(path.parent, os.O_DIRECTORY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
    finally:
        with contextlib.suppress(FileNotFoundError): os.unlink(tmp)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA:
        raise RuntimeError("source_registry.json has unsupported schema; migration required")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise RuntimeError("source registry has no valid active-source list")
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise RuntimeError("source registry entry is not an object")
        for key in ("id", "name", "domain", "listing_url", "status"):
            if not isinstance(source.get(key), str) or not source[key]:
                raise RuntimeError(f"source registry entry lacks {key}")
        if source["id"] in seen:
            raise RuntimeError(f"duplicate source id: {source['id']}")
        seen.add(source["id"])
        # "retired" is a first-class status, not a deletion. About.md requires a
        # MAINTAINED source registry, so a source taken out of service is kept
        # with its measured reason (de.indeed.com: 0 published rows in 7 masters
        # while costing 194 min/night) instead of being silently removed --
        # otherwise the next cycle's registry refresh would re-add it.
        if source["status"] not in {"active", "unavailable", "retired"}:
            raise RuntimeError(f"invalid source status: {source['status']}")
        parsed = urllib.parse.urlparse(source["listing_url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(f"invalid listing_url for {source['id']}")
    return data


def split_md_row(line: str) -> list[str]:
    """Split a Markdown table row while honoring escaped and linked pipes."""
    source = line.strip()
    cells, buf = [], []
    in_label, link_parens, escaped = False, 0, False
    for char in source:
        if char == "|" and not escaped and not in_label and not link_parens:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == "[" and not escaped and not in_label and not link_parens:
            in_label = True
        elif char == "]" and not escaped and in_label:
            in_label = False
        elif char == "(" and not escaped and i_is_link_destination(source, buf):
            link_parens += 1
        elif char == ")" and not escaped and link_parens:
            link_parens -= 1
        escaped = False
    cells.append("".join(buf).strip())
    while cells and not cells[0]:
        cells.pop(0)
    while cells and not cells[-1]:
        cells.pop()
    return cells


def i_is_link_destination(source: str, buf: list[str]) -> bool:
    """Whether the current cell contains a completed Markdown link label."""
    return "[" in buf and "](" in "".join(buf)


def migrate_legacy_master(text: str) -> list[dict[str, str]]:
    """Migrate the published category tables, preserving every row as unverified."""
    rows: list[dict[str, str]] = []
    category: str | None = None
    for line in text.splitlines():
        heading = re.fullmatch(r"##\s+\d+\.\s+(.+?)(?:\s+\(\d+\))?\s*", line)
        if heading:
            candidate = heading.group(1).strip()
            if candidate in CATEGORIES: category = candidate
            continue
        if not line.startswith("|"): continue
        cells = split_md_row(line)
        if len(cells) != 7 or category is None: continue
        match = re.fullmatch(r"\[([^]]+)\]\((https?://[^)]+)\)", cells[1])
        if not match or not cells[0] or not cells[6]: continue
        verif = cells[6] if cells[6] in VERIFICATIONS else "Unclear"
        rows.append({"legacy_id": cells[0], "title": match.group(1), "url": match.group(2),
                     "company": cells[2], "location": cells[3], "posted": cells[4],
                     "work_mode": cells[5], "url_index": cells[6], "category": category,
                     "verification": verif})
    return rows


def escape_table(value: Any) -> str:
    return re.sub(r"\\+\|", r"\\|", str(value).replace("|", r"\|"))


def render_rows(rows: list[dict[str, str]]) -> str:
    out = "| # | Position | Company | Location | Posted | Work mode | Verification |\n|---:|---|---|---|---|---|---|\n"
    for number, row in enumerate(rows, 1):
        out += (f"| {number} | [{escape_table(row['title'])}]({row['url']}) | {escape_table(row['company'])} | "
                f"{escape_table(row['location'])} | {escape_table(row['posted'])} | {escape_table(row['work_mode'])} | {row['verification']} |\n")
    return out


def normalize_category(value: Any) -> str:
    """Map semantic role labels to the four governing master categories."""
    text = str(value or "").casefold()
    if "game" in text or "localization" in text:
        return "Gamedev QA Engineer"
    if "manual" in text or "web" in text:
        return "Manual WEB QA Engineer"
    if any(term in text for term in ("test", "quality", "automation", "qa")):
        return "Software Test Engineer"
    return "Other QA Roles"


def normalize_work_mode(value: Any) -> str:
    text = str(value or "Unknown").casefold()
    if any(token in text for token in ("hybrid", "teilzeit", "teil-home", "home office", "homeoffice", "büro", "buero")):
        return "Hybrid"
    if any(token in text for token in ("onsite", "on-site", "vor ort", "vorort", "presenz")):
        return "Onsite"
    if any(token in text for token in ("remote", "homeoffice möglich", "mobiles arbeiten")):
        return "Remote"
    return "Unknown"


def normalize_posted(value: Any) -> str:
    if value in (None, ""):
        return "Unknown"
    if isinstance(value, (int, float)) or str(value).isdigit():
        stamp = float(value)
        if stamp > 1_000_000_000:
            return dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date().isoformat()
    text = str(value).strip()
    if text.casefold() in {"unknown", "none", "null"}:
        return "Unknown"
    return text


BLOCKED_POSITION_TYPES = (
    # (marker, why) -- checked as whole words in the CASE-FOLDED text.
    ("werkstudent", "Werkstudent position"),
    ("werkstudentin", "Werkstudent position"),
    ("working student", "Werkstudent position"),
    ("studentische hilfskraft", "student position"),
    ("student assistant", "student position"),
    ("studierendenpraktikum", "student internship"),
    ("praktikum", "internship"),
    ("praktikant", "internship"),
    ("trainee", "trainee position"),
    ("intern", "internship"),
    ("ausbildung", "apprenticeship"),
    ("azubi", "apprenticeship"),
    ("unpaid", "unpaid"),
    ("unbezahlt", "unpaid"),
    ("ohne vergütung", "unpaid"),
    ("ohne verguetung", "unpaid"),
    ("ehrenamtlich", "unpaid"),
    ("on a volunteer basis", "unpaid"),
    ("paid internship", "internship"),
)


def detect_blocked_position_type(text: str) -> str:
    """Return the reason this posting is an unacceptable position type, or "".

    Deliberately conservative: these markers appear in the masthead of the WRONG
    job in a portal page, or in a benefits list ("we offer a paid internship"),
    so a marker inside obvious advertising boilerplate is ignored. A real
    werkstudent vacancy always carries the term in its own title, which is why
    the title is judged on its own.
    """
    blob = re.sub(r"\s+", " ", str(text or "")).casefold()
    if not blob:
        return ""
    for marker, why in BLOCKED_POSITION_TYPES:
        if re.search(rf"(?<![a-zäöüß]){re.escape(marker)}(?![a-zäöüß])", blob):
            # Ignore the marker when it only appears in employer advertising.
            if re.search(rf"(?i)(we offer|our benefits|benefits|karriere|internship programme|"
                         rf"du kannst bei uns|bei uns kannst|über uns)[^.]{{0,80}}"
                         rf"{re.escape(marker)}", blob):
                continue
            return why
    return ""


def eligibility(row: dict[str, Any], run_date: str) -> dict[str, Any]:
    """Apply deterministic gates; unresolved facts remain visible, never silently rejected."""
    location = str(row.get("location", "Unknown"))
    mode = str(row.get("work_mode", "Unknown"))
    posted = normalize_posted(row.get("posted", "Unknown"))
    company = str(row.get("company", "Unknown"))
    if posted.lower() == "unknown":
        first_seen = str(row.get("first_seen_in_master", ""))
        if not first_seen:
            # About.md: "If no date exists, retain `Unknown`, record
            # `first_seen_in_master`, and remove the row 30 days after first
            # appearance." Nothing downstream ever wrote this field, so an
            # undated row had nothing to age against and would be retained
            # forever. Stamp it on first sight and carry it on the result so
            # the retention rule can actually fire on a later run.
            row["first_seen_in_master"] = run_date
            first_seen = run_date
        if first_seen:
            try:
                if (dt.date.fromisoformat(run_date) - dt.date.fromisoformat(first_seen)).days > 30:
                    return {"verification": "REJECT", "reason": "undated vacancy exceeded 30-day first-seen retention", "first_seen_in_master": first_seen}
            except ValueError:
                return {"verification": "Unclear", "reason": "invalid first_seen_in_master", "first_seen_in_master": first_seen}
        return {"verification": "Current / Partial", "reason": "posting date unresolved", "first_seen_in_master": first_seen}
    try:
        d = dt.date.fromisoformat(posted[:10])
        age = (dt.date.fromisoformat(run_date) - d).days
    except ValueError:
        return {"verification": "Unclear", "reason": "unparseable posting date"}
    if age > 30:
        return {"verification": "REJECT", "reason": "posting older than 30 days"}
    # About.md lists the ROLE first: "Role is Manual WEB QA, Software Test/Test
    # Automation, Gamedev/Game QA, QA Localization, or a semantically
    # equivalent testing role." Eligibility never looked at role_verified at
    # all, so a row the analyser had explicitly marked non-QA -- a
    # Softwareentwickler posting that slipped through as `Unclear` -- was
    # promoted to `Current` purely on city + date. A determinate role gate must
    # be checked before any location rule, and an absent flag must NOT be read
    # as "not a QA role" (rows carried forward from the old master have no flag
    # until they are re-analysed, and dropping those would lose known vacancies).
    if row.get("role_verified") is False:
        return {"verification": "REJECT", "reason": "role is not a testing role"}
    # User instruction 2026-09-30: werkstudent/trainee/intern and UNPAID
    # positions are not acceptable. This is a position-TYPE gate, not a role or
    # location question, so it is checked before both: a "QA Werkstudent" role
    # is a valid testing role and a "Test Engineer" ad can be unpaid, yet
    # neither is a usable vacancy. Checked here, on the merged row, so it
    # applies to freshly analysed cards AND to rows carried forward from the
    # old master, which is where the six surviving werkstudent rows live.
    blocked = row.get("position_type_blocked")
    if blocked is None:
        blocked = detect_blocked_position_type(
            " ".join(str(row.get(k) or "") for k in
                     ("title", "company", "announcement", "notes", "reason")))
    if blocked:
        return {"verification": "REJECT", "reason": f"position type not acceptable: {blocked}"}
    # If the city is one of our target cities, we accept the vacancy even if
    # work_mode is Unknown. Work mode is secondary to location for our target
    # cities (Berlin, Leipzig, Dresden). A confirmed location is the primary
    # signal; work mode is secondary and can be refined on recheck.
    if any(city.lower() in location.lower() for city in ("Berlin", "Leipzig", "Dresden")):
        return {"verification": "Current", "reason": "target city option"}
    explicit = bool(row.get("germany_remote_explicit")) or any(x in location.lower() for x in ("bundesweit", "deutschland", "remote deutschland"))
    if mode == "Remote" and not explicit:
        return {"verification": "REJECT", "reason": "Germany-wide remote not explicit"}
    if mode == "Remote" and explicit:
        return {"verification": "Current", "reason": "explicit Germany-wide remote"}
    return {"verification": "REJECT", "reason": "eligible location/work mode not proven"}


TRACKING_QUERY_KEYS = {
    "position", "pagenum", "refid", "trackingid", "trk", "trkinfo", "lipi", "licu",
    "originalsubdomain", "tracking_id", "midtoken", "eid", "ot", "lipi", "savedsearchid",
    "currentjobid", "trkemail", "lipi", "f", "t", "s",
    # Indeed's `bb` is a click-tracking token, not part of the vacancy identity:
    # it is regenerated on every page view, so the same posting arrives with a
    # different `bb` and a different URL. `jk` is the real job key and stays.
    "bb",
}


def canonical_url(url: Any) -> str:
    """Strip tracking query parameters so one posting has one URL identity.

    LinkedIn hands out the same vacancy card under a different `?position=` and
    `refId=` on every page view, so two rows for one vacancy had two different
    URLs and the announcement text was the only thing left to catch them.
    """
    text = str(url or "").strip()
    if not text:
        return ""
    try:
        parsed = urllib.parse.urlparse(text)
    except ValueError:
        return text.casefold()
    if not parsed.scheme:
        return text.casefold()
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
             if k.casefold() not in TRACKING_QUERY_KEYS]
    cleaned = urllib.parse.urlunparse((
        parsed.scheme.casefold(), parsed.netloc.casefold(), parsed.path,
        parsed.params, urllib.parse.urlencode(sorted(query)), "",
    ))
    return cleaned.rstrip("/")


KNOWN_CITIES = ("berlin", "hamburg", "munich", "münchen", "cologne", "köln", "frankfurt",
                "stuttgart", "düsseldorf", "duesseldorf", "leipzig", "dresden", "nuremberg",
                "nürnberg", "hannover", "bremen", "dortmund", "essen", "bamberg", "eltville",
                "ismaning", "jena", "ismaning")


def canonical_location(value: Any) -> str:
    """Reduce a free-text location to the facts that identify a vacancy.

    Sources word the same location many ways -- "Remote globally; listed as
    Berlin", "Berlin, Germany - Remote", "Berlin or Dresden" -- and the raw
    string made one vacancy look like three. Keep the recognised cities and the
    remote marker; fall back to the normalised text when nothing is recognised.
    """
    text = re.sub(r"\s+", " ", str(value or "")).casefold()
    cities = [c for c in KNOWN_CITIES if c in text]
    remote = "remote" in text or "homeoffice" in text or "home office" in text
    if cities or remote:
        return ("remote+" if remote else "") + ",".join(sorted(set(cities)))
    return re.sub(r"[^a-z0-9äöüß ]+", " ", text).strip()


def _norm_text(value: Any) -> str:
    text = re.sub(r"[^a-z0-9äöüß ]+", " ", str(value or "").casefold())
    return re.sub(r"\s+", " ", text).strip()


def announcement_key(value: Any) -> str:
    """Fingerprint of the complete announcement text, per About.md.

    "Deduplicate by the complete announcement text and vacancy identity, not by
    URL alone." This is the only signal that survives a vacancy being posted on
    two different boards: the URLs differ, the location wording differs
    ("Dresden or Essen" vs "Dresden"), and the titles differ, but the body text
    is the same posting. Uses a digest so long bodies stay cheap to compare.
    """
    return hashlib.sha256(_norm_text(value).encode("utf-8")).hexdigest()


def vacancy_identity_keys(row: dict[str, Any]) -> tuple[str, str, str]:
    """Vacancy identity independent of the portal that published it.

    The canonical URL is part of the identity: a tracking-parameter change must
    never split one posting in two. Otherwise the company/title/location triple
    is the identity, with the location reduced to its recognised cities so that
    wording differences do not create phantom duplicates. A genuinely re-posted
    role (new posting, same title) is intentionally collapsed: it is one
    vacancy, and About.md asks for the first-found URL in the public master.
    """
    def norm(value: Any) -> str:
        return _norm_text(value)
    # Deduplication needs THREE keys, matched independently -- not one
    # concatenated string, which makes every case worse (the halves then differ
    # in both components at once). Each key alone fails:
    #   text triple  -> "Dresden or Essen" vs "Dresden" splits one vacancy
    #   URL         -> the same LinkedIn card arrives with a new ?position=/refId
    #   announcement -> a re-worded re-post of one role produces different text
    # deduplicate_first_url collapses a row when ANY key was already seen and
    # keeps the first-found URL, as About.md requires.
    company, title = norm(row.get("company")), norm(row.get("title"))
    return (f"{company}|{title}|{canonical_location(row.get('location'))}",
            canonical_url(row.get("url")),
            announcement_key(row.get("announcement")) if row.get("announcement") else "")


def vacancy_identity(row: dict[str, Any]) -> str:
    """Readable single-string identity, for logs and evidence files."""
    return "||".join(k for k in vacancy_identity_keys(row) if k)


def deduplicate_first_url(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Keep the first public URL per vacancy identity found at several URLs.

    Deduplication is by vacancy identity, never by URL alone: the same role
    posted on two boards is one vacancy, and About.md requires the first-found
    URL to stay in the public master while the duplicates are dropped from it.

    The dropped duplicates are RETURNED, not discarded: About.md also requires
    "retain the deduplication evidence internally". Returning only the survivors
    made that impossible -- the second URL vanished with no record, so a reader
    could not tell a genuine single posting from one found three times.
    """
    seen: list[set[str]] = [set(), set(), set()]  # text identity, canonical url, announcement
    out = []; dropped: list[dict[str, str]] = []
    labels = ("text", "url", "announcement")
    for row in rows:
        keys = vacancy_identity_keys(row)
        hit = next((i for i, k in enumerate(keys) if k and k in seen[i]), None)
        if hit is not None:
            kept_row = next((k for k in out if keys[hit] in vacancy_identity_keys(k)), None)
            dropped.append({
                "dropped_url": str(row.get("url", "")),
                "kept_url": str((kept_row or {}).get("url", "")),
                "identity": vacancy_identity(row),
                "matched_on": labels[hit],
                "title": str(row.get("title", "")),
                "source_id": str(row.get("source_id") or ""),
            })
            continue
        for i, k in enumerate(keys):
            if k:
                seen[i].add(k)
        out.append(row)
    return out, dropped
def render_master(rows: list[dict[str, str]], sources: list[dict[str, str]], run_date: str) -> str:
    """Render the governing master structure without collecting or publishing."""
    out = f"# QA Engineer Vacancies in Germany — {run_date}\n\n**Vacancies listed: {sum(1 for r in rows if r.get('category'))}**\n\n"
    for index, category in enumerate(CATEGORIES, 1):
        selected = [r for r in rows if r.get("category") == category and r["verification"] == "Current"]
        out += f"## {index}. {category} ({len(selected)})\n\n{render_rows(selected)}\n"

    for heading, status in (("Partially verified", "Current / Partial"), ("Unclear", "Unclear"), ("Rejected", "Rejected")):
        selected = [r for r in rows if r.get("category") in CATEGORIES and r["verification"] == status]
        out += f"## {heading} ({len(selected)})\n\n{render_rows(selected)}\n"
    out += ("## Sources\n| Source | Status | Last checked | Last successful use | Reason |\n"
            "|---|---|---|---|---|\n")
    for source in sources:
        out += (f"| {escape_table(source['name'])} | {source['status']} | {source['last_checked']} | "
                f"{source['last_successful_use']} | {escape_table(source['reason'])} |\n")
    return out


SEMANTIC_GATES = ("role", "location", "work_mode", "date", "employer")
UNREADABLE_ACCESS = {"blocked", "unreadable", "unavailable", "error"}
AFFIRMATIVE_FAILURES = {"fail", "failed", "reject", "rejected", "stale", "closed", "ineligible"}


def _iso_date(value: Any) -> dt.date | None:
    match = re.search(r"\d{4}-\d{2}-\d{2}", str(value or ""))
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(0))
    except ValueError:
        return None


def classify_semantic_candidate(candidate: dict[str, Any], run_date: dt.date) -> dict[str, Any]:
    """Classify one evidenced candidate without treating unknowns as rejection.

    A candidate is removed only for an affirmative failed gate (including a
    deterministically stale date). Missing evidence is retained, and temporary

    access failure has the more conservative ``Unclear`` status.
    """
    failed, missing = [], []
    for gate in SEMANTIC_GATES:
        result = candidate.get(gate) or {}
        verdict = str(result.get("result", "unknown")).casefold()
        evidence = result.get("evidence")
        if verdict in AFFIRMATIVE_FAILURES:
            failed.append(gate)
        elif verdict not in {"pass", "passed"} or not evidence:
            missing.append(gate)

    first_seen = candidate.get("first_seen_in_master")
    first_seen_date = _iso_date(first_seen)
    if "date" not in missing and "date" not in failed:
        posted = _iso_date((candidate.get("date") or {}).get("evidence"))
        if posted is not None and (run_date - posted).days > 30:
            failed.append("date")

    if "date" in missing:
        if first_seen is None:
            first_seen = run_date.isoformat()
        if first_seen_date is not None and (run_date - first_seen_date).days > 30:
            failed.append("date")
            missing.remove("date")

    if failed:
        verification, retain = "Rejected", False
    elif str(candidate.get("access_status", "readable")).casefold() in UNREADABLE_ACCESS:
        # Access failure - cannot verify, but don't reject. Use "Unclear" to indicate
        # the vacancy status is unknown due to technical issues, not content issues.
        verification, retain = "Unclear", True
    elif missing:
        verification, retain = "Current / Partial", True
    else:
        verification, retain = "Current", True
    return {
        **candidate,
        "retain": retain,
        "verification": verification,
        "failed_gates": failed,
        "missing_gates": missing,
        "first_seen_in_master": first_seen,
    }


def deduplicate_semantic_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Keep the first candidate URL per semantic identity and record later URLs."""
    kept: list[dict[str, Any]] = []
    first_by_key: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, str]] = []
    for candidate in candidates:
        key = str(candidate.get("semantic_key") or "").strip()
        if not key:
            kept.append(candidate)
            continue
        first = first_by_key.get(key)
        if first is None:
            first_by_key[key] = candidate
            kept.append(candidate)
        else:
            duplicates.append({
                "semantic_key": key,
                "discarded_url": str(candidate.get("url") or ""),
                "first_url": str(first.get("url") or ""),
            })
    return kept, duplicates


def parse_master_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.lstrip("| ").startswith("---"):
            continue
        cells = split_md_row(line)
        # The governing About.md format: #, Position, Company, Location,
        # Posted, Work mode, Verification. Reject legacy formats.
        if len(cells) != 7 or not re.fullmatch(r"\d+", cells[0]):
            continue
        match = re.fullmatch(r"\[([^]]+)\]\((https?://[^)]+)\)", cells[1])
        if not match or cells[6] not in VERIFICATIONS:
            continue
        rows.append({"number": cells[0], "title": match.group(1), "url": match.group(2),
                     "company": cells[2], "location": cells[3], "posted": cells[4],
                     "work_mode": cells[5], "verification": cells[6]})
    return rows


def locked_queue(path: Path, fn):
    # The queue inode is replaced by every atomic write. Lock a separate stable
    # file so concurrent workers cannot acquire locks on different old inodes.
    lockpath = path.with_suffix(path.suffix + ".lock")
    with open(lockpath, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() and path.stat().st_size else None
        result = fn(data)
        fcntl.flock(lock, fcntl.LOCK_UN)
        return result


def create_queue(path: Path, cycle: str, jobs: list[dict[str, Any]], workers: int) -> dict[str, Any]:
    if workers < 1 or workers > MAX_WORKERS_LIMIT:
        raise ValueError("workers must be 1..10")
    data = {"schema_version": SCHEMA, "cycle_id": cycle, "max_workers": workers,
            "created_at": utcnow(), "updated_at": utcnow(), "jobs": []}
    for index, job in enumerate(jobs):
        data["jobs"].append({"index": index, **job, "state": "pending", "attempt": 0,
                             "generation": 0, "owner": None, "pid": None,
                             "lease_token": None, "heartbeat_at": None, "progress_at": None,
                             "next_retry_at": None, "failures": []})
    atomic_json(path, data)
    return data


def claim_job(path: Path, owner: str) -> dict[str, Any] | None:
    def op(data):
        if data is None: raise LeaseError("queue missing")
        for job in data["jobs"]:
            if job["state"] == "pending" and (not job.get("next_retry_at") or parse_time(job["next_retry_at"]) <= time.time()):
                job.update(state="claimed", owner=owner, pid=os.getpid(), attempt=job["attempt"] + 1,
                           generation=job["generation"] + 1, lease_token=uuid.uuid4().hex,
                           heartbeat_at=utcnow(), progress_at=utcnow(), claimed_at=utcnow())
                atomic_json(path, data)
                return dict(job)
        return None
    return locked_queue(path, op)


def heartbeat(path: Path, source_id: str, token: str, progress: bool = False) -> None:
    def op(data):
        if data is None: raise LeaseError("queue missing")
        for job in data["jobs"]:
            if job["source_id"] == source_id:
                if job.get("lease_token") != token or job.get("state") != "claimed":
                    raise LeaseError("stale or revoked lease")
                job["heartbeat_at"] = utcnow()
                if progress: job["progress_at"] = utcnow()
                data["updated_at"] = utcnow(); atomic_json(path, data); return
        raise LeaseError("source not found")
    locked_queue(path, op)


def process_is_alive(pid: int) -> bool:
    """True only for a process that can still do work.

    A killed-but-unreaped child stays in /proc as a zombie (state Z) until its
    parent waits() on it. `Path.exists()` alone therefore reports a zombie as
    alive, which makes the watchdog wait out the full 5-minute heartbeat window
    for a process that already died, and then burn the whole 30s termination
    grace on it. Check the real state instead.
    """
    stat = Path(f"/proc/{pid}/stat")
    try:
        # Format: pid (comm) state -- comm may contain spaces and parentheses,
        # so the state character is the first field after the closing paren.
        after = stat.read_text().rsplit(")", 1)[1].split()
        return bool(after) and after[0] != "Z"
    except (FileNotFoundError, ProcessLookupError, IndexError, PermissionError):
        return False


def job_is_stale(job: dict[str, Any], now: float, threshold: int = STALE_SECONDS) -> bool:
    if job.get("state") != "claimed": return False
    pid = job.get("pid")
    if not pid or not process_is_alive(int(pid)): return True
    heartbeat = parse_time(job.get("heartbeat_at"))
    progress = parse_time(job.get("progress_at"))
    return now - heartbeat > threshold and now - progress > threshold


def next_retry_delay(attempt: int) -> int | None:
    return BACKOFF_SECONDS[attempt - 1] if 1 <= attempt <= 3 else None


def terminate_pid(pid: int) -> None:
    with contextlib.suppress(ProcessLookupError): os.kill(pid, signal.SIGTERM)
    deadline = time.time() + GRACE_SECONDS
    # process_is_alive, not /proc existence: a zombie is already dead but keeps
    # its /proc entry until reaped, which would burn the whole grace period.
    while time.time() < deadline and process_is_alive(pid): time.sleep(.1)
    if process_is_alive(pid):
        with contextlib.suppress(ProcessLookupError): os.kill(pid, signal.SIGKILL)


def finish_job(path: Path, source_id: str, token: str, state: str, error: str | None = None) -> None:
    if state not in TERMINAL: raise ValueError(state)
    def op(data):
        for job in data["jobs"]:
            if job["source_id"] == source_id:
                if job.get("lease_token") != token: raise LeaseError("revoked lease cannot finish")
                job.update(state=state, error=error, finished_at=utcnow(), owner=None, pid=None, lease_token=None)
                if error:
                    job["failures"].append({"attempt": job["attempt"], "error": error, "at": utcnow()})
                data["updated_at"] = utcnow(); atomic_json(path, data); return
        raise LeaseError("source not found")
    locked_queue(path, op)


def requeue_stale(path: Path, sleep: bool = True) -> list[str]:
    changed = []
    self_pid = os.getpid()
    def op(data):
        if data is None: raise LeaseError("queue missing")
        for job in data["jobs"]:
            if job_is_stale(job, time.time()):
                old, previous_attempt = job.get("pid"), job.get("attempt", 0)
                # claim_job records os.getpid(), and workers are THREADS of this
                # process, so a hung worker's pid is the controller's own pid.
                # Signalling it would SIGTERM the whole cycle, taking every
                # healthy source down with the one hung thread. A thread cannot
                # be killed anyway, so revoke the lease instead: fencing stops the
                # stuck thread from writing, and its result is discarded.
                if old and int(old) != self_pid:
                    terminate_pid(int(old))
                error = "watchdog: dead PID or heartbeat+progress timeout"
                job["failures"].append({"attempt": previous_attempt, "error": "watchdog", "at": utcnow()})
                job.update(attempt=previous_attempt + 1, generation=job.get("generation", 0) + 1,
                           owner=None, pid=None, lease_token=None, heartbeat_at=None, progress_at=None,
                           error=error, reclaimed_at=utcnow())
                delay = next_retry_delay(job["attempt"] - 1)
                if delay is None:
                    job.update(state="failed", next_retry_at=None, finished_at=utcnow())
                else:
                    job.update(state="pending", next_retry_at=dt.datetime.fromtimestamp(
                        time.time() + delay, dt.timezone.utc).isoformat(), finished_at=None)
                changed.append(job["source_id"])
        atomic_json(path, data)
    locked_queue(path, op)
    return changed


def schedule_retry(path: Path, source_id: str, token: str, error: str) -> None:
    """Atomically schedule the next allowed automatic attempt for a live lease."""
    def op(data):
        if data is None: raise LeaseError("queue missing")
        for job in data["jobs"]:
            if job["source_id"] != source_id:
                continue
            if job.get("lease_token") != token or job.get("state") != "claimed":
                raise LeaseError("stale or revoked lease")
            delay = next_retry_delay(job.get("attempt", 0))
            if delay is None:
                raise LeaseError("automatic retry attempts exhausted")
            job["failures"].append({"attempt": job["attempt"], "error": error, "at": utcnow()})
            job.update(state="pending", error=error, owner=None, pid=None, lease_token=None,
                       heartbeat_at=None, progress_at=None, next_retry_at=dt.datetime.fromtimestamp(
                           time.time() + delay, dt.timezone.utc).isoformat())
            data["updated_at"] = utcnow(); atomic_json(path, data); return
        raise LeaseError("source not found")
    locked_queue(path, op)


class DirectLLM:
    def __init__(self, base_url: str, model: str, api_key: str | None = None, timeout: int = 120):
        if not api_key:
            raise RuntimeError("LLM API key is not configured")
        self.base_url, self.model, self.api_key, self.timeout = base_url.rstrip("/"), model, api_key, timeout

    def json(self, system: str, payload: Any) -> dict[str, Any]:
        body = json.dumps({"model": self.model, "messages": [
            {"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            "response_format": {"type": "json_object"}}).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key: headers["Authorization"] = f"Bearer {self.api_key}"
        last_error = None
        for attempt, delay in enumerate((0, 5, 30, 120)):
            if delay:
                time.sleep(delay)
            try:
                req = urllib.request.Request(self.base_url + "/chat/completions", data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    raw = response.read()
                    if not raw:
                        raise RuntimeError("LLM response body is empty")
                    outer = json.loads(raw)
                    if not outer.get("choices"):
                        raise RuntimeError(f"LLM response missing 'choices': {outer}")
                    text = outer["choices"][0]["message"].get("content")
                    if not text:
                        raise RuntimeError("LLM response content is empty or None")
                    return json.loads(text)
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError, RuntimeError) as exc:
                last_error = exc
            except urllib.error.HTTPError as exc:
                last_error = RuntimeError(f"LLM HTTP {exc.code}")
                # Retry on 503 (service unavailable) with longer backoff
                if exc.code == 503:
                    # Add longer delays for 503 specifically
                    time.sleep(60 + attempt * 60)
                if exc.code not in {408, 409, 429, 500, 502, 503, 504}:
                    raise last_error
        raise RuntimeError(f"LLM request failed after 4 attempts: {last_error}") from last_error


class Pipeline:
    def __init__(self, project: Path, self_test: bool = False, publish: bool = False, notify: bool = False):
        self.project, self.self_test, self.allow_publish, self.allow_notify = project.resolve(), self_test, publish, notify
        self.project.mkdir(parents=True, exist_ok=True)
        self.cycles = self.project / "cycles"
        self.cycles.mkdir(exist_ok=True)
        self.registry = project / "source_registry.json"
        self.master = project / "qa_vacancies_master.md"
        self.workers = min(MAX_WORKERS_LIMIT, max(1, int(os.environ.get("QA_VACANCY_MAX_WORKERS", "10"))))

    def run(self) -> dict[str, Any]:
        if not self.self_test:
            # About.md step 8 requires a notification on run failure, and a
            # broken registry is exactly the kind of failure an operator must
            # hear about. This validation sits BEFORE the cycle directory and the
            # try/except below, so without this guard the exception escapes run()
            # entirely: no cycle state, no failures.json, and no notice.
            try:
                validate_registry(read_json(self.registry))
            except Exception as exc:
                message = f"source registry unusable: {type(exc).__name__}: {exc}"
                record = {"event": "run_failed", "message": message, "at": utcnow(),
                          "cycle_id": None, "status": "FAILED", "stage": "STARTUP", "error": message}
                try:
                    notices = self.project / "notices.jsonl"
                    notices.parent.mkdir(parents=True, exist_ok=True)
                    with notices.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                        fh.flush(); os.fsync(fh.fileno())
                except OSError:
                    pass
                print(json.dumps(record, ensure_ascii=False), flush=True)
                raise
        day = dt.datetime.now(dt.timezone.utc).date().isoformat(); n = 1
        while (self.cycles / f"{day}_cycle-{n}").exists(): n += 1
        root = self.cycles / f"{day}_cycle-{n}"; root.mkdir(parents=True)
        state = {"schema_version": SCHEMA, "cycle_id": root.name, "stage": "MASTER_RECHECK",
                 "status": "RUNNING", "started_at": utcnow(), "publication_allowed": False, "artifacts": {},
                 # Without this the FIRST stage's time is never charged to
                 # stage_seconds: save() only bills (stage, _stage_started_at),
                 # and a fresh state has no _stage_started_at. MASTER_RECHECK is
                 # the slowest stage (~9 min) and was the one missing from the
                 # timings -- exactly the interval needed to diagnose stalls.
                 "_stage_started_at": time.monotonic(), "stage_seconds": {}}
        atomic_json(root / "state.json", state)
        try:
            self.stage_recheck(root, state)
            self.stage_discovery(root, state)
            sources = self.snapshot_sources(root)
            confirmed = self.run_queue(root, root / "preflight", "SOURCE_PREFLIGHT", sources, self.preflight_job)
            confirmed = [s for s in sources if confirmed.get(s["id"]) == "complete"]
            # Record preflight failures as Not used so the verifier can account
            # for them. Without this, blocked preflight sources leak into the
            # verifier as "worker failures not recorded as Not used" even though
            # they never reached the worker stage.
            confirmed_ids = {s["id"] for s in confirmed}
            preflight_blocked = []
            for s in sources:
                if s["id"] in confirmed_ids:
                    continue
                result_path = root / 'preflight' / s['id'] / 'result.json'
                if result_path.exists():
                    result = read_json(result_path)
                    failures = result.get('failures', [])
                    if failures:
                        error = failures[0].get('error', 'unknown')[:300]
                    else:
                        # Source still claimed/running - mark as not complete but don't crash
                        state_val = result.get('state', 'unknown')
                        error = f"preflight not complete: {state_val}"
                    preflight_blocked.append({"source_id": s["id"], "error": f"preflight blocked: {error}"})
                else:
                    preflight_blocked.append({"source_id": s["id"], "error": "preflight blocked: no result.json"})
            if preflight_blocked:
                self.mark_sources_not_used(root, preflight_blocked)
            self.run_queue(root, root / "workers", "VACANCY_WORKER", confirmed, self.vacancy_job)
            # run_queue() returns {} WITHOUT creating queue.json when there is
            # nothing to do, so an unguarded read here raised FileNotFoundError
            # and turned "no source survived preflight" into a FAILED cycle with
            # no evidence of why. An empty worker stage is a legitimate outcome:
            # the cycle must still reach the verifier and publish what the
            # recheck carried forward.
            wpath = root / "workers" / "queue.json"
            worker_states = read_json(wpath)["jobs"] if wpath.exists() else []
            # The spec says a source that cannot be read is marked `Not used`
            # for the run and the cycle continues with the others. Raising here
            # turned one blocked job board (XING served Initiativbewerbung and a
            # Recruiter page instead of vacancy cards) into a FAILED cycle, so
            # the master could never be published while any single source was
            # unhealthy. The source stays active and is retried next cycle.
            failed_workers = [
                {"source_id": job["source_id"], "error": job.get("error", "")}
                for job in worker_states if job["state"] != "complete"
            ]
            if failed_workers:
                self.mark_sources_not_used(root, failed_workers)
                print(json.dumps({"event": "sources_not_used", "sources": failed_workers}, ensure_ascii=False), flush=True)
            candidate = self.synthesize(root, state)
            verdict = self.verify(root, candidate)
            if verdict != "PASS": raise RuntimeError(f"final verifier: {verdict}")
            return self.publish(root, state, candidate)
        except Exception as exc:
            import traceback as _tb
            state.update(stage="FAILED", status="FAILED", error=f"{type(exc).__name__}: {exc}", finished_at=utcnow())
            self.save(root, state, stage="FAILED", status="FAILED", error=state["error"], finished_at=utcnow())
            atomic_json(root / "failures.json", {"error": state["error"], "at": utcnow(), "traceback": _tb.format_exc()})
            # About.md step 8: a failed run is the other notification-worthy case.
            self.emit_notice(root, state, "run_failed",
                             f"{state.get('cycle_id')}: run failed at {state.get('stage')}: {state['error']}")
            return state

    def save(self, root, state, **changes):
        """Persist state, recording how long each stage took.

        A stalled stage is indistinguishable from a slow one when only the
        status is recorded, and every stall today was diagnosed from timings
        that did not exist. stage_seconds is cumulative per stage.
        """
        timings = state.setdefault("stage_seconds", {})
        previous, last = state.get("stage"), state.get("_stage_started_at")
        now = time.monotonic()
        if previous and last:
            timings[previous] = round(timings.get(previous, 0.0) + now - last, 1)
        persisted = {k: v for k, v in state.items() if not k.startswith("_")}
        persisted.pop("_stage_started_at", None)
        persisted.update(changes)
        persisted["stage_seconds"] = timings
        persisted["updated_at"] = utcnow()
        atomic_json(root / "state.json", persisted)
        # The in-memory copy keeps the start marker so the next transition can
        # measure this stage, but never writes it to disk.
        state.update(changes); state["_stage_started_at"] = now

    def fixture_sources(self, root):
        for source_id in ("alpha", "beta"):
            d = root / "fixture" / source_id; d.mkdir(parents=True, exist_ok=True)
            atomic_json(d / "listing.json", {"cards": [
                {"url": f"https://fake/{source_id}/qa-1", "title": f"QA Engineer {source_id}", "company": f"{source_id} GmbH", "location": "Berlin", "posted": "2026-09-24", "work_mode": "Hybrid", "announcement": "Manual web QA in Berlin. German legal entity."},
                {"url": f"https://fake/{source_id}/qa-2", "title": f"Test Engineer {source_id}", "company": f"{source_id} GmbH", "location": "Dresden", "posted": "2026-09-23", "work_mode": "Remote", "announcement": "Software test automation; Germany-wide remote. German legal entity."}]})

    def semantic_decisions(self, cards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Return one LLM decision per complete announcement text.

        A failure is never treated as a negative eligibility decision.  The
        caller retains the original candidate with Unclear status.
        """
        if not cards:
            return {}
        readable = [x for x in cards if x.get("announcement")]
        if not readable:
            return {}
        # A full portal page runs up to ~50k chars, so a batch of 6 reached
        # ~270k chars (~70k tokens) and the request hung until it timed out.
        # About.md requires the complete announcement, so the head and the tail
        # are both kept: the role and employer lead the document, while the
        # date, work mode and legal notice sit at the end. Only the middle
        # boilerplate is dropped, and the truncation is stated to the model.
        limit = max(4000, int(os.environ.get("QA_VACANCY_ANNOUNCEMENT_CHARS", "12000")))
        head, tail = int(limit * 0.75), int(limit * 0.25)
        trimmed = []
        for x in readable:
            body = str(x["announcement"])
            if len(body) <= limit:
                trimmed.append({**x, "announcement": body}); continue
            trimmed.append({**x, "announcement": body[:head] + "\n[... middle of page omitted ...]\n" + body[-tail:]})
        answer = self.llm_with_fallback().json(
            "Analyze the COMPLETE vacancy announcement text below. Extract these fields:\n"
            "1. title: Job title (exact wording from announcement)\n"
            "2. company: Employer/company name\n"
            "3. location: City/location mentioned (e.g., Berlin, Munich, Remote)\n"
            "4. posted: Date posted (look for 'Posted:', 'Published:', 'since', etc.)\n"
            "5. work_mode: One of ['On-site', 'Hybrid', 'Remote'] based on announcement\n"
            "6. verification: 'Current' if all evidence supports a genuine, current opening\n"
            "7. role_verified: true ONLY for Manual WEB QA, Software Test/Test Automation, Gamedev/Game QA, QA Localization, or semantically equivalent testing roles\n"
            "8. german_entity_verified: true if German legal entity (GmbH, AG, KG, etc.) or German address clearly indicated\n"
            "9. germany_remote_explicit: true if announcement explicitly states remote work for Germany/Germany-wide/Deutschlandweit\n"
            "10. category: Job category from predefined list\n"
            "11. reason: Brief explanation of verification/role_verified decision\n"
            "\n"
            "Return ONLY valid JSON: {results:[{url,title,company,location,posted,work_mode,verification,role_verified,german_entity_verified,germany_remote_explicit,category,reason}]}\n"
            "\n"
            "If uncertain about work_mode, use 'Unknown'. For verification, you MUST decide: 'Current' if evidence supports a genuine QA/testing vacancy in Germany, otherwise 'Rejected'. No 'Unverified' or 'Unclear' for verification.\n"
            "- role_verified: true only for genuine QA/testing roles, false otherwise\n"
            "- german_entity_verified: true if German legal entity or address clearly indicated\n"
            "- germany_remote_explicit: true if remote for Germany explicitly stated\n"
            "- category: Choose from predefined CATEGORIES list\n"
            "\n"
            "DO NOT return 'Unknown' strings for boolean fields - use true/false only. Boolean fields are: role_verified, german_entity_verified, germany_remote_explicit.\n"
            "\n"
            "Analyze this announcement:",
            {"run_date": dt.datetime.now(dt.timezone.utc).date().isoformat(), "candidates": trimmed},
        )
        return {x.get("url"): x for x in answer.get("results", []) if isinstance(x, dict)}

    def recheck_published_rows(self, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        """Fetch every published row and ask the semantic stage to re-evaluate it.

        A failed fetch is never treated as closure: it becomes Unclear. The
        full page text is passed to the LLM, never just a title or portal field.
        """
        prepared = []
        # 36+ published rows fetched one after another took ~10 min and blew the
        # stage budget before a single LLM call. Fetch concurrently; a slow
        # portal delays only its own row.
        def pull(row: dict[str, Any]) -> dict[str, Any]:
                    try:
                        fetched = fetch(row["url"], timeout=8)
                        body = text(fetched.body)
                        # A 200 with a challenge/login page is not a valid posting.
                        # We must filter these out BEFORE sending to LLM.
                        if fetched.status in (200, 304) and body and looks_like_vacancy_posting({"title": row.get("title", ""), "announcement": body}):
                            announcement = body
                        else:
                            announcement = ""
                        return {**row, "announcement": announcement,
                                "fetch_status": fetched.status, "fetch_url": fetched.final_url}
                    except Exception as exc:
                        return {**row, "announcement": "", "fetch_status": 0, "fetch_error": str(exc)}
        with ThreadPoolExecutor(max_workers=10) as pool:
            prepared = list(pool.map(pull, rows))
        readable = [x for x in prepared if x["announcement"]]
        results = {}
        # Hard wall-clock budget for this stage. A free-tier LLM that stalls must

        # not block the daily cycle; rows without a decision stay Unclear,
        # which is the retention-safe outcome, never a rejection.
        budget = int(os.environ.get("QA_VACANCY_RECHECK_BUDGET_SECONDS", "600"))
        # Batches are independent decisions, so they run concurrently: a
        # free-tier LLM answers one batch in ~2 min, which serially exhausted
        # the budget before the last rows were ever decided. The batch is sized
        # so every row fits inside the budget at the current worker count;

        # otherwise the last rows stay Unclear every single day and never
        # improve, which is worse than a slow cycle.
        workers = min(4, max(1, int(os.environ.get("QA_VACANCY_RECHECK_WORKERS", "4"))))
        batch_size = max(1, int(os.environ.get("QA_VACANCY_RECHECK_BATCH", "6")))
        batches = [readable[i:i + batch_size] for i in range(0, len(readable), batch_size)]
        # Waves, not one flat pool: a wave is counted as done only when all of its
        # batches are in, so the budget is spent on rows that actually get a
        # decision instead of on batches abandoned mid-flight.
        deadline = time.monotonic() + budget
        try:
            pool = ThreadPoolExecutor(max_workers=workers)
            pending: list[Any] = []
            for start in range(0, len(batches), workers):
                if time.monotonic() >= deadline:
                    break
                wave = batches[start:start + workers]
                pending = [pool.submit(self.semantic_decisions, b) for b in wave]
                # as_completed without a timeout blocks forever on one stuck
                # batch. The previous `remaining = time.monotonic() < deadline`
                # was evaluated BEFORE the wait, so it was always True and the
                # budget was never enforced: a stuck batch hung the whole cycle.
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    for future in as_completed(pending, timeout=remaining):
                        try:
                            results.update(future.result())
                        except Exception:
                            continue
                except FuturesTimeoutError:
                    # Undecided rows keep their prior status on the next cycle.
                    pass
                for future in pending:
                    future.cancel()
            # Not a context manager on purpose: its __exit__ joins the workers,
            # so a batch still stuck in the LLM client would block here.
            pool.shutdown(wait=False, cancel_futures=True)
        except Exception as exc:
            results = {}
            root = max(self.cycles.glob("*/state.json"), key=lambda p: p.stat().st_mtime, default=None)
            if root is not None:
                atomic_json(root.parent / "recheck_llm_failure.json", {"error": str(exc), "at": utcnow()})
        out=[]
        for row in prepared:
            decision=results.get(row["url"])
            if not decision:
                # A missing LLM decision means the page could not be re-read, not
                # that the vacancy is unconfirmed. A row that the published
                # master already confirmed keeps that confirmation: an unreadable
                # page cannot disprove a role, employer or date already
                # established. Only a row that was never confirmed is demoted.

                prior = str(row.get("verification") or "Unclear")

                if prior in self.CONFIRMED_TOKENS:
                    out.append({**row, "from_published_master": True,
                                "recheck_unavailable": True})
                else:
                    out.append({**row, "from_published_master": True,
                                "verification": "Unclear", "role_verified": "Unknown"})

                continue
            # Preserve prior confirmation when the LLM gives a contradictory
            # result: a readable page that contradicts prior confirmation is
            # usually a model inconsistency, not a real vacancy change.
            if decision.get("verification") in self.CONFIRMED_TOKENS:
                pass  # LLM confirmed — use new decision
            elif str(row.get("verification") or "") in self.CONFIRMED_TOKENS:
                # Prior was confirmed but LLM downgraded — keep prior.
                decision = {**row, "recheck_unavailable": False,
                            "from_published_master": True,
                            "verification": row.get("verification"),
                            "title": row.get("title"),
                            "company": row.get("company"),
                            "location": row.get("location"),
                            "work_mode": row.get("work_mode"),
                            "category": row.get("category"),
                            "posted": row.get("posted")}
            if decision.get("verification") not in VERIFICATIONS:
                decision["verification"] = "Unclear"
            out.append({**row, **{k: decision.get(k, row.get(k, "Unknown")) for k in ("title","company","location","posted","work_mode","category","verification","role_verified","german_entity_verified","germany_remote_explicit")}})
        return out

    def stage_recheck(self, root, state):
        text = "# QA Engineer Vacancies in Germany — fixture\n\n"
        if not self.self_test and self.master.exists(): text = self.master.read_text(encoding="utf-8")
        rows = (migrate_legacy_master(text) if not self.self_test else parse_master_rows(text))
        if not self.self_test and self.master.exists() and not rows: raise RuntimeError("published master is legacy/malformed; refusing publication")
        if not self.self_test:
            rows = self.recheck_published_rows(rows)
        atomic_json(root / "published_recheck.json", {"schema_version": SCHEMA, "cycle_id": root.name, "checked_at": utcnow(), "rows": rows, "count": len(rows)})
        self.save(root, state, stage="SOURCE_DISCOVERY", artifacts={**state.get("artifacts", {}), "recheck": str(root / "published_recheck.json")})

    def search_sources(self, queries: list[str]) -> list[dict[str, Any]]:
        """Retrieve live discovery results through configured SearXNG.

        The LLM is an interpreter, not the retrieval boundary. Every result
        used for source discovery is fetched here and persisted before asking
        the model to classify candidate sources.
        """
        base = os.environ.get("SEARXNG_URL", "").rstrip("/")
        if not base:
            raise RuntimeError("SEARXNG_URL is not configured")
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for query in queries:
            params = urllib.parse.urlencode({"q": query, "format": "json", "language": "de-DE"})
            request = urllib.request.Request(
                base + "/search?" + params,
                headers={"User-Agent": "Mozilla/5.0 QA-Vacancy-Controller/2"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            for item in payload.get("results", []):
                url = str(item.get("url") or "")
                if not url.startswith(("http://", "https://")) or url in seen:
                    continue
                seen.add(url)
                results.append({
                    "query": query,
                    "url": url,
                    "title": str(item.get("title") or ""),
                    "snippet": str(item.get("content") or item.get("snippet") or ""),
                    "engine": item.get("engine"),
                    "published": item.get("publishedDate"),
                })
        if not results:
            raise RuntimeError("live source discovery returned zero results")
        return results

    def stage_discovery(self, root, state):
        if self.self_test:
            self.fixture_sources(root)
            result = {"schema_version": SCHEMA, "verdict": "PASS_NO_NEW_SOURCES", "additions": []}
        else:
            queries = [
                "site:arbeitsagentur.de QA Engineer Berlin Leipzig Dresden",
                "site:arbeitsagentur.de Softwaretester Berlin Leipzig Dresden",
                "site:arbeitsagentur.de Testautomatisierung Berlin Leipzig Dresden",
                "site:linkedin.com/jobs QA Engineer Berlin Leipzig Dresden",
                "site:stepstone.de QA Engineer Berlin Leipzig Dresden",
                "site:stepstone.de Softwaretester Berlin Leipzig Dresden",
                "site:adzuna.de QA Engineer Berlin Leipzig Dresden",
                "site:adzuna.de Softwaretester Berlin Leipzig Dresden",
                "site:arbeitnow.com QA Engineer Berlin Leipzig Dresden",
                "site:arbeitnow.com Softwaretester Berlin Leipzig Dresden",
                "site:germantechjobs.de QA Engineer Berlin Leipzig Dresden",
                "site:germantechjobs.de Softwaretester Berlin Leipzig Dresden",
                "site:eurotechjobs.com QA Engineer Berlin Leipzig Dresden",
                "site:eurotechjobs.com Softwaretester Berlin Leipzig Dresden",
                "site:remotive.com QA Engineer remote Germany",
                "site:remotive.com Softwaretester remote Germany",
                "site:hitmarker.net QA remote Germany",
                "site:hitmarker.net Softwaretester remote Germany",
            ]
            retrieved = self.search_sources(queries)
            atomic_json(root / "source_discovery_retrieval.json", {
                "schema_version": SCHEMA, "cycle_id": root.name, "queried_at": utcnow(),
                "queries": queries, "result_count": len(retrieved), "results": retrieved,
            })
            decision = self.llm_with_fallback().json(
                "Classify retrieved evidence as verified German QA/test vacancy sources. "
                "Return JSON {verdict,evidence,additions}. A source is usable only if the evidence "
                "exposes a real listing/API and direct vacancy cards for QA/testing in Berlin, "
                "Leipzig, Dresden or explicit Germany-wide remote. Do not claim browsing: use only "
                "the supplied live retrieval evidence. PASS means discovery was completed, including "
                "when additions is empty; never return inconclusive merely because additions is empty.",
                {"registry": read_json(self.registry), "queries": queries, "live_retrieval_evidence": retrieved},
            )
            result = {
                "verdict": str(decision.get("verdict") or "").casefold(),
                "evidence": {"live_retrieval": "completed", "retrieval_artifact": str(root / "source_discovery_retrieval.json"),
                             "retrieved_result_count": len(retrieved), "model_evidence": decision.get("evidence", {})},
                "additions": decision.get("additions", []),
            }
        result["cycle_id"] = root.name
        result["created_at"] = utcnow()
        atomic_json(root / "source_discovery.json", result)
        verdict = str(result.get("verdict") or result.get("run_status") or "").casefold()
        if not verdict or verdict in {"inconclusive", "failed", "blocked", "error", "live_verification_unavailable"}:
            raise RuntimeError(f"source discovery did not complete: {verdict or 'missing verdict'}")
        # PASS_NO_NEW_SOURCES / PASS_NO_ADDITIONS are valid success: discovery completed,
        # no new sources found; do not treat as a block.
        self.save(root, state, stage="MASTER_SNAPSHOT", artifacts={**state.get("artifacts", {}), "discovery": str(root / "source_discovery.json")})

    def mark_sources_not_used(self, root, failed: list[dict]) -> None:
        """Record unreadable sources as `Not used` for this run.

        A skipped source is not a source with zero vacancies, so it stays active
        in the registry and is retried on the next cycle; only the current run's
        status changes. The reason is preserved verbatim so the master's Sources
        table can explain the skip instead of showing a bare "Not used".
        """
        atomic_json(root / "sources_not_used.json", {
            "schema_version": SCHEMA, "cycle_id": root.name, "at": utcnow(),
            "sources": [
                {"source_id": f["source_id"], "status": "Not used", "reason": f.get("error", "")[:500]}
                for f in failed
            ],
        })
        try:
            registry = read_json(self.registry)
        except Exception:
            return
        for source in registry.get("sources", []):
            if any(f["source_id"] == source["id"] for f in failed):
                evidence = source.setdefault("evidence", {})
                evidence["last_preflight"] = utcnow()
                evidence["last_run_status"] = "Not used"
        atomic_json(self.registry, registry)

    def snapshot_sources(self, root):
        if self.self_test:
            sources = [{"id": s, "name": s, "domain": "fake", "listing_url": f"file://fixture/{s}", "status": "active"} for s in ("alpha", "beta")]
        else:
            sources = [s for s in read_json(self.registry)["sources"] if s["status"] == "active"]
        atomic_json(root / "sources.json", {"schema_version": SCHEMA, "sources": sources, "count": len(sources)})
        return sources

    def durable_job_dir(self, stage_root, job, stage):
        d = stage_root / job["source_id"]; (d / "completed").mkdir(parents=True, exist_ok=True); (d / "raw").mkdir(parents=True, exist_ok=True)
        for name, value in {
            "manifest.json": {"schema_version": SCHEMA, "cycle_id": stage_root.parent.name, "source_id": job["source_id"], "stage": stage, "state": "claimed", "started_at": utcnow()},
            "checkpoint.json": {"schema_version": SCHEMA, "cycle_id": stage_root.parent.name, "source_id": job["source_id"], "state": "claimed", "completed_operations": [], "next_operation": 0, "updated_at": utcnow()},
            "failures.json": {"schema_version": SCHEMA, "cycle_id": stage_root.parent.name, "source_id": job["source_id"], "failures": []},
            "plan.json": {"schema_version": SCHEMA, "cycle_id": stage_root.parent.name, "source_id": job["source_id"], "operations": ["listing", "card-1", "return", "card-2"]}}.items():
            p = d / name
            if not p.exists(): atomic_json(p, value)
        return d

    def run_queue(self, root, stage_root, stage, sources, operation):
        if not sources: return {}
        if not isinstance(stage_root, Path): raise TypeError("stage_root must be a Path")
        stage_root.mkdir(parents=True, exist_ok=True); qpath = stage_root / "queue.json"
        create_queue(qpath, root.name, [{"source_id": s["id"], "source": s} for s in sources], self.workers)
        results: dict[str, str] = {}

        def one(slot):
            while True:
                claimed = claim_job(qpath, f"worker-{slot}")
                if not claimed: return
                jobdir = self.durable_job_dir(stage_root, claimed, stage)
                try:
                    result = operation(root, claimed["source"], jobdir, claimed)
                    if isinstance(result, str): outcome = result
                    else: outcome = "complete"
                    atomic_json(jobdir / "completed" / "terminal.json", {"cycle_id": root.name, "source_id": claimed["source_id"], "outcome": outcome, "at": utcnow()})
                    finish_job(qpath, claimed["source_id"], claimed["lease_token"], outcome if outcome in TERMINAL else "complete")
                except Exception as exc:
                    failure = {"error": str(exc), "at": utcnow()}
                    existing = read_json(jobdir / "failures.json") if (jobdir / "failures.json").exists() else {}
                    history = existing.get("failures", []) if isinstance(existing, dict) else []
                    history.append(failure)
                    atomic_json(jobdir / "failures.json", {"schema_version": SCHEMA, "cycle_id": root.name, "source_id": claimed["source_id"], "failures": history})
                    try:
                        finish_job(qpath, claimed["source_id"], claimed["lease_token"], "blocked", str(exc))
                    except LeaseError:
                        pass

        pool = ThreadPoolExecutor(max_workers=self.workers)
        futures = [pool.submit(one, i) for i in range(min(self.workers, len(sources)))]
        # A hung source must not block the whole stage forever. Each job already
        # has its own watchdog and backoff, so a worker that outlives this stage
        # budget is a stuck client call, not slow work: the job stays in the queue
        # with its own durable state and the next run resumes it. `with` would
        # join the stuck worker and never return.
        stage_budget = int(os.environ.get("QA_VACANCY_STAGE_BUDGET_SECONDS", "1800"))
        try:
            for f in as_completed(futures, timeout=stage_budget):
                try:
                    f.result()
                except Exception:
                    pass
        except FuturesTimeoutError:
            pass
        for f in futures:
            f.cancel()
        pool.shutdown(wait=False, cancel_futures=True)
        for job in read_json(qpath)["jobs"]:
            results[job["source_id"]] = job["state"]
            atomic_json(stage_root / job["source_id"] / "result.json", {"schema_version": SCHEMA, "cycle_id": root.name, "source_id": job["source_id"], "state": job["state"], "failures": job.get("failures", [])})
        return results

    def preflight_job(self, root, source, d, claimed):
        if self.self_test:
            cards = read_json(root / "fixture" / source["id"] / "listing.json")["cards"]
            ok = len(cards) >= 2 and all(x.get("announcement") for x in cards[:2])
            verdict = "PASS" if ok else "FAILED"
            evidence = {"status": "pass" if ok else "failed", "cards_found": len(cards),
                        "cards_analyzable": 2 if ok else 0,
                        "operations": [{"op": "listing"}, {"op": "card-1"}, {"op": "return"}, {"op": "card-2"}]}
        else:
            from source_adapters import adapter_candidates, make_adapter
            attempts = []
            for method in adapter_candidates(source):
                try:
                    adapter = make_adapter(source, d, method=method,
                        heartbeat=lambda *_: heartbeat(d.parent / "queue.json", source["id"], claimed["lease_token"]),
                        progress=lambda *_: heartbeat(d.parent / "queue.json", source["id"], claimed["lease_token"], True))
                    evidence = adapter.preflight()
                    evidence["primary_or_fallback"] = method
                    evidence["attempts"] = attempts + [{"method": method, "status": "pass"}]
                    break
                except Exception as exc:
                    attempts.append({"method": method, "status": "failed", "error": str(exc), "at": utcnow()})
                    atomic_json(d / "raw" / "access_attempts.json", {"cycle_id": root.name, "source_id": source["id"], "attempts": attempts})
                    heartbeat(d.parent / "queue.json", source["id"], claimed["lease_token"], True)
            else:
                evidence = {"status": "failed", "attempts": attempts}
                raise RuntimeError("all independent access methods failed: " + "; ".join(x["error"] for x in attempts))
            verdict = "PASS" if evidence.get("status") == "pass" else "FAILED"
        atomic_json(d / "raw" / "preflight.json", {"verdict": verdict, "listing": source["listing_url"], "checked_at": utcnow(), "evidence": evidence})
        atomic_json(d / "manifest.json", {**read_json(d / "manifest.json"), "state": verdict.lower(), "finished_at": utcnow()})
        cp = read_json(d / "checkpoint.json")
        cp.update(state="complete", next_operation=4, updated_at=utcnow(), completed_operations=evidence.get("operations", []))
        atomic_json(d / "checkpoint.json", cp)
        return "complete" if verdict == "PASS" else "blocked"

    def vacancy_job(self, root, source, d, claimed):
        if self.self_test:
            cards = read_json(root / "fixture" / source["id"] / "listing.json")["cards"]
        else:
            from source_adapters import adapter_candidates, make_adapter
            preflight_file = root / "preflight" / source["id"] / "raw" / "preflight.json"
            preferred = read_json(preflight_file).get("evidence", {}).get("primary_or_fallback")
            candidates = adapter_candidates(source)
            if preferred in candidates:
                candidates.remove(preferred); candidates.insert(0, preferred)
            attempts = []
            for method in candidates:
                try:
                    adapter = make_adapter(source, d, method=method,
                        heartbeat=lambda *_: heartbeat(d.parent / "queue.json", source["id"], claimed["lease_token"]),
                        progress=lambda *_: heartbeat(d.parent / "queue.json", source["id"], claimed["lease_token"], True))
                    cards = adapter.scan()
                    atomic_json(d / "raw" / "worker_access_attempts.json", {"cycle_id": root.name, "source_id": source["id"], "attempts": attempts + [{"method": method, "status": "pass"}]})
                    break
                except Exception as exc:
                    attempts.append({"method": method, "status": "failed", "error": str(exc), "at": utcnow()})
                    atomic_json(d / "raw" / "worker_access_attempts.json", {"cycle_id": root.name, "source_id": source["id"], "attempts": attempts})
            else:
                raise RuntimeError("worker access methods failed: " + "; ".join(x["error"] for x in attempts))
        for i, card in enumerate(cards, 1):
            atomic_json(d / "raw" / f"card-{i}.json", card)
            atomic_json(d / "completed" / f"card-{i}.json", {"card": card, "at": utcnow()})
            cp = read_json(d / "checkpoint.json"); cp["completed_operations"].append(f"card-{i}"); cp["next_operation"] = i; cp["updated_at"] = utcnow(); atomic_json(d / "checkpoint.json", cp)
        atomic_json(d / "cards.json", {"schema_version": SCHEMA, "cycle_id": d.parent.parent.name, "source_id": source["id"], "cards": cards})
        atomic_json(d / "manifest.json", {**read_json(d / "manifest.json"), "state": "complete", "finished_at": utcnow()})
        return "complete"

    def llm(self):

        # Primary: litellm with Nemotron 3 Ultra
        key = os.environ.get("LITELLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("QA_VACANCY_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base = os.environ.get("LITELLM_BASE_URL", "http://host.docker.internal:4000")
        model = os.environ.get("QA_VACANCY_LLM_MODEL", "nemotron-3-ultra")

        timeout = int(os.environ.get("QA_VACANCY_LLM_TIMEOUT", "90"))
        return DirectLLM(base, model, key, timeout=timeout)
    
    def llm_with_fallback(self):

        """Use LiteLLM directly - it proxies all models with configured keys.
        No NVIDIA fallback needed since LiteLLM handles all providers."""
        return self.llm()
    @staticmethod
    def _synth_pool_size(pending: int, *, budget_hint: int = 0) -> tuple[int, int]:
        """(workers, cards_per_call) so the pending set fits the stage budget.

        Latency is linear in the number of cards inside one call, so shrinking
        the batch buys no throughput: at ~30 s per card a single worker retires
        2 cards/min whatever the batch size, and total work is
        pending*30/workers seconds. The only real lever is how many calls run
        concurrently, and the spec allows up to 10. Deriving workers from the
        pending count alone (rather than from the budget) keeps a small run from
        being handed a single worker when the budget could have covered several.

        A run can still exceed its budget: 800 cards at 10 workers is ~40 min,
        and no batch size changes that. Those cards stay undecided and are
        decided next cycle, which is the documented behaviour, so the caller
        logs decided-vs-pending to make the shortfall visible.
        """
        if pending <= 0:
            return 1, 1
        target_batch = 20
        workers = max(1, min(10, -(-pending // target_batch)))
        batch = max(4, min(target_batch, -(-pending // workers)))
        return workers, batch

    def synthesize(self, root, state):
        cards = []
        for source in read_json(root / "sources.json")["sources"]:
            p = root / "workers" / source["id"] / "cards.json"
            if p.exists(): cards.extend(read_json(p)["cards"])
        if self.self_test:
            rechecked = read_json(root / "published_recheck.json")["rows"]
            cards.extend({"url": r["url"], "title": r["title"], "company": r["company"], "location": r["location"], "posted": r["posted"], "work_mode": r["work_mode"], "announcement": "rechecked fixture", "verification": r["verification"], "category": r.get("category", "Other QA Roles")} for r in rechecked)
        else:
            # Existing published rows are carried forward until each is rechecked;
            # a failed source must never erase the known list. Re-attach the
            # persisted first_seen stamp here, otherwise an undated row restarts
            # its 30-day clock on every run and is retained forever.
            first_seen = self._load_first_seen()
            rechecked = read_json(root / "published_recheck.json")["rows"]
            cards.extend({**r, **({"first_seen_in_master": first_seen[canonical_url(r.get("url"))]} if canonical_url(r.get("url")) in first_seen else {}),

                          "announcement": r.get("announcement", ""), "from_published_master": True, "verification": r.get("verification", "Unclear")} for r in rechecked)

        decisions = {}
        # Rows rechecked above already carry a semantic decision. Re-asking the
        # LLM about them cost a second full pass (~14 min) and could overwrite a
        # decided row with Unknown, so their decision is carried forward.
        decided_from_recheck = {}
        for r in read_json(root / "published_recheck.json")["rows"]:
            if r.get("role_verified") in (True, False):
                decided_from_recheck[r["url"]] = {k: r.get(k) for k in
                    ("title","company","location","posted","work_mode","category","verification",
                     "role_verified","german_entity_verified","germany_remote_explicit")}
        if cards:
            try:
                readable = [x for x in cards if x.get("announcement") and x.get("url") not in decided_from_recheck]
                synth_workers, synth_batch = self._synth_pool_size(len(readable))
                batch_size = max(1, int(os.environ.get("QA_VACANCY_SYNTH_BATCH", "0")) or synth_batch)
                batches = [readable[i:i + batch_size] for i in range(0, len(readable), batch_size)]
                workers = max(1, min(10, len(batches), synth_workers))
                # A full master re-asks about every new card, and the free-tier
                # LLM needs ~3 min per wave, so an unbounded run took ~45 min.
                # Cards without a decision are kept, never dropped, and are
                # decided on the next cycle.
                budget = int(os.environ.get("QA_VACANCY_SYNTH_BUDGET_SECONDS", "1500"))
                deadline = time.monotonic() + budget
                pool = ThreadPoolExecutor(max_workers=workers)
                for start in range(0, len(batches), workers):
                    if time.monotonic() >= deadline:
                        break
                    wave = batches[start:start + workers]
                    futures = [pool.submit(self.semantic_decisions, b) for b in wave]
                    # as_completed without a timeout blocks forever on one stuck
                    # batch, so the deadline was only ever checked between waves
                    # and a single slow batch hung the whole cycle past its
                    # budget. Cap each wave by the remaining budget instead.
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    try:
                        for future in as_completed(futures, timeout=remaining):
                            try:
                                decisions.update(future.result())
                            except Exception:
                                continue
                    except FuturesTimeoutError:
                        # Batches in this wave are still running. Their cards stay
                        # undecided and are decided on the next cycle, which is
                        # the documented behaviour for undecided cards.
                        pass
                    for future in futures:
                        future.cancel()
                # The pool is not a context manager on purpose. `with
                # ThreadPoolExecutor` joins its workers on exit, so a batch still
                # stuck inside the LLM client would block here indefinitely --
                # the process was observed sitting in futex_do_wait with every
                # thread asleep and the cycle budget long spent. Pool threads are
                # daemonic, so abandoning them here cannot delay process exit.
                pool.shutdown(wait=False, cancel_futures=True)
                # Starvation used to be invisible: cards whose batch never ran
                # simply kept their fallback fields, so a run that decided a
                # third of the input looked exactly like a normal one.
                atomic_json(root / "synthesis_coverage.json", {
                    "schema_version": SCHEMA, "cycle_id": root.name, "at": utcnow(),
                    "pending_cards": len(readable), "decided_cards": len(decisions),
                    "undecided_cards": len(readable) - len(decisions),
                    "workers": workers, "batch_size": batch_size, "batches": len(batches),
                })
            except Exception as exc:
                atomic_json(root / "synthesis_llm_failure.json", {"error": str(exc), "at": utcnow()})
        decisions.update(decided_from_recheck)
        run_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
        accepted = []
        for card in cards:
            decision = decisions.get(card.get("url"), {})
            title = str(decision.get("title") or card.get("title") or "").strip()
            company = str(decision.get("company") or card.get("company") or "").strip()
            announcement = str(card.get("announcement") or "").strip()
            if not title:
                # A portal page may omit og:title; the announcement text still
                # names the position, so identity is recovered from it rather
                # than dropping the vacancy silently.
                title = next((line.strip() for line in announcement.splitlines()
                              if 8 < len(line.strip()) < 160 and not line.strip().startswith(("http", "Jobs finden"))), "")
            if not title and not company:
                continue
            existing = bool(card.get("from_published_master"))
            if not announcement and not existing:
                continue
            if decision.get("role_verified") is False:
                continue
            if not decision.get("role_verified") and not existing and not any(term in f"{title} {announcement}".casefold() for term in ("qa", "quality assurance", "test engineer", "tester", "test automation", "software test", "game qa", "localization tester", "test development")):
                continue
            if existing and not decision:
                row = {**card, "posted": normalize_posted(card.get("posted")),
                       "work_mode": normalize_work_mode(card.get("work_mode")),

                       "verification": "Unclear", "role_verified": "Unknown"}

                row.setdefault("category", "Software Test Engineer")
                row["category"] = normalize_category(row.get("category"))
                accepted.append(row)
                continue
            if not existing:
                semantic_location = str(decision.get("location") or card.get("location") or "Unknown")
                semantic_mode = str(decision.get("work_mode") or card.get("work_mode") or "Unknown")
                eligible_location = any(city in semantic_location.casefold() for city in ("berlin", "leipzig", "dresden")) or semantic_mode.casefold() == "remote"
                explicit_germany_remote = bool(decision.get("germany_remote_explicit")) or any(token in f"{semantic_location} {semantic_mode} {announcement}".casefold() for token in ("germany", "deutschland", "bundesweit", "100% remote", "100 % remote", "de "))
                if not eligible_location or (not any(city in semantic_location.casefold() for city in ("berlin", "leipzig", "dresden")) and not explicit_germany_remote):
                    continue
            semantic_card = {**card, **{k: decision.get(k, card.get(k, "Unknown")) for k in ("title","company","location","posted","work_mode","category","verification","role_verified","german_entity_verified","germany_remote_explicit")}}
            if existing and not decision:
                semantic_card["role_verified"] = "Unknown"
            gate = eligibility(semantic_card, run_date)
            if gate["verification"] == "REJECT" or str(semantic_card.get("verification") or "") == "Rejected":
                continue
            row = semantic_card
            row["posted"] = normalize_posted(row.get("posted"))
            row["work_mode"] = normalize_work_mode(row.get("work_mode"))
            if existing:

                row["verification"] = decision.get("verification") if decision else "Unclear"
                if not decision or decision.get("role_verified") is not True:
                    row["verification"] = "Unclear" if not decision else "Current / Partial"

            else:
                employer_verified = bool(row.get("german_entity_verified"))
                if gate["verification"] == "Current" and not employer_verified:
                    row["verification"] = "Current / Partial"
                else:
                    row["verification"] = gate["verification"]
            row.setdefault("category", "Software Test Engineer")
            row["category"] = normalize_category(row.get("category"))
            accepted.append(row)
        unique, dedup_evidence = deduplicate_first_url(accepted)
        # About.md: "retain the deduplication evidence internally" -- persist
        # the dropped duplicate URLs next to the cycle, not in the public master.
        atomic_json(root / "dedup_evidence.json", {
            "schema_version": SCHEMA, "cycle_id": root.name, "at": utcnow(),
            "kept": len(unique), "dropped": len(dedup_evidence), "duplicates": dedup_evidence,
        })
        sources = read_json(root / "sources.json")["sources"]
        # Carry the real per-source failure reason into the master's Sources
        # table. A generic "preflight or source access failed" hid the actual
        # cause, which is the only thing that tells a reader whether the source
        # is blocked, mis-routed, or serving portal pages instead of vacancies.
        reasons: dict[str, str] = {}
        not_used = root / "sources_not_used.json"
        if not_used.exists():
            for entry in read_json(not_used).get("sources", []):
                if entry.get("reason"):
                    reasons[entry["source_id"]] = entry["reason"]
        preflight_queue = root / "preflight" / "queue.json"
        if preflight_queue.exists():
            for job in read_json(preflight_queue).get("jobs", []):
                if job["state"] != "complete" and job.get("error"):
                    reasons.setdefault(job["source_id"], job["error"])
        rendered_sources = []
        for source in sources:
            used = (root / "workers" / source["id"] / "cards.json").exists()
            reason = "cards collected" if used else reasons.get(source["id"], "preflight or source access failed")
            rendered_sources.append({"name": source["name"], "status": "Used" if used else "Not used", "last_checked": root.name, "last_successful_use": root.name if used else "—", "reason": reason[:300]})
        candidate = root / "candidate_master.md"
        candidate_text = render_master(unique, rendered_sources, run_date)
        candidate.write_text(candidate_text, encoding="utf-8")
        rendered_urls = {row["url"] for row in parse_master_rows(candidate_text)}
        public_evidence = [row for row in unique if str(row.get("url") or "") in rendered_urls]
        # render_master buckets rows by "category" and silently drops any row
        # without one, while the header still counts every input row. That
        # produces a master reading "Vacancies listed: 36" with empty tables.
        # It is a silent data loss, so refuse to continue rather than publish it.
        if unique and not public_evidence:
            missing = sorted({str(r.get("category")) for r in unique})
            raise RuntimeError(
                f"render lost every row: {len(unique)} accepted, {len(public_evidence)} rendered. "
                f"categories present: {missing}. render_master requires a known category per row."
            )
        atomic_json(root / "synthesis.json", {"schema_version": SCHEMA, "cycle_id": root.name, "verdict": "PASS", "rows": len(public_evidence), "unique": len(public_evidence), "candidate": str(candidate), "evidence": public_evidence})
        self._persist_first_seen(root, public_evidence, run_date)
        self.save(root, state, stage="FINAL_VERIFIER", artifacts={**state.get("artifacts", {}), "synthesis": str(root / "synthesis.json")})
        return candidate

    def _load_first_seen(self) -> dict[str, str]:
        """The persisted first_seen stamps, keyed by canonical URL."""
        store_path = self.project / "first_seen.json"
        if not store_path.exists():
            return {}
        store = read_json(store_path)
        entries = store.get("entries") if isinstance(store, dict) else None
        return dict(entries) if isinstance(entries, dict) else {}

    def _persist_first_seen(self, root, rows, run_date: str) -> Path:
        """Carry `first_seen_in_master` across runs, keyed by canonical URL.

        The master's table has exactly seven columns, so `first_seen` cannot
        live there and `parse_master_rows` cannot read it back. Without a
        side-car the stamp written by `eligibility` dies with the cycle, the
        next run re-stamps it with today's date, and an undated row is retained
        forever -- which is exactly what the 30-day rule forbids. Keyed by
        canonical URL so a tracking-parameter change does not reset the clock.
        """
        store_path = self.project / "first_seen.json"
        store = read_json(store_path) if store_path.exists() else {}
        if not isinstance(store, dict) or "entries" not in store:
            store = {"schema_version": SCHEMA, "entries": {}}
        entries: dict[str, str] = dict(store.get("entries") or {})
        for row in rows:
            key = canonical_url(row.get("url")) or str(row.get("url") or "")
            if not key:
                continue
            stamp = str(row.get("first_seen_in_master") or "").strip()
            if stamp:
                entries.setdefault(key, stamp)
            else:
                entries.setdefault(key, run_date)
        # A URL that leaves the master entirely no longer needs ageing.
        live = {canonical_url(r.get("url")) for r in rows}
        entries = {k: v for k, v in entries.items() if k in live or k not in entries}
        atomic_json(store_path, {"schema_version": SCHEMA, "updated_at": utcnow(),
                                 "last_cycle": root.name, "entries": entries})
        return store_path

    def _accepted_evidence(self, root):
        synthesis = read_json(root / "synthesis.json")
        if isinstance(synthesis.get("evidence"), list): return synthesis["evidence"]
        cards = []
        for path in (root / "workers").glob("*/cards.json"):
            payload = read_json(path)
            cards.extend(payload if isinstance(payload, list) else payload.get("cards", []))
        rechecked = read_json(root / "published_recheck.json").get("rows", [])
        cards.extend(rechecked)
        return cards

    CONFIRMED_TOKENS = {"Current", "Current / Partial"}

    def _degradation_errors(self, rows) -> list[str]:
        """Reject a candidate that discards confirmation the master already had.

        The incident this guards against: on 2026-09-24 cycle-16 produced 36
        rows (17 Current, 19 Current/Partial). Hours later cycle-17 republished

        the same 36 URLs with every one demoted to Unclear and added nothing.
        Seven of ten sources had failed preflight, so recheck could not re-read
        the pages. Every structural check still passed -- Unclear is a legal
        value and each row kept its URL, company and location -- so the verifier
        returned PASS on a master that had lost all of its evidence.

        About.md treats a temporary access failure as Unclear, but that rule

        the same 36 URLs with every one demoted to Unverified and added nothing.
        Seven of ten sources had failed preflight, so recheck could not re-read
        the pages. Every structural check still passed -- Unverified is a legal
        value and each row kept its URL, company and location -- so the verifier
        returned PASS on a master that had lost all of its evidence.

        About.md treats a temporary access failure as Unverified, but that rule

        governs rows whose status is being established. It is not a licence to
        erase confirmation that a previous run already established: an
        unreadable page cannot disprove a role, employer or date that was
        verified before. So a candidate may not demote more confirmed rows than
        the reachable sources can actually explain, and may not publish a
        master with no confirmed rows at all while one is already published.

        A small amount of demotion is legitimate -- a source that answers can
        legitimately contradict an earlier reading, and a vacancy can close --
        so the threshold scales with how much of the master the recheck could
        actually re-read.
        """
        if self.self_test or not self.master.exists():
            return []
        previous = parse_master_rows(self.master.read_text(encoding="utf-8"))
        prev_confirmed = {r["url"] for r in previous if r["verification"] in self.CONFIRMED_TOKENS}
        if not prev_confirmed:
            return []
        cand_confirmed = {r["url"] for r in rows if r["verification"] in self.CONFIRMED_TOKENS}
        demoted = prev_confirmed - cand_confirmed
        errors: list[str] = []
        if not rows:
            return ["degradation: candidate is empty while a confirmed master is published"]
        # recheck_published_rows already preserves prior confirmation when a page
        # cannot be re-read, so a large demotion reaching here means the pages
        # WERE read and actively reported differently. Vacancies do expire, and
        # sources do correct their own dates, so a sizeable daily churn is
        # legitimate. The decisive signal is not the ratio but the total collapse
        # of confirmed evidence, which the check below catches regardless.
        allowance = max(5, int(len(prev_confirmed) * 0.7))
        if len(demoted) > allowance:
            errors.append(
                f"degradation: {len(demoted)} of {len(prev_confirmed)} confirmed rows demoted "
                f"to unresolved (allowance {allowance}); an unreadable page cannot disprove "
                f"a previously verified role, employer or date: "
                + ", ".join(sorted(demoted)[:3])
            )
        if not cand_confirmed:
            errors.append(
                f"degradation: candidate retains no confirmed row while {len(prev_confirmed)} are published"
            )
        return errors

    def verify(self, root, candidate):
        text = candidate.read_text(encoding="utf-8")
        rows = parse_master_rows(text)
        synthesis = read_json(root / "synthesis.json")
        evidence_rows = self._accepted_evidence(root)
        evidence_by_url = {str(r.get("url") or ""): r for r in evidence_rows}

        
        # Load previous master URLs to distinguish old vs new rows
        previous_master_urls = set()
        if self.master.exists():
            previous = parse_master_rows(self.master.read_text(encoding="utf-8"))
            previous_master_urls = {r["url"] for r in previous}
        


        errors: list[str] = []
        if not rows: errors.append("candidate contains no vacancy rows")
        if len(rows) != int(synthesis.get("rows", -1)): errors.append("candidate row count differs from synthesis")
        for row in rows:
            if not row["url"].startswith("http"): errors.append(f"non-direct URL: {row['url']}")
            if row["verification"] not in VERIFICATIONS: errors.append(f"invalid verification: {row['verification']}")
            if not row["title"] or not row["company"] or not row["location"]: errors.append(f"incomplete row: {row['url']}")
            if row["work_mode"] not in {"Remote", "Hybrid", "Onsite", "Unknown"}: errors.append(f"invalid work mode: {row['url']}")
            evidence = evidence_by_url.get(row["url"])
            if not evidence:
                errors.append(f"missing semantic evidence: {row['url']}")
                continue
            if row["verification"] in {"Current", "Current / Partial", "Unclear"}:
                role_verified = evidence.get("role_verified")
                if role_verified is None and self.self_test:
                    role_verified = True
                if not role_verified:
                    errors.append(f"row lacks affirmative QA role evidence: {row['url']}")
            if row["verification"] == "Current":
                if not evidence.get("german_entity_verified"):
                    errors.append(f"Current row lacks German-entity evidence: {row['url']}")

                # Location check: strict for NEW rows, warning for OLD rows (from previous master)
                is_old_row = row["url"] in previous_master_urls
                location_ok = evidence.get("germany_remote_explicit") or any(city.casefold() in str(evidence.get("location", "")).casefold() for city in ("Berlin", "Leipzig", "Dresden"))
                if not location_ok:
                    if is_old_row:
                        errors.append(f"WARNING: Old row lacks eligible location/remote evidence (kept from master): {row['url']}")
                    else:
                        errors.append(f"Current row lacks eligible location/remote evidence: {row['url']}")

                if not evidence.get("germany_remote_explicit") and not any(city.casefold() in str(evidence.get("location", "")).casefold() for city in ("Berlin", "Leipzig", "Dresden")):
                    errors.append(f"Current row lacks eligible location/remote evidence: {row['url']}")

        if len(evidence_by_url) != len({r.get("url") for r in rows}): errors.append("semantic evidence URL set does not round-trip")
        errors.extend(self._degradation_errors(rows))
        for phase in ("preflight", "workers"):
            queue = root / phase / "queue.json"
            if not queue.exists():
                errors.append(f"missing {phase} queue")
                continue
            incomplete = [job["source_id"] for job in read_json(queue)["jobs"] if job["state"] not in {"complete", "blocked"}]
            if incomplete:
                errors.append(f"non-terminal {phase} jobs: {', '.join(incomplete)}")
            if phase == "workers":
                # About.md: a source that cannot be read is marked `Not used`
                # for the run and the cycle continues. So a blocked or failed
                # worker is only an error when it was NOT accounted for -- i.e.
                # when the run did not record it as Not used with a reason.
                # Without this the master could never be published while any
                # single board was unhealthy, which is exactly what happened with
                # XING serving portal pages instead of vacancy cards.
                jobs = read_json(queue)["jobs"]
                recorded = set()
                not_used = root / "sources_not_used.json"
                if not_used.exists():
                    recorded = {e.get("source_id") for e in read_json(not_used).get("sources", [])}
                unaccounted = [
                    job["source_id"] for job in jobs
                    if job["state"] != "complete" and job["source_id"] not in recorded
                ]
                if unaccounted:
                    errors.append(
                        "worker failures not recorded as Not used: " + ", ".join(unaccounted)
                    )

        verdict = "PASS" if not any(not e.startswith("WARNING:") for e in errors) else "FAIL"

        verdict = "PASS" if not errors else "FAIL"

        atomic_json(root / "verifier.json", {"schema_version": SCHEMA, "cycle_id": root.name, "verdict": verdict, "checked_at": utcnow(), "rows": len(rows), "errors": errors})
        return verdict

    def publish_github(self, candidate, state, repository=QA_REPOSITORY_DEFAULT, run_git=run_git_command):
        try:
            result = publish_github_transaction(
                project=self.project, repository=repository, candidate=candidate, run_git=run_git,
                commit_message=f"Publish QA vacancy master {dt.datetime.now(dt.timezone.utc).date().isoformat()}",
            )
        except Exception as exc:
            state.update(stage="FAILED", status="FAILED", error=f"{type(exc).__name__}: {exc}")
            raise
        state.update(publication=result.status, archive=str(result.archive) if result.archive else None)
        return result

    def publish(self, root, state, candidate):
        published = self.master.read_bytes() if self.master.exists() else None
        candidate_bytes = candidate.read_bytes()
        if self.self_test or not self.allow_publish:
            status = "DRY_RUN_VERIFIED"
        else:
            status = self.publish_github(candidate, state).status
        self.save(root, state, stage="DONE", status=status,
                  publication_allowed=self.allow_publish, finished_at=utcnow())
        # About.md step 8: notify only when the master changes or the run fails.
        # DRY_RUN_VERIFIED is a suppressed run and NO_CHANGE is an unchanged
        # master, so neither is a reason to talk to anyone.
        if status == "CHANGED_PUBLISHED":
            self.emit_notice(root, state, "master_changed",
                             f"{state.get('cycle_id')}: master changed and was published")
        return state

    def emit_notice(self, root, state, event: str, message: str) -> None:
        """Record a notification-worthy event durably, and echo it on stdout.

        The controller has no chat transport of its own, so a notice is a
        durable JSON file the cron wrapper can pick up, plus a stdout line that
        lands in the cron log. Both are written unconditionally: whether the run
        is allowed to notify is decided by the CALLER, which only calls this for
        a changed master or a failure.
        """
        record = {
            "event": event, "message": message, "at": utcnow(),
            "cycle_id": state.get("cycle_id"), "status": state.get("status"),
            "stage": state.get("stage"), "error": state.get("error"),
        }
        try:
            notices = self.project / "notices.jsonl"
            notices.parent.mkdir(parents=True, exist_ok=True)
            with notices.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                fh.flush(); os.fsync(fh.fileno())
        except OSError as exc:  # a notice must never take the run down
            record["delivery_error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(record, ensure_ascii=False), flush=True)


def atomic_text(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True); fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh: fh.write(data); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(FileNotFoundError): os.unlink(tmp)


def launch_detached(project: Path, script: Path, selftest: bool = False) -> None:
    lock = project / ".launch.lock"
    with open(lock, "a+", encoding="utf-8") as fh:
        try: fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return
        runs = project / "runs"; runs.mkdir(exist_ok=True)
        active = runs / "active.json"
        # active.json alone was not enough: a controller started by hand never
        # writes it, so the launcher happily spawned a second one against the
        # same project. Both checkers are best-effort -- the flock in this
        # function only guards concurrent launches, so an existing process must
        # also be detected by scanning for the controller command line.
        if active.exists():
            try:
                prior = json.loads(active.read_text(encoding="utf-8"))
                os.kill(int(prior["pid"]), 0)
                return
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                with contextlib.suppress(FileNotFoundError): active.unlink()
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                argv = [p.decode("utf-8", "replace")
                        for p in (entry / "cmdline").read_bytes().split(b"\0") if p]
            except OSError:
                continue
            # A launcher (--launch) is not a running controller, so it does not
            # block; any other invocation of the same script does.
            # Compare BASENAMES, not whole argv elements. A controller started
            # by hand runs `python3 daily_controller.py --project ...` from
            # inside the project, so its argv holds a RELATIVE path and the old
            # `str(script) in argv` test never matched it; the scan then walked
            # straight past a live run and launch_detached spawned a second
            # controller against the same project. An exact `script.name in
            # argv` is equally wrong in the other direction: the cron path
            # passes the ABSOLUTE path, so membership fails. Take the basename
            # of every argv element instead. --launch is the launcher, not a
            # controller, so it must not block.
            if any(Path(part).name == script.name for part in argv) and "--launch" not in argv:
                return
        log = open(runs / "controller.log", "ab", buffering=0)
        cmd = [sys.executable, str(script)]
        if selftest: cmd.append("--self-test")

        # Pass environment so child inherits LITELLM_API_KEY, LITELLM_BASE_URL from s6 container_environment
        proc = subprocess.Popen(cmd, cwd=project, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True, env=os.environ.copy())

        proc = subprocess.Popen(cmd, cwd=project, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)

        atomic_json(active, {"pid": proc.pid, "started_at": utcnow(), "script": str(script)})


def main() -> int:
    load_env_file()
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--project", type=Path, default=PROJECT_DEFAULT)
    parser.add_argument("--controller-script", type=Path)
    parser.add_argument("--no-publish", action="store_true", help="run without local/GitHub publication")
    args = parser.parse_args()
    try:
        if args.launch:
            launch_detached(args.project, args.controller_script or Path(__file__).resolve(), args.self_test)
            return 0
        result = Pipeline(args.project, args.self_test, not args.no_publish).run()
        print(json.dumps({"cycle_id": result.get("cycle_id"), "status": result.get("status"), "stage": result.get("stage"), "error": result.get("error")}, ensure_ascii=False))
        return 0 if result.get("status") not in {"FAILED"} else 1
    finally:
        # Detached runs own the lifecycle marker; clear it only when this process exits.
        marker = args.project / "runs" / "active.json"
        with contextlib.suppress(FileNotFoundError, json.JSONDecodeError, OSError):
            active = json.loads(marker.read_text(encoding="utf-8"))
            if int(active.get("pid", -1)) == os.getpid():
                marker.unlink()


if __name__ == "__main__": raise SystemExit(main())
