# GitHub historical vacancy audit — unique URLs 1–22

**Audit date:** 2026-09-24  
**Rules:** `/opt/data/SPEC.md` and `qa-vacancy-search-de/SKILL.md`  
**Freshness boundary:** dates on or after 2026-08-25.  
**Access standard:** direct HTTP/LinkedIn guest card + independent `web_extract`; StepStone failures used direct fetch + extraction.  
**Scope note:** URLs are numbered by first appearance in `github_history_urls.json` (commit `63f53a2`); historical table row numbers are reported verbatim. The project master was not modified.

## Summary

| Verdict | Count |
|---|---:|
| PASS | 7 |
| REJECT | 12 |
| UNCLEAR | 3 |
| **Total** | **22** |

## Detailed audit

### 1. PASS — https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S

**Reason:** QA role is explicit; Dresden Onsite is inside the gate.

**Evidence:** BA direct card and independent web extraction both live. Card: “Softwaretester”, “Land Deutschland”, “Standort Dresden”, full-time; “Veröffentlichungsdatum: Vor 14 Tagen”. No remote option, normalized Onsite. Robotron Datenbank-Software GmbH is a German legal entity.

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 1 | Softwaretester (m/w/d) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-10 | Onsite | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) |`
- `372f41757315` — historical table row `| 1 | Softwaretester (m/w/d) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-10 | Onsite | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) |`
- `3ad3e8fe0970` — historical table row `| 1 | 1 | Softwaretester (m/w/d) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-10 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) |`
- `15f4e6600603` — historical table row `| 1 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-10 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) |`
- `715983c8bd12` — historical table row `| 1 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-10 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) |`
- `de6181d1fc57` — historical table row `| 25 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-10 | Onsite |`
- `8e071115731a` — historical table row `| 9 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/20808-2736381788991201-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-10 | Onsite |`

### 2. PASS — https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S

**Reason:** Dresden Hybrid is explicitly allowed.

**Evidence:** BA direct card and independent extraction: “Besondere Merkmale Homeoffice möglich”, “Arbeitsort Dresden”, “Vor 21 Tagen veröffentlicht”. This establishes the allowed Dresden Hybrid route; employer Robotron Datenbank-Software GmbH (DE).

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 2 | Softwaretester (m/w/d) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-03 | Hybrid | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) |`
- `372f41757315` — historical table row `| 2 | Softwaretester (m/w/d) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-03 | Hybrid | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) |`
- `3ad3e8fe0970` — historical table row `| 2 | 2 | Softwaretester (m/w/d) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-03 | Hybrid | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) |`
- `15f4e6600603` — historical table row `| 2 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-03 | Hybrid | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) |`
- `715983c8bd12` — historical table row `| 2 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-03 | Hybrid | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) |`
- `de6181d1fc57` — historical table row `| 39 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-03 | Onsite |`
- `8e071115731a` — historical table row `| 11 | [Softwaretester (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13644-309295-S) | Robotron Datenbank-Software GmbH | Dresden | 2026-09-03 | Onsite |`

### 3. PASS — https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S

**Reason:** QA role, Dresden and Onsite route are supported.

**Evidence:** BA direct card + extraction: Engineer Software Quality Assurance; “Arbeitsort Dresden”; “Vor 20 Tagen veröffentlicht”. Duties cover DO-178/DO-330 QA. No remote option, normalized Onsite. Employer Diehl Aviation Gilching GmbH (DE).

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 3 | Engineer (m/w/d) Software Quality Assurance | Diehl Aviation | Dresden | 2026-09-04 | Onsite (DO-178 Embedded-SW-QA) | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) |`
- `372f41757315` — historical table row `| 3 | Engineer (m/w/d) Software Quality Assurance | Diehl Aviation | Dresden | 2026-09-04 | Onsite (DO-178 Embedded-SW-QA) | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) |`
- `3ad3e8fe0970` — historical table row `| 3 | 3 | Engineer (m/w/d) Software Quality Assurance | Diehl Aviation | Dresden | 2026-09-04 | Onsite (DO-178 Embedded-SW-QA) | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) |`
- `15f4e6600603` — historical table row `| 3 | [Engineer (m/w/d) Software Quality Assurance](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) | Diehl Aviation | Dresden | 2026-09-04 | Onsite (DO-178 Embedded-SW-QA) | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) |`
- `715983c8bd12` — historical table row `| 3 | [Engineer (m/w/d) Software Quality Assurance](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) | Diehl Aviation | Dresden | 2026-09-04 | Onsite (DO-178 Embedded-SW-QA) | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) |`
- `de6181d1fc57` — historical table row `| 38 | [Engineer (m/w/d) Software Quality Assurance](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) | Diehl Aviation | Dresden | 2026-09-04 | Onsite |`
- `8e071115731a` — historical table row `| 10 | [Engineer (m/w/d) Software Quality Assurance](https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003658566-S) | Diehl Aviation | Dresden | 2026-09-04 | Onsite |`

### 4. UNCLEAR — https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S

**Reason:** Current card no longer proves the historical Dresden Hybrid route or explicit Germany-wide remote eligibility.

**Evidence:** BA direct card and extraction: “Vor 27 Tagen”; “bis zu 100% Homeoffice möglich nach … Einarbeitung vor Ort”; “verschiedene Arbeitsorte”; alternatively fillable in Switzerland. No stable Dresden Onsite/Hybrid route or explicit Germany-wide Remote.

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 4 | Quality Assurance Engineer (m/w/d) | N.O.C Engineering GmbH | Dresden | 2026-08-28 | bis 100% Remote (nach Einarbeitung vor Ort) | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) |`
- `372f41757315` — historical table row `| 4 | Quality Assurance Engineer (m/w/d) | N.O.C Engineering GmbH | Dresden | 2026-08-28 | bis 100% Remote (nach Einarbeitung vor Ort) | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) |`
- `3ad3e8fe0970` — historical table row `| 4 | 4 | Quality Assurance Engineer (m/w/d) | N.O.C Engineering GmbH | Dresden | 2026-08-28 | bis 100% Remote (nach Einarbeitung vor Ort) | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) |`
- `15f4e6600603` — historical table row `| 4 | [Quality Assurance Engineer (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) | N.O.C Engineering GmbH | Dresden | 2026-08-28 | bis 100% Remote (nach Einarbeitung vor Ort) | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) |`
- `715983c8bd12` — historical table row `| 4 | [Quality Assurance Engineer (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) | N.O.C Engineering GmbH | Dresden | 2026-08-28 | bis 100% Remote (nach Einarbeitung vor Ort) | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) |`
- `de6181d1fc57` — historical table row `| 43 | [Quality Assurance Engineer (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) | N.O.C Engineering GmbH | Dresden | 2026-08-28 | Hybrid |`
- `8e071115731a` — historical table row `| 13 | [Quality Assurance Engineer (m/w/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/13552-ZEOSLFX6R0Z9I2JL-S) | N.O.C Engineering GmbH | Dresden | 2026-08-28 | Hybrid |`

### 5. PASS — https://www.linkedin.com/jobs/view/4457769285

**Reason:** Same live Dresden QA vacancy as URL 3; URL-level PASS, but semantic duplicate of 3.

**Evidence:** LinkedIn guest card + extraction: Engineer Software Quality Assurance, Diehl Aviation, Dresden, “3 weeks ago”; DO-178/DO-330 duties. No remote option, normalized Onsite. Employer Diehl Aviation Gilching GmbH (DE).

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 5 | Engineer (m/w/d) Software Quality Assurance | Diehl Aviation | Dresden | 2026-08-27 | Onsite (DO-178) | 2026-09-21 | [Link](https://www.linkedin.com/jobs/view/4457769285) |`
- `372f41757315` — historical table row `| 5 | Engineer (m/w/d) Software Quality Assurance | Diehl Aviation | Dresden | 2026-08-27 | Onsite (DO-178) | 2026-09-21 | [Link](https://www.linkedin.com/jobs/view/4457769285) |`
- `3ad3e8fe0970` — historical table row `| 5 | 5 | Engineer (m/w/d) Software Quality Assurance | Diehl Aviation | Dresden | 2026-08-27 | Onsite (DO-178) | [Link](https://www.linkedin.com/jobs/view/4457769285) |`
- `15f4e6600603` — historical table row `| 5 | [Engineer (m/w/d) Software Quality Assurance](https://www.linkedin.com/jobs/view/4457769285) | Diehl Aviation | Dresden | 2026-08-27 | Onsite (DO-178) | [Link](https://www.linkedin.com/jobs/view/4457769285) |`
- `715983c8bd12` — historical table row `| 5 | [Engineer (m/w/d) Software Quality Assurance](https://www.linkedin.com/jobs/view/4457769285) | Diehl Aviation | Dresden | 2026-08-27 | Onsite (DO-178) | [Link](https://www.linkedin.com/jobs/view/4457769285) |`
- `de6181d1fc57` — historical table row `| 45 | [Engineer (m/w/d) Software Quality Assurance](https://www.linkedin.com/jobs/view/4457769285) | Diehl Aviation | Dresden | 2026-08-27 | Onsite |`

### 6. REJECT — https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S

**Reason:** Freshness gate fails on the current card.

**Evidence:** BA direct card and extraction identify the Bosch wafer-test role, but the direct card states “Veröffentlichungsdatum: Vor 30+ Tagen veröffentlicht”. As of 2026-09-24 it is older than 30 days, regardless of edit date.

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 6 | Senior Testingenieur Wafertest (w/m/div) | Robert Bosch GmbH | Dresden | 2026-09-14 | Onsite | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) |`
- `372f41757315` — historical table row `| 6 | Senior Testingenieur Wafertest (w/m/div) | Robert Bosch GmbH | Dresden | 2026-09-14 | Onsite | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) |`
- `3ad3e8fe0970` — historical table row `| 1 | 6 | Senior Testingenieur Wafertest (w/m/div) | Robert Bosch GmbH | Dresden | 2026-09-14 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) |`
- `15f4e6600603` — historical table row `| 1 | [Senior Testingenieur Wafertest (w/m/div)](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) | Robert Bosch GmbH | Dresden | 2026-09-14 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) |`
- `715983c8bd12` — historical table row `| 1 | [Senior Testingenieur Wafertest (w/m/div)](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) | Robert Bosch GmbH | Dresden | 2026-09-14 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) |`
- `de6181d1fc57` — historical table row `| 15 | [Senior Testingenieur Wafertest (w/m/div)](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) | Robert Bosch GmbH | Dresden | 2026-09-14 | Onsite |`
- `8e071115731a` — historical table row `| 2 | [Senior Testingenieur Wafertest (w/m/div)](https://www.arbeitsagentur.de/jobsuche/jobdetail/15986-REF270793G-129145d-S) | Robert Bosch GmbH | Dresden | 2026-09-14 | Onsite |`

### 7. PASS — https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S

**Reason:** QA role, Dresden Onsite and freshness are supported.

**Evidence:** BA direct card + extraction: “Quality Engineer – Outgoing Quality Assurance (OQA)”, “Arbeitsort Dresden”, “Vor 22 Tagen veröffentlicht”, Qualitätsingenieur/in. No remote option, normalized Onsite; German employer context confirmed.

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 7 | Quality Engineer – Outgoing Quality Assurance (OQA) (m/f/d) | European Semiconductor Mfg. Company (ESMC) | Dresden | 2026-09-02 | Onsite | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) |`
- `372f41757315` — historical table row `| 7 | Quality Engineer – Outgoing Quality Assurance (OQA) (m/f/d) | European Semiconductor Mfg. Company (ESMC) | Dresden | 2026-09-02 | Onsite | 2026-09-21 | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) |`
- `3ad3e8fe0970` — historical table row `| 6 | 7 | Quality Engineer – Outgoing Quality Assurance (OQA) (m/f/d) | European Semiconductor Mfg. Company (ESMC) | Dresden | 2026-09-02 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) |`
- `15f4e6600603` — historical table row `| 6 | [Quality Engineer – Outgoing Quality Assurance (OQA) (m/f/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) | European Semiconductor Mfg. Company (ESMC) | Dresden | 2026-09-02 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) |`
- `715983c8bd12` — historical table row `| 6 | [Quality Engineer – Outgoing Quality Assurance (OQA) (m/f/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) | European Semiconductor Mfg. Company (ESMC) | Dresden | 2026-09-02 | Onsite | [Link](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) |`
- `de6181d1fc57` — historical table row `| 42 | [Quality Engineer – Outgoing Quality Assurance (OQA) (m/f/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) | European Semiconductor Mfg. Company (ESMC) | Dresden | 2026-09-02 | Onsite |`
- `8e071115731a` — historical table row `| 12 | [Quality Engineer – Outgoing Quality Assurance (OQA) (m/f/d)](https://www.arbeitsagentur.de/jobsuche/jobdetail/12288-4928648696-S) | European Semiconductor Mfg. Company (ESMC) | Dresden | 2026-09-02 | Onsite |`

### 8. REJECT — https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519

**Reason:** Onsite in Regensburg is outside the allowed cities; no Germany-wide remote evidence.

**Evidence:** LinkedIn guest card + extraction: CipSoft GmbH, Softwaretester Online Spiele, Regensburg, within 30 days. The description offers flexible hours, not remote. Regensburg Onsite is outside target cities.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 8 | Softwaretester Online Spiele (m/w/d) | CipSoft GmbH | Regensburg, DE | 2026-09-20 | OK (200) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) |`
- `372f41757315` — historical table row `| 8 | Softwaretester Online Spiele (m/w/d) | CipSoft GmbH | Regensburg, DE | 2026-09-20 | OK (200) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) |`
- `3ad3e8fe0970` — historical table row `| 7 | 8 | Softwaretester Online Spiele (m/w/d) | CipSoft GmbH | Regensburg, DE | 2026-09-20 | OK (200) | [Link](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) |`
- `15f4e6600603` — historical table row `| 7 | [Softwaretester Online Spiele (m/w/d)](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) | CipSoft GmbH | Regensburg, DE | 2026-09-20 | OK (200) | [Link](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) |`
- `715983c8bd12` — historical table row `| 7 | [Softwaretester Online Spiele (m/w/d)](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) | CipSoft GmbH | Regensburg, DE | 2026-09-20 | — | [Link](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) |`
- `de6181d1fc57` — historical table row `| 5 | [Softwaretester Online Spiele (m/w/d)](https://de.linkedin.com/jobs/view/softwaretester-online-spiele-m-w-d-at-cipsoft-gmbh-4412002519) | CipSoft GmbH | Regensburg, DE | 2026-09-20 | Onsite |`

### 9. PASS — https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937

**Reason:** Explicit 100% Remote in Germany satisfies the remote route.

**Evidence:** LinkedIn guest card + extraction: “Softwaretester … 100 % Remote”, “Deutschland”, “Vor 2 Wochen”; body says “zu 100 % remote” and about five client trips/year. Test design/manual testing/automation confirmed. eightbit experts GmbH is German.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 9 | Softwaretester (m/w/d) 100 % Remote | eightbit experts GmbH | bundesweit, 100 % Remote | 2026-09-04 | ✅ `Berlin` (Impressum; site also lists Berlin) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) |`
- `372f41757315` — historical table row `| 9 | Softwaretester (m/w/d) 100 % Remote | eightbit experts GmbH | bundesweit, 100 % Remote | 2026-09-04 | ✅ `Berlin` (Impressum; site also lists Berlin) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) |`
- `3ad3e8fe0970` — historical table row `| 8 | 9 | Softwaretester (m/w/d) 100 % Remote | eightbit experts GmbH | bundesweit, 100 % Remote | 2026-09-04 | ✅ `Berlin` (Impressum; site also lists Berlin) | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) |`
- `15f4e6600603` — historical table row `| 8 | [Softwaretester (m/w/d) 100 % Remote](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) | eightbit experts GmbH | bundesweit, 100 % Remote | 2026-09-04 | ✅ Berlin (Impressum; site also lists Berlin) | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) |`
- `715983c8bd12` — historical table row `| 8 | [Softwaretester (m/w/d) 100 % Remote](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) | eightbit experts GmbH | bundesweit, 100 % Remote | 2026-09-04 | — | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) |`
- `de6181d1fc57` — historical table row `| 36 | [Softwaretester (m/w/d) 100 % Remote](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-100-%25-remote-im-consulting-umfeld-at-eightbit-experts-gmbh-4463646937) | eightbit experts GmbH | bundesweit, 100 % Remote | 2026-09-04 | Remote |`

### 10. PASS — https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202

**Reason:** Explicit Germany location plus 100% Homeoffice satisfies Remote DE.

**Evidence:** LinkedIn guest card + extraction: “Softwaretester”, “Deutschland”, “Vor 1 Woche”; “100 %Homeoffice möglich”. Existing independent check confirms deltra Business Software GmbH & Co. KG, Gildestraße 9, D-32760 Detmold, HRA 4748, AG Lemgo.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 10 | Softwaretester (m/w/d) | deltra Business Software GmbH & Co. KG | Deutschland (remote-friendly) | 2026-09-14 | ✅ `Gildestraße 9, 32760 Detmold` — HRA 4748, AG Lemgo | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) |`
- `372f41757315` — historical table row `| 10 | Softwaretester (m/w/d) | deltra Business Software GmbH & Co. KG | Deutschland (remote-friendly) | 2026-09-14 | ✅ `Gildestraße 9, 32760 Detmold` — HRA 4748, AG Lemgo | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) |`
- `3ad3e8fe0970` — historical table row `| 9 | 10 | Softwaretester (m/w/d) | deltra Business Software GmbH & Co. KG | Deutschland (remote-friendly) | 2026-09-14 | ✅ `Gildestraße 9, 32760 Detmold` — HRA 4748, AG Lemgo | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) |`
- `15f4e6600603` — historical table row `| 9 | [Softwaretester (m/w/d)](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) | deltra Business Software GmbH & Co. KG | Deutschland (remote-friendly) | 2026-09-14 | ✅ Gildestraße 9, 32760 Detmold — HRA 4748, AG Lemgo | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) |`
- `715983c8bd12` — historical table row `| 9 | [Softwaretester (m/w/d)](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) | deltra Business Software GmbH & Co. KG | Deutschland (remote-friendly) | 2026-09-14 | — | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) |`
- `de6181d1fc57` — historical table row `| 21 | [Softwaretester (m/w/d)](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202) | deltra Business Software GmbH & Co. KG | Deutschland (remote-friendly) | 2026-09-14 | Remote |`

### 11. REJECT — https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731

**Reason:** Current card is Bonlanden, not Berlin, and offers no explicit Germany-wide remote eligibility.

**Evidence:** LinkedIn guest card + extraction: Software QA Engineer, Instaffo, “Bonlanden”, “Vor 2 Wochen”. Existing independent recheck confirms Bite AG (Filderstadt)/Instaffo GmbH and Bonlanden. No Germany-wide Remote statement.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 11 | Software QA Engineer (m/w/d) | Instaffo GmbH | Germany (remote) | 2026-09-09 | ✅ `Mannheim` (Impressum: Registergericht Mannheim, Country: Germany) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) |`
- `372f41757315` — historical table row `| 11 | Software QA Engineer (m/w/d) | Instaffo GmbH | Germany (remote) | 2026-09-09 | ✅ `Mannheim` (Impressum: Registergericht Mannheim, Country: Germany) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) |`
- `3ad3e8fe0970` — historical table row `| 10 | 11 | Software QA Engineer (m/w/d) | Instaffo GmbH | Germany (remote) | 2026-09-09 | ✅ `Mannheim` (Impressum: Registergericht Mannheim, Country: Germany) | [Link](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) |`
- `15f4e6600603` — historical table row `| 10 | [Software QA Engineer (m/w/d)](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) | Instaffo GmbH | Germany (remote) | 2026-09-09 | ✅ Mannheim (Impressum: Registergericht Mannheim, Country: Germany) | [Link](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) |`
- `715983c8bd12` — historical table row `| 10 | [Software QA Engineer (m/w/d)](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) | Instaffo GmbH | Germany (remote) | 2026-09-09 | — | [Link](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) |`
- `de6181d1fc57` — historical table row `| 28 | [Software QA Engineer (m/w/d)](https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731) | Instaffo GmbH | Germany (remote) | 2026-09-09 | Remote |`

### 12. UNCLEAR — https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646

**Reason:** Berlin QA role and freshness are supported, but work mode is not established under the strict vocabulary.

**Evidence:** LinkedIn guest card + extraction: Senior Testingenieur:in/QA Engineer, Instaffo, Berlin, “Vor 2 Wochen”, Tosca/test-infrastructure duties. “Remote” strings are similar-job boilerplate; no reliable work-mode statement for the vacancy.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 12 | Senior Testingenieur:in – QA Engineer | Instaffo GmbH | Berlin (remote/hybrid) | 2026-09-08 | ✅ same as #3 | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) |`
- `372f41757315` — historical table row `| 12 | Senior Testingenieur:in – QA Engineer | Instaffo GmbH | Berlin (remote/hybrid) | 2026-09-08 | ✅ same as #3 | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) |`
- `3ad3e8fe0970` — historical table row `| 2 | 12 | Senior Testingenieur:in – QA Engineer | Instaffo GmbH | Berlin (remote/hybrid) | 2026-09-08 | ✅ same as #3 | [Link](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) |`
- `15f4e6600603` — historical table row `| 2 | [Senior Testingenieur:in – QA Engineer](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) | Instaffo GmbH | Berlin (remote/hybrid) | 2026-09-08 | ✅ same as #3 | [Link](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) |`
- `715983c8bd12` — historical table row `| 2 | [Senior Testingenieur:in – QA Engineer](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) | Instaffo GmbH | Berlin (remote/hybrid) | 2026-09-08 | — | [Link](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) |`
- `de6181d1fc57` — historical table row `| 21 | [Senior Testingenieur:in – QA Engineer](https://de.linkedin.com/jobs/view/senior-testingenieur-in-%E2%80%93-testautomatisierung-qualit%C3%A4tssicherung-qa-engineer-at-instaffo-4422965646) | Instaffo GmbH | Berlin (remote/hybrid) | 2026-09-08 | Remote |`

### 13. REJECT — https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652

**Reason:** Current role is Lübeck and no explicit Germany-wide remote wording is present.

**Evidence:** LinkedIn guest card + extraction: Software Tester – Cloud & Applications, SOA Experts GmbH, Lübeck, “Vor 5 Tagen”; QA duties confirmed. No reliable “bundesweit/100% remote” statement for this role.

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 13 | Software Tester (m/w/d) – Cloud & Applications | SOA Experts GmbH | Lübeck / bundesweit Remote | 2026-09-18 | ✅ `Lübeck` (Impressum SOA Experts GmbH, § 5 TMG) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) |`
- `372f41757315` — historical table row `| 13 | Software Tester (m/w/d) – Cloud & Applications | SOA Experts GmbH | Lübeck / bundesweit Remote | 2026-09-18 | ✅ `Lübeck` (Impressum SOA Experts GmbH, § 5 TMG) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) |`
- `3ad3e8fe0970` — historical table row `| 11 | 13 | Software Tester (m/w/d) – Cloud & Applications | SOA Experts GmbH | Lübeck / bundesweit Remote | 2026-09-18 | ✅ `Lübeck` (Impressum SOA Experts GmbH, § 5 TMG) | [Link](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) |`
- `15f4e6600603` — historical table row `| 11 | [Software Tester (m/w/d) – Cloud & Applications](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) | SOA Experts GmbH | Lübeck / bundesweit Remote | 2026-09-18 | ✅ Lübeck (Impressum SOA Experts GmbH, § 5 TMG) | [Link](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) |`
- `715983c8bd12` — historical table row `| 11 | [Software Tester (m/w/d) – Cloud & Applications](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) | SOA Experts GmbH | Lübeck / bundesweit Remote | 2026-09-18 | — | [Link](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) |`
- `de6181d1fc57` — historical table row `| 13 | [Software Tester (m/w/d) – Cloud & Applications](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) | SOA Experts GmbH | Lübeck / bundesweit Remote | 2026-09-18 | Remote |`
- `8e071115731a` — historical table row `| 3 | [Software Tester (m/w/d) – Cloud & Applications](https://de.linkedin.com/jobs/view/software-tester-m-w-d-%E2%80%93-cloud-applications-at-soa-experts-gmbh-4467863652) | SOA Experts GmbH | Lübeck / bundesweit Remote | 2026-09-18 | Remote |`

### 14. UNCLEAR — https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763

**Reason:** Berlin QA role and freshness are clear, but work mode is not.

**Evidence:** LinkedIn guest card + extraction: (Senior) QA Engineer, DKB Code Factory GmbH, Berlin, “Vor 2 Wochen”. Current card does not reliably state Berlin Hybrid or Germany-wide Remote; remote strings are similar-job boilerplate.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 14 | (Senior) QA Engineer (x/f/m) | DKB Code Factory GmbH | Berlin (remote option) | 2026-09-09 | ✅ `Berlin` (DKB subsidiary, registered in DE) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) |`
- `372f41757315` — historical table row `| 14 | (Senior) QA Engineer (x/f/m) | DKB Code Factory GmbH | Berlin (remote option) | 2026-09-09 | ✅ `Berlin` (DKB subsidiary, registered in DE) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) |`
- `3ad3e8fe0970` — historical table row `| 12 | 14 | (Senior) QA Engineer (x/f/m) | DKB Code Factory GmbH | Berlin (remote option) | 2026-09-09 | ✅ `Berlin` (DKB subsidiary, registered in DE) | [Link](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) |`
- `15f4e6600603` — historical table row `| 12 | [(Senior) QA Engineer (x/f/m)](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) | DKB Code Factory GmbH | Berlin (remote option) | 2026-09-09 | ✅ Berlin (DKB subsidiary, registered in DE) | [Link](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) |`
- `715983c8bd12` — historical table row `| 12 | [(Senior) QA Engineer (x/f/m)](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) | DKB Code Factory GmbH | Berlin (remote option) | 2026-09-09 | ✅ Berlin (DKB subsidiary, registered in DE) | [Link](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) |`
- `de6181d1fc57` — historical table row `| 30 | [(Senior) QA Engineer (x/f/m)](https://de.linkedin.com/jobs/view/senior-qa-engineer-x-f-m-at-dkb-code-factory-gmbh-4463017763) | DKB Code Factory GmbH | Berlin (remote option) | 2026-09-09 | Remote |`

### 15. REJECT — https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277

**Reason:** Munich role has no explicit Germany-wide remote eligibility; remote strings are unrelated similar-job cards.

**Evidence:** LinkedIn guest card + extraction: Quality Assurance Specialist, TeleClinic, München, “Vor 1 Woche”. No Germany-wide remote wording for this vacancy; remote strings are unrelated similar-job cards.

**Commits (7):**
- `63f53a2cb4c8` — historical table row `| 15 | Quality Assurance Specialist (m/f/d) | TeleClinic | Munich (hybrid/remote-DE) | 2026-09-13 | known-DE (TeleClinic GmbH, Munich) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) |`
- `372f41757315` — historical table row `| 15 | Quality Assurance Specialist (m/f/d) | TeleClinic | Munich (hybrid/remote-DE) | 2026-09-13 | known-DE (TeleClinic GmbH, Munich) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) |`
- `3ad3e8fe0970` — historical table row `| 13 | 15 | Quality Assurance Specialist (m/f/d) | TeleClinic | Munich (hybrid/remote-DE) | 2026-09-13 | known-DE (TeleClinic GmbH, Munich) | [Link](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) |`
- `15f4e6600603` — historical table row `| 13 | [Quality Assurance Specialist (m/f/d)](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) | TeleClinic | Munich (hybrid/remote-DE) | 2026-09-13 | known-DE (TeleClinic GmbH, Munich) | [Link](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) |`
- `715983c8bd12` — historical table row `| 13 | [Quality Assurance Specialist (m/f/d)](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) | TeleClinic | Munich (hybrid/remote-DE) | 2026-09-13 | — | [Link](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) |`
- `de6181d1fc57` — historical table row `| 23 | [Quality Assurance Specialist (m/f/d)](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) | TeleClinic | Munich (hybrid/remote-DE) | 2026-09-13 | Remote |`
- `8e071115731a` — historical table row `| 8 | [Quality Assurance Specialist (m/f/d)](https://de.linkedin.com/jobs/view/quality-assurance-specialist-m-f-d-at-teleclinic-4447191277) | TeleClinic | Munich (hybrid/remote-DE) | 2026-09-13 | Remote |`

### 16. REJECT — https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html

**Reason:** The historical StepStone URL no longer resolves to this vacancy and is a wrong-page/dead-link rejection.

**Evidence:** Web extraction rendered a replacement “Software Quality Engineer … in Pulsnitz”, not the historical seca Hamburg card. Curl failed (status 0). Two methods do not support the claimed role/date/mode/company.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 16 | Software-Tester (w/m/d) – Schwerpunkt manuelle Tests | seca GmbH & Co. KG | Hamburg / Home-Office | ~vor 1 Woche | ✅ `Hamburg` (seca DE entity, registered DE) | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) |`
- `372f41757315` — historical table row `| 16 | Software-Tester (w/m/d) – Schwerpunkt manuelle Tests | seca GmbH & Co. KG | Hamburg / Home-Office | ~vor 1 Woche | ✅ `Hamburg` (seca DE entity, registered DE) | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) |`
- `3ad3e8fe0970` — historical table row `| 1 | 16 | Software-Tester (w/m/d) – Schwerpunkt manuelle Tests | seca GmbH & Co. KG | Hamburg / Home-Office | ~vor 1 Woche | ✅ `Hamburg` (seca DE entity, registered DE) | [Link](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) |`
- `15f4e6600603` — historical table row `| 1 | [Software-Tester (w/m/d) – Schwerpunkt manuelle Tests](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) | seca GmbH & Co. KG | Hamburg / Home-Office | ~vor 1 Woche | ✅ Hamburg (seca DE entity, registered DE) | [Link](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) |`
- `715983c8bd12` — historical table row `| 1 | [Software-Tester (w/m/d) – Schwerpunkt manuelle Tests](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) | seca GmbH & Co. KG | Hamburg / Home-Office | ~vor 1 Woche | ✅ Hamburg (seca DE entity, registered DE) | [Link](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) |`
- `de6181d1fc57` — historical table row `| 6 | [Software-Tester (w/m/d) – Schwerpunkt manuelle Tests](https://www.stepstone.de/stellenangebote--Software-Tester-w-m-d-Schwerpunkt-manuelle-Tests-Hamburg-seca-GmbH-Co-KG--14519955-inline.html) | seca GmbH & Co. KG | Hamburg / Home-Office | ~vor 1 Woche | Remote |`

### 17. REJECT — https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576

**Reason:** Dortmund Onsite is outside the allowed cities.

**Evidence:** LinkedIn guest card + extraction: CHECK24 QA Engineer/Software-Tester, Dortmund, current age within 30 days; Web/iOS/Android QA duties. No explicit Germany-wide remote. German employer Verbraucherportal Deutschland GmbH.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 17 | (Junior) QA Engineer/Software-Tester (m/w/d) | CHECK24 | Dortmund | 2026-09-20 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) |`
- `372f41757315` — historical table row `| 17 | (Junior) QA Engineer/Software-Tester (m/w/d) | CHECK24 | Dortmund | 2026-09-20 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) |`
- `3ad3e8fe0970` — historical table row `| 14 | 17 | (Junior) QA Engineer/Software-Tester (m/w/d) | CHECK24 | Dortmund | 2026-09-20 | known-DE | [Link](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) |`
- `15f4e6600603` — historical table row `| 14 | [(Junior) QA Engineer/Software-Tester (m/w/d)](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) | CHECK24 | Dortmund | 2026-09-20 | known-DE | [Link](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) |`
- `715983c8bd12` — historical table row `| 14 | [(Junior) QA Engineer/Software-Tester (m/w/d)](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) | CHECK24 | Dortmund | 2026-09-20 | — | [Link](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) |`
- `de6181d1fc57` — historical table row `| 9 | [(Junior) QA Engineer/Software-Tester (m/w/d)](https://de.linkedin.com/jobs/view/junior-qa-engineer-software-tester-m-w-d-%E2%80%93-produktqualit%C3%A4t-testautomatisierung-at-check24-4433870576) | CHECK24 | Dortmund | 2026-09-20 | Onsite |`

### 18. REJECT — https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338

**Reason:** Stuttgart Onsite is outside the allowed cities.

**Evidence:** LinkedIn guest card + extraction: Quality Assurance Engineer, Quantum Machines, Stuttgart, “Vor 4 Tagen”. No explicit Germany-wide remote; Stuttgart Onsite fails the location gate.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 18 | Quality Assurance Engineer | Quantum Machines | Stuttgart | 2026-09-20 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) |`
- `372f41757315` — historical table row `| 18 | Quality Assurance Engineer | Quantum Machines | Stuttgart | 2026-09-20 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) |`
- `3ad3e8fe0970` — historical table row `| 15 | 18 | Quality Assurance Engineer | Quantum Machines | Stuttgart | 2026-09-20 | known-DE | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) |`
- `15f4e6600603` — historical table row `| 15 | [Quality Assurance Engineer](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) | Quantum Machines | Stuttgart | 2026-09-20 | known-DE | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) |`
- `715983c8bd12` — historical table row `| 15 | [Quality Assurance Engineer](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) | Quantum Machines | Stuttgart | 2026-09-20 | — | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) |`
- `de6181d1fc57` — historical table row `| 7 | [Quality Assurance Engineer](https://de.linkedin.com/jobs/view/quality-assurance-engineer-at-quantum-machines-4468447338) | Quantum Machines | Stuttgart | 2026-09-20 | Onsite |`

### 19. REJECT — https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021

**Reason:** Aachen is outside target cities; “Homeoffice possibility” is not explicit Germany-wide Remote.

**Evidence:** LinkedIn guest card + extraction: QA Engineer, Nexburg, Aachen, within 30 days; test-system/test-case duties and “Möglichkeit zum Homeoffice”. Optional home office is not explicit Germany-wide Remote and Aachen is outside target cities.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 19 | (Senior) QA Engineer | Nexburg GmbH | Aachen | 2026-09-10 | ✅ `Nexburg GmbH` (site footer, Aachen) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) |`
- `372f41757315` — historical table row `| 19 | (Senior) QA Engineer | Nexburg GmbH | Aachen | 2026-09-10 | ✅ `Nexburg GmbH` (site footer, Aachen) | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) |`
- `3ad3e8fe0970` — historical table row `| 16 | 19 | (Senior) QA Engineer | Nexburg GmbH | Aachen | 2026-09-10 | ✅ `Nexburg GmbH` (site footer, Aachen) | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) |`
- `15f4e6600603` — historical table row `| 16 | [(Senior) QA Engineer](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) | Nexburg GmbH | Aachen | 2026-09-10 | ✅ Nexburg GmbH (site footer, Aachen) | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) |`
- `715983c8bd12` — historical table row `| 16 | [(Senior) QA Engineer](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) | Nexburg GmbH | Aachen | 2026-09-10 | ✅ Nexburg GmbH (site footer, Aachen) | [Link](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) |`
- `de6181d1fc57` — historical table row `| 27 | [(Senior) QA Engineer](https://de.linkedin.com/jobs/view/quality-assurance-engineer-m-w-d-at-nexburg-4463475021) | Nexburg GmbH | Aachen | 2026-09-10 | Onsite |`

### 20. REJECT — https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181

**Reason:** Explicit Hybrid in Aschleim/Munich region is outside target cities.

**Evidence:** LinkedIn guest card + extraction: ERP Quality Assurance Engineer, mytheresa.com, Munich region, within 30 days; “Working Model: Hybrid” and “Location: Aschleim”. Aschleim is outside target cities.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 20 | ERP Quality Assurance Engineer (f/m/d) | Mytheresa | Munich | 2026-09-07 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) |`
- `372f41757315` — historical table row `| 20 | ERP Quality Assurance Engineer (f/m/d) | Mytheresa | Munich | 2026-09-07 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) |`
- `3ad3e8fe0970` — historical table row `| 17 | 20 | ERP Quality Assurance Engineer (f/m/d) | Mytheresa | Munich | 2026-09-07 | known-DE | [Link](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) |`
- `15f4e6600603` — historical table row `| 17 | [ERP Quality Assurance Engineer (f/m/d)](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) | Mytheresa | Munich | 2026-09-07 | known-DE | [Link](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) |`
- `715983c8bd12` — historical table row `| 17 | [ERP Quality Assurance Engineer (f/m/d)](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) | Mytheresa | Munich | 2026-09-07 | — | [Link](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) |`
- `de6181d1fc57` — historical table row `| 35 | [ERP Quality Assurance Engineer (f/m/d)](https://de.linkedin.com/jobs/view/erp-quality-assurance-engineer-f-m-d-at-mytheresa-4464363181) | Mytheresa | Munich | 2026-09-07 | Onsite |`

### 21. REJECT — https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998

**Reason:** Düsseldorf is outside target cities; limited mobile days are not Germany-wide Remote.

**Evidence:** LinkedIn guest card + extraction: DMRZ Softwaretester Healthcare SaaS, Düsseldorf, “Vor 1 Woche”; “bis zu 2 Tage mobiles Arbeiten pro Woche”. Limited mobile days are not Germany-wide Remote; Düsseldorf is outside target cities.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 21 | Softwaretester (m/w/d) – Healthcare SaaS | Deutsches Medizinrechenzentrum GmbH | Düsseldorf | 2026-09-16 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) |`
- `372f41757315` — historical table row `| 21 | Softwaretester (m/w/d) – Healthcare SaaS | Deutsches Medizinrechenzentrum GmbH | Düsseldorf | 2026-09-16 | known-DE | 2026-09-21 | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) |`
- `3ad3e8fe0970` — historical table row `| 18 | 21 | Softwaretester (m/w/d) – Healthcare SaaS | Deutsches Medizinrechenzentrum GmbH | Düsseldorf | 2026-09-16 | known-DE | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) |`
- `15f4e6600603` — historical table row `| 18 | [Softwaretester (m/w/d) – Healthcare SaaS](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) | Deutsches Medizinrechenzentrum GmbH | Düsseldorf | 2026-09-16 | known-DE | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) |`
- `715983c8bd12` — historical table row `| 18 | [Softwaretester (m/w/d) – Healthcare SaaS](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) | Deutsches Medizinrechenzentrum GmbH | Düsseldorf | 2026-09-16 | — | [Link](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) |`
- `de6181d1fc57` — historical table row `| 20 | [Softwaretester (m/w/d) – Healthcare SaaS](https://de.linkedin.com/jobs/view/softwaretester-m-w-d-%E2%80%93-healthcare-saas-at-deutsches-medizinrechenzentrum-gmbh-4466469998) | Deutsches Medizinrechenzentrum GmbH | Düsseldorf | 2026-09-16 | Onsite |`

### 22. REJECT — https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html

**Reason:** The historical StepStone URL now resolves to a different vacancy (wrong page).

**Evidence:** Web extraction rendered “Senior QA Engineer … in Lübbecke”, not igus Cologne. Curl failed (status 0). Two methods do not support the historical igus role/freshness/mode; direct URL fails SPEC §2.8.

**Commits (6):**
- `63f53a2cb4c8` — historical table row `| 22 | Quality Assurance Engineer (m/w/d) E-Commerce | igus SE & Co. KG | Cologne | aktiv ≤30d | known-DE | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) |`
- `372f41757315` — historical table row `| 22 | Quality Assurance Engineer (m/w/d) E-Commerce | igus SE & Co. KG | Cologne | aktiv ≤30d | known-DE | 2026-09-21 | [Link](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) |`
- `3ad3e8fe0970` — historical table row `| 19 | 22 | Quality Assurance Engineer (m/w/d) E-Commerce | igus SE & Co. KG | Cologne | aktiv ≤30d | known-DE | [Link](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) |`
- `15f4e6600603` — historical table row `| 19 | [Quality Assurance Engineer (m/w/d) E-Commerce](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) | igus SE & Co. KG | Cologne | aktiv ≤30d | known-DE | [Link](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) |`
- `715983c8bd12` — historical table row `| 19 | [Quality Assurance Engineer (m/w/d) E-Commerce](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) | igus SE & Co. KG | Cologne | aktiv ≤30d | — | [Link](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) |`
- `de6181d1fc57` — historical table row `| 47 | [Quality Assurance Engineer (m/w/d) E-Commerce](https://www.stepstone.de/stellenangebote--Quality-Assurance-Engineer-m-w-d-E-Commerce-Koeln-igus-SE-Co-KG--14501510-inline.html) | igus SE & Co. KG | Cologne | aktiv ≤30d | Onsite |`

## Audit observations

- URL 5 is a valid duplicate representation of URL 3; URL-level PASS does not authorize two published rows.
- URL 6 is demonstrably older than 30 days on the current card; an edit date is not a fresh posting date.
- Historical notes such as “remote-friendly”, “hybrid/remote-DE”, or home-office possibility do not override absent/ambiguous current-card evidence.
- Four rows remain UNCLEAR rather than being guessed: 4, 12, 14, and 14 is listed once; the actual set is 4, 12, and 14 (3 total).

## Local evidence

- Direct captures: `/opt/data/qa-vacancy-project/.history_001-022_curl/*.html`
- Fetch metadata: `/opt/data/qa-vacancy-project/.history_001-022_curl/records.json`
- Independent extraction snapshot: `/opt/data/qa-vacancy-project/.history_001-022_web_extract.json`
- Prior focused independent check reused for URLs 10–11: `/opt/data/qa-vacancy-project/recheck_unclear_001-035.md`
