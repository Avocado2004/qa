# QA Vacancy Search Project — About

## Goal

Maintain a daily-updated markdown list of unique, verified QA/test vacancies in Germany.

## Acceptance criteria

A vacancy is included only if all conditions are met:

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
- Unclear or unverifiable work mode, location, date or employer is rejected.
- Vacancies are deduplicated by URL and by normalized `company + title`.

## Output format

The public list preserves the four original category blocks: Manual WEB QA Engineer, Software Test Engineer, Gamedev QA Engineer, and Other QA Roles. Every exact target-city vacancy is placed in its matching category even when another gate is unresolved; unresolved work mode is rendered as `Unknown`, and the `PARTIAL-###` marker is retained. The separate `Partially verified — not counted` block contains only unresolved records outside Berlin, Leipzig, and Dresden. Each category contains accepted PASS rows and target-city PARTIAL rows. The final `Work mode` vocabulary is `Remote`, `Onsite`, `Hybrid`, or `Unknown`; `Unknown` is allowed only for exact target-city locations. PARTIAL records remain on the mandatory next-run review list and do not receive a final `QADE-...` semantic ID until all mandatory gates pass. All accepted rows require row-level provenance covering role, date, location, work mode, German legal entity and verification method.

## Daily pipeline

1. Create or update `SPEC.md` with the hard acceptance gate.
2. Run parallel workers for Berlin, Leipzig, Dresden and Germany-wide Remote scopes.
3. Require workers to submit only accepted rows; rejected and near-miss candidates stay in rejected logs.
4. Parse, validate, deduplicate and independently verify every candidate.
5. Compare URLs with the accumulated known-URL database.
6. Archive the previous published master before replacing it.
7. Write the new master and `result.md`, then publish to GitHub.

## Archive and repeat rule

Before replacing the canonical master, save the previous published file as:

`/opt/data/qa-vacancy-project/qa_vacancies_master_YYYY-MM-DD.md`

Never overwrite an existing dated archive. Keep an accumulated known-URL database and continue full passes until two consecutive complete passes find zero new unique accepted vacancies. Each pass must use the same acceptance gate.

## Search and verification requirements

- Search queries and vacancy extraction should use German terms such as `Softwaretester`, `QA Engineer`, `Test Engineer`, `Qualitätssicherung`, `Spiele-Tester`, `Manuelle Tests`, `Test Automation` and `Game QA`.
- Use multiple working sources: LinkedIn Jobs, Arbeitsagentur, StepStone, XING, hitmarker and direct company ATS pages.
- Try at least two access methods for blocked sources.
- For every URL use `curl -L` or browser/web extraction and record the verification method.
- Verify the posting date from JSON-LD or visible source text.
- Verify the German legal entity from Impressum/Handelsregister/legal page.
- If evidence is ambiguous, reject the row instead of guessing.

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
- A run is complete only after the final master passes the location/work-mode gate, link checks, deduplication, date checks and table validation.
- Published files must be synchronized between the project master, `result.md` and GitHub `README.md`.
- Keep dated historical masters; do not delete them.

## Verification checklist

- [ ] SPEC exists and contains the exact acceptance gate.
- [ ] All five worker scopes completed.
- [ ] Every accepted row has a clickable direct URL.
- [ ] Every row has seven columns (`ID`, `Position`, `Company`, `Location`, `Posted`, `Work mode`, `URL index`).
- [ ] `Hybrid` appears only in Berlin, Leipzig or Dresden.
- [ ] `Onsite` appears only in Berlin, Leipzig or Dresden.
- [ ] Remote rows have explicit Germany-wide eligibility.
- [ ] All rows are posted within 30 days.
- [ ] German legal entity is evidenced.
- [ ] URLs and semantic duplicates are verified.
- [ ] Row-level provenance coverage is 100%.
- [ ] Previous master is archived before replacement.
- [ ] Final master, result.md and GitHub README are synchronized.
- [ ] Search continues until two consecutive complete passes produce zero new unique vacancies.
