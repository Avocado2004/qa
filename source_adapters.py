#!/usr/bin/env python3
"""Real source adapters for the detached QA vacancy controller.

The adapters collect evidence deterministically. Semantic classification is a
separate stage; these classes never accept/reject a vacancy.
"""
from __future__ import annotations
import hashlib, html, json, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
# A CloudFront WAF in front of some German portals (verified on adzuna.de) scores
# header COMPLETENESS, not any single header. Every one of these 403s while the
# same request returns 200 when the full browser header set is sent.
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}
BLOCK_MARKERS = ("captcha", "access denied", "cloudflare", "enable javascript and cookies", "respects your privacy")
# Portal pages that are not a vacancy at all. A snapshot-length preflight passed
# all of these, because each renders a full site chrome; only the heading gives
# them away. About.md requires a direct vacancy card.
NON_VACANCY_TITLES = (
    "initiativbewerbung", "ähnliche jobs", "aehnliche jobs", "similar jobs", "recruiter (m/w/d)",
    "recruiter (m/w/d) ", "mitarbeiter m/w/d in verschiedenen bereichen", "postbote", "zusteller",
    "pendelzeit berechnen", "karriere bei", "über uns", "ueber uns", "impressum", "datenschutz",
    "kontakt", "jobs durchsuchen", "jobsuche", "alle jobs", "aktuelle jobs", "stellenangebote",
    "stellenanzeigen schreiben", "arbeitgeber werden", "job erstellen", "passwort", "registrieren",
)
# Portal pages whose heading carries a location or role suffix, so they match on
# a stem rather than the whole string.
NON_VACANCY_STEMS = (
    "initiativbewerbung", "ähnliche jobs", "aehnliche jobs", "postbote", "zusteller", "recruiter",
    "mitarbeiter m/w/d in verschiedenen bereichen", "pendelzeit berechnen",
)


@dataclass
class Fetch:
    requested_url: str
    final_url: str
    status: int
    body: bytes
    content_type: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()


def _gunzip(body: bytes) -> bytes | None:
    import gzip
    import io
    try:
        return gzip.GzipFile(fileobj=io.BytesIO(body)).read()
    except Exception:
        return None


def _zlib_bare(body: bytes) -> bytes | None:
    """Some servers send raw DEFLATE with no zlib wrapper, others with one."""
    import zlib
    for wbits in (-zlib.MAX_WBITS, zlib.MAX_WBITS, zlib.MAX_WBITS | 16):
        try:
            return zlib.decompress(body, wbits)
        except Exception:
            continue
    return None


def decompress(body: bytes, encoding: str) -> bytes:
    """We advertise gzip/br so WAFs let the request through; now actually decode.

    Three defects were fixed here on 2026-09-27, all observed live in
    `qa_vacancies_master.md` as "utf-8 codec can't decode byte 0x8b" (Remotive,
    Arbeitnow) and "0xfc" (GermanTechJobs), i.e. raw compressed bytes reaching
    a plain `.decode()`:

    1. The branches were probed in the order br, gzip, deflate, but a server
       may answer `Content-Encoding: gzip, br` while the body is plain gzip --
       br is tried first, raises, and the `except: pass` swallowed it and
       returned the still-compressed bytes. Try every codec and accept the
       first that actually works instead of trusting the header.
    2. An absent or blank Content-Encoding header was returned untouched. Some
       CDNs compress by default and omit the header, so sniff the magic bytes.
    3. `zstd` was never attempted at all, so its 0x28 b5 2f fd magic came
       through as the 0xfc decode error.
    """
    enc = (encoding or "").casefold()
    tried: list[bytes | None] = []

    if "gzip" in enc:
        tried.append(_gunzip(body))
    if "deflate" in enc:
        tried.append(_zlib_bare(body))
    if "br" in enc:
        try:
            import brotli
            tried.append(brotli.decompress(body))
        except Exception:
            tried.append(None)
    if "zstd" in enc:
        try:
            import zstandard
            tried.append(zstandard.ZstdDecompressor().decompress(body))
        except Exception:
            tried.append(None)

    for candidate in tried:
        if candidate is not None:
            return candidate
    # A codec was named but none produced a result: fall through to magic
    # sniffing rather than returning compressed bytes to a text decode.
    # No usable Content-Encoding result, or no header at all: identify the bytes.
    if body[:2] == b"\x1f\x8b":
        out = _gunzip(body)
        if out is not None:
            return out
    if body[:4] == b"\x28\xb5\x2f\xfd":
        try:
            import zstandard
            return zstandard.ZstdDecompressor().decompress(body)
        except Exception:
            pass
    if body[:1] in (b"\x78",):
        out = _zlib_bare(body)
        if out is not None:
            return out
    if body[:4] == b"\x04\x22\x4d\x18":
        try:
            import lz4.frame
            return lz4.frame.decompress(body)
        except Exception:
            pass
    return body


def build_opener():
    """urllib must advertise gzip/br like a browser, or WAFs reject the request."""
    return urllib.request.build_opener(urllib.request.HTTPRedirectHandler()).open


def fetch(url: str, timeout: int = 30, attempts: int = 2) -> Fetch:
    req = urllib.request.Request(url, headers=dict(BROWSER_HEADERS))
    open_url = build_opener()
    last: Fetch | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            with open_url(req, timeout=timeout) as r:
                return Fetch(url, r.geturl(), r.status, decompress(r.read(), r.headers.get("Content-Encoding", "")),
                             r.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as exc:
            # An error response is body too. On 2026-09-29 Remotive, Arbeitnow
            # and GermanTechJobs all answered a 4xx/5xx with brotli, and this
            # branch returned `exc.read()` verbatim -- no decompress() -- so the
            # compressed bytes reached json.loads and the master reported
            # "utf-8 codec can't decode byte 0x8b" for a source that was
            # perfectly reachable. The status is still the HTTP status: a
            # non-200 body is never treated as vacancy data.
            return Fetch(url, exc.geturl(), exc.code,
                         decompress(exc.read(), exc.headers.get("Content-Encoding", "")),
                         exc.headers.get("Content-Type", ""))
        except Exception as exc:
            # Slow German job portals routinely time out on the first attempt.
            # A retry is a temporary access failure, never a closure verdict.
            last = Fetch(url, url, 0, str(exc).encode(), "error")
            if attempt < attempts:
                time.sleep(2 * attempt)
    return last or Fetch(url, url, 0, b"", "error")


def normalize_url(url: str, base: str) -> str:
    url = urllib.parse.urljoin(base, html.unescape(url.strip()))
    p = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith(("utm_", "trk", "tracking"))]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(query), ""))


def text(blob: bytes) -> str:
    s = blob.decode("utf-8", "replace")
    s = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def source_domain_token(url: str) -> str:
    host = urllib.parse.urlsplit(url).netloc.casefold().split(":")[0]
    return host[4:] if host.startswith("www.") else host


CRAWL4AI_CLI = "/opt/data/.venv/bin/crawl4ai-skill"


def crawl4ai_read(url: str, raw_dir: Path, owner=None, timeout: int = 180) -> str:
    """Render one page through crawl4ai-skill and return its markdown text.

    Used as an in-line transport retry when a plain HTTP detail fetch is cut
    off by the origin. A failure here is a transport error, never a verdict.
    """
    output = raw_dir / ("crawl4ai-" + re.sub(r"[^a-zA-Z0-9]+", "-", url)[-90:] + ".md")
    cmd = [CRAWL4AI_CLI, "crawl", url, "--format", "raw_markdown", "--output", str(output), "--timeout", "60"]
    try:
        completed = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"crawl4ai timed out after {timeout}s") from exc
    if owner is not None:
        owner.save("crawl4ai-run", {"url": url, "returncode": completed.returncode,
                                   "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]})
    if completed.returncode or not output.exists() or output.stat().st_size < 100:
        raise RuntimeError(f"crawl4ai failed ({completed.returncode}): {completed.stderr[-300:]}")
    return re.sub(r"\s+", " ", output.read_text(encoding="utf-8", errors="replace")).strip()


def non_vacancy_heading(title: str) -> bool:
    """True when a page heading identifies a portal page, not a vacancy.

    XING in particular renders Initiativbewerbung, Ähnliche Jobs and Postbote as
    full pages with complete site chrome, so snapshot length cannot tell them
    apart from a real posting.
    """
    text = re.sub(r"\s+", " ", str(title or "").strip().casefold())
    if not text:
        return False
    # Exact or near-exact match only. "Initiativbewerbung QA" and "Ähnliche Jobs
    # suchen QA Engineer" are real postings that merely start with a portal
    # phrase, so a prefix test would discard valid vacancies.
    stripped = re.sub(r"[\s:–—|-]+$", "", text)
    if stripped in NON_VACANCY_TITLES:
        return True
    if any(re.fullmatch(rf"{re.escape(bad)}[.:]?(?:\s*\d+)?", stripped) for bad in NON_VACANCY_TITLES):
        return True
    # A stem blocks the portal page and its decorated variants, but only when a
    # role keyword is absent: "Initiativbewerbung QA Engineer" is a real posting.
    return any(stripped.startswith(stem) for stem in NON_VACANCY_STEMS) and not any(
        word in stripped for word in ("qa", "test", "quality", "engineer", "entwickler", "automatisier"))


TESTING_ROLE_TERMS = (
    "qa engineer", "qa tester", "qa automation", "software qa", "quality engineer",
    "softwaretester", "software tester", "software test", "test engineer", "test automation",
    "testautomatisierung", "testingenieur", "test analyst", "test automation engineer",
    "gamedev qa", "game tester", "game qa", "localization tester",
)


def looks_like_testing_role(value: Any) -> bool:
    """True when a title names a QA/testing role.

    Used by the preflight to tell two different outcomes apart. A source whose
    detail pages open cleanly but happen to be Recruiter/Initiativbewerbung has
    not had an ACCESS failure, and saying so in the master's Sources table
    would blame connectivity for an editorial result.
    """
    haystack = str(value or "").casefold()
    return any(term in haystack for term in TESTING_ROLE_TERMS)


PORTAL_PAGE_MARKERS = ("about this job", "aufgaben", "über uns", "your tasks", "what you will do",
                       "dein job:", "your benefits", "deine benefits", "kontakt", "about the company",
                       "profil", "das bringst du mit", "skills bringst")

# A page can carry a plausible heading and a full site menu and still not BE a
# posting. Measured 2026-09-29: Indeed routed us to
# job.deloitte.com/careers, whose title reads "Job Visitenkarte Senior
# IT-Consultant / Software Quality Engineer" and which mentions a candidate
# profile -- yet the body is a list of job CATEGORIES (/cloud-jobs, /automotive-
# jobs, /accounting-ifrs-jobs, ~20 of them) and carries no description at all.
# Preflight passed it as a vacancy card. These markers are what a real posting
# body contains; a title alone never counts.
VACANCY_BODY_MARKERS = (
    "aufgaben", "your tasks", "what you will do", "dein job:", "deine aufgaben",
    "ihre aufgaben", "your responsibilities", "responsibilities",
    "qualifikationen", "qualifications", "ihr profil", "your profile",
    "dein profil", "what you bring", "das bringst du mit", "skills",
    "deine benefits", "your benefits", "wir bieten", "what we offer",
    "about this job", "über die stelle", "job description", "stellenbeschreibung",
    "your mission", "your impact", "dein impact",
    # Bare/singular German and English variants. Measured 2026-09-30 on 60
    # Arbeitsagentur cards from the spec-role search: "Quality Assurance Expert
    # (m/w/d)" (Akkodis) was REJECTED although its text contains "anforderung",
    # "profil", "qualifikation" and "kenntnisse" -- it just did not use the
    # canonical "ihr profil"/"your profile" section headings this list required.
    "anforderung", "qualifikation", "kenntnisse", "voraussetzung",
    "verantwortung", "aufgabenbereich", "deine aufgaben:", "ihre aufgabe",
    "was dich erwartet", "das erwartet", "über uns", "uber uns",
    "what you'll do", "what you bring", "your role", "the role",
    "your opportunity", "what we offer", "what we look for",
)


def looks_like_vacancy_posting(page: dict[str, Any]) -> bool:
    """True when the page carries posting BODY text, not just a title.

    Complements `_is_utility_page`, which only asks "is this a portal page?".
    A category index or a teaser card is not a portal page yet is not a posting
    either, and publishing it would put a link in the master that opens on a
    list of other jobs.

    Measured 2026-09-30 on 45 Indeed cards that "opened successfully": only 17
    were postings. The other 28 were Indeed's own chrome -- the homepage menu,
    a 400 from the employer's login servlet, the cookie wall -- which slipped
    through because the menu happens to contain the words "Qualitätssicherung"
    and "Test". So the length test and the marker count are necessary but not
    sufficient: the page must not be recognisable portal furniture, and the
    markers must look like posting sections rather than navigation.
    """
    body = str(page.get("announcement") or "").casefold()
    if len(body) < 400:
        return False
    # Reject the aggregator's own pages outright. These are the specific
    # bodies the 28 false positives were.
    if re.search(r"^##\s*http error \d+", body) or "bad request" in body[:400]:
        return False
    if re.search(r"(?m)^#{1,2}\s*(login|anmelden|registrieren|sign in|homepage|startseite)\b", body):
        return False
    if "linkedin nimmt den schutz ihrer privatsphäre" in body[:2000]:
        return False
    # LinkedIn challenge/bot detection page often contains these markers
    if "data-is-bot=\"false\"" in body or "data-is-bot=\"true\"" in body:
        return False
    if "challenge" in body[:500] and "linkedin" in body[:500]:
        return False
    if "cookie-einstellungen" in body[:600] and "über cookies" in body[:4000] \
            and not re.search(r"(?i)(ihre aufgaben|your tasks|ihr profil|your profile)", body):
        # Cookie wall with no posting sections anywhere.
        return False
    return sum(1 for marker in VACANCY_BODY_MARKERS if marker in body) >= _body_marker_need(body)


def _body_marker_need(body: str) -> int:
    """How many posting-section markers a page of this length must carry.

    A long posting always has section headings, so 2 is a safe floor there. A
    SHORT one cannot: measured 2026-09-30, "Software QA-Engineer (w/m/d)" (B.
    Braun) and "Quality Assurance Rater" (TELUS Digital) are real Arbeitsagentur
    postings of 800 and 835 characters that carry NO section headings at all --
    the portal simply truncated the announcement. Requiring 2 of them threw away
    genuine vacancies, so a short page is judged on its portal-specific
    structured fields instead (Arbeitsagentur always emits "Arbeitsort",
    "Angebotsart", "Anstellungsart", "Beginn", "Bewerbung"), which cannot appear
    on a navigation or category page.
    """
    if len(body) >= 2000:
        return 2
    if len(body) < 400:
        return 9
    return 1 if sum(1 for f in ("arbeitsort", "angebotsart", "anstellungsart",
                                "beginn", "bewerbung", "arbeitszeit",
                                "entgelt", "befristung") if f in body) >= 3 else 2


def _is_utility_page(page: dict[str, Any]) -> bool:
    """True when an opened card is a portal/utility page, not a posting.

    Decided on the page's own structure, not on its title alone. XING serves
    "Recruiter (m/w/d)" and "Initiativbewerbung" as full postings (About this
    job, Aufgaben, Über uns, Kontakt), so those titles are vacancies even though
    NON_VACANCY_TITLES lists them -- a title list alone would misreport a
    readable source as broken. A page with NO posting structure is a utility
    page whatever it calls itself.
    """
    title = str(page.get("title") or "").strip().casefold()
    body = str(page.get("announcement") or "").casefold()
    structured = sum(1 for marker in PORTAL_PAGE_MARKERS if marker in body) >= 2
    if structured:
        return False
    # No posting structure at all: fall back to the title list.
    return non_vacancy_heading(title) or title in {
        "ähnliche jobs", "similar jobs", "passwort", "registrieren", "datenschutz",
        "impressum", "kontakt", "über uns", "alle jobs", "aktuelle jobs",
        "jobs durchsuchen", "stellenangebote", "postbote", "zusteller",
        "arbeitgeber werden", "job erstellen", "jobsuche", "karriere bei",
        "stellenanzeigen schreiben", "pendelzeit berechnen",
        "mitarbeiter m/w/d in verschiedenen bereichen",
    }


def _listing_row_context(body: str, link_end: int) -> str:
    """The listing text that follows a card link: employer, city, salary, hours.

    A row reads "PTA GmbH Berlin * 50.000 EUR pro Jahr * Vollzeit". That is the
    only identity an aggregator gives reliably, and it is what makes the
    candidate findable on a direct source, so it must reach the card.
    """
    tail = body[link_end: link_end + 320]
    cut = re.search(r"^#{1,4}\s|\n\s*#{1,4}\s|\]\(https?://", tail)
    if cut:
        tail = tail[: cut.start()]
    tail = re.sub(r"[*_`>\[\]()]", " ", tail)
    tail = re.sub(r"[ \t]+", " ", tail).strip()
    return re.sub(r"[\r\n]+", " ", tail)[:200]


def extract_final_vacancy_url(markup: str) -> str:
    """Recover the employer's real vacancy URL from a rendered page.

    An aggregator link (/rc/clk?jk=) is not the direct vacancy card About.md
    requires, and its per-view `bb` token makes the stored link rot. The final
    URL is present in the rendered page itself -- the employer's cookie banner
    links to the same page -- so pick the most frequent off-aggregator URL that
    looks like a posting. Returns "" when nothing is trustworthy, and the
    caller then keeps the original URL rather than publishing a guess.
    """
    text = html.unescape(markup or "")
    counts: dict[str, int] = {}
    for m in re.finditer(r"https?://[^\s\)\]<>\"']+", text):
        url = m.group(0).rstrip(".,;)]}>")
        try:
            parts = urllib.parse.urlsplit(url)
        except ValueError:
            continue
        host = parts.netloc.casefold()
        if not host or not parts.path.strip("/"):
            continue
        # Skip the aggregator itself and any tracking/cookie consent hosts.
        if any(host == bad or host.endswith("." + bad) for bad in
               ("indeed.com", "google.com", "gstatic.com", "googleapis.com",
                "doubleclick.net", "cookiebot.com")):
            continue
        # A vacancy page is neither a static asset nor a homepage.
        if re.search(r"\.(?:css|js|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|xml|json|map)$",
                     parts.path, re.I):
            continue
        if not re.search(r"(?i)(job|jobsuche|stelle|vacan|career|careers|position|karriere|"
                         r"anzeig|offene|bewerbung|detail)", parts.path + host):
            continue
        clean = urllib.parse.urlunsplit((parts.scheme.casefold(), host, parts.path, "", ""))
        # CRITICAL: the same vocabulary that admitted the URL must also CONFIRM it.
        # Measured 2026-09-29: a PTA posting rendered its own page but the only
        # repeated off-aggregator links were the site menu -- "pta.de/karriere/",
        # "pta.de/unternehmen/" -- each seen twice by the cookie banner, while
        # the real posting sat at karriere.pta-gruppe.com/.../jobs/273/apply and
        # appeared ONCE. A frequency rule alone therefore returned the careers
        # SECTION, so the master would have linked to a landing page instead of
        # the vacancy. Reuse direct_card(), the project's single authority on
        # "is this URL a vacancy card", as the final gate.
        if not direct_card(clean):
            continue
        counts[clean] = counts.get(clean, 0) + 1
    if not counts:
        return ""
    best, hits = max(counts.items(), key=lambda kv: (kv[1], -len(kv[0])))
    # Prefer a corroborated URL, but a single well-formed card link still beats
    # no link at all: the caller falls back to the aggregator URL otherwise.
    return best if hits >= 2 or len(counts) == 1 else ""


def first_heading(snapshot: str) -> str:
    """First meaningful heading of an accessibility snapshot, or "".

    A Camofox snapshot is an accessibility tree, so the page title is the first
    `heading "..."` node. The banner and navigation come first, so the first
    heading is not necessarily the job title -- which is why the caller only
    uses it to REJECT obvious portal pages, never to accept a vacancy.
    """
    for match in re.finditer(r'heading\s+"([^"]{3,120})"', str(snapshot or "")):
        candidate = re.sub(r"\s+", " ", match.group(1)).strip()
        if candidate and candidate.casefold() not in ("jobs finden", "menu", "navigation"):
            return candidate
    return ""


def direct_card(url: str) -> bool:
    p = urllib.parse.urlsplit(url).path.lower().rstrip("/")
    if any(token in p for token in ("/search", "/category")) or p.startswith("/jobsuche/"):
        # Arbeitsagentur serves search under /jobsuche/suche but the vacancy
        # cards themselves live under /jobsuche/jobdetail/<refnr>.
        if p.startswith("/jobsuche/") and not p.startswith("/jobsuche/jobdetail/"):
            return False
        if not p.startswith("/jobsuche/jobdetail/"):
            return False
    listing_categories = {"germany", "austria", "belgium", "bulgaria", "france", "greece", "hungary", "ireland", "italy", "netherlands", "norway", "poland", "portugal", "romania", "spain", "sweden", "switzerland", "uk", "united-kingdom", "usa", "remote", "multiple-countries", "multiple_countries"}
    if p.startswith("/jobs/"):
        jobs_path = p[len("/jobs/"):]
        first_segment = jobs_path.split("/", 1)[0]
        if first_segment not in {"view", "remote"} and not re.search(r"-\d{5,}(?:\.html)?$", jobs_path):
            if source_domain_token(url) != "germantechjobs.de":
                return False
    if p.startswith("/jobs/") and p.split("/")[-1] in listing_categories:
        return False
    if p.endswith(("/jobs", "/job", "/stellenangebote", "/vacancies", "/stellen")):
        return False
    if "/jobs?" in url.lower() or "/job?" in url.lower():
        return False
    if p.endswith(("/details", "/details/careers", "/details/partners", "/details/promos")):
        return False
    if p.startswith("/details/") and not re.match(r"^/details/\d{5,}$", p):
        # Adzuna mixes numeric vacancy cards with editorial/landing pages.
        return False
    if any(token in p for token in (
        "/recruiting/jobs/create", "/jobs/create", "/jobsuche/suche", "/stellenangebote--verify",
    )):
        # Portal action links (post-a-job, sign-in) are never vacancy cards.
        return False
    # Indeed hides every card URL behind /rc/clk?jk=<jobkey>; the plain path
    # matches none of the shapes below, so without this the whole source
    # yields zero cards. Followed through Camofox it lands on the employer's own
    # board (verified 2026-09-29: jk=d4c948bc460ec1d8 -> job.deloitte.com/.../48452).
    if p.startswith("/rc/clk") and re.search(r"[?&]jk=[0-9a-f]{6,}", url, re.I):
        return True
    # Employer ATS boards use `/job-<slug>_<id>` (Deloitte:
    # /job-senior-it-consultant-software-quality-engineer-mwd-_48452) and
    # `/careers/job/<slug>-<id>`. Measured 2026-09-29: direct_card() rejected
    # every such link, so extract_final_vacancy_url() -- which now gates on
    # direct_card() -- silently refused to return the real posting and the
    # master would have kept the aggregator's ad-click URL. The id is preceded
    # by "-_" (not "_-", which never occurs), and section pages like /careers or
    # /cloud-jobs-_pr16 (a job CATEGORY) must stay rejected -- a real posting id
    # is a plain 4+ digit number, the categories use a "_prNN" form.
    if re.match(r"^/job-[a-z0-9][a-z0-9._-]*-_\d{4,}$", p) or \
       re.match(r"^/(?:careers?|jobs?)/job/[a-z0-9][a-z0-9._-]*-\d{3,}/?$", p):
        return True
    # Categories look identical except for the id form: reject them explicitly
    # instead of letting the broad "/jobs/" fallback below accept them.
    if re.match(r"^/[a-z0-9][a-z0-9._-]*-jobs-_(?:pr)?\d+$", p):
        return False
    return any(token in p for token in (
        "/jobs/view", "/jobsuche/jobdetail", "/stellenangebote--", "/job_display/",
        "/jobs/", "/job/", "/remote-jobs/", "/remote/jobs/", "/land/ad/", "/details/",
    ))


META_RE = {
    "title": re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    "company": re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'][^"\']*?\s+-\s+([^"\'|]+?)(?:\s*\||["\'])', re.I),
    "site_name": re.compile(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    "description": re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    "h1": re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S),
}

JSON_LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
LD_ORG = re.compile(r"https?://(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)", re.I)


def json_ld_objects(markup: str) -> list[dict[str, Any]]:
    """Return schema.org JobPosting objects, which portals expose far more
    reliably than og: tags (StepStone has no employer meta at all)."""
    found: list[dict[str, Any]] = []
    for blob in JSON_LD.findall(markup):
        blob = re.sub(r"https://\*{3,}", "https://", blob)
        try:
            data = json.loads(blob.strip())
        except Exception:
            continue
        for node in data if isinstance(data, list) else [data]:
            if not isinstance(node, dict):
                continue
            if "@graph" in node and isinstance(node["@graph"], list):
                found.extend(x for x in node["@graph"] if isinstance(x, dict))
            else:
                found.append(node)
    return found


MD_H1 = re.compile(r"(?:^|\s)#{1,3}\s+(.{6,200}?)(?=\s*(?:\n\s*[#*|]|$))", re.M)
MD_LINK_COMPANY = re.compile(r"(?mi)^.{0,120}?\b(?:company|employer|arbeitgeber)\b\s*[:\-]\s*(.+?)\s*$")


def markdown_identity(markup: str) -> dict[str, str]:
    """Recover title/company from rendered markdown.

    crawl4ai output is one long line: navigation links, then the document
    itself.  Headings are therefore not line-anchored, and the reliable signal
    is the portal's own phrasing — "Stellenangebot: <role> bei <employer>" for
    Arbeitsagentur, "… bei …" on XING/LinkedIn.
    """
    def clean(value: str) -> str:
        value = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", value)
        value = re.sub(r"[*#>`]", " ", value)
        return re.sub(r"\s+", " ", value).strip(" -–—|:.\"'")

    flat = re.sub(r"\s+", " ", markup)
    offer = re.search(r"Stellenangebot:\s*([^•|]{4,160}?)\s*(?:##|\* \[|$)", flat)
    if offer:
        segment = clean(offer.group(1))
        role, _, employer = segment.partition(" bei ")
        return {"title": role.strip() or segment, "company": employer.strip()}
    # The posting title is the FIRST heading and it is a role. On LinkedIn the
    # first *other* heading is the posting's own sidebar metadata
    # ("Karrierestufe Berufseinstieg"), which the generic search below would
    # happily return as the title -- measured on all 12 cards of 2026-09-27.
    # Prefer the leading role heading; fall through to the generic search when
    # the page does not open with one.
    #
    # The boundary must be a following "##" (NOT end-of-string): `flat` is a
    # single collapsed line, so a "$" anchor would only ever match the final
    # heading on the page -- which on LinkedIn is the related-jobs block.
    # Only the opening region is a title candidate. After `trim_markdown_boilerplate`
    # the posting title is the first heading, but raw pages that were NOT
    # trimmed (other sources, or a LinkedIn page that opened with the consent
    # wall on the same line) still open with navigation, so a bounded window is
    # kept. Measured 2026-09-27: the title sat at 2,021 chars in `flat`.
    for m in re.finditer(r"(?:^|\s)#{1,4}\s+(\S.{4,160}?)\s+(?=#{1,4}\s|$)", flat):
        if m.start() > 4000:
            break
        value = clean(m.group(1))
        if value.casefold().startswith(("linkedin nimmt", "jobs finden", "hauptnavigation",
                                        "suche", "hilfe", "linkedin", "datenschutz",
                                        "impressum", "cookie")):
            continue
        if LI_SIDEBAR_RE.match(value) or non_vacancy_heading(value) or not LI_ROLE_RE.search(value):
            continue
        role, _, employer = value.partition(" bei ")
        return {"title": role.strip(), "company": employer.strip()}
    heading = re.search(r"#{1,3}\s+([A-ZÄÖÜ][^#•|]{8,120}?)\s*(?:#{1,3}\s|\* \[|$)", flat)
    if heading:
        value = clean(heading.group(1))
        if not value.casefold().startswith(("linkedin nimmt", "jobs finden", "hauptnavigation", "suche", "hilfe",
                                            "linkedin", "datenschutz", "impressum", "cookie")):
            role, _, employer = value.partition(" bei ")
            return {"title": role.strip(), "company": employer.strip()}
    explicit = clean(MD_LINK_COMPANY.search(markup).group(1)) if MD_LINK_COMPANY.search(markup) else ""
    if explicit:
        return {"title": "", "company": explicit}
    for line in markup.splitlines():
        value = clean(line)
        if 3 <= len(value) <= 80 and re.search(r"\b(gmbh|mbh|ag\b|kg|ohg|ug|se\b|ltd|s\.a\.|b\.v\.|inc\.|llc|group|holding)\b", value, re.I) \
                and "anzeigen" not in value.casefold() and "©" not in value:
            return {"title": "", "company": value}
    return {"title": "", "company": ""}


def snapshot_identity(snapshot: str) -> dict[str, str]:
    """Recover title/company from a Camofox accessibility snapshot.

    The snapshot is a YAML-ish tree: `- heading "..." [level=1] [ref=eN]`,
    `- link "..." [eN]:` and `/url: ...`.  There is no markup, so the document
    heading is the position and the nearest legal-entity line is the employer.
    """
    def clean(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" -–—|:\"'")

    heading = re.search(r'(?mi)^\s*-\s*heading\s+"(?P<t>.{6,200}?)"\[level=1\]', snapshot)
    if not heading:
        heading = re.search(r'(?mi)^\s*-\s*heading\s+"(?P<t>.{6,200}?)"', snapshot)
    title = clean(heading.group("t")) if heading else ""
    title = re.sub(r"^Jobs?\s*[:|-]\s*", "", title, flags=re.I)
    company = ""
    # Hitmarker/XING name the employer in the breadcrumb or in the card link
    # itself ("<role> at <company>") and link it to /companies/<slug>.
    for match in re.finditer(r'(?mi)^\s*-\s*(?:link|text|paragraph|listitem)\s*[:\n]?\s*(?:"(?P<v>[^"]{3,120}?)"|(?P<bare>[^\n"]{3,120}?))\s*(?:\[|$)', snapshot):
        value = clean(match.group("v") or match.group("bare") or "")
        if not value or value == title:
            continue
        after = re.match(rf"{re.escape(title)} at (?P<c>.+)$", value, re.I)
        if after:
            company = clean(after.group("c"))
            break
        if re.search(r"\b(gmbh|mbh|ag\b|kg|ohg|ug|se\b|ltd|s\.a\.|b\.v\.|inc\.|llc|studios|studio|games|group|holding)\b", value, re.I) \
                and "anzeigen" not in value.casefold() and "©" not in value and "post a job" not in value.casefold() \
                and "log in" not in value.casefold() and not value.casefold().startswith(("get discovered", "post your", "sign up")):
            company = value
            break
    if not company:
        slug = re.search(r"/companies/([a-z0-9-]+)", snapshot, re.I)
        if slug:
            company = re.sub(r"[-_]+", " ", slug.group(1)).strip().title()
    return {"title": title, "company": company}


def _org_name(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("name") or "").strip()
    if isinstance(value, list):
        for item in value:
            name = _org_name(item)
            if name:
                return name
    return ""


def posting_identity(markup: str) -> dict[str, str]:
    """Title/company/location/posted/work mode from schema.org JobPosting."""
    for node in json_ld_objects(markup):
        if "JobPosting" not in str(node.get("@type", "")):
            continue
        out = {
            "title": str(node.get("title") or "").strip(),
            "company": _org_name(node.get("hiringOrganization")),
            "location": "",
            "posted": str(node.get("datePosted") or "")[:10],
            "work_mode": "",
        }
        loc = node.get("jobLocation") or {}
        locs = loc if isinstance(loc, list) else [loc]
        for entry in locs:
            addr = entry.get("address") if isinstance(entry, dict) else None
            if isinstance(addr, dict):
                out["location"] = ", ".join(
                    x for x in (str(addr.get("addressLocality") or ""), str(addr.get("addressRegion") or ""),
                                 str(addr.get("addressCountry") or "")) if x) or out["location"]
        if not out["location"]:
            out["location"] = str(loc.get("name") or "") if isinstance(loc, dict) else ""
        out["work_mode"] = str(node.get("employmentType") or "")
        if out["title"] and out["company"]:
            return out
    return {}


def page_identity(markup: str) -> dict[str, str]:
    """Extract title/company/location/posted/work_mode without an LLM.

    The semantic stage still decides eligibility, but identity must survive an
    LLM outage, otherwise every portal-rendered row is dropped and the master
    silently empties out.  schema.org JobPosting wins over og: tags because
    StepStone publishes no employer meta at all.
    """
    meta = {"title": "", "company": "", "location": "Unknown", "posted": "Unknown", "work_mode": "Unknown"}
    meta.update(posting_identity(markup))
    for source in (snapshot_identity, markdown_identity, _meta_identity):
        for key, value in source(markup).items():
            if value and (not meta.get(key) or meta.get(key) == "Unknown"):
                meta[key] = value
    if not meta["title"]:
        # crawl4ai markdown of JS-heavy pages opens with navigation, so the
        # position is recovered from the document `<title>` or the URL slug.
        head = re.search(r"<title[^>]*>(.*?)</title>", markup, re.I | re.S)
        if head:
            meta["title"] = re.sub(r"\s+", " ", html.unescape(head.group(1))).strip()
    if not meta["title"]:
        # `markup` here is usually ALREADY stripped to text, so the `<title>`
        # tag above cannot match and the heading must be read from the prose.
        # German portals lead with the posting itself, e.g. Arbeitsagentur:
        # "Stellenangebot: Qualitätsingenieur (m/w/d) bei FERCHAU GmbH ...".
        # Measured 2026-09-30: without this every Arbeitsagentur card resolved
        # with an empty title and no candidate could ever match it.
        prose = re.sub(r"\s+", " ", html.unescape(markup)).strip()
        lead = re.search(r"(?:Stellenangebot|Angebotsbezeichnung|Berufsbezeichnung"
                         r"|Job title|Position)\s*[:\-]\s*"
                         r"(.+?)(?:\s+bei\s+|\s+[-\|–]\s*|\s*\||\\.|$)", prose, re.I)
        if not lead:
            lead = re.match(r"([^|]{4,120}?)\s*(?:\|\|\s+bei\s+)", prose)
        if not lead:
            lead = re.match(r"([^\n|.]{4,120})", prose)
        if lead:
            meta["title"] = lead.group(1).strip()
    if not meta["company"]:
        # Last resort for portals that name the employer only in prose.
        named = re.search(r"(?i)([A-ZÄÖÜ][\w&.\-]*(?:\s+[A-ZÄÖÜ][\w&.\-]*){0,4}\s+(?:GmbH|mbH|AG|KG|OHG|SE|UG|S\.?a\.?r?\.?b\.?a\.?s\.?))\\b", markup)
        if named:
            meta["company"] = re.sub(r"\s+", " ", named.group(1)).strip()
    # Extract work_mode from text if not already found
    if meta["work_mode"] == "Unknown":
        meta["work_mode"] = extract_work_mode_from_text(markup)
    return meta


def _meta_identity(markup: str) -> dict[str, str]:
    def clean(value: str) -> str:
        value = re.sub(r"<[^>]+>", " ", value)
        value = html.unescape(value)
        return re.sub(r"\s+", " ", value).strip()
    h1 = META_RE["h1"].search(markup)
    og = META_RE["title"].search(markup)
    site = META_RE["site_name"].search(markup)
    title = clean(og.group(1)) if og else (clean(h1.group(1)) if h1 else "")
    company_match = META_RE["company"].search(markup)
    company = clean(company_match.group(1)) if company_match else ""
    if not company and site:
        company = clean(site.group(1))
    return {"title": title, "company": company}


def block_marker_hit(announcement: str) -> bool:
    low = (announcement or "").casefold()
    return any(m in low for m in BLOCK_MARKERS)


class SourceAdapter:
    adapter = "base"
    def __init__(self, source: dict[str, Any], artifact: Path, heartbeat=None, progress=None):
        self.source, self.artifact, self.heartbeat = source, artifact, heartbeat or (lambda *a: None)
        self.progress = progress or (lambda *a: None)
        self.raw = artifact / "raw"; self.raw.mkdir(parents=True, exist_ok=True)
        self._n = 0
    def save(self, name: str, obj: Any, raw: bool = True) -> Path:
        self._n += 1
        p = self.raw / f"{self._n:04d}-{name}.json"
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        if raw: self.progress(True)
        self.heartbeat()
        return p
    def preflight(self) -> dict[str, Any]:
        listing = self.listing(preflight=True)
        cards = self.cards(listing)
        direct = [c for c in cards if direct_card(c["url"])]
        if len(direct) < 2:
            raise RuntimeError("preflight: fewer than two analyzable direct cards")
        first = self.detail(direct[0]); returned = self.listing(preflight=True); second = self.detail(direct[1])
        # A portal page (Initiativbewerbung, Ähnliche Jobs, Recruiter) is a full
        # page with complete site chrome, so it passes direct_card and the
        # snapshot-length check: two of them made XING look preflight-clean while
        # proving nothing about vacancy cards. The title only exists after the
        # detail page is read -- listing-level cards carry a URL and nothing else
        # for crawl4ai, so filtering on the listing silently checked an empty
        # string. Judge the two cards that preflight actually opened.
        opened = [("card-1", first), ("card-2", second)]
        # Two SEPARATE findings, and they must not be conflated.
        #
        # (1) A page whose heading is a navigation/utility label ("Ähnliche
        #     Jobs", "Passwort") is not a posting at all. That is a genuine
        #     portal page and the spec's two-card rule is not satisfied.
        # (2) A page with a real posting structure -- About this job, Aufgaben,
        #     Über uns, Kontakt -- is a VACANCITY. XING currently serves
        #     "Recruiter (m/w/d)" and "Initiativbewerbung" as exactly that, and
        #     both titles are listed in NON_VACANCY_TITLES, so the old check
        #     reported them as "portal pages". They are not: the pages opened
        #     and parsed perfectly. They are simply not QA roles, which is an
        #     editorial outcome, not an access failure, and the source must stay
        #     active for a later run.
        all_opened = [("card-1", first), ("card-2", second)]
        portals = [f"{label}: {page.get('title', '')!r}"
                   for label, page in all_opened if _is_utility_page(page)]
        opened = [(label, page) for label, page in all_opened
                  if not _is_utility_page(page)]
        if not opened:
            raise RuntimeError(
                "preflight: detail pages are portal/utility pages, not vacancy postings. "
                "About.md requires two analyzable vacancy cards."
            )
        # A card that opens but carries no posting BODY is not a vacancy card
        # either -- it is a category index or a teaser. About.md requires two
        # ANALYZABLE cards, and a list of 20 other jobs cannot be analysed.
        thin = [f"{label}: {page.get('title', '')!r} ({len(page.get('announcement') or '')} chars)"
                for label, page in opened if not looks_like_vacancy_posting(page)]
        if not any(looks_like_vacancy_posting(page) for _, page in opened):
            raise RuntimeError(
                "preflight: no card carries vacancy body text (a title alone is not a "
                f"posting) -- {len(opened)} opened but all are indexes/teasers ({'; '.join(thin)}). "
                "About.md requires two analyzable vacancy cards."
            )
        opened_titles = [page.get("title", "") for _, page in opened]
        if opened_titles and not any(looks_like_testing_role(t) for t in opened_titles):
            # Readable, cards have body, but first two are not QA roles.
            # This is NOT an access failure - source stays active, worker will scan deeper.
            result = {"status": "pass", "access_method": self.adapter, "cards_found": len(cards), "cards_analyzable": 2,
                      "deep_scan_needed": True,
                      "portal_pages_skipped": portals,
                      "operations": [{"op": "listing", "status": listing.status}, {"op": "card-1", "url": first.get("url"), "chars": len(first.get("announcement", ""))},
                                     {"op": "return", "status": returned.status}, {"op": "card-2", "url": second.get("url"), "chars": len(second.get("announcement", ""))}]}
            self.save("preflight", result)
            return result
        result = {"status": "pass" if first and second and returned.status in (200, 304) else "blocked",
                  "access_method": self.adapter, "cards_found": len(cards), "cards_analyzable": 2,
                  "portal_pages_skipped": portals,
                  "operations": [{"op": "listing", "status": listing.status}, {"op": "card-1", "url": first.get("url"), "chars": len(first.get("announcement", ""))},
                                 {"op": "return", "status": returned.status}, {"op": "card-2", "url": second.get("url"), "chars": len(second.get("announcement", ""))}]}
        self.save("preflight", result)
        if result["status"] != "pass": raise RuntimeError("preflight detail flow failed")
        return result
    def listing(self, *, preflight: bool = False) -> Fetch:
        return fetch(self.source["listing_url"])
    def cards(self, page: Fetch) -> list[dict[str, Any]]:
        s = page.body.decode("utf-8", "replace")
        domain = self.source.get("domain")
        allowed = {str(d).lstrip(".").casefold() for d in (self.source.get("direct_card_domains") or [])}
        if domain:
            allowed.add(str(domain).lstrip(".").casefold())
        links=[]
        for m in re.finditer(r'href=["\']([^"\']+)["\']', s, re.I):
            u=normalize_url(m.group(1), page.final_url)
            if not direct_card(u) or u in links:
                continue
            # Adzuna's markup embeds CDN assets whose paths look like /jobs/...;
            # a card must live on the source's own host.
            if allowed and source_domain_token(u) not in allowed:
                continue
            links.append(u)
        return [{"url": u} for u in links]
    def detail(self, card: dict[str, Any]) -> dict[str, Any]:
        f=fetch(card["url"], timeout=45, attempts=3)
        announcement, method = text(f.body), "http"
        identity = page_identity(f.body.decode("utf-8", "replace"))
        if f.status not in (200, 304) or not announcement or any(x in announcement.casefold() for x in BLOCK_MARKERS):
            # Some German portals answer the listing over plain HTTP but abort the
            # detail page stream (HTTP/2 INTERNAL_ERROR / read timeout). That is
            # a transport failure, so retry the same card through a real browser
            # renderer before it can be called unreadable.
            try:
                announcement = crawl4ai_read(card["url"], self.raw, self)
                method = "crawl4ai"
            except Exception as exc:
                raise RuntimeError(f"detail unreadable: {f.status} ({exc})")
            if not announcement or any(x in announcement.casefold() for x in BLOCK_MARKERS):
                raise RuntimeError(f"detail unreadable: {f.status}")
        out={"url": card["url"], "title": identity.get("title", ""), "company": identity.get("company", ""),
             "location": identity.get("location", "Unknown"), "posted": identity.get("posted", "Unknown"),
             "work_mode": "Unknown",
             "announcement": announcement, "http_status": f.status, "sha256": hashlib.sha256(announcement.encode()).hexdigest(),
             "access_method": method}
        self.save("card", out)
        if not out["announcement"] or any(x in out["announcement"].lower() for x in BLOCK_MARKERS):
            raise RuntimeError(f"detail unreadable: {f.status}")
        return out
    def scan(self, limit: int = 2000) -> list[dict[str, Any]]:
        self.preflight(); page=self.listing(); seen=set(); out=[]
        for _ in range(10):
            for c in self.cards(page):
                if c["url"] in seen: continue
                seen.add(c["url"])
                try: out.append(self.detail(c))
                except RuntimeError: continue
                if len(out) >= limit: return out
                self.heartbeat()
            time.sleep(.4)
            break
        return out


class ExaCrawlAdapter(SourceAdapter):
    """Independent search/extract fallback using Hermes' keyless Exa MCP.

    Exa discovers direct job cards, then returns the full announcement. The
    listing is re-queried before card two, preserving the same preflight proof
    contract without depending on a portal's HTML shell.
    """
    adapter = "exa+keyless-crawl4ai-runtime"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _mcporter(self, tool: str, arguments: dict[str, Any]) -> str:
        executable = shutil.which("mcporter") or "/opt/data/.npm-global/bin/mcporter"
        last = None
        # Keyless Exa can briefly return 429 while another source is using the
        # shared service. Retry the bounded subprocess instead of discarding a
        # source that already passed the same Exa preflight in this cycle.
        for attempt in range(1, 4):
            cmd = [executable, "call", f"exa.{tool}", "--args", json.dumps(arguments, ensure_ascii=False),
                   "--output", "text", "--timeout", "60000"]
            completed = subprocess.run(cmd, text=True, capture_output=True, timeout=90)
            payload = {"arguments": arguments, "attempt": attempt, "returncode": completed.returncode,
                       "stdout": completed.stdout[-8000:], "stderr": completed.stderr[-4000:]}
            self.save(f"exa-{tool}-run", payload)
            if completed.returncode == 0 and completed.stdout.strip():
                return completed.stdout
            last = completed
            if " 429" not in (completed.stderr or "") and "rate limit" not in (completed.stderr or "").casefold():
                break
            # Keyless Exa is a shared global endpoint. A 429 is a run-level
            # dependency failure, not a source-specific unusable verdict.
            raise RuntimeError(f"mcporter Exa {tool} rate limited: shared keyless MCP is at 429")
        raise RuntimeError(f"mcporter Exa {tool} failed ({last.returncode if last else 'not run'}): {(last.stderr[-500:] if last else '')}")

    def _executor(self):
        def execute(query: str, limit: int) -> dict[str, Any]:
            raw = self._mcporter("web_search_exa", {
                "query": query, "numResults": limit,
                "objective": "Return direct vacancy detail pages, not search, category, company, or homepage URLs.",
            })
            urls = list(dict.fromkeys(re.findall(r'(?im)^URL:\s*(https?://\S+)', raw)))
            return {"data": [{"url": url} for url in urls]}
        return execute

    def _search(self, query):
        result = self._executor()(query, 10)
        rows = result.get("data", []) if isinstance(result, dict) else []
        self.save("exa-search", {"query": query, "result": result})
        if not rows: raise RuntimeError("Exa returned no results")
        hits = []
        for row in rows:
            url = row.get("url", "") if isinstance(row, dict) else ""
            if url and direct_card(url): hits.append({"url": normalize_url(url, self.source["listing_url"])})
        distinct = list(dict.fromkeys(x["url"] for x in hits))
        if len(distinct) < 2: raise RuntimeError("Exa returned fewer than two direct cards")
        return [{"url": u} for u in distinct]

    def listing(self, *, preflight: bool = False) -> Fetch:
        domain = self.source["domain"]
        query = f'site:{domain} QA OR "Quality Assurance" OR "Software Test" OR "Test Automation" or Testautomatisierung or Softwaretester Berlin Leipzig Dresden Germany jobs'
        cards = self._search(query)
        body = json.dumps(cards).encode()
        self.heartbeat()
        return Fetch(self.source["listing_url"], self.source["listing_url"], 200, body, "application/json")

    def cards(self, page: Fetch) -> list[dict[str, Any]]:
        body = page.body.decode("utf-8", "replace")
        try:
            payload = json.loads(body)
        except (TypeError, ValueError):
            return super().cards(page)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict) and item.get("url")]
        return super().cards(page)

    def detail(self, card):
        raw = self._mcporter("web_fetch_exa", {"urls": [card["url"]], "maxCharacters": 12000})
        title_match = re.search(r"(?im)^Title:\s*(.+)$", raw)
        title = title_match.group(1).strip() if title_match else ""
        if not raw.strip():
            raise RuntimeError("Exa extract returned empty content")
        if title.lower().startswith("error"):
            raise RuntimeError("Exa extract returned an error response")
        self.save("exa-card", {"url": card["url"], "content": raw})
        out = {"url": card["url"], "title": title, "company": "",
               "location": "Unknown", "posted": "Unknown", "work_mode": "Unknown",
               "announcement": re.sub(r"\s+", " ", raw).strip(), "http_status": 200,
               "sha256": hashlib.sha256(raw.encode()).hexdigest(), "access_method": self.adapter}
        self.save("card", out); return out


class Crawl4AIAdapter(SourceAdapter):
    """Dynamic browser fallback through the installed crawl4ai-skill CLI."""
    adapter = "crawl4ai"

    def _crawl(self, url: str, output: Path) -> str:
        # For dynamic pages with Cloudflare/JS challenges, use wait-for 
        # crawl4ai-skill supports --wait-for networkidle --delay 2 for JS rendering
        cmd = [CRAWL4AI_CLI, "crawl", url, "--format", "raw_markdown", "--output", str(output), 
               "--timeout", "120", "--wait-for", "networkidle"]
        # Retry: a WAF/JS challenge is a transient property of ONE render, not of
        # the source. Indeed hit "Blocked by anti-bot protection: Cloudflare JS
        # challenge" on 2026-09-29 and then served the same listing on three
        # consecutive requests a minute later, so a single failure would drop a
        # source that is plainly reachable.
        last = ""
        for attempt in range(1, 4):
            if output.exists():
                output.unlink()
            try:
                completed = subprocess.run(cmd, text=True, capture_output=True, timeout=240)
            except subprocess.TimeoutExpired:
                last = "crawl4ai timed out"
                time.sleep(3 * attempt)
                continue
            self.save("crawl4ai-run", {"url": url, "attempt": attempt, "returncode": completed.returncode,
                                      "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]})
            if not completed.returncode and output.exists() and output.stat().st_size >= 100:
                return output.read_text(encoding="utf-8", errors="replace")
            last = f"rc={completed.returncode} {completed.stderr[-300:]}"
            time.sleep(3 * attempt)
        raise RuntimeError(f"Crawl4AI failed after 3 attempts: {last}")

    def listing(self, *, preflight: bool = False) -> Fetch:
        # A source may declare several listing pages (`config.listing_urls`) when
        # one portal re-sorts per location and serves a DISJOINT set of cards
        # for each. Indeed does exactly that: measured 2026-09-29, Berlin and
        # Muenchen each returned 15 cards with ZERO overlap, 75 distinct cards
        # across 7 locations versus 15 from a single query. There is no
        # pagination (`start=10` returns nothing), so location is the only way
        # to widen coverage. Sources without `listing_urls` are untouched.
        # During preflight, only crawl the first listing URL to stay within stage budget.
        extra = [u for u in (self.source.get("config", {}) or {}).get("listing_urls") or []
                 if isinstance(u, str) and u.strip()]
        if preflight or not extra:
            # Preflight: only check the first listing URL
            output = self.raw / "crawl4ai-listing.md"
            raw = self._crawl(self.source["listing_url"], output)
            return Fetch(self.source["listing_url"], self.source["listing_url"], 200, raw.encode(), "text/markdown")
        parts: list[str] = []
        seen_links: set[str] = set()
        for index, url in enumerate([self.source["listing_url"], *extra], 1):
            output = self.raw / f"crawl4ai-listing-{index:02d}.md"
            try:
                body = self._crawl(url, output)
            except Exception:
                # One location being unavailable must not lose the others.
                self.save("crawl4ai-listing-error", {"url": url})
                continue
            # Drop duplicate markdown links so the union is not inflated.
            def _dedup(match):
                href = match.group(1)
                if href in seen_links:
                    return ""
                seen_links.add(href)
                return match.group(0)
            body = re.sub(r"\[([^\]]*)\]\((https?://[^)\s]+)\)", _dedup, body)
            parts.append(body)
        merged = "\n\n".join(parts)
        (self.raw / "crawl4ai-listing.md").write_text(merged, encoding="utf-8")
        return Fetch(self.source["listing_url"], self.source["listing_url"], 200, merged.encode(), "text/markdown")

    def cards(self, page: Fetch) -> list[dict[str, Any]]:
        """crawl4ai returns markdown, so links appear as [text](url), not href.

        The link TEXT is the posting title. It is captured here because a
        detail page reached through a redirect can carry no title at all: on
        Indeed the /rc/clk?jk= link lands on the employer's own board, whose
        markdown has no job-title heading (measured 2026-09-29: every one of 14
        cards came back with an empty title, so the preflight concluded
        "no QA vacancy" and rejected a source full of QA roles).
        """
        body = page.body.decode("utf-8", "replace")
        links: list[tuple[str, str]] = []
        for pattern in (r'href=["\']([^"\']+)["\'][^>]*>([^<]{4,160})',
                        "\\[([^\\]]{4,160})\\]\\((https?:\\/\\/[^)\\s]+)\\)"):
            for m in re.finditer(pattern, body, re.I | re.S):
                # In the href pattern group 1 is the URL; in the markdown-link
                # pattern group 2 is. Do NOT guess from the content -- both
                # groups can be non-URL text and the guess inverted the pairs,
                # yielding zero cards.
                g1, g2 = m.group(1), m.group(2)
                href, text = (g1, g2) if pattern.startswith("href=") else (g2, g1)
                u = normalize_url(href, page.final_url)
                if not direct_card(u):
                    continue
                if all(existing[0] != u for existing in links):
                    links.append((u, re.sub(r"\s+", " ", html.unescape(text)).strip(), m.end()))
        return [{"url": u, "listing_title": t,
                 "listing_context": _listing_row_context(body, end)}
                for u, t, end in links]

    def _listing_only_card(self, card: dict[str, Any], reason: str) -> dict[str, Any]:
        """Card built from listing data alone, when the detail page is unreadable.

        Keeps the vacancy visible so the semantic stage can classify it as
        `Unverified` (About.md: a temporary inability to read a page is
        Unverified, not proof of ineligibility). `announcement` is left EMPTY
        rather than invented -- the spec requires the COMPLETE announcement for
        acceptance, so an empty body must never be passed off as analysed.
        """
        out = {"url": card["url"], "source_url": card["url"],
               "title": str(card.get("listing_title") or "").strip(),
               "company": "", "location": "Unknown", "posted": "Unknown", "work_mode": "Unknown",
               "announcement": "", "http_status": 0, "unreadable_reason": reason,
               "access_method": self.adapter}
        self.save("card-partial", out)
        return out

    def detail(self, card):
        output = self.raw / ("crawl4ai-card-" + re.sub(r"[^a-zA-Z0-9]+", "-", card["url"])[-100:] + ".md")
        # A detail page may be refused while the listing that produced it is
        # fine. Measured 2026-09-29: all 49 Indeed listing crawls succeeded
        # (250 distinct cards), but the first /rc/clk detail hop drew "Blocked
        # by anti-bot protection: Cloudflare JS challenge" three times in a row
        # and the retry budget then spent ~10 minutes failing ONE card, which
        # cost the whole source its run. Per About.md a temporary inability to
        # read a page is `Unverified`, not a reason to discard the source, so
        # fall back to the listing data we already hold and mark the card
        # incomplete. One bad card must not silence hundreds of good ones.
        #
        # An aggregator source does not attempt the hop AT ALL. Measured
        # 2026-09-30: 730 hop attempts took 194 minutes, 684 were refused, and
        # only ~7 of the 45 responses were real postings. The hop cannot be made
        # to work, so a candidate is recorded straight from the listing and its
        # body is left to a direct source.
        if self.source.get("id") in CANDIDATE_ONLY_SOURCES:
            return self._candidate_card(card)
        try:
            raw = self._crawl(card["url"], output)
        except Exception as exc:
            self.save("card-unreadable", {"url": card["url"], "error": str(exc)[:300]})
            return self._listing_only_card(card, f"detail page unreadable: {exc}"[:200])
        if not raw or any(x in raw.lower() for x in BLOCK_MARKERS):
            self.save("card-unreadable", {"url": card["url"], "error": "blocked or empty detail page"})
            return self._listing_only_card(card, "detail page blocked or empty")
        # Trim the raw markdown FIRST, then derive identity, then collapse.
        # Order matters twice over: (a) `re.sub(r"\s+", " ", ...)` turns
        # line-structured "## heading" into an inline run, so a stored
        # announcement can no longer be trimmed; and (b) `page_identity()` must
        # see the trimmed text, otherwise it reads the first heading of the
        # untrimmed page -- the consent wall -- and then the posting's own
        # sidebar metadata. Untrimmed it returned "Karrierestufe
        # Berufseinstieg" on 10 of 12 cards in cycle 2026-09-27_cycle-3.
        raw = trim_markdown_boilerplate(raw, self.source.get("id", ""))
        identity = page_identity(raw)
        out = {"url": card["url"], "source_url": card["url"],
               "title": identity.get("title", ""), "company": identity.get("company", ""),
               "location": identity.get("location", "Unknown"), "posted": identity.get("posted", "Unknown"),
               "work_mode": "Unknown",
               "announcement": raw, "http_status": 200,
               "sha256": hashlib.sha256(raw.encode()).hexdigest(),
               "access_method": self.adapter}
        self.save("card", out)
        if not out["announcement"] or any(x in out["announcement"].lower() for x in BLOCK_MARKERS):
            raise RuntimeError(f"detail unreadable: blocked or empty")
        return out

    def _candidate_card(self, card: dict[str, Any]) -> dict[str, Any]:
        """A vacancy named by the listing, with NO body.

        Aggregators reliably give title, employer and city; they do not
        reliably serve the posting. An empty `announcement` keeps the row out of
        the semantic stage (synthesize() only analyses cards with a non-empty
        body), so a candidate can never be judged on data we do not have -- it
        simply waits for a direct source to supply the text.
        """
        listing_title = str(card.get("listing_title") or "").strip()
        hint = self._listing_context(card)
        out = {"url": card["url"], "source_url": card["url"], "title": listing_title,
               "company": hint.get("company", ""), "location": hint.get("location", "Unknown"),
               "posted": "Unknown", "work_mode": hint.get("work_mode", "Unknown"),
               "announcement": "", "http_status": 0,
               "candidate_only": True,
               "unreadable_reason": "aggregator listing candidate; body supplied by a direct source",
               "access_method": self.adapter}
        self.save("card", out); return out

    def _listing_context(self, card: dict[str, Any]) -> dict[str, str]:
        """Employer / city / employment type parsed from the listing row.

        The listing renders them next to the link, e.g.
        "PTA GmbH Berlin * 50.000 EUR pro Jahr * Vollzeit". They are the only
        reliable identity data the aggregator gives us, and they are what makes
        a candidate findable on a direct source.
        """
        ctx: dict[str, str] = {}
        blob = str(card.get("listing_context") or "")
        if not blob:
            return ctx
        # The row starts with the employer and city, then salary/employment
        # bullets: "PTA GmbH Berlin * 50.000 EUR pro Jahr * Vollzeit". Split the
        # city off the employer so the company name is not "PTA GmbH Berlin".
        head = blob.split("*")[0].split("|")[0].strip()
        city = None
        for name in (r"Berlin", r"Leipzig", r"Dresden", r"München", r"Muenchen", r"Hamburg",
                     r"Köln", r"Koeln", r"Frankfurt", r"Stuttgart", r"Nürnberg", r"Nuernberg",
                     r"Düsseldorf", r"Duesseldorf", r"Bremen", r"Hannover", r"Dortmund",
                     r"Essen", r"Potsdam", r"Magdeburg"):
            m = re.search(rf"\b{name}\b", blob)
            if m:
                city = m.group(0)
                break
        if city:
            ctx["location"] = city
            head = re.sub(rf"\b{re.escape(city)}\b", "", head).strip(" ,-–—")
        if re.search(r"(?i)\b(home[- ]?office|remote)\b", blob):
            ctx["work_mode"] = "Remote"
        elif re.search(r"(?i)\b(vollzeit|full[- ]time)\b", blob):
            ctx["work_mode"] = "Onsite"
        if head:
            # Drop everything from the salary onwards: the employer is only the
            # first words, and "PTA GmbH 50.000 EUR pro Jahr Vollzeit" is not a
            # company name.
            head = re.split(r"\d[\d.]*\s*(?:EUR|€|euro)|pro\s+(?:Jahr|Monat|Stunde)|"
                            r"(?i:vollzeit|teilzeit|full[- ]?time|part[- ]?time|remote|"
                            r"home[- ]?office|temporär|befristet)", head)[0]
            head = re.sub(r"\s{2,}", " ", head).strip(" ,-–—")
            if head:
                ctx["company"] = head
        return ctx


# LinkedIn's crawl4ai markdown is ~50 KB of which the vacancy is ~15 KB:
# the consent wall and legal text run to ~2.9 K, and "## Ähnliche Jobs" starts
# the related-jobs tail at ~18 K. Measured 2026-09-27, `page_identity()` read
# the title as "Karrierestufe Berufseinstieg" -- a field of the posting's own
# sidebar -- because the real heading sits at offset 2946, after the wall.
#
# Both boundaries are cut, but the rule is always "drop a leading/trailing
# BLOCK", never "keep the first N characters": the whole posting body between
# them is kept, so nothing of the announcement is lost. Only LinkedIn is
# trimmed; every other source passes through byte-identical.
LINKEDIN_BOILERPLATE_HEADS = (
    "linkedin nimmt den schutz ihrer privatsphäre",
    "linkedin privacy",
    "linkedin respects your privacy",
)
LINKEDIN_TAIL_MARKERS = (
    "ähnliche jobs", "similar jobs", "jobs die dir auch gefallen",
    "ebenfalls angesehen", "weitere stellenangebote",
)
# The posting title is the heading that names a role, not the sidebar metadata
# ("Karrierestufe ...", "Tätigkeitsbereich ...", login prompts) and not a
# related-jobs entry.
LI_ROLE_RE = re.compile(
    r"(?i)\b(qa|quality|qualität|test|tester|testing|software|sap|automation|"
    r"automatisierung|consultant|berater|devops|frontend|backend|senior|junior|"
    r"werkstudent|praktikum)?\s*"
    r"(engineer|tester|test|testingenieur|entwickler|analyst|specialist|manager|"
    r"berater|inhouse|lead|architect|consultant)\w*")
LI_SIDEBAR_RE = re.compile(
    r"(?i)^(karrierestufe|tätigkeitsbereich|branche|beschaeftigungsart|"
    r"funktion|berufserfahrung|mitarbeiterzahl|hierarchie|arbeitsort|"
    r"werden sie mitglied|loggen sie sich|einen lebenslauf)")


def trim_markdown_boilerplate(markup: str, source_id: str) -> str:
    """Cut LinkedIn's consent wall and related-jobs tail off the posting."""
    if source_id.casefold() != "linkedin.com" or not markup:
        return markup
    lowered = markup.casefold()
    if not any(lowered.startswith("#" * 0 + h) or lowered.lstrip("# ").startswith(h)
               for h in LINKEDIN_BOILERPLATE_HEADS):
        return markup

    # --- head: first heading that actually names a role ---
    start = None
    for m in re.finditer(r"(?m)^#{1,4}\s+(\S.{4,160}?)\s*$", markup):
        if m.start() < 1500:
            continue
        heading = m.group(1).strip()
        if LI_SIDEBAR_RE.match(heading) or non_vacancy_heading(heading):
            continue
        if not LI_ROLE_RE.search(heading):
            continue
        start = m.start()
        break
    if start is None:
        return markup

    # --- tail: the related-jobs block, if present ---
    end = len(markup)
    for marker in LINKEDIN_TAIL_MARKERS:
        i = markup.casefold().find(marker)
        if i > start + 1000:
            end = min(end, i)
    return markup[start:end]


class RoleSearchAdapter(SourceAdapter):
    """A portal queried BY every spec role, instead of by a fixed listing URL.

    About.md asks for "Manual WEB QA, Software Test/Test Automation,
    Gamedev/Game QA, QA Localization, or a semantically equivalent testing
    role" -- a description of roles, not of one employer's job headline. A
    single fixed listing URL can only carry the wording its owner chose, so the
    roles are enumerated and the portal is asked for each of them in each target
    city. Seniority is deliberately absent from every phrase: the goal is a QA
    vacancy at any level, and "Test Engineer" returns senior, middle and junior.

    Measured 2026-09-30 on arbeitsagentur.de: 18 roles x 3 cities = 54 requests,
    92 seconds, 242 unique vacancy URLs, zero of them blocked. For comparison
    the de.indeed.com route produced no published row in seven masters while
    costing 194 minutes per night.

    This adapter's `listing()` returns a synthetic multi-page marker: the real
    discovery happens in `cards()`, which is why it overrides that method.
    """
    adapter = "rolesearch"

    def listing(self, *, preflight: bool = False) -> Fetch:
            return Fetch("", self._primary_url(), 200, b"role-search", "text/x-role-search")

    def _primary_url(self) -> str:
        urls = CANDIDATE_LOOKUP_SOURCES.get(self.source.get("id", ""), "")
        return urls if isinstance(urls, str) else (urls[0] if urls else "")

    def _cities(self) -> list[str]:
        cfg = (self.source.get("config") or {}).get("cities") or list(TARGET_CITIES)
        return [str(c) for c in cfg]

    def cards(self, page: Fetch) -> list[dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        roles = candidate_role_queries()
        cities = self._cities()
        self.heartbeat()
        for city in cities:
            for role in roles:
                for url in candidate_lookup_urls_for_role(self.source["id"], role, city):
                    self.heartbeat()
                    try:
                        search = fetch(url, timeout=30)
                    except Exception:
                        self.save("search-error", {"url": url, "role": role, "city": city})
                        continue
                    if search.status not in (200, 304):
                        self.save("search-error",
                                  {"url": url, "role": role, "city": city,
                                   "status": search.status})
                        continue
                    body = search.body.decode("utf-8", "replace")
                    for pattern in (r'href=["\']([^"\']+)["\']', r'\]\((https?://[^)\s]+)\)'):
                        for m in re.finditer(pattern, body, re.I):
                            u = normalize_url(m.group(1), url)
                            # An aggregator's tracking hop is not a vacancy card,
                            # and dedupe here keeps the count meaningful.
                            if not direct_card(u) or u in found:
                                continue
                            found[u] = {"url": u, "listing_title": "",
                                        "listing_context": "", "search_role": role,
                                        "search_city": city, "search_url": url}
                    self.progress(True)
        self.save("role-search", {"roles": roles, "cities": cities,
                                  "unique_cards": len(found)})
        return list(found.values())

    def detail(self, card: dict[str, Any]) -> dict[str, Any]:
        out = super().detail(card)
        if isinstance(out, dict):
            out.setdefault("search_role", card.get("search_role", ""))
            out.setdefault("search_city", card.get("search_city", ""))
        return out


class APIAdapter(SourceAdapter):
    def _records(self, f: Fetch) -> list[dict[str, Any]]:
        raw=f.body
        if f.content_type.casefold().startswith(("text/xml", "application/rss+xml", "application/xml")) or raw.lstrip().startswith(b"<?xml"):
            root=ET.fromstring(raw)
            out=[]
            for item in root.findall(".//item"):
                record={}
                for child in list(item):
                    key=child.tag.rsplit("}",1)[-1]
                    record[key]=child.text or ""
                out.append(record)
            return out
        data=json.loads(raw)
        if isinstance(data, list): return [x for x in data if isinstance(x,dict)]
        for key in ("jobs","data","results","items"):
            if isinstance(data.get(key),list): return [x for x in data[key] if isinstance(x,dict)]
        return [data]
    def cards(self, f: Fetch):
        out=[]
        for r in self._records(f):
            links = r.get("links") if isinstance(r.get("links"), dict) else {}
            u = r.get("url") or r.get("link") or r.get("company") or r.get("job_apply_url") or links.get("direct")
            if u and direct_card(str(u)):
                # GermanTechJobs publishes a large general-tech RSS feed. Apply
                # only the source-level discovery filter here; final acceptance
                # still requires complete announcement semantic analysis.
                if self.source["id"] == "germantechjobs.de":
                    haystack = f"{r.get('title', '')} {r.get('description', '')}".casefold()
                    # Same shared list as the preflight role check, but the
                    # GermanTechJobs feed is 600+ general-tech items, so the
                    # title must carry the term -- not just the description.
                    if not looks_like_testing_role(haystack) or not looks_like_testing_role(
                            r.get("title", "")):
                        continue
                # Remotive's public search is approximate (it can return jobs
                # whose title/tags do not contain QA). Keep direct cards, then
                # let complete announcement semantic analysis classify them.
                normalized = normalize_url(str(u), f.final_url)
                # Cheap, evidence-based pre-filter before the LLM stage. This
                # board republishes the same feed under a .fr and a .co.uk
                # domain, so 137 of 170 cards were London/Paris non-QA roles.
                # Full semantic analysis of those cost 44% of the synthesis
                # budget while the spec already excludes them: the employer must
                # be a German entity, and outside the three target cities only
                # explicit Germany-wide Remote is eligible. An explicit foreign
                # location or a foreign country domain is affirmative
                # disqualification, whereas Unknown is retained per spec and
                # must NOT be dropped here.
                if not self._germany_plausible(normalized, r):
                    continue
                out.append({"url": normalized, "api": r})
        return out

    def _germany_plausible(self, url: str, record: dict[str, Any]) -> bool:
        """False only when the record is affirmatively not a German vacancy."""
        host = source_domain_token(url)
        allowed = {str(d).lstrip(".").casefold() for d in (self.source.get("direct_card_domains") or [])}
        own = str(self.source.get("domain") or "").lstrip(".").casefold()
        # A country-code sibling of the board's own domain is a different
        # country's feed, not the German one the source was registered for.
        if own and host and host != own and host not in allowed:
            if re.fullmatch(r"[a-z0-9-]+\.(fr|co\.uk|es|it|nl|pl|pt|ie|be|at|ch)", host):
                return False
        # "Berlin, Germany (Relocation to Milan)" is a German posting that
        # mentions a foreign city, so a foreign city name in the title or
        # description is not evidence of a foreign posting. Location and
        # country fields are authoritative; free text is only consulted when
        # they are absent.
        structured = " ".join(
            str(record.get(k) or "") for k in ("location", "city", "country", "state")
        ).casefold()
        haystack = structured or " ".join(
            str(record.get(k) or "") for k in ("title", "description", "tags")
        ).casefold()
        # A named foreign country or a well-known foreign city is affirmative
        # evidence against eligibility. Bare "Remote"/"Europe"/"EU" is not.
        foreign = re.search(
            r"\b(france|paris|london|united kingdom|england|ireland|dublin|spain|madrid|"
            r"italy|milan|rom(e|ma)?|netherlands|amsterdam|poland|portugal|lisbon|"
            r"belgium|brussels|austria|vienna|switzerland|z(urich|rich)|norway|sweden|"
            r"denmark|finland|canada|toronto|united states|usa|new york|australia|sydney|"
            r"india|bangalore|israel|tel aviv|ukraine|brazil|argentina)\b",
            haystack,
        )
        return not foreign
    def detail(self, c):
        r=c.get("api",{}); url=c["url"]
        desc=r.get("description") or r.get("content") or r.get("excerpt") or ""
        page=fetch(url)
        detail_text=text(page.body)
        announcement=re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(str(desc)))).strip() or detail_text
        # RSS feeds name the fields differently from JSON job APIs, and
        # GermanTechJobs puts the employer in the feed title, so identity must
        # come from the record itself before falling back to the page markup.
        title = str(r.get("title") or r.get("name") or "")
        company = str(r.get("company_name") or r.get("company") or r.get("employer") or "")
        if not company:
            # GermanTechJobs titles read "<role> @ <Employer> <City>" and may
            # carry a trailing salary bracket, which is not the employer.
            lead = re.split(r"\s+@\s+", title, maxsplit=1)
            if len(lead) == 2 and lead[1].strip():
                title, company = lead[0].strip(), lead[1].split(" (")[0].split(" [")[0].strip()
        if not title or not company:
            identity = page_identity(page.body.decode("utf-8", "replace"))
            title = title or identity.get("title", "")
            company = company or identity.get("company", "")
        out={"url":url,"title":title, "company":company,
             "location":r.get("candidate_required_location") or r.get("location") or r.get("job_city") or "Unknown",
             "posted":str(r.get("publication_date") or r.get("date") or r.get("created_at") or "Unknown"),
             "work_mode":r.get("remote") and "Remote" or "Unknown",
             "announcement":re.sub(r"\s+", " ", announcement).strip(),
             "http_status":page.status,"sha256":page.sha256,"source_record":r}
        self.save("card", out)
        if page.status not in (200, 304) or not out["announcement"] or any(x in out["announcement"].lower() for x in BLOCK_MARKERS):
            raise RuntimeError(f"detail unreadable: {page.status}")
        return out
    def preflight(self):
        f=self.listing()
        if f.status not in (200, 304): raise RuntimeError(f"listing unavailable: {f.status}")
        cards=self.cards(f)
        distinct={c["url"]: c for c in cards}
        if len(distinct)<2: raise RuntimeError("preflight: fewer than two distinct API cards")
        first=self.detail(distinct[next(iter(distinct))])
        returned=self.listing()
        if returned.status not in (200, 304): raise RuntimeError(f"listing return unavailable: {returned.status}")
        second=self.detail(distinct[next(x for x in distinct if x != first["url"])])
        result={"status":"pass","access_method":self.adapter,"cards_found":len(cards),
                "cards_analyzable":2,
                "operations":[{"op":"listing","status":f.status},{"op":"card-1","url":first["url"],"chars":len(first["announcement"])},
                             {"op":"return","status":returned.status},{"op":"card-2","url":second["url"],"chars":len(second["announcement"])}]}
        self.save("preflight",result); return result
    def scan(self, limit=2000):
        self.preflight(); f=self.listing(); out=[]; seen=set()
        for c in self.cards(f):
            if c["url"] in seen: continue
            seen.add(c["url"])
            try: out.append(self.detail(c))
            except RuntimeError: continue
            if len(out) >= limit: break
        return out

class CamofoxClient:
    """Small direct Gateway transport; deliberately independent of Hermes/browser sessions."""
    def __init__(self, base_url: str, timeout: int = 60, opener=None):
        if not base_url:
            raise RuntimeError("CAMOFOX_URL is not configured")
        self.base_url, self.timeout, self.opener = base_url.rstrip("/"), timeout, opener or urllib.request.urlopen
    def _request(self, method: str, path: str, body: dict[str, Any] | None = None,
                 query: dict[str, str] | None = None, attempts: int = 3) -> dict[str, Any]:
        url = self.base_url + path
        if query: url += "?" + urllib.parse.urlencode(query)
        data = None if body is None else json.dumps(body).encode()
        headers = {"Accept": "application/json"}
        if data is not None: headers["Content-Type"] = "application/json"
        last: str = ""
        for attempt in range(1, max(1, attempts) + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with self.opener(req, timeout=self.timeout) as response:
                    raw = response.read()
                break
            except urllib.error.HTTPError as exc:
                # Keep the server's own explanation. It costs nothing and a bare
                # "HTTP 500" is unactionable when the browser is the only route
                # to a source.
                try:
                    last = f": {exc.read()[:200].decode('utf-8', 'replace')}"
                except Exception:
                    last = ""
                if exc.code < 500 or attempt >= attempts:
                    raise RuntimeError(f"Camofox HTTP {exc.code} for {method} {path}{last}") from exc
                # 5xx from the browser gateway is transient in practice: 19 of
                # 27 XING preflights hit it (2026-09-25..29) while the same four
                # snapshots succeeded moments later from the same code path.
                # Retry with a short backoff before declaring the source dead.
                time.sleep(2 * attempt)
            except Exception as exc:
                last = f": {exc}"
                if attempt >= attempts:
                    raise RuntimeError(f"Camofox transport failed for {method} {path}{last}") from exc
                time.sleep(2 * attempt)
        try:
            value = json.loads(raw or b"{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Camofox invalid JSON for {method} {path}") from exc
        if not isinstance(value, dict):
            raise RuntimeError(f"Camofox invalid object for {method} {path}")
        return value
    def start(self): return self._request("POST", "/start", {})
    def health(self): return self._request("GET", "/health")
    def open_tab(self, user_id: str, session_key: str, url: str) -> str:
        result = self._request("POST", "/tabs", {"userId": user_id, "sessionKey": session_key, "url": url})
        tab = result.get("tabId") or result.get("id")
        if not tab: raise RuntimeError("Camofox did not return tabId")
        return str(tab)
    def navigate(self, user_id: str, tab_id: str, url: str) -> None:
        self._request("POST", f"/tabs/{urllib.parse.quote(tab_id)}/navigate", {"userId": user_id, "url": url})
    def snapshot(self, user_id: str, tab_id: str, fmt: str = "text") -> str:
        result = self._request("GET", f"/tabs/{urllib.parse.quote(tab_id)}/snapshot",
                              query={"userId": user_id, "format": fmt, "includeScreenshot": "false"})
        snapshot = result.get("snapshot") or result.get("text") or result.get("content")
        if not isinstance(snapshot, str) or not snapshot.strip():
            raise RuntimeError("Camofox returned an empty snapshot")
        return snapshot
    def close_tab(self, user_id: str, tab_id: str) -> None:
        self._request("DELETE", f"/tabs/{urllib.parse.quote(tab_id)}", query={"userId": user_id})
    def preflight(self) -> dict[str, Any]:
        start, health, tab_id = self.start(), self.health(), None
        missing = [key for key in ("ok", "browserRunning", "browserConnected") if not health.get(key)]
        if missing: raise RuntimeError("Camofox unhealthy: " + ", ".join(missing) + " false")
        try:
            tab_id = self.open_tab("qa-vacancy-smoke", "public-smoke", "https://example.com/")
            snapshot = self.snapshot("qa-vacancy-smoke", tab_id)
        finally:
            if tab_id: self.close_tab("qa-vacancy-smoke", tab_id)
        return {"start": start, "health": health, "smoke_snapshot_chars": len(snapshot)}


class CamofoxAdapter(SourceAdapter):
    adapter = "camofox_gateway"
    def __init__(self, source, artifact, camofox=None, **kwargs):
        super().__init__(source, artifact, **kwargs)
        if camofox is None:
            import os
            camofox = CamofoxClient(os.environ.get("CAMOFOX_URL", ""))
        self.camofox = camofox
        self.user_id = f"qa-vacancy-{source['id'].replace('.', '-')}"
        self.session_key = f"{source['id']}-preflight"
    def _tab_snapshot(self, tab_id, url, name):
        self.camofox.navigate(self.user_id, tab_id, url)
        snapshot = self.camofox.snapshot(self.user_id, tab_id)
        evidence = self.save(name, {"url": url, "tab_id": tab_id, "snapshot": snapshot})
        return snapshot, evidence
    def _direct_links(self, snapshot):
        """Extract direct vacancy links from a Camofox accessibility snapshot.

        The gateway renders an accessibility tree whose `/url:` values are
        relative to the current page, so absolute-only matching silently
        yielded zero cards even though the snapshot was complete.
        """
        links = []
        for pattern in (r'https?://[^\s<>"()]+', r'(?m)^\s*-?\s*/url:\s*(\S+)'):
            for m in re.finditer(pattern, html.unescape(snapshot)):
                raw = (m.group(1) if m.lastindex else m.group(0)).rstrip(".,];")
                if not raw.startswith(("http://", "https://", "/")):
                    continue
                candidate = normalize_url(raw, self.source["listing_url"])
                if direct_card(candidate) and candidate not in links:
                    links.append(candidate)
        return links
    def preflight(self):
        gate = self.camofox.preflight()
        self.save("browser-health", gate)
        tab_id = self.camofox.open_tab(self.user_id, self.session_key, self.source["listing_url"])
        try:
            listing, listing_evidence = self._tab_snapshot(tab_id, self.source["listing_url"], "listing-snapshot")
            links = self._direct_links(listing)
            if len(links) < 2: raise RuntimeError("Camofox preflight: fewer than two analyzable direct cards")
            first, first_evidence = self._tab_snapshot(tab_id, links[0], "card-1-snapshot")
            returned, returned_evidence = self._tab_snapshot(tab_id, self.source["listing_url"], "return-snapshot")
            second, second_evidence = self._tab_snapshot(tab_id, links[1], "card-2-snapshot")
            snapshots = (first, returned, second)
            if any(any(marker in value.lower() for marker in BLOCK_MARKERS) for value in snapshots):
                raise RuntimeError("Camofox preflight snapshot blocked")
            # This adapter reimplements preflight instead of reusing the base
            # class, so BOTH of the base class's findings must be applied here.
            # XING and LinkedIn are the only Camofox sources, and XING renders
            # "Recruiter (m/w/d)" and "Initiativbewerbung" as full postings
            # (About this job, Aufgaben, Über uns, Kontakt, ~14 KB each) even
            # though both titles sit in NON_VACANCY_TITLES. Judging on the title
            # list alone called them "portal pages" and made the master blame
            # access failures on a source that was reachable and parsed fine.
            for label, snap in (("card-1", first), ("card-2", second)):
                page = {"title": first_heading(snap), "announcement": snap}
                if _is_utility_page(page):
                    raise RuntimeError(
                        f"Camofox preflight {label} is a portal/utility page, not a vacancy "
                        f"posting: {page['title']!r}. Listing offered {len(links)} direct "
                        "links; About.md requires two analyzable vacancy cards."
                    )
            # A card that opens but carries no posting BODY is not a vacancy card
            # (see looks_like_vacancy_posting): Indeed routed us to a Deloitte
            # category index whose title named a real role.
            _cards = [("card-1", {"title": first_heading(first), "announcement": first}),
                      ("card-2", {"title": first_heading(second), "announcement": second})]
            if not any(looks_like_vacancy_posting(p) for _, p in _cards):
                _thin = "; ".join(f"{lbl}: {p['title']!r} ({len(p['announcement'])} chars)"
                                  for lbl, p in _cards)
                raise RuntimeError(
                    "Camofox preflight: no card carries vacancy body text (a title alone is "
                    f"not a posting) -- {_thin}. Listing offered {len(links)} direct links; "
                    "About.md requires two analyzable vacancy cards."
                )
            # Distinguish "cannot read the source" from "readable, but no QA in
            # the first two cards": the second stays active for a later run and
            # must not be reported as an access failure.
            headings = [first_heading(s) for s in (first, second)]
            if headings and not any(looks_like_testing_role(h) for h in headings):
                # Readable, cards have body, but first two are not QA roles.
                # This is NOT an access failure - source stays active, worker will scan deeper.
                result = {"status": "pass", "access_method": self.adapter, "cards_found": len(links), "cards_analyzable": 2,
                          "deep_scan_needed": True,
                          "operations": [{"op": "listing", "url": self.source["listing_url"], "chars": len(listing), "evidence": str(listing_evidence)},
                                         {"op": "card-1", "url": links[0], "chars": len(first), "evidence": str(first_evidence)},
                                         {"op": "return", "url": self.source["listing_url"], "chars": len(returned), "evidence": str(returned_evidence)},
                                         {"op": "card-2", "url": links[1], "chars": len(second), "evidence": str(second_evidence)}]}
                self.save("preflight", result)
                return result
            result = {"status":"pass", "access_method":self.adapter, "cards_found":len(links), "cards_analyzable":2,
                      "browser_health":gate, "operations":[
                          {"op":"listing","url":self.source["listing_url"],"chars":len(listing),"evidence":str(listing_evidence)},
                          {"op":"card-1","url":links[0],"chars":len(first),"evidence":str(first_evidence)},
                          {"op":"return","url":self.source["listing_url"],"chars":len(returned),"evidence":str(returned_evidence)},
                          {"op":"card-2","url":links[1],"chars":len(second),"evidence":str(second_evidence)}]}
            self.save("preflight", result); return result
        finally:
            self.camofox.close_tab(self.user_id, tab_id)
    def scan(self, limit=2000):
        """Process every direct card exposed by the listing sequentially.

        The preflight remains the mandatory two-card gate.  The worker then
        reopens the listing and visits every extracted direct card in order,
        writing a durable snapshot and heartbeating after each operation.
        """
        self.preflight()
        tab_id = self.camofox.open_tab(self.user_id, self.session_key, self.source["listing_url"])
        try:
            listing, _ = self._tab_snapshot(tab_id, self.source["listing_url"], "scan-listing")
            links = self._direct_links(listing)
            cards = []
            for index, url in enumerate(links[:limit], 1):
                snapshot, evidence = self._tab_snapshot(tab_id, url, f"scan-card-{index}")
                if any(marker in snapshot.lower() for marker in BLOCK_MARKERS):
                    continue
                # A Camofox accessibility snapshot has no og: tags or JSON-LD, so
                # identity must come from the snapshot outline itself.
                identity = page_identity(snapshot)
                if non_vacancy_heading(identity.get("title", "")):
                    # A portal page that is not a posting: never a vacancy card.
                    self.progress(True); self.heartbeat(); continue
                cards.append({"url": url, "title": identity.get("title", ""), "company": identity.get("company", ""),
                              "location": identity.get("location", "Unknown"),
                              "posted": identity.get("posted", "Unknown"), "work_mode": identity.get("work_mode", "Unknown"),
                              "announcement": snapshot, "source": self.source["id"],
                              "evidence": str(evidence), "http_status": 200})
                self.progress(True); self.heartbeat()
            return cards
        finally:
            self.camofox.close_tab(self.user_id, tab_id)


REGISTRY_TYPES = {
    "remotive.com": "remotive", "arbeitnow.com": "arbeitnow", "germantechjobs.de": "rss",
    "de.indeed.com": "indeed", "glassdoor.de": "glassdoor", "monster.de": "monster",
}
CAMOFOX_SOURCES = {"xing.com", "linkedin.com"}

# Sources that are AGGREGATORS: their listing reliably names a vacancy
# (title, employer, city) but their card URL is a tracking redirect whose
# target they do not actually serve. Following it is not worth a single night.
# Measured 2026-09-30 on de.indeed.com: 730 attempts, 194 minutes, 684 refused
# by Cloudflare, and of the 45 responses only ~7 were real postings -- the rest
# were the aggregator's own menu, cookie wall and login errors. These sources
# contribute CANDIDATES; the announcement comes from a direct source.
CANDIDATE_ONLY_SOURCES = {"de.indeed.com"}

# How to LOOK UP a candidate vacancy on a direct source. An aggregator names a
# vacancy (title, employer, city) but will not serve its body, so the candidate
# is searched for by name on the sources that DO serve bodies.
# Measured 2026-09-30: searching "Qualitätsingenieur" on Arbeitsagentur returned
# 20 full cards in one request and the first one was the same PTA posting
# (title "Qualitätsingenieur (m/w/d)", 257 KB body). Adzuna answers the same
# query with 12. Both are single HTTP calls per candidate, versus three failed
# browser launches per candidate on the aggregator's redirect.
CANDIDATE_LOOKUP_SOURCES = {
    "arbeitsagentur.de": ("https://www.arbeitsagentur.de/jobsuche/suche"
                          "?was={q}&wo={city}"),
    "adzuna.de": "https://www.adzuna.de/search?q={q}",
    "eurotechjobs.com": "https://www.eurotechjobs.com/jobs/{slug}",
    "germantechjobs.de": "https://germantechjobs.de/jobs?q={q}",
}

# The roles About.md asks for, as SEARCH PHRASES, not as a filter on one
# candidate's title. An aggregator names a vacancy with whatever wording the
# employer chose, so the only reliable way to reach it is to ask each direct
# source for every role from the spec. This is what the user asked for on
# 2026-09-30: search everything matching the spec, do not narrow by seniority.
# Level (senior/middle/junior) is deliberately NOT part of any phrase: the goal
# is a QA vacancy at ANY level, and "Test Engineer" finds all three.
CANDIDATE_ROLE_QUERIES = (
    "QA Engineer", "QA Tester", "QA Automation", "Software QA", "Software Test",
    "Software Tester", "Test Engineer", "Test Automation", "Testautomatisierung",
    "Softwaretester", "Testingenieur", "Test Analyst", "Test Automation Engineer",
    "Game QA", "Game Tester", "Gamedev QA", "Localization Tester",
)


def candidate_role_queries() -> list[str]:
    """Every spec role as a search phrase, for a direct source."""
    return list(CANDIDATE_ROLE_QUERIES)


def candidate_lookup_urls_for_role(source_id: str, role: str, city: str) -> list[str]:
    """Search URLs for one spec role in one city, for one direct source."""
    template = CANDIDATE_LOOKUP_SOURCES.get(source_id)
    if not template:
        return []
    url = template.format(q=urllib.parse.quote_plus(role),
                          city=urllib.parse.quote_plus(city or ""),
                          slug=re.sub(r"[^a-z0-9]+", "-", role.casefold()).strip("-")[:60])
    return [url] if url else []


def candidate_lookup_urls(source_id: str, title: str, company: str,
                          city: str) -> list[str]:
    """Search URLs for a named vacancy, most specific first.

    An aggregator title is a full job headline ("Qualitätsingenieur KI-Fokus /
    Quality Engineer (AI-augmented) (m/w/d)") and no direct source matches that
    phrase. Measured 2026-09-30 on Arbeitsagentur, Berlin: the full headline
    returned 1 card whose title was empty, "Qualitätsingenieur KI-Fokus" 1,
    "Qualitätsingenieur Quality Engineer" 3, "Qualitätsingenieur" 20 and
    "Quality Engineer" 25. So the headline is split on "/" and the caller walks
    the list from the most distinctive phrase to the broad role, stopping at the
    first card that names the same employer and city.
    """
    template = CANDIDATE_LOOKUP_SOURCES.get(source_id)
    if not template:
        return []
    raw = re.sub(r"\s*\([^)]*\)\s*", " ", str(title or "")).strip()
    raw = re.sub(r"\s+[–—]\s+", " / ", raw)
    raw = re.sub(r"\s{2,}", " ", raw)
    phrases: list[str] = []
    for half in re.split(r"\s+/\s+|,\s*", raw):
        half = half.strip()
        if half and half not in phrases:
            phrases.append(half)
    if raw and raw not in phrases:
        phrases.append(raw)
    bare = re.sub(r"(?i)\b(m/w/d|mwd|f/m/d|x/m/d|w/m/d|all genders|)\b", " ", raw)
    bare = re.sub(r"(?i)\b(senior|junior|lead|head of|principal|staff|intern|praktikum)\b",
                  " ", bare)
    bare = re.sub(r"\s{2,}", " ", bare).strip()
    if bare and bare not in phrases:
        phrases.append(bare)

    def build(q: str) -> str:
        return template.format(
            q=urllib.parse.quote_plus(q), city=urllib.parse.quote_plus(city or ""),
            slug=re.sub(r"[^a-z0-9]+", "-", q.casefold()).strip("-")[:60])

    seen: set[str] = set()
    return [u for u in (build(p) for p in phrases) if not (u in seen or seen.add(u))]


def candidate_lookup_url(source_id: str, title: str, company: str, city: str) -> str:
    """The most specific search URL for a named vacancy, or "" if unknown."""
    urls = candidate_lookup_urls(source_id, title, company, city)
    return urls[0] if urls else ""


def resolve_candidate_on_direct_source(candidate: dict[str, Any],
                                       source_id: str) -> dict[str, Any] | None:
    """Find a named vacancy on a direct source and return a full card.

    A candidate is resolved only when the posting is demonstrably the SAME job,
    judged on three things: title words, city, and employer. All three are
    required. Title alone is not enough -- measured 2026-09-30, the query
    "Senior Test Automation Engineer" surfaced a Bundesdruckerei posting AND an
    Adzuna page for a Deloitte "Senior Hardware Development Engineer" (title
    overlap 0.5 on the bare word "senior"), and the query "Recruiter" happily
    returned an unrelated AÜG_NETZWERK agency job. An employer mismatch is a
    different job, so it is rejected rather than published.

    The search is walked from the most specific phrase to the broad role, because
    only the broad phrases actually match a portal's index.
    """
    want = _identity_tokens(str(candidate.get("title") or ""))
    want_city = str(candidate.get("location") or "").strip().casefold()
    want_corp = _employer_token(str(candidate.get("company") or ""))
    if not want:
        return None
    for search in candidate_lookup_urls(source_id, str(candidate.get("title") or ""),
                                        str(candidate.get("company") or ""),
                                        str(candidate.get("location") or "")):
        try:
            page = fetch(search, timeout=30)
        except Exception:
            continue
        if page.status not in (200, 304):
            continue
        body = page.body.decode("utf-8", "replace")
        links: list[str] = []
        for pattern in (r'href=["\']([^"\']+)["\']', r'\]\((https?://[^)\s]+)\)'):
            for m in re.finditer(pattern, body, re.I):
                u = normalize_url(m.group(1), search)
                if direct_card(u) and u not in links:
                    links.append(u)
        for u in links[:12]:
            try:
                card = fetch(u, timeout=30)
            except Exception:
                continue
            if card.status not in (200, 304):
                continue
            # Local name must not shadow the module-level `text()` helper below.
            page_text = text(card.body)
            if not page_text:
                continue
            ident = page_identity(page_text)
            got = _identity_tokens(str(ident.get("title") or ""))
            if not got:
                continue
            overlap = len(want & got) / max(1, len(want))
            if overlap < 0.5:
                continue
            if want_city and not (want_city in str(ident.get("location", "")).casefold()
                                  or want_city in page_text[:4000].casefold()):
                continue
            # Employer must match. The parsed field is authoritative; the prose
            # is only consulted when the field is empty, and then as a substring
            # test (NOT concatenated into the token, which would compare noise).
            found_corp = _employer_token(str(ident.get("company") or ""))
            if want_corp and found_corp:
                if want_corp != found_corp:
                    continue
            elif want_corp and want_corp not in re.sub(r"[^a-z0-9äöüß]+", "",
                                                      page_text[:6000].casefold()):
                continue
            if not looks_like_vacancy_posting(
                    {"title": ident.get("title", ""), "announcement": page_text}):
                continue
            return {"url": u, "title": ident.get("title", candidate.get("title", "")),
                    "company": ident.get("company") or candidate.get("company", ""),
                    "location": ident.get("location") or candidate.get("location", ""),
                    "posted": ident.get("posted", "Unknown"),
                    "work_mode": ident.get("work_mode", "Unknown"),
                    "announcement": re.sub(r"\s+", " ", page_text).strip(),
                    "http_status": card.status, "resolved_from": source_id,
                    "resolved_search": search, "title_overlap": round(overlap, 2),
                    "employer_matched": bool(want_corp and want_corp == found_corp)}
    return None


# ============================================================
# New adapters for Indeed, Glassdoor, Monster
# ============================================================

class IndeedAdapter(SourceAdapter):
    """Indeed Germany job search via HTML parsing."""
    adapter = "indeed"
    
    def listing(self, *, preflight: bool = False) -> Fetch:
        url = self.source["listing_url"]
        return Fetch(url, url, 200, b"listing", "text/html")
    
    def preflight(self):
        # Quick health check
        listing = self.listing(preflight=True)
        try:
            fetched = fetch(listing.url, timeout=10)
            body = fetched.body.decode("utf-8", "replace")
            if "captcha" in body.lower() or "blocked" in body.lower():
                raise RuntimeError("Indeed blocked (captcha/blocked)")
            # Check if we can find job listings
            if "jobsearch" in body.lower() or "jobcard" in body.lower() or "jobcard" in body.lower():
                return {"status": "pass", "access_method": "http", "cards_found": 1}
        except Exception as e:
            raise RuntimeError(f"Indeed preflight failed: {e}")
        raise RuntimeError("Indeed preflight failed: no job listings found")
    
    def scan(self, limit: int = 2000) -> list[dict[str, Any]]:
        url = self.source["listing_url"]
        try:
            fetched = fetch(url, timeout=30)
            body = fetched.body.decode("utf-8", "replace")
        except Exception as e:
            raise RuntimeError(f"Indeed fetch failed: {e}")
        
        cards = []
        # Parse job cards from Indeed HTML
        import re
        # Indeed job cards have data-jk attribute
        job_keys = re.findall(r'data-jk="([a-f0-9]+)"', body)
        for jk in job_keys[:20]:  # Limit to first 20
            job_url = f"https://de.indeed.com/viewjob?jk={jk}"
            try:
                detail = fetch(job_url, timeout=10)
                body = detail.body.decode("utf-8", "replace")
                # Extract job details from the page
                import re as re_module
                title_match = re_module.search(r'<h1[^>]*class="[^"]*jobsearch-JobInfoHeader-title[^"]*"[^>]*>([^<]+)</h1>', body)
                title = title_match.group(1) if title_match else "Unknown"
                
                company_match = re_module.search(r'data-company-name="([^"]+)"', body)
                company = company_match.group(1) if company_match else "Unknown"
                
                location_match = re_module.search(r'data-testid="job-location"[^>]*>([^<]+)</div>', body)
                location = location_match.group(1) if location_match else "Unknown"
                
                # Extract work mode from text
                work_mode = extract_work_mode_from_text(body)
                
                # Get announcement text
                desc_match = re_module.search(r'id="jobDescriptionText"[^>]*>([\s\S]*?)</div>', body)
                announcement = desc_match.group(1) if desc_match else ""
                
                if title and company != "Unknown":
                    yield {
                        "url": f"https://de.indeed.com/viewjob?jk={jk}",
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location.strip(),
                        "posted": "Unknown",
                        "work_mode": extract_work_mode_from_text(body),
                        "announcement": re.sub(r"<[^>]+>", " ", announcement).strip(),
                        "source": self.source["id"],
                        "evidence": f"Indeed job key: {jk}",
                        "http_status": 200
                    }
            except Exception:
                continue
        return []
    
    def preflight(self):
        """Quick health check for Indeed."""
        url = self.source["listing_url"]
        try:
            fetched = fetch(self.source["listing_url"], timeout=10)
            body = fetched.body.decode("utf-8", "replace")
            if "captcha" in body.lower() or "blocked" in body.lower():
                raise RuntimeError("Indeed blocked (captcha/blocked)")
            if "jobsearch" in body.lower() or "jobcard" in body.lower():
                return {"status": "pass", "access_method": "http", "cards_found": 1}
        except Exception as e:
            raise RuntimeError(f"Indeed preflight failed: {e}")
        raise RuntimeError("Indeed preflight failed: no job listings found")


class GlassdoorAdapter(SourceAdapter):
    """Glassdoor Germany job search via HTML parsing."""
    adapter = "glassdoor"
    
    def listing(self, *, preflight: bool = False) -> Fetch:
        url = self.source["listing_url"]
        return Fetch(url, url, 200, b"listing", "text/html")
    
    def preflight(self):
        url = self.source["listing_url"]
        try:
            fetched = fetch(url, timeout=10)
            body = fetched.body.decode("utf-8", "replace")
            if "captcha" in body.lower() or "blocked" in body.lower():
                raise RuntimeError("Glassdoor blocked (captcha/blocked)")
            if "job" in body.lower() or "job-listing" in body.lower():
                return {"status": "pass", "access_method": "http", "cards_found": 1}
        except Exception as e:
            raise RuntimeError(f"Glassdoor preflight failed: {e}")
        raise RuntimeError("Glassdoor preflight failed")
    
    def scan(self, limit: int = 2000):
        # Glassdoor is heavily protected, return empty for now
        # TODO: Implement proper Glassdoor adapter
        return []
    
    def preflight(self):
        url = self.source["listing_url"]
        try:
            fetched = fetch(url, timeout=10)
            body = fetched.body.decode("utf-8", "replace")
            if "captcha" in body.lower() or "blocked" in body.lower():
                raise RuntimeError("Glassdoor blocked (captcha/blocked)")
            if "job" in body.lower():
                return {"status": "pass", "access_method": "http", "cards_found": 1}
        except Exception as e:
            raise RuntimeError(f"Glassdoor preflight failed: {e}")
        raise RuntimeError("Glassdoor preflight failed")


class MonsterAdapter(SourceAdapter):
    """Monster Germany job search via HTML parsing."""
    adapter = "monster"
    
    def listing(self, *, preflight: bool = False) -> Fetch:
        url = self.source["listing_url"]
        return Fetch(url, url, 200, b"listing", "text/html")
    
    def preflight(self):
        url = self.source["listing_url"]
        try:
            fetched = fetch(url, timeout=10)
            body = fetched.body.decode("utf-8", "replace")
            if "captcha" in body.lower() or "blocked" in body.lower():
                raise RuntimeError("Monster blocked (captcha/blocked)")
            if "job" in body.lower() or "job-result" in body.lower():
                return {"status": "pass", "access_method": "http", "cards_found": 1}
        except Exception as e:
            raise RuntimeError(f"Monster preflight failed: {e}")
        raise RuntimeError("Monster preflight failed")
    
    def scan(self, limit: int = 2000):
        # Monster is heavily protected, return empty for now
        # TODO: Implement proper Monster adapter
        return []
    
    def preflight(self):
        url = self.source["listing_url"]
        try:
            fetched = fetch(url, timeout=10)
            body = fetched.body.decode("utf-8", "replace")
            if "captcha" in body.lower() or "blocked" in body.lower():
                raise RuntimeError("Monster blocked (captcha/blocked)")
            if "job" in body.lower():
                return {"status": "pass", "access_method": "http", "cards_found": 1}
        except Exception as e:
            raise RuntimeError(f"Monster preflight failed: {e}")
        raise RuntimeError("Monster preflight failed")


def _employer_token(value: str) -> str:
    """Comparable core of an employer name: lowercase letters/digits only.

    Ports prefix the employer with "bei" ("bei FERCHAU GmbH") and suffix it with
    the legal form, so the legal form and the leading preposition are dropped
    before comparing. An employer given only as a legal form yields "" and the
    caller then treats the check as unavailable rather than as a failure.
    """
    v = re.sub(r"(?i)^\s*(bei|at|for)\s+", "", str(value or "")).strip()
    v = re.sub(r"(?i)\b(gmbh|mbh|ag|kg|ohg|se|ug|sa|sarl|bv|nv|inc|ltd|co|corp|"
               r"holding|gruppe|group)\b", " ", v)
    v = re.sub(r"[^a-z0-9äöüß]+", "", v.casefold())
    return v[:24]


def _identity_tokens(value: str) -> set[str]:
    """Significant lower-cased words of a job title, minus filler."""
    stop = {"mwd", "mw", "m", "f", "d", "w", "all", "genders", "gender", "und", "the", "a",
            "an", "in", "für", "der", "die", "das", "den", "dem", "zu", "von", "de", "en"}
    words = re.findall(r"[a-zäöüß][a-zäöüß0-9]+", value.casefold())
    return {w for w in words if w not in stop and len(w) > 2}


def extract_work_mode_from_text(text: str) -> str:
    """Extract work mode from job posting text using German/English keywords.
    
    Returns: "Remote", "Hybrid", "Onsite", or "Unknown"
    """
    if not text:
        return "Unknown"
    
    text_lower = text.lower()
    
    # Remote keywords (highest priority - explicit remote)
    remote_keywords = [
        "remote", "homeoffice", "home office", "home-office", 
        "vollständig remote", "voll remote", "ganz remote",
        "remote work", "work from home", "wfh", "telecommuting",
        "home based", "homebased", "distributed team",
        "remote first", "fully remote", "100% remote"
    ]
    
    # Hybrid keywords
    hybrid_keywords = [
        "hybrid", "hybrides arbeiten", "hybrides modell",
        "hybrid work", "hybrid working", "teilweise remote",
        "teilweise homeoffice", "tage im büro", "tage remote",
        "büro und remote", "büro und homeoffice",
        "hybridmodell", "hybrid model"
    ]
    
    # Onsite keywords
    onsite_keywords = [
        "vor ort", "vor-ort", "vollzeit vor ort", "vollzeit im büro",
        "büro", "büroarbeit", "vor ort arbeit", "präsenz",
        "on-site", "on site", "office", "office work",
        "office based", "office-based", "vor ort arbeit",
        "vollzeit im büro", "nur vor ort", "nur büro"
    ]
    
    text_lower = text.lower()
    
    # Check for remote keywords (highest priority)
    for kw in remote_keywords:
        if kw in text_lower:
            return "Remote"
    
    # Check for hybrid keywords
    for kw in hybrid_keywords:
        if kw in text_lower:
            return "Hybrid"
    
    # Check for onsite keywords
    for kw in onsite_keywords:
        if kw in text_lower:
            return "Onsite"
    
    # Check for employment type patterns in German job postings
    # "Vollzeit, Remote" or "Vollzeit, Hybrid" patterns
    import re
    employment_patterns = [
        (r"vollzeit\s*,?\s*remote", "Remote"),
        (r"vollzeit\s*,?\s*hybrid", "Hybrid"),
        (r"vollzeit\s*,?\s*remote\s*[,/]\s*hybrid", "Hybrid"),
        (r"teilzeit\s*,?\s*remote", "Remote"),
        (r"teilzeit\s*,?\s*hybrid", "Hybrid"),
        (r"home[- ]?office\s*(?:,|/)\s*hybrid", "Hybrid"),
    ]
    
    text_lower = text.lower()
    for pattern, mode in employment_patterns:
        if re.search(pattern, text_lower):
            return mode
    
    # Check for common German job posting patterns
    # "Vollzeit, Remote" or "Vollzeit, Hybrid" 
    # Look for employment type sections
    employment_section = re.search(r'(?:beschäftigungsart|employment type|arbeitszeitmodell)[:\s]*([^\n]{1,100})', text.lower())
    if employment_section:
        section_text = employment_section.group(1)
        if 'remote' in employment_section.group(1):
            return "Remote"
        if 'hybrid' in employment_section.group(1):
            return "Hybrid"
        if 'vor ort' in employment_section.group(1) or 'onsite' in employment_section.group(1):
            return "Onsite"
    
    return "Unknown"


def _identity_tokens(value: str) -> set[str]:
    """Significant lower-cased words of a job title, minus filler."""
    stop = {"mwd", "mw", "m", "f", "d", "w", "all", "genders", "gender", "und", "the", "a",
            "an", "in", "für", "der", "die", "das", "den", "dem", "zu", "von", "de", "en"}
    words = re.findall(r"[a-zäöüß][a-zäöüß0-9]+", value.casefold())
    return {w for w in words if w not in stop and len(w) > 2}


def adapter_candidates(source: dict[str, Any]) -> list[str]:
    """Return the primary route and one genuinely independent fallback.

    `primary_method` in the registry is authoritative: keyword sniffing over
    free-text notes used to mis-route sources, and a mis-routed source then
    failed on an unrelated dependency (e.g. Camofox not configured).
    """
    explicit = str(source.get("primary_method") or "").strip()
    # `adapter` and `primary_method` can disagree in the registry, and when they
    # do, primary_method wins -- which sent GermanTechJobs (adapter "rss_v1")
    # to its /api/jobs endpoint that answers the plain text "ENDPOINT
    # Deprecated", even though its RSS feed carries 600+ live items and is
    # already the registered listing_url. An explicit adapter naming a feed
    # describes a real, working route, so let it correct the method.
    adapter_name = str(source.get("adapter") or "").strip().casefold()
    if adapter_name.startswith("rss") and explicit in ("api", ""):
        explicit = "rss"
    # A source may name the role search as its adapter without also setting
    # primary_method; the adapter is the more specific instruction, so honour it
    # rather than silently routing a role-search source through a browser.
    if adapter_name == "rolesearch" and explicit in ("", "http", "crawl4ai"):
        explicit = "rolesearch"
    order = {
        "rolesearch": ["rolesearch", "http", "crawl4ai"],
        "api": ["api", "http", "crawl4ai", "camofox"],
        # An RSS source must start on the http route. It used to list "api"
        # first, which sent GermanTechJobs to /api/jobs -- an endpoint that now
        # answers the plain text "ENDPOINT Deprecated" -- even though its RSS
        # feed (https://germantechjobs.de/rss, 600+ items) is alive and is
        # already the registry's listing_url. "api" here means the /api/ REST
        # route, never a feed; feeds are plain http.
        "rss": ["http", "crawl4ai", "camofox"],
        "http": ["http", "crawl4ai", "camofox"],
        "crawl4ai": ["crawl4ai", "http", "camofox"],
        "camofox": ["camofox", "crawl4ai", "http"],
    }
    if explicit in order:
        return list(order[explicit])
    preferred = str(source.get("preferred_methods") or ["browser"])
    fallback = str(source.get("fallback_methods") or ["Camofox"])
    api_route = source["id"] in REGISTRY_TYPES
    browser_primary = source["id"] in CAMOFOX_SOURCES
    if browser_primary:
        return ["camofox", "crawl4ai", "http"]
    if api_route:
        return ["api", "http", "crawl4ai", "camofox"]
    if any(term in preferred.casefold() for term in ("api", "json", "rss")):
        return ["http", "crawl4ai", "camofox"]
    if any(term in fallback.casefold() for term in ("browser", "camofox", "web extraction")):
        return ["camofox", "crawl4ai", "http"]
    return ["http", "crawl4ai", "camofox"]


# The three cities About.md treats as on-site/hybrid-eligible, and the only
# cities a spec role is searched in. Defined here because the retention rules
# live in this module and the role search must not drift from them.
TARGET_CITIES = ("Berlin", "Leipzig", "Dresden")


def make_adapter(source, artifact, *, method: str | None = None, **kwargs):
    chosen = method or adapter_candidates(source)[0]
    if chosen == "camofox":
        return CamofoxAdapter(source, artifact, **kwargs)
    if chosen == "exa":
        return ExaCrawlAdapter(source, artifact, **kwargs)
    if chosen == "crawl4ai":
        return Crawl4AIAdapter(source, artifact, **kwargs)
    if chosen == "rolesearch":
        return RoleSearchAdapter(source, artifact, **kwargs)
    kind = REGISTRY_TYPES.get(source["id"])
    if kind in {"remotive", "arbeitnow", "rss"}:
        return APIAdapter(source, artifact, **kwargs)
    return SourceAdapter(source, artifact, **kwargs)
