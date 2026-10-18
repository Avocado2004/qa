# Recheck: old UNCLEAR records, IDs 71–105

Checked: **2026-09-24**  
Scope: only the 12 records marked `UNCLEAR` in `verify_old_105.md` with IDs 71–105.  
Gate: `/opt/data/SPEC.md`; master was **not modified**.

## Counts

- **PASS: 9**
- **REJECT: 3**
- **UNCLEAR left: 0**
- **Total rechecked: 12**

## Method

Each record was checked using at least two access paths:

1. source extraction (`web_extract`) and/or rendered browser access for StepStone;
2. direct HTTP fetch with browser user-agent (HTTP 200 for LinkedIn; StepStone timed out/Cloudflare in curl, but its alternative extraction/browser path succeeded).

The evidence below revalidates the actual card rather than copying the old UNCLEAR reason. Date is evaluated against the 2026-09-24 audit date. German-company suffixes plus the company named in the direct vacancy are used as the card-level entity evidence; no unsupported inferred relocation is accepted.

## Verdicts

| ID | Verdict | Card | Freshness and mode evidence | Role/location/entity evidence | Access evidence | Reason |
|---:|---|---|---|---|---|---|
| 71 | **PASS** | Senior Test Engineer (m/f/d), Renesas Electronics, Dresden | LinkedIn: “1 week ago”; Dresden posting; ATE/test-development duties. No Germany-wide remote language, so treated as **Onsite**. | “Renesas Electronics”; “join … ATCC in Dresden”; direct card explicitly identifies the Dresden employer and test role. Semiconductor/ATE is still within the broad Test Engineer / Quality role cluster. | `web_extract` full card; direct HTTP **200**. | All fields support Onsite + Dresden, fresh role, direct URL. |
| 75 | **PASS** | Software Test Engineer (m/w/x) – Sichere Kommunikation, K-tronik GmbH, Dresden | LinkedIn: “2 weeks ago”; full-time employment; no remote option stated → **Onsite**. | Explicit “K-tronik GmbH”, Dresden; tasks include test cases, code testing, test automation and pipelines. | `web_extract` full card; direct HTTP **200**. | Fresh, direct QA/test role at German GmbH in Dresden. Card says “No longer accepting applications”, but SPEC tests validity/evidence, not current application availability. |
| 76 | **PASS** | Test Automation Engineer (m/w/d), MEDIFOX DAN, Germany | LinkedIn: “Vor 2 Wochen”; text: “100 % remote” and “vollständig ortsunabhängig in Deutschland ausgeübt werden” → **Remote + explicit Germany-wide**. | “MEDIFOX DAN Deutschland”; automated functional/regression/UI/API/integration/security tests. | `web_extract` full card; direct HTTP **200**. | Satisfies the only remote acceptance route. |
| 79 | **PASS** | Software Test Automation Engineer (m/w/d), Nexus AG, Berlin | LinkedIn: “Vor 2 Wochen”; page’s posting location heading is Berlin and the text says “an unserem Standort in Berlin, Ismaning und Jena”. No remote option → **Onsite**; Berlin is explicitly one valid base. | Nexus AG; manual and automated software tests, Playwright, QA; direct card identifies Berlin. | `web_extract` full card; direct HTTP **200**. | Onsite role explicitly includes Berlin, so the current OR-gate is met. |
| 83 | **PASS** | Test Automation Engineer (all genders), msg systems ag | StepStone: “Erschienen: vor 3 Wochen”; “Homeoffice möglich”; locations explicitly include Berlin and other cities → **Hybrid**, with confirmed Berlin location. | msg systems ag; development of modern software/cloud test-automation strategies and CI/CD integration. | `web_extract` full card; direct curl timed out (source wall), but content is fully available through extraction. | Hybrid is acceptable because the card explicitly includes Berlin among work locations. |
| 86 | **REJECT** | Game Localization Tester (m/f/d), Lionbridge Games, Berlin | LinkedIn extraction now says “Vor 2 Tagen”; explicitly “not a remote position”, Berlin office, legally work in Germany → **Onsite** in a valid city. | Card text confirms game testing and Berlin. But “Lionbridge Games” is not presented as a German GmbH/AG; it is the group’s games business. The card does not identify a German legal entity, while requiring employees to be legally able to work in Germany is not entity proof. | `web_extract` full card; direct HTTP **200**. | **DE legal-entity criterion fails.** The old master/company label cannot substitute for a German legal-entity imprint. |
| 87 | **PASS** | Prüfingenieur Aktive Medizinprodukte (m/w/d), DEKRA Germany, Dresden | LinkedIn: “Vor 5 Stunden”; “mobiles Arbeiten (wo möglich)” → **Hybrid**, Dresden confirmed. | “DEKRA Germany”; product testing under IEC 60601, electrical safety, usability and software aspects IEC 62304. | `web_extract` full card; direct HTTP **200**. | Fresh Hybrid QA/quality/test role at the German DEKRA entity in Dresden. |
| 88 | **PASS** | Software Quality Engineer (m/w/d), secupay AG, Pulsnitz | StepStone: “vor 5 Tagen”; benefits explicitly state **“Festanstellung | Vollzeit | Remote | Deutschland”** → Germany-wide **Remote**, not merely the header’s Pulsnitz office. | secupay AG; software quality, SonarQube, static analysis, security scans, quality gates and automated test/deployment checks. | Rendered browser full card; `web_extract` attempted but timed out. | Although the physical office is Pulsnitz, the card explicitly offers `Remote | Deutschland`, satisfying the second SPEC route. The old “Hybrid/Pulsnitz” interpretation was wrong. |
| 89 | **REJECT** | Senior IT-Consultant Testmanagement (all genders), adesso SE, Dresden | LinkedIn: “4 days ago”; text only says the benefit is also available “im Home-Office”; it does not state Germany-wide, bundesweit, or unrestricted 100% remote. | adesso SE, Dresden; software test-management role. | `web_extract` full card; direct HTTP **200**. | The mode cannot be treated as Onsite if home office is offered, but neither can it pass as Germany-wide Remote. Under the strict three-mode gate it is an ambiguous Hybrid/Remote option without the required explicit Germany-wide eligibility; **REJECT** rather than guess. |
| 95 | **PASS** | Test-Entwickler (m/w/d) Satellitenkommunikation, NEOSAT GmbH, Dresden | StepStone: “Erschienen: vor 5 Tagen”; “Homeoffice möglich”, with the vacancy location Dresden → **Hybrid + Dresden**. | NEOSAT GmbH, Dresden; automated tests, test frameworks, CI/CD, error analysis and quality assurance. | `web_extract` full card; direct curl timed out (source wall). | Fresh QA/test role with explicit Dresden location and optional home office. |
| 99 | **PASS** | SDV Architekt Test & vECU, MHP – A Porsche Company, Dresden | LinkedIn: “1 week ago”; direct posting location Dresden; no remote option stated → **Onsite**. | Explicit MHP role focused on SDV test strategy, vECU/cloud test environments, CI/CD and quality assurance. | `web_extract` full card; direct HTTP **200**. | Fresh, direct test/QA role at the named German operating company in Dresden. |
| 104 | **REJECT** | Software Quality & Compliance Engineer (w/m/d), Endress+Hauser Gruppe | LinkedIn current card says **Jena**, “Vor 2 Wochen”; “Homeoffice-Möglichkeiten”. | Direct card explicitly locates the role at the Jena site, not Leipzig. The body supports software QA/compliance and a German industrial employer, but not the requested location route. | `web_extract` full card; direct HTTP **200**. | **Location gate fails:** Jena is outside Berlin/Leipzig/Dresden; generic home-office possibility is not Germany-wide Remote. |

## Final disposition

Accepted: **IDs 71, 75, 76, 79, 83, 87, 88, 95, 99**.  
Rejected: **IDs 86, 89, 104**.

No master/source dataset was changed. This file is an audit-only decision record.
