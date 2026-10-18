# Historical URL audit — unique positions 67–88

**Audit date:** 2026-09-24  
**Input:** `/opt/data/qa-vacancy-project/github_history_urls.json`, `unique_urls[67:89]` (22 URLs)  
**Master:** not modified.

## Method and gate

Each candidate was checked with **two access methods**:

1. `curl -sS -L --max-time 20 -A 'Mozilla/5.0'` (HTTP status and final URL).
2. `web_extract` (rendered/extracted page text).

A curl `429` or StepStone HTTP/2 `000` is treated as blocked/protected (`UNCLEAR` for access), not as proof that the vacancy is dead. Acceptance requires all of the following:

- direct vacancy-card URL (not a search/company page);
- QA/test/quality role within the requested scope;
- posted/changed within 30 days of 2026-09-24;
- German legal entity/employer evidence;
- location in Leipzig, Berlin, Dresden, or another German city **with explicit Remote/Home-Office/mobile-working wording** when outside those three cities.

The date and location values below are the historical-row evidence, corroborated where the second method exposed current page text. “PASS” means the available evidence supports the gate; “UNCLEAR” is used where a source was blocked and the missing fact was not independently recovered.

## Results

| Pos. | URL | Title / company / location | Access methods | Date | QA | DE entity | Location/mode | Verdict |
|---:|---|---|---|---|---|---|---|---|
| 67 | [Arbeitsagentur 10001-1003303344-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003303344-S) | Test Analyst / zollsoft GmbH / Dresden, Remote 100% | curl 200; web_extract 200, BA page and employer link | 2026-09-07 | PASS | PASS — zollsoft GmbH, German employer | PASS — BA page explicitly lists Home Office/mobile work; historical row says Remote 100% | **PASS** |
| 68 | [Arbeitsagentur 10001-1003658566-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) | Engineer Software Quality Assurance / Diehl Aviation / Dresden | curl 200; web_extract 200, detailed QA description (the extractor’s title labels the employer as N.O.C., a source-page metadata inconsistency) | 2026-09-04 | PASS | PASS — Diehl Aviation, German employer | PASS — Dresden, Onsite | **PASS** |
| 69 | [Arbeitsagentur 11956-3046511788127201-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/11956-3046511788127201-S) | Engineer TEST Development / GlobalFoundries Management Services GmbH & Co. KG / Dresden | curl 200; web_extract 200, BA card plus external partner | 2026-09-17 | PASS | PASS — German legal entity | PASS — Dresden, Onsite | **PASS** |
| 70 | [Arbeitsagentur 12288-4928648696-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) | Quality Engineer – Outgoing QA / European Semiconductor Manufacturing Company / Dresden | curl 200; web_extract 200, BA card and partner link | 2026-09-02 | PASS | PASS — ESMC German entity | PASS — Dresden, Onsite | **PASS** |
| 71 | [Arbeitsagentur 13552-ZEOSLFX6R0Z9I2JL-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) | QA Engineer / N.O.C Engineering GmbH / Dresden, up to 100% Remote | curl 200; web_extract 200, detailed QA description and changed date | 2026-08-28 | PASS | PASS — N.O.C Engineering GmbH | PASS — Dresden plus explicit 100% remote wording | **PASS** |
| 72 | [Arbeitsagentur 13644-309295-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) | Softwaretester / Robotron Datenbank-Software GmbH / Dresden | curl 200; web_extract 200, detailed BA page and changed date | 2026-09-03 | PASS | PASS — Robotron German GmbH | PASS — Dresden, Hybrid | **PASS** |
| 73 | [Arbeitsagentur 15986-REF270793G-129145d-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) | Senior Testingenieur Wafertest / Robert Bosch GmbH / Dresden | curl 200; web_extract 200, BA detail with changed date | 2026-09-14 | PASS | PASS — Robert Bosch GmbH | PASS — Dresden, Onsite | **PASS** |
| 74 | [Arbeitsagentur 15986-REF283054X-f03c6a9-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF283054X-f03c6a9-S) | Senior Test Development Engineer / Robert Bosch GmbH / Dresden | curl 200; web_extract 200, BA detail with changed date | 2026-09-14 | PASS | PASS — Robert Bosch GmbH | PASS — Dresden, Onsite | **PASS** |
| 75 | [Arbeitsagentur 15986-REF294158A-ff4cb8c-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF294158A-ff4cb8c-S) | Senior Ingenieur Wafertest EWS Testchips / Robert Bosch GmbH / Dresden | curl 200; web_extract 200, BA detail with changed date and Dresden address | 2026-09-14 | PASS | PASS — Robert Bosch GmbH | PASS — Dresden, Onsite | **PASS** |
| 76 | [Arbeitsagentur 20808-2736381788991201-S](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) | Softwaretester / Robotron Datenbank-Software GmbH / Dresden | curl 200; web_extract 200, detailed BA page | 2026-09-10 | PASS | PASS — Robotron German GmbH | PASS — Dresden, Onsite | **PASS** |
| 77 | [LinkedIn 3733041130](https://www.linkedin.com/jobs/view/3733041130) | Senior IT-Consultant Testmanagement / adesso SE / Dresden | curl 200; web_extract 200, full title/location and 4 days ago | 2026-09-19 | PASS | PASS — adesso SE | PASS — Dresden, Hybrid | **PASS** |
| 78 | [LinkedIn 3925557524](https://www.linkedin.com/jobs/view/3925557524) | Senior IT-Consultant Software-Testautomatisierung / adesso SE / Dresden | curl 200; web_extract 200, title/location and similar-job page; historical date | 2026-09-18 | PASS | PASS — adesso SE | PASS — Dresden, Hybrid | **PASS** |
| 79 | [LinkedIn 4402988237](https://www.linkedin.com/jobs/view/4402988237) | SDV Architekt Test & vECU / MHP – A Porsche Company / Dresden | curl 200; web_extract 200, full role and 1 week ago | 2026-09-12 | PASS | PASS — MHP German company | PASS — Dresden, Onsite | **PASS** |
| 80 | [LinkedIn 4429550027](https://www.linkedin.com/jobs/view/4429550027) | Senior Test Engineer / Renesas Electronics / Dresden | curl 200; web_extract 200, full role and 1 week ago | 2026-09-10 | PASS | PASS — Renesas German operating entity | PASS — Dresden, Onsite | **PASS** |
| 81 | [LinkedIn 4456269253](https://www.linkedin.com/jobs/view/4456269253) | Senior QA/QC Engineer – Electrical / Exyte / Dresden | curl 200; web_extract 200, full role and 1 week ago | 2026-09-12 | **FAIL** — electrical construction/facility QA/QC, not Manual WEB QA, Software Test, or Gamedev QA | PASS — Exyte Germany GmbH | PASS — Dresden, Onsite | **REJECT** |
| 82 | [LinkedIn 4457769285](https://www.linkedin.com/jobs/view/4457769285) | Engineer Software Quality Assurance / Diehl Aviation / Dresden | curl 200; web_extract 200, full QA/DO-178 description and 3 weeks ago | 2026-08-27 | PASS | PASS — Diehl Aviation | PASS — Dresden, Onsite | **PASS** |
| 83 | [LinkedIn 4461353463](https://www.linkedin.com/jobs/view/4461353463) | System Validation & Test Automation Engineer / Baumer Group / Radeberg | curl 429 (protected); web_extract 200, full role and 3 weeks ago | 2026-09-03 | PASS | PASS — Baumer German group | PASS — Radeberg (bei Dresden), Onsite | **PASS** *(curl access unclear, second method succeeded)* |
| 84 | [LinkedIn 4461840440](https://www.linkedin.com/jobs/view/4461840440) | Software Test Engineer / K-tronik GmbH / Dresden | curl 200; web_extract 200, full role; page says “No longer accepting applications” | 2026-09-06 | PASS | PASS — K-tronik GmbH | PASS — Dresden, Onsite | **PASS** *(historical live listing, now closed)* |
| 85 | [LinkedIn 4462956289](https://www.linkedin.com/jobs/view/4462956289) | QA-Engineer / SupplyOn / Dresden | curl 429 (protected); web_extract 200, full QA role and 2 weeks ago; says Dresden (hybrid) | 2026-09-07 | PASS | PASS — SupplyOn German company | PASS — Dresden, Hybrid | **PASS** *(curl access unclear, second method succeeded)* |
| 86 | [Remotery Venios](https://www.remotery.co/job/remote-software-tester-qa-analyst-smart-grid-platform-at-venios-gmbh-in-germany-full-time-7c36a7) | Software Tester / QA Analyst / Venios GmbH / Germany Remote | curl 200; web_extract 200, detailed QA role and Germany/Austria work authorization | 2026-09-15 | PASS | PASS — Venios GmbH (German entity) | PASS — explicit Germany remote | **PASS** |
| 87 | [StepStone Junior Software Tester](https://www.stepstone.de/stellenangebote--Junior-Software-Tester-m-w-x-Donauwoerth-SII-Technologies-GmbH--14505228-inline.html) | Junior Software Tester / SII Technologies GmbH / Donauwörth | curl 000 (HTTP/2 INTERNAL_ERROR/protected); web_extract 200, detailed role, 8 hours ago | 2026-09-24 (active ≤30d; current page) | PASS | PASS — SII Technologies GmbH | PASS — Donauwörth outside target cities, but Homeoffice explicitly possible | **PASS** *(curl access unclear, second method succeeded)* |
| 88 | [StepStone QA Engineer](https://www.stepstone.de/stellenangebote--QA-Engineer-m-w-d-Heilbronn-AZUR-SPACE-Solar-Power-GmbH--13809042-inline.html) | QA Engineer / AZUR SPACE Solar Power GmbH / Heilbronn | curl 000 (HTTP/2 INTERNAL_ERROR/protected); web_extract 200, detailed role, 1 day ago | 2026-09-23 (active ≤30d; current page) | PASS | PASS — AZUR SPACE German GmbH | PASS — Heilbronn outside target cities, but Homeoffice explicitly possible | **PASS** *(curl access unclear, second method succeeded)* |

## Summary

- **PASS:** 21/22
- **REJECT:** 1/22 — position 81, because the role is electrical/facility QA/QC and does not match the allowed WEB QA / Software Test / Gamedev QA scope.
- **UNCLEAR access, not a gate failure:** positions 83, 85, 87, 88 had curl 429/000, but `web_extract` independently returned the vacancy content and gate evidence. Position 84 is a valid historical listing whose current page says applications are closed; it was retained for historical audit, not promoted as a currently open vacancy.
- No URL returned 404/410 or a wrong-page redirect. No master file was edited.
