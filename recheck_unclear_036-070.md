# Recheck old UNCLEAR IDs 36–70

Recheck date: 2026-09-24  
Gate: `/opt/data/SPEC.md` (exactly one accepted route; freshness <=30 days; QA role; German legal entity; live direct URL).  
Scope: only rows marked `UNCLEAR` in `verify_old_105.md` with IDs 36–70. Master files were not modified.

## Counts

- **PASS: 6** — IDs 36, 40, 41, 45, 61, 69
- **REJECT: 2** — IDs 60, 63
- **UNCLEAR: 0**
- **Total rechecked: 8**

## Method notes

At least two access methods were used across every row:

1. deterministic `curl -L` against the direct URL (status, redirect target, rendered text, and LinkedIn JSON-LD where present); and
2. an independent page renderer/extractor (`web_extract`, plus browser rendering for Cresta).

Employer identity was checked against an official imprint/legal page where available. The `web_search` backend returned no results in this environment, so it supplied no verdict evidence.

## Verdicts

| ID | Verdict | Vacancy / URL | Evidence and gate result |
|---:|---|---|---|
| 36 | **PASS** | Softwaretester (m/w/d) 100 % Remote — eightbit experts GmbH — https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937 | `curl`: HTTP 200, no wrong redirect; page title and rendered card identify **eightbit experts GmbH**, location **Deutschland**, and relative date **“Vor 2 Wochen”**. `web_extract`: independent successful render; exact mode text **“In der Position kannst Du zu 100 % remote arbeiten”** and benefits **“100 % Remote-Tätigkeit”**. The Germany context plus 100% remote wording satisfies SPEC §1/§3. Role is explicit Softwaretester with manual tests and test automation. Listed legal name is an `GmbH`; direct recruitment is stated as **“direkte Personalvermittlung”**. Fresh, direct, QA/test, and Germany-wide remote are evidenced. |
| 40 | **PASS** | Senior Technical QA Tester — Kolibri Games — https://de.linkedin.com/jobs/view/senior-technical-qa-tester-f-m-d-at-kolibri-games-4460476943 | `curl`: HTTP 200, no wrong redirect; JSON-LD `datePosted=2026-09-03T09:59:56Z`, `addressCountry=DE`, `addressLocality=Berlin`; description gives manual/technical QA and automated testing. `web_extract`: independent render, **Kolibri Games / Berlin, Deutschland / Vor 2 Wochen**, explicit QA Tester role. Official imprint `https://www.kolibrigames.com/impressum/`: **Kolibri Games GmbH, HRB 193057 Amtsgericht Charlottenburg, Elisabeth-Schwarzhaupt-Platz 5, 10115 Berlin**. All gate fields pass. |
| 41 | **PASS** | Engineer (m/w/d) Software Quality Assurance — Diehl Aviation — https://de.linkedin.com/jobs/view/engineer-m-w-d-software-quality-assurance-at-diehl-aviation-4457769285 | `curl`: HTTP 200; JSON-LD `datePosted=2026-08-27T11:31:01Z`, `addressCountry=DE`, `addressLocality=Dresden`; description explicitly covers software quality assurance. `web_extract`: independent render, **Diehl Aviation / Dresden / Vor 3 Wochen**, direct job. Official group legal page `https://new.diehl.com/group/en/imprint` proves the German Diehl group legal operator **Diehl Stiftung & Co. KG, HRA 552 Amtsgericht Nürnberg**, and names Diehl Aviation as a corporate division. Pass. |
| 45 | **PASS** | Engineer (m/w/d) Software Quality Assurance — Diehl Aviation — https://www.linkedin.com/jobs/view/4457769285 | `curl`: HTTP 200 and the short canonical LinkedIn URL rendered the same direct card: **Diehl Aviation / Dresden / Vor 3 Wochen**. `web_extract`/LinkedIn canonical page plus the ID-41 canonical card independently identify the same job and JSON-LD date `2026-08-27`; Diehl official imprint supplies German-entity evidence as for ID 41. This URL passes the gate, but it is a **duplicate of ID 41** and must be deduplicated before any final publication. |
| 60 | **REJECT** | System Validation & Test Automation Engineer (a) — Baumer Optronic GmbH — https://www.stepstone.de/stellenangebote--System-Validation-Test-Automation-Engineer-a-Radeberg-bei-Dresden-Baumer-Optronic-GmbH--14460761-inline.html | `curl`: blocked/000. `web_extract`: successful independent render identifies the direct role and **Baumer Optronic GmbH**, but the advertised location is **Radeberg (bei Dresden)**. The page merely lists “Homeoffice” as a general employee benefit; it does not establish Germany-wide remote. **Radeberg is not Berlin, Leipzig, or Dresden**, so Onsite fails SPEC §1/§2 route 1. The informal “bei Dresden” wording is not a Dresden workplace address. Reject. |
| 61 | **PASS** | Senior IT-Consultant Software-Testautomatisierung (all genders) — adesso SE — https://www.linkedin.com/jobs/view/3925557524 | `curl`: HTTP 200; direct rendered card is **adesso SE / Dresden / Vor 5 Tagen**, with Software-Testautomatisierung in the title and test-automation content. `web_extract`: independent retrieval resolved the same LinkedIn job card (short URL) and direct title. Official imprint `https://www.adesso.de/de/impressum/index.jsp`: **adesso SE, Adessoplatz 1, 44269 Dortmund, HRB 20663, Amtsgericht Dortmund**. Fresh QA/test role and Dresden location pass. |
| 63 | **REJECT** | Software Engineer in Test (Berlin) — Cresta — https://de.linkedin.com/jobs/view/software-engineer-in-test-berlin-at-cresta-4343158227 | `curl`: HTTP 200; JSON-LD `datePosted=2026-09-17T14:25:15Z`, `addressCountry=DE`, `addressLocality=Berlin`; description is explicitly Software Engineer in Test. Browser rendering independently loaded the direct card. However, neither the vacancy nor independent official legal evidence identifies a **German legal entity**: LinkedIn names only **Cresta**, and Cresta’s official legal page lists a Berlin address but does not name a German `GmbH/AG` or register. A foreign company with a German office/address does not satisfy SPEC §1 requirement for a German legal entity. Reject. |
| 69 | **PASS** | Senior Test Engineer (m/w/d) — Bundesdruckerei-Gruppe — https://de.linkedin.com/jobs/view/senior-test-engineer-m-w-d-at-bundesdruckerei-gruppe-4457332496 | `curl`: HTTP 200; JSON-LD `datePosted=2026-09-12T12:28:14Z`, `addressCountry=DE`, `addressLocality=Berlin`; description explicitly covers test strategy, automated suites and test cases. `web_extract`: independent render, **Bundesdruckerei-Gruppe / Berlin, Germany**, direct job. Official imprint `https://www.bundesdruckerei.de/de/impressum`: **Bundesdruckerei Gruppe GmbH, Kommandantenstraße 18, 10969 Berlin, HRB 80443 Amtsgericht Berlin Charlottenburg**. All gate fields pass. |

## Decision summary

- Six URLs satisfy the hard gate and may be treated as verified candidates, subject to the required master-level deduplication/provenance merge.
- ID 45 is valid but duplicates ID 41; it must not yield two final rows.
- ID 60 fails the exact city route (Radeberg is not Dresden; generic Homeoffice does not mean Germany-wide remote).
- ID 63 fails the German-legal-entity requirement despite a valid Berlin QA vacancy and a Berlin company address.
