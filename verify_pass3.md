# Independent verification — Pass 3 Dresden vacancies

**Run date:** 2026-09-24  
**Inputs checked:** `result.md`, `provenance.json`, all three cited capture files, live HTTP responses/page extraction, and the current known-URL baseline.  
**Master modified:** no.

## Verdict summary

| Row | Vacancy | URL new vs baseline | Verdict | Reason |
|---:|---|---:|---|---|
| 1 | SupplyOn AG — QA-Engineer | Yes | **REJECT** | The direct URL is not in the baseline and all vacancy fields are valid, but this is not a new unique vacancy: the baseline already contains the same SupplyOn QA vacancy under LinkedIn URL `https://de.linkedin.com/jobs/view/qa-engineer-w-m-d-at-supplyon-4462956289`. The legal-entity evidence is also for a different named entity (`SupplyOn GmbH`, not hiring organization `SupplyOn AG`). |
| 2 | EffiCon — QA Automation Engineer | Yes | **ACCEPT** | Live official direct vacancy card; explicit QA automation duties; Dresden; short initial on-site Dresden phase followed by remote work, hence Hybrid; official `datePosted` 2026-09-18 (6 days old); exact German legal entity confirmed. |
| 3 | Diehl Aviation — Software Quality Assurance | Yes | **ACCEPT** | Live direct XING vacancy card; explicit safety-critical software QA duties; Dresden; explicit `Vor Ort`; `datePosted` 2026-09-07 (17 days old); German GmbH employer explicitly identified. |

**Accepted: 2 / 3**  
**Rejected: 1 / 3**  
**Direct URLs new against exact URL baseline: 3 / 3**  
**New unique vacancies after semantic dedupe: 2 / 3**

## Detailed evidence

### 1. SupplyOn AG — QA-Engineer (w/m/d)

- **Direct URL:** `https://jobs.supplyon.com/QA-Engineer-wmd-de-j649.html` — independently returned HTTP 200 and rendered the matching job card.
- **QA role:** confirmed by visible text: “Qualitätssicherung unserer Softwarelösungen,” manual and automated tests, test cases/strategies, and software-defect verification.
- **Dresden:** JobPosting JSON-LD gives `addressLocality: Dresden`, `addressCountry: DE`; visible heading also says Dresden.
- **Mode:** visible text explicitly says “für unseren Standort in Dresden (hybrid).”
- **Date:** official JobPosting JSON-LD `datePosted: 2026-09-07`; 17 days old on the run date.
- **German legal entity:** the vacancy names `SupplyOn AG`, while the supplied provenance points to the official imprint for `SupplyOn GmbH`, HRB 311380. That confirms a German SupplyOn group entity, but **not the exact named hiring entity**.
- **Newness:** exact SupplyOn job URL is absent from `qa-known-urls-current.json`, but that baseline already includes LinkedIn job ID 4462956289 for the same `QA-Engineer (m/w/d) at SupplyOn` vacancy. Therefore it fails the requested **new unique vacancy** condition.
- **Provenance assessment:** useful direct capture and accurate role/location/mode/date evidence; insufficient exact legal-entity linkage and no semantic duplicate check recorded.

### 2. EffiCon GmbH & Co. KG — QA Automation Engineer (m/w/d) Remote

- **Direct URL:** `https://www.efficon.eu/karriere/it/qa-automation-engineer-m-w-d-remote` — official employer card, independently returned HTTP 200.
- **QA role:** confirmed by explicit test-automation work: end-to-end, integration and regression tests; test-automation frameworks; Web/API testing; CI/CD; Software Testing, QA and Quality Engineering.
- **Dresden:** visible job attributes show `Dresden`, `Deutschland`; JSON-LD includes Dresden, DE.
- **Mode:** official text says “Nach einer kurzen Einarbeitungsphase in Dresden ist die Stelle remote abbildbar.” Because on-site Dresden onboarding is required and remote work follows, **Hybrid** is appropriate.
- **Date:** official JobPosting JSON-LD `datePosted: 2026-09-18 16:12:22`; 6 days old. The cited XING copy showed 2026-09-16, a two-day discrepancy but still within the ≤30-day window. The official employer timestamp is preferable.
- **German legal entity:** official imprint confirms **EffiCon GmbH & Co. KG**, Seiferitzer Allee 14, 08393 Meerane, HRA 7956, Amtsgericht Chemnitz.
- **Newness:** URL absent from all 107 entries in `qa-known-urls-current.json`; no baseline entry with the same employer/title was found.
- **Provenance assessment:** substantively complete; the cross-source posting-date disagreement should be noted, but it does not affect freshness.

### 3. Diehl Aviation Gilching GmbH — Engineer (m/w/d) Software Quality Assurance

- **Direct URL:** `https://www.xing.com/jobs/dresden-engineer-software-quality-assurance-157692452` — direct XING vacancy card, independently returned HTTP 200; not a search page.
- **QA role:** confirmed by explicit responsibility for quality assurance of safety-critical embedded software, quality processes, and aviation standards including DO-178/DO-330.
- **Dresden:** JobPosting JSON-LD gives `Zum Windkanal 10, 01109 Dresden, Sachsen, DE`.
- **Mode:** XING visible work-mode marker is explicitly `Vor Ort`; **Onsite** confirmed.
- **Date:** JobPosting JSON-LD `datePosted: 2026-09-07T17:08:40Z`; visible metadata says published 7 Sept 2026. It is 17 days old.
- **German legal entity:** vacancy explicitly identifies **Diehl Aviation Gilching GmbH** (German GmbH). Official Diehl legal notice confirms Diehl Stiftung & Co. KG, HRA 552, Amtsgericht Nürnberg, and states the group notice covers its subsidiaries/affiliates. This is less direct than a registry extract for the exact GmbH, but the exact German legal employer is explicit in the vacancy and group affiliation is established.
- **Newness:** exact XING URL is absent from the baseline. The baseline contains two different LinkedIn URLs for the same Diehl title/job family (IDs 4457769285 and 4469424453), so URL-newness is true but this appears to be another source URL for an already-known Diehl vacancy, not a genuinely new vacancy.
- **Provenance assessment:** vacancy, date, location, role and mode are well evidenced; legal-entity evidence is indirect. On the task’s literal URL-newness criterion it is new, but semantic dedupe against the known LinkedIn listings should be resolved before master insertion.

## Important newness caveat

The exact-URL test gives **3/3 new**, but a stricter semantic vacancy test gives only:

- **SupplyOn:** duplicate of a known LinkedIn vacancy → reject.
- **Diehl:** same employer/title already represented by two known LinkedIn URLs → probable duplicate; accepted above only because the delegated task explicitly defined newness by URL absence, but this should be reviewed before merging.
- **EffiCon:** genuinely new → accept.

Thus, a conservative master-merge recommendation is **1 unquestionably new unique vacancy**, with **2 additional source-level rows requiring duplicate-policy review**.
