# GitHub history URL audit — unique positions 23–44

**Audit date:** 2026-09-24  
**Gate:** `/opt/data/SPEC.md` (current; exact city route and <=30 days)  
**Scope:** zero-based unique historical URL positions 23–44 inclusive from `github_history_urls.json`.  
**Commits represented:** `63f53a2cb4c8676be7e6646c8b19b6ef085c87be`, `372f41757315256206b1d6c8ecf975e7bae30846`, `3ad3e8fe0970ca958210edc9562739959fe9d5f2`, `15f4e660060321063f6f9729216068dc3710f0ae`, `715983c8bd12eea7e93409b71063b76b3decf145`, `de6181d1fc57ab4868a3641d366910bef26df60b`.  
**Access methods:** every candidate received at least two independent checks where feasible: (1) direct `curl` using default HTTP/2 and forced HTTP/1.1/browser UA, and (2) a separate `web_extract` or LinkedIn guest endpoint request. HTTP 000/429/timeout is access evidence, not fabricated success.  
**Freshness cutoff:** posting date must be on/after 2026-08-25. Dates are assessed against 2026-09-24, not the historical “first found” date.

## Summary

- **VERIFIED:** 1 (position 38)
- **UNCLEAR:** 4 (26, 35, 37, 44)
- **REJECTED:** 17
- Master untouched.

## Position-by-position audit

### Position 23 — REJECTED

**URL:** https://www.stepstone.de/stellenangebote--Junior-Software-Tester-m-w-x-Donauwoerth-SII-Technologies-GmbH--14505228-inline.html

**Original row:**  `| 24 | Junior Software Tester (m/w/x) | SII Technologies GmbH | Donauwörth | aktiv ≤30d | known-DE | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Junior-Software-Tester-m-w-x-Donauwoerth-SII-Technologies-GmbH--14505228-inline.html) |`

**Reason:** Onsite/Hybrid: Donauwörth; обычный Homeoffice не делает его Germany-wide Remote.

**Evidence (two access methods):** StepStone extraction: title/company/location Donauwörth, `Homeoffice möglich`; role is Junior Software Tester. Дата `Erschienen: vor 8 Stunden` (fresh). Curl HTTP/2 stream error и HTTP/1.1 timeout — независимые попытки; web_extract подтвердил карточку.

### Position 24 — REJECTED

**URL:** https://www.stepstone.de/stellenangebote--QA-Engineer-m-w-d-Heilbronn-AZUR-SPACE-Solar-Power-GmbH--13809042-inline.html

**Original row:**  `| 25 | QA Engineer (m/w/d) | AZUR SPACE Solar Power GmbH | Heilbronn | aktiv ≤30d | known-DE | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--QA-Engineer-m-w-d-Heilbronn-AZUR-SPACE-Solar-Power-GmbH--13809042-inline.html) |`

**Reason:** Wrong/retired URL: requested AZUR SPACE Heilbronn ID 13809042 сейчас отдаёт другую вакансию HOCHTIEF, Cologne; исходный Heilbronn route всё равно reject.

**Evidence (two access methods):** StepStone web_extract title/content: `Quality Assurance Engineer (m/w/d) E-Commerce`, HOCHTIEF PPP Solutions GmbH, Essen, 1 week. Curl failed twice; URL identity no longer matches row.

### Position 25 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/senior-software-quality-engineer-expleo-group-4468447342

**Original row:**  `| 26 | Senior Software Quality Engineer (all genders) - Vollzeit & Teilzeit | Expleo Group | Görlitz, Saxony, Germany | 2 weeks ago | Onsite/Hybrid | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/senior-software-quality-engineer-expleo-group-4468447342) |`

**Reason:** LinkedIn job ID 4468447342 переиспользован: сейчас карточка MTR/MTRA Klinik Dr. Hancken в Buxtehude. Görlitz/hybrid QA row больше не существует.

**Evidence (two access methods):** LinkedIn main page and independent guest endpoint both returned title `Nebenjob - MTR / MTRA ... Buxtehude`; HTTP 200. Wrong page ⇒ direct-URL gate fail.

### Position 26 — UNCLEAR

**URL:** https://de.linkedin.com/jobs/view/engineer-m-w-d-software-quality-assurance-at-diehl-aviation-4457769285

**Original row:**  `| 27 | Engineer (m/w/d) Software Quality Assurance | Diehl Aviation | Dresden, Saxony, Germany | 3 weeks ago | Onsite (DO-178 Embedded-SW-QA) | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/engineer-m-w-d-software-quality-assurance-at-diehl-aviation-4457769285) |`

**Reason:** QA role, Dresden and date remain supported, but current card does not explicitly prove Onsite/Hybrid/Remote; historical `Onsite` label is not sufficient current evidence.

**Evidence (two access methods):** LinkedIn HTML+guest endpoint (HTTP 200): matching Diehl QA title; JSON-LD datePosted 2026-08-27 (28 days on 2026-09-24), addressLocality Dresden. No explicit work-mode phrase found. Fresh but gate item 5 missing.

### Position 27 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/qa-engineer-softwaretester-automotive-software-bwsolution-4468447343

**Original row:**  `| 28 | QA Engineer/Softwaretester Automotive-Software (m/w/d) | BWSolution GmbH | Hamburg, Hamburg, Germany | 4 days ago | ✅ Hamburg (Impressum) | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/qa-engineer-softwaretester-automotive-software-bwsolution-4468447343) |`

**Reason:** LinkedIn ID 4468447343 now points to Pflegefachkraft in Hannover, not BWSolution QA; also Hamburg is outside scope.

**Evidence (two access methods):** Main LinkedIn page and guest endpoint independently returned matching Pflegefachkraft/Med. Hochschule Hannover title, HTTP 200. Historical BWSolution card is gone.

### Position 28 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/quality-assurance-engineer-quantum-machines-4468447338

**Original row:**  `| 29 | Quality Assurance Engineer | Quantum Machines | Stuttgart, Baden-Württemberg, Germany | 2 days ago | known-DE | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-quantum-machines-4468447338) |`

**Reason:** Onsite/Hybrid Stuttgart is outside Berlin/Leipzig/Dresden; no explicit Germany-wide remote claim.

**Evidence (two access methods):** LinkedIn HTML and guest endpoint HTTP 200 both show `Quality Assurance Engineer bei Quantum Machines — Stuttgart`; role fits QA and row is fresh, but route fails.

### Position 29 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/softwaretester-m-w-d-healthcare-saas-deutsches-medizinrechenzentrum-4466469998

**Original row:**  `| 30 | Softwaretester (m/w/d) – Healthcare SaaS | Deutsches Medizinrechenzentrum GmbH | Düsseldorf, NRW, Germany | 6 days ago | known-DE | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-healthcare-saas-deutsches-medizinrechenzentrum-4466469998) |`

**Reason:** Düsseldorf is outside allowed cities; text only mentions up to 2 mobile days/week, which SPEC treats as ambiguous/limited remote and not Germany-wide eligibility.

**Evidence (two access methods):** LinkedIn main page and guest endpoint HTTP 200 both show DMRZ Softwaretester Healthcare SaaS, Düsseldorf. Current description includes `bis zu 2 Tage mobiles Arbeiten pro Woche`; no DE-wide remote route.

### Position 30 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-ferchau-4467085202

**Original row:**  `| 31 | Softwaretester (m/w/d) | FERCHAU | Kassel, Hesse, Germany | 1 week ago | known-DE | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-ferchau-4467085202) |`

**Reason:** Wrong retargeted job/URL: ID 4467085202 is now orgaMAX `Softwaretester ... in Deutschland`; it is not FERCHAU and the historical URL identity is invalid. The replacement is not evidence for the original row.

**Evidence (two access methods):** LinkedIn main page and guest endpoint both returned orgaMAX title, HTTP 200; body says `100 % Homeoffice möglich`, but no reliable current date/employer match for the historical FERCHAU row. Reject rather than rewrite URL.

### Position 31 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/softwaretester-qualitaetssicherung-soloplan-4468447344

**Original row:**  `| 32 | [Softwaretester Qualitätssicherung [m\ | w\ | d]](https://de.linkedin.com/jobs/view/softwaretester-qualitaetssicherung-soloplan-4468447344) | Soloplan GmbH | Kempten, Bavaria, Germany | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/softwaretester-qualitaetssicherung-soloplan-4468447344) |`

**Reason:** LinkedIn ID 4468447344 now points to Pflegefachkraft at VONBERG in Schotten; original Soloplan Kempten QA card is gone. Schotten is outside scope.

**Evidence (two access methods):** Initial curl got 429; retry HTTP/1.1 and independent guest endpoint both returned current `Pflegefachkraft (m/w/d) ... Schotten` title, HTTP 200. Wrong page.

### Position 32 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/software-tester-m-w-d-cloud-applications-soa-experts-4467863652

**Original row:**  `| 33 | Software Tester (m/w/d) – Cloud & Applications | SOA Experts GmbH | Lübeck, Schleswig-Holstein, Germany | 4 days ago | ✅ Lübeck (Impressum) | 2026-09-23 | [Link](https://de.linkedin.com/jobs/view/software-tester-m-w-d-cloud-applications-soa-experts-4467863652) |`

**Reason:** SOA Experts card is live/fresh QA, but Lübeck Hybrid/onsite route is outside allowed cities; no Germany-wide remote evidence.

**Evidence (two access methods):** LinkedIn HTML+guest endpoint HTTP 200 independently matched `Software Tester ... SOA Experts GmbH — Lübeck`; page shows recent posting. Location/work-mode route fails.

### Position 33 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/software-tester-testautomatisierer-m-w-d-at-deloitte-4243056914

**Original row:**  `| 1 | Software Tester / Testautomatisierer (m/w/d) | Deloitte | Leipzig (+Frankfurt) | 15.09.2026 | Onsite/Hybrid | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/software-tester-testautomatisierer-m-w-d-at-deloitte-4243056914) |`

**Reason:** Deloitte Leipzig route is ambiguous: page mentions `EU Remote Working`, not an explicit Onsite/Hybrid classification or Germany-wide 100% remote eligibility. SPEC does not allow inferring mode.

**Evidence (two access methods):** LinkedIn HTML+guest endpoint HTTP 200: matching Leipzig title; JSON-LD datePosted 2026-09-15, addressLocality Leipzig; description explicitly says `EU Remote Working`. Fresh but gate item 5/route not proved.

### Position 34 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/groupware-test-engineer-m-w-d-at-bwi-gmbh-4467098925

**Original row:**  `| 2 | Groupware Test Engineer (m/w/d) | BWI GmbH | Leipzig | 14.09.2026 | Onsite (mobiles Arbeit möglich) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/groupware-test-engineer-m-w-d-at-bwi-gmbh-4467098925) |`

**Reason:** `mobiles Arbeiten` is optional/ambiguous rather than an explicit accepted mode; cannot convert it to Hybrid/Remote. Leipzig otherwise fits and card is fresh.

**Evidence (two access methods):** LinkedIn HTML+guest endpoint HTTP 200: matching BWI title; datePosted 2026-09-14, addressLocality Leipzig; description says `mobiles Arbeiten` possible. Work-mode gate fails.

### Position 35 — UNCLEAR

**URL:** https://de.linkedin.com/jobs/view/senior-it-consultant-software-testautomatisierung-all-genders-at-adesso-se-3733041547

**Original row:**  `| 3 | Senior IT-Consultant Software-Testautomatisierung (all genders) | adesso SE | Leipzig | 20.09.2026 | Onsite/Hybrid | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/senior-it-consultant-software-testautomatisierung-all-genders-at-adesso-se-3733041547) |`

**Reason:** Matching adesso Leipzig QA card is live and fresh, but current evidence mentions Home-Office generically and does not explicitly establish Onsite vs Hybrid; do not infer from a benefits sentence.

**Evidence (two access methods):** LinkedIn HTML+guest endpoint HTTP 200: matching title; datePosted 2026-09-20 and addressLocality Leipzig. Home-Office appears in employer boilerplate, not an unambiguous vacancy work-mode statement.

### Position 36 — REJECTED

**URL:** https://de.linkedin.com/jobs/view/werkstudent-m-w-d-%E2%80%93-softwarequalit%C3%A4tssicherung-amp-testautomatisierung-at-swiss-life-lebensversicherung-se-4464381712

**Original row:**  `| 4 | Werkstudent Softwarequalitätssicherung & Testautomatisierung (m/w/d) | Swiss Life Lebensversicherung SE | Leipzig | 07.09.2026 | Onsite (Werkstudent) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/werkstudent-m-w-d-%E2%80%93-softwarequalit%C3%A4tssicherung-amp-testautomatisierung-at-swiss-life-lebensversicherung-se-4464381712) |`

**Reason:** No explicit Onsite/Hybrid/Remote work mode on current card; role, Leipzig, and date alone do not satisfy the gate.

**Evidence (two access methods):** LinkedIn HTML+guest endpoint HTTP 200: matching Swiss Life Werkstudent QA title; datePosted 2026-09-07, addressLocality Leipzig. No accepted work-mode wording found.

### Position 37 — UNCLEAR

**URL:** https://apply.j-vers.com/v3/job/AAAAAAAAAAAAAAAAAAAAAGQD_o2s1lvo2LlgC4A_3AJgEbC8Xk-MnmnR4U4SkR0MJXX18NA92_dlH5GS5KKU5Ii64tU5k5YaF97R_AoIv3d3xjf1rRMfZFv7LTq89W4Q89XJrrQK38xqoUNU2bsza1IXFvQg1eKizeWv7_jt0OIhunJR2lEdgQWwdKdIal-PEZqiurmSlMfovkg4yatAnhI3UDZcADgI11bHIK6e64TRq4zAsWc8Z-TmEtmDQRNPAzG3e2VMMTULzd6AEkRvZALE0kkNfZOsk6rFuo6CoAxo4AAsAuhPE6BGa3NE4yveiRHcY2je2v7cM1p3WHVq1JTO4MyV-dgnfVucUbTnrman2_3tNrpduBe-xcD4g1aUHeln4L37MNP_EhmkrOtnCA==

**Original row:**  `| 5 | Team Lead Quality Assurance & Testautomatisierung (w/m/d) | FIO Systems AG | Leipzig | 21.09.2026 (NEU) | UNCLEAR — externe Anzeige (j-vers) | 2026-09-21 | [Link](https://apply.j-vers.com/v3/job/AAAAAAAAAAAAAAAAAAAAAGQD_o2s1lvo2LlgC4A_3AJgEbC8Xk-MnmnR4U4SkR0MJXX18NA92_dlH5GS5KKU5Ii64tU5k5YaF97R_AoIv3d3xjf1rRMfZFv7LTq89W4Q89XJrrQK38xqoUNU2bsza1IXFvQg1eKizeWv7_jt0OIhunJR2lEdgQWwdKdIal-PEZqiurmSlMfovkg4yatAnhI3UDZcADgI11bHIK6e64TRq4zAsWc8Z-TmEtmDQRNPAzG3e2VMMTULzd6AEkRvZALE0kkNfZOsk6rFuo6CoAxo4AAsAuhPE6BGa3NE4yveiRHcY2je2v7cM1p3WHVq1JTO4MyV-dgnfVucUbTnrman2_3tNrpduBe-xcD4g1aUHeln4L37MNP_EhmkrOtnCA==) |`

**Reason:** Direct j-vers card title survives, but rendered page exposes essentially no job facts; historical posting date/work mode/legal-entity evidence cannot be independently confirmed, and external source alone is insufficient.

**Evidence (two access methods):** curl HTTP/1.1 HTTP 200 and web_extract both reached the same direct URL/title `Team Lead Quality Assurance & Testautomatisierung`; body only yielded privacy link/no substantive fields. Historical row itself said UNCLEAR.

### Position 38 — VERIFIED

**URL:** https://www.xing.com/jobs/leipzig-test-automation-engineer-geomagic-157527998

**Original row:**  `| 6 | Test Automation Engineer (m/w/d) - GEOMAGIC | GEOMAGIC | Leipzig | 29.08.2026 | Onsite (Remote nicht bestätigt) | 2026-09-21 | [Link](https://www.xing.com/jobs/leipzig-test-automation-engineer-geomagic-157527998) |`

**Reason:** Explicit `Vor Ort` + Leipzig satisfies the sole allowed route; role matches; active card and historical 2026-08-29 date is 26 days old at audit time. GEOMAGIC is presented as a German GmbH employer page.

**Evidence (two access methods):** XING page HTTP 200 shows exact title/employer/location, `Vor Ort`, `Aktiv auf der Suche`; web_extract independently shows same. XING employer link is `https://www.xing.com/pages/geomagicgmbh`. Historical date evidence: 2026-08-29.

### Position 39 — REJECTED

**URL:** https://www.stepstone.de/stellenangebote--Senior-Test-Engineer-m-w-d-Erprobung-und-Validierung-Leipzig-Falk-Defence--14341604-inline.html

**Original row:**  `| 7 | Senior Test Engineer (m/w/d) Erprobung und Validierung | Falk Defence | Leipzig | 17.09.2026 | Onsite (+Reisen zu Test-Ranges) | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Senior-Test-Engineer-m-w-d-Erprobung-und-Validierung-Leipzig-Falk-Defence--14341604-inline.html) |`

**Reason:** Wrong URL/card: Falk Defence Leipzig URL now resolves to AZUR SPACE QA in Heilbronn. Heilbronn is outside scope; requested employer/role/location identity fails.

**Evidence (two access methods):** StepStone web_extract for this exact URL returned `QA Engineer (m/w/d)`, AZUR SPACE, Heilbronn, `vor 1 Tag`. Curl failed twice; canonical identity contradicts historical Falk row.

### Position 40 — REJECTED

**URL:** https://www.stepstone.de/stellenangebote--Testautomatisierer-m-w-d-bundesweit-Berlin-Frankfurt-Hamburg-Koeln-Leipzig-Muenchen-Sopra-Steria--13163223-inline.html

**Original row:**  `| 8 | Testautomatisierer (m/w/d) | Sopra Steria | Leipzig (+bundesweit) | 16.09.2026 | Hybrid (Homeoffice möglich) | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Testautomatisierer-m-w-d-bundesweit-Berlin-Frankfurt-Hamburg-Koeln-Leipzig-Muenchen-Sopra-Steria--13163223-inline.html) |`

**Reason:** Sopra Steria page is fresh and includes Leipzig, but only says `Homeoffice möglich`; that is ambiguous/limited flexibility, not explicit Onsite/Hybrid or Germany-wide Remote. Strict mode gate fails.

**Evidence (two access methods):** StepStone web_extract exact URL: title/employer/location, `Homeoffice möglich`, `Erschienen: vor 1 Woche`; curl failed twice. Role and DE entity fit, mode/route does not.

### Position 41 — REJECTED

**URL:** https://www.stepstone.de/stellenangebote--System-Validation-Test-Automation-Engineer-a-Radeberg-bei-Dresden-Baumer-Optronic-GmbH--14460761-inline.html

**Original row:**  `| 9 | System Validation & Test Automation Engineer (a) | Baumer Optronic GmbH | Radeberg (bei Dresden) | 2026-09-18 | Onsite | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--System-Validation-Test-Automation-Engineer-a-Radeberg-bei-Dresden-Baumer-Optronic-GmbH--14460761-inline.html) |`

**Reason:** Radeberg (bei Dresden) is not Dresden; strict SPEC rejects every onsite/hybrid location outside the three exact cities. Generic `Homeoffice` benefit is not Germany-wide remote eligibility.

**Evidence (two access methods):** StepStone web_extract exact URL: Baumer Optronic, Radeberg (bei Dresden), valid QA role; page lists `Homeoffice` only as a benefit. Curl failed twice. Route fails.

### Position 42 — REJECTED

**URL:** https://www.stepstone.de/stellenangebote--Test-Automation-Engineer-m-w-d-Dresden-Essen-secunet-Security-Networks-AG--14337141-inline.html

**Original row:**  `| 10 | Test Automation Engineer (m/w/d) | secunet Security Networks AG | Dresden | 2026-08-31 | Hybrid (Mobile Office; 20 Tage EU-remote/Jahr) | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Test-Automation-Engineer-m-w-d-Dresden-Essen-secunet-Security-Networks-AG--14337141-inline.html) |`

**Reason:** Wrong URL/card: secunet Dresden ID now resolves to Materna Test Automation Engineer with many-city locations. Cannot retain it as evidence for the historical secunet row.

**Evidence (two access methods):** StepStone web_extract exact URL returned Materna title/employer, not secunet; curl failed twice. Requested identity is invalid and extracted multi-city mode is not explicit accepted route.

### Position 43 — REJECTED

**URL:** https://www.stepstone.de/stellenangebote--Test-Automation-Engineer-m-w-d-Berlin-Bremen-Dortmund-Dresden-Duesseldorf-Erlangen-Frankfurt-Hamburg-Hannover-Koeln-Muenchen-Materna-Information-Communications-SE--14342627-inline.html

**Original row:**  `| 11 | Test Automation Engineer (m/w/d) | Materna Information & Communications SE | Dresden (u.a.) | 2026-08-31 | Hybrid (Homeoffice möglich) | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Test-Automation-Engineer-m-w-d-Berlin-Bremen-Dortmund-Dresden-Duesseldorf-Erlangen-Frankfurt-Hamburg-Hannover-Koeln-Muenchen-Materna-Information-Communications-SE--14342627-inline.html) |`

**Reason:** Wrong URL/card: Materna multi-city ID now resolves to secunet Test Automation Engineer in Dresden/Essen; URL-employer mismatch. Also current extraction does not prove one strict mode for the selected city.

**Evidence (two access methods):** StepStone web_extract exact URL: secunet title, Dresden/Essen, test duties; requested URL slug names Materna. Curl failed twice. Canonical identity mismatch ⇒ reject rather than silently replace.

### Position 44 — UNCLEAR

**URL:** https://www.linkedin.com/jobs/view/3925557524

**Original row:**  `| 12 | Senior IT-Consultant Software-Testautomatisierung (all genders) | adesso SE | Dresden | 2026-09-18 | Hybrid | 2026-09-21 | [Link](https://www.linkedin.com/jobs/view/3925557524) |`

**Reason:** Direct LinkedIn ID 3925557524 still matches adesso QA in Dresden, but no explicit current work-mode classification was recoverable; generic Home-Office employer boilerplate is insufficient.

**Evidence (two access methods):** LinkedIn HTTP/1.1 main page HTTP 200 title: `adesso SE hiring Senior IT-Consultant Software-Testautomatisierung ... Dresden`; historical row supplies 2026-09-18 and Hybrid, but current extraction did not independently prove mode/date. Not accepted as VERIFIED.

