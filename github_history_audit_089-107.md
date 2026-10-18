# Historical URL audit — unique positions 89–107

Checked: **2026-09-24**  
Source: `github_history_urls.json` → `unique_urls[88:107]` (1-based positions 89–107).  
Rules: current `SPEC.md` plus the stricter location/mode gate in `qa-vacancy-search-de`: QA role; posted within 30 days; German legal entity; direct vacancy URL; Onsite/Hybrid only in Berlin/Leipzig/Dresden; Remote only with explicit Germany-wide eligibility. Master and source dataset were not modified.

## Access methods

- **StepStone (89–105):** direct `curl -L` was attempted and failed at the HTTP/2 stream/protection layer; `web_extract` independently rendered the vacancy content. A representative StepStone card (93) was also rendered in the browser.
- **XING (106–107):** direct HTTP fetch returned **200** and `web_extract` independently rendered the vacancy card.
- Thus a StepStone access failure was not treated as a dead URL; verdicts rely on the second successful content path.

## Verdicts

| Pos. | Verdict | Freshness / role / entity | Location-mode gate | Evidence summary |
|---:|---|---|---|---|
| 89 | **REJECT** | AZUR SPACE, “vor 1 Tag”; product/quality-engineering work, not the accepted manual-web/software/gamedev QA role. | Heilbronn + Homeoffice is not Germany-wide Remote and Heilbronn is not a target city. | StepStone extraction: direct role, Heilbronn, Homeoffice possible. |
| 90 | **PASS** | PTA GmbH; “vor 1 Woche”; test automation/testing/quality consulting. German GmbH is explicit. | Berlin and Dresden are listed; Homeoffice is possible → valid Hybrid. | Full StepStone card extraction. |
| 91 | **REJECT** | URL now renders unrelated job content (HOCHTIEF), not the historical igus vacancy. | No valid card from which to establish the gate. | Extraction title/content is for **Quality Assurance Engineer at HOCHTIEF PPP Solutions**, a wrong-page result. |
| 92 | **REJECT** | adp MERKUR GmbH; “vor 5 Tagen”; clear game-QA role and German GmbH. | Lübbecke is outside the three target cities; no Homeoffice/remote option is stated. | Full StepStone card extraction. |
| 93 | **REJECT** | Falk Defence; “vor 1 Woche”; hardware/missile test and validation, outside the accepted software/game QA categories. | Leipzig would satisfy the city gate, but the role gate fails. Also, the card names only “Falk Defence,” not a German legal-entity suffix. | `web_extract` + independent browser render. |
| 94 | **REJECT** | Aveyara Software GmbH; “vor 1 Woche”; genuine software QA role and German GmbH. | Stuttgart + optional Homeoffice is not explicit Germany-wide Remote; Stuttgart is outside the target cities. | Full StepStone card extraction. |
| 95 | **REJECT** | WERTGARANTIE Group; “vor 1 Tag”; automated software testing role. | Hannover + partial Homeoffice is outside the target cities and not Germany-wide Remote. | StepStone extraction. |
| 96 | **REJECT** | Bedifol GmbH; current related card indicates “vor 1 Woche”; software/quality role and German GmbH. | Konstanz + up to two Homeoffice days/week fails both allowed location routes. | Full StepStone card extraction. |
| 97 | **PASS** | secupay AG; prior recheck found “vor 5 Tagen”; software quality/SonarQube/CI-CD role and German AG. | Card evidence explicitly stated **Remote — Deutschland**; Germany-wide Remote route is satisfied despite Pulsnitz office. | StepStone extraction was partially contaminated/wrong-page this run; corroborated by `recheck_unclear_071-105.md` ID 88, which independently rendered the actual card. |
| 98 | **REJECT** | seca GmbH & Co. KG; “vor 5 Tagen”; manual software testing role and German legal entity. | Hamburg + Homeoffice is not explicit Germany-wide Remote; Hamburg is not a target city. | Full StepStone card extraction. |
| 99 | **REJECT** | Baumer Optronic GmbH; fresh test/validation role and German GmbH. | Radeberg (bei Dresden) is not Dresden; the generic Homeoffice benefit does not establish Germany-wide Remote. | Full StepStone card extraction. |
| 100 | **PASS** | msg systems ag; “vor 3 Wochen”; software test-automation/CI-CD role and German `ag`. | Berlin is an explicit location and Homeoffice is possible → valid Hybrid. | Full StepStone card extraction. |
| 101 | **PASS** | Materna Information & Communications SE; fresh test-automation/quality role and German `SE`. | Dresden is an explicit location and Homeoffice is possible → valid Hybrid. | Full StepStone card extraction. |
| 102 | **PASS** | secunet Security Networks AG; fresh automated-test role and German `AG`. | Dresden is explicit and Homeoffice is possible → valid Hybrid. | Full StepStone card extraction. |
| 103 | **PASS** | NEOSAT GmbH; “vor 5 Tagen”; automated software tests, frameworks and CI/CD; German GmbH. | Dresden + Homeoffice possible → valid Hybrid. | Full StepStone card extraction. |
| 104 | **PASS** | Sopra Steria; “vor 1 Woche”; test-automation role; German employing group is established. | Location explicitly says `bundesweit` and Homeoffice is possible → Germany-wide Remote (and Leipzig is also listed). | Full StepStone card extraction. |
| 105 | **PASS** | PTA GmbH; current card identifies the direct test-management role and German GmbH; prior audit recorded “4 days ago.” | Berlin/Dresden are explicit locations and Homeoffice is possible → valid Hybrid. | StepStone extraction; freshness corroborated by `recheck_unclear_071-105.md` ID 89. |
| 106 | **REJECT** | SEDIWORK, Leipzig; fresh QA/software-testing card. | Leipzig + Homeoffice would pass the location gate, but the direct card supplies no German legal-entity name (no GmbH/AG or legal/imprint evidence); DE-entity requirement is unproven. | XING direct HTTP 200 + independent extraction. |
| 107 | **PASS** | GEOMAGIC; historical date 2026-08-29 (26 days old at audit); software test-automation role; XING employer profile identifies GEOMAGIC in Leipzig, Germany. | XING explicitly says **Vor Ort** in Leipzig → valid Onsite. | XING direct HTTP 200 + independent extraction. |

## Summary

- **PASS: 9** — 90, 97, 100, 101, 102, 103, 104, 105, 107
- **REJECT: 10** — 89, 91, 92, 93, 94, 95, 96, 98, 99, 106
- **UNCLEAR remaining: 0**

## Notable corrections

- Position 91 is a **wrong-page URL**, not merely a mode rejection.
- Position 93's Leipzig location passes, but its hardware test domain and missing explicit legal-entity suffix fail other gates.
- Position 97 is accepted only on the verified card evidence stating `Remote | Deutschland`; the latest extractor response was contaminated by a different StepStone card.
- Position 106 remains rejected despite a valid Leipzig QA card because the required German legal entity is not evidenced.
