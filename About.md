# QA Vacancy Search Project — About

## Goal

Maintain a daily-updated markdown list of unique, verified QA/test vacancies in Germany.

## Acceptance criteria

The pipeline first reads and semantically analyzes the complete announcement, because wording and formats differ across portals. Keyword, title, URL-slug, regex and compact-field matches may discover candidates but cannot independently accept or reject a vacancy.

A vacancy is rendered publicly as `PASS` only if all required conditions are met. A vacancy with a proven QA/test role and a proven eligible location/work-mode option is retained as `PARTIAL` when a secondary evidence gate remains unresolved; formatting differences, compact location fields and unknown work mode are not rejection reasons.

- Role is QA/test-related: Manual WEB QA, Software Test, Test Automation, Gamedev QA, Game QA, QA Localization or a semantically equivalent testing role.
- The employer has a German legal entity, verified through Impressum, Handelsregister or an official company legal page.
- The direct vacancy card is available; search pages, category pages and homepages are forbidden.
- The vacancy was posted no more than 30 days before the run date.
- The location/work-mode combination is accepted:
  - `Onsite` in **Berlin, Leipzig or Dresden**;
  - `Hybrid` in **Berlin, Leipzig or Dresden**;
  - `Remote` only with explicit Germany-wide eligibility (`Germany`, `DE`, `Deutschland`, `bundesweit`, `100% Remote`, or equivalent).
- `Onsite` or `Hybrid` in any other city is rejected.
- Hybrid is rejected outside Berlin, Leipzig and Dresden.
- A generic `Germany` location without explicit remote eligibility is rejected.
- Unclear mode in a confirmed target-city vacancy is retained as `Unknown`; a nonstandard format, compressed location field, or missing dedicated city field is not itself a rejection. Reject only when the complete announcement proves that no target city or Germany-wide remote option exists.
- Vacancies are deduplicated first by exact URL and then by semantic vacancy identity: normalized German legal employer plus official requisition ID when available; otherwise normalized employer + role core + seniority + accepted eligibility scope. Different legal employers are never duplicates merely because titles match. Distinct requisitions at the same employer are not duplicates.

## Output format

The public list preserves the four original category blocks: Manual WEB QA Engineer, Software Test Engineer, Gamedev QA Engineer, and Other QA Roles. Every exact target-city vacancy is placed in its matching category even when another gate is unresolved; unresolved work mode is rendered as `Unknown`, and the `PARTIAL-###` marker is retained. The separate `Partially verified — not counted` block contains only unresolved records outside Berlin, Leipzig, and Dresden. Each category contains accepted PASS rows and target-city PARTIAL rows. The final `Work mode` vocabulary is `Remote`, `Onsite`, `Hybrid`, or `Unknown`; `Unknown` is allowed only for exact target-city locations. PARTIAL records remain on the mandatory next-run review list and do not receive a final `QADE-...` semantic ID until all mandatory gates pass. All accepted rows require row-level provenance covering role, date, location, work mode, German legal entity and verification method.

## Daily pipeline

1. Create or update `SPEC.md` with the recall-oriented semantic gate, including the six evidence gates and the `PASS`/`PARTIAL`/`REJECT` state machine.
2. Before changing the accepted set, extract every unique vacancy URL from all README.md commits in GitHub history and semantically re-audit the full set; historical rows must not disappear silently during filter or source changes.
3. Launch exactly one dedicated **Source Scout subagent at the start of every complete search cycle**. It searches beyond the fixed source list for new ATS platforms, regional and niche boards, employer career sites and other independent sources; verifies live direct vacancy evidence; updates the persistent `/opt/data/qa-vacancy-project/source_registry.json`; and writes a per-cycle scout report. Every newly confirmed source must be queried in the same cycle. Scout failure or an unqueried confirmed addition invalidates the cycle.
4. Parse and validate the complete announcement semantically, then independently verify every candidate. Analyze all location/work-mode blocks: if Berlin, Leipzig or Dresden appears anywhere in a multi-location offer, canonicalize `Location` to one matching target city and keep the vacancy in its role category.
5. Compare exact URLs and semantic vacancy identities with the accumulated known-URL database. Re-fetch every old URL before removal; portal URLs may have expired or retargeted to another vacancy, so a URL alone is never proof of continuing availability.
6. Deduplicate by exact URL and semantic vacancy identity, preserving all alternate source URLs in `url_index`; never merge distinct employers or distinct requisitions merely because titles match.
7. Recheck every carried-forward `PARTIAL` record before searching for new candidates. Promote only when all required gates are affirmatively proven; otherwise retain it in the proper category when a target-city option is proven.
8. Archive the previous published master before replacing it, run the final verifier, and write the new master, `result.md`, and GitHub `README.md` with identical row sets.

## Archive and repeat rule

Before replacing the canonical master, save the previous published file as:

`/opt/data/qa-vacancy-project/qa_vacancies_master_YYYY-MM-DD.md`

Never overwrite an existing dated archive. Keep an accumulated known-URL database and the persistent Source Registry. A search cycle is complete only after exactly one Source Scout has run, every newly confirmed source has been queried, every active registered source and every scope (Berlin, Leipzig, Dresden, Gamedev, Other QA Roles, and Germany-wide Remote) has been searched, and every returned candidate has been semantically checked and deduplicated. If a complete cycle finds at least one new unique eligible vacancy or a newly confirmed useful source, immediately start another full cycle with a new Source Scout. Stop only after one complete cycle finds zero new unique eligible vacancies, adds no new source, and leaves no carried-forward PARTIAL/UNCLEAR unresolved. Scout failure, a skipped/blocked source, an unqueried confirmed source, empty worker output, or timeout invalidates the cycle. Every cycle uses the same acceptance gate.

## Search and verification requirements

- Search queries and vacancy extraction should use German terms such as `Softwaretester`, `QA Engineer`, `Test Engineer`, `Qualitätssicherung`, `Spiele-Tester`, `Manuelle Tests`, `Test Automation` and `Game QA`.
- The listed sources are an active registry baseline, **not a closed allowlist**. Exactly one Source Scout searches for new sources at the start of every complete cycle and updates `/opt/data/qa-vacancy-project/source_registry.json` with verified additions, duplicates, access methods and retirement history.
- Try at least two access methods for blocked sources.
- For every URL use `curl -L` or browser/web extraction and record the verification method. Expand dynamic sections and analyze the complete announcement semantically; do not infer validity from one compact location field.
- Verify the posting date from JSON-LD or visible source text.
- Verify the German legal entity from Impressum/Handelsregister/legal page.
- If evidence is ambiguous, do not guess. The decision is recall-oriented: preserve a proven target-city or Germany-wide remote opportunity as `PARTIAL` when a secondary evidence gate is unresolved, instead of rejecting it because the portal format is unusual or a compact field omits information.
- For multi-location postings, accept the opportunity when any applicable work-location block includes Berlin, Leipzig or Dresden. Canonicalize the public `Location` to one matching target city. A city merely described as “bei Dresden” is not Dresden and must not be treated as an exact target city.
- Before rejecting an existing row because its portal returned 404/410, retargeted, or lost the original card, try at least two independent access methods and inspect the full current page. Reject only when the identity is proven lost or the current evidence affirmatively fails a gate. If identity cannot be established, retain the historical opportunity as `PARTIAL` with an audit note.

## Sources

| Source | Method | Notes |
|---|---|---|
| LinkedIn Jobs | Guest API/browser | Good coverage; use `f_TPR=r2592000`, remote filters when available |
| Arbeitsagentur | Public API/JSON-LD/browser | Reliable dates and German locations |
| StepStone | Browser/Camofox | Cloudflare may block curl; browser verification is acceptable |
| XING | Browser | Use last-month filters |
| hitmarker | Browser/web_extract | Gamedev-specific source |
| Company ATS | Browser/web_extract | Prefer direct employer cards |

## Pipeline schedule and maintenance

- Daily cron runs the full pipeline and stores a dated run log.
- A run is complete only after the final master passes full-announcement semantic validation, exact-URL and semantic-identity deduplication, evidence-state checks, link identity checks and table validation. Regex, keyword, URL-slug and compact-field matches are discovery aids only; they cannot independently accept or reject a vacancy.
- Published files must be synchronized between the project master, `result.md` and GitHub `README.md`.
- Keep dated historical masters; do not delete them.

## Verification checklist

- [ ] SPEC contains the recall-oriented semantic gate and the PASS/PARTIAL/REJECT state machine.
- [ ] Exactly one Source Scout ran at the start of every complete cycle, updated the persistent source registry, and every newly confirmed source was queried in that same cycle.
- [ ] All worker scopes completed; workers submitted both PASS and recall-oriented PARTIAL candidates.
- [ ] Every unique URL from GitHub README history was included in the historical re-audit before the accepted set was changed.
- [ ] Every candidate was evaluated from the complete announcement, including all location/work-mode blocks.
- [ ] A multi-location vacancy with any exact Berlin, Leipzig, or Dresden option is in the matching category; “bei Dresden” was not normalized as Dresden.
- [ ] Every accepted row has a clickable direct URL.
- [ ] Every row has seven columns (`ID`, `Position`, `Company`, `Location`, `Posted`, `Work mode`, `URL index`).
- [ ] `Hybrid` appears only in Berlin, Leipzig or Dresden.
- [ ] `Onsite` appears only in Berlin, Leipzig or Dresden.
- [ ] Remote rows have explicit Germany-wide eligibility.
- [ ] PASS rows meet all required gates; unresolved secondary evidence is represented as PARTIAL rather than silently rejected.
- [ ] German legal entity is evidenced for PASS; missing legal-entity proof is recorded as the unresolved gate for PARTIAL.
- [ ] Exact-URL and semantic-identity duplicates are verified; alternate URLs are retained in `url_index`.
- [ ] Retargeted, expired, and identity-ambiguous URLs were checked through at least two access methods before removal.
- [ ] Row-level provenance coverage is 100%.
- [ ] Every carried-forward PARTIAL was rechecked and carry-forward/promoted/retained/rejected counts were reported.
- [ ] Previous master is archived before replacement.
- [ ] Final master, result.md and GitHub README have identical row sets and are synchronized.
- [ ] Every search cycle covered all active sources and all Berlin, Leipzig, Dresden, Gamedev, Other QA Roles, and Germany-wide Remote scopes.
- [ ] A cycle that found any new unique eligible vacancy or new useful source triggered another full cycle with a new Source Scout.
- [ ] Stop occurred only after one complete cycle found zero new unique eligible vacancies, added zero new sources, and left no carried-forward PARTIAL/UNCLEAR unresolved.
