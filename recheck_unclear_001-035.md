# Recheck of old `UNCLEAR` vacancies — audit IDs 1–35

Recheck date: 2026-09-24. Rules: current `/opt/data/SPEC.md`. Source audit: `verify_old_105.md`.  
Scope note: IDs 1–35 contain **7** rows marked `UNCLEAR` (not 29); all 7 were rechecked. The master was not modified.

## Counts

- **PASS: 5**
- **REJECT: 2**
- **UNCLEAR remaining: 0**
- **Total rechecked: 7**

## Verdicts and evidence

### ID 21 — PASS
- **Vacancy:** Softwaretester (m/w/d), deltra Business Software GmbH & Co. KG
- **URL:** https://de.linkedin.com/jobs/view/softwaretester-m-w-d-at-deltra-business-software-gmbh-co-kg-4467085202
- **Verdict rationale:** Fresh direct QA vacancy, explicit Germany-wide remote arrangement, and a German legal entity are all confirmed.
- **Method 1 — direct LinkedIn guest API:** `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4467085202` returned the direct card HTML. Evidence: employer `deltra Business Software GmbH & Co. KG`; location `Germany`; age `1 week ago`; role evidence includes functional/non-functional test runs, manual/automatic test cases and defect analysis; work-mode evidence: **“100 %Homeoffice möglich”**.
- **Method 2 — independent page extraction:** `web_extract` of the vacancy URL returned the same title/employer, **“Vor 1 Woche”**, Germany location, QA duties, and **“100 %Homeoffice möglich.”**
- **DE-entity evidence:** official `https://www.orgamax.de/impressum/` states **“deltra Business Software GmbH & Co. KG, Gildestraße 9, D-32760 Detmold”**, Amtsgericht Lemgo HRA 4748, and DE VAT DE264995557.
- **Gate:** QA role **confirmed**; freshness **≤30 days**; German entity **confirmed**; mode `Remote`; Germany-wide eligibility is explicit through Germany location + 100% home-office wording; direct card live.

### ID 24 — REJECT
- **Vacancy:** Senior QA/QC Engineer – Electrical (m/f/d), Exyte
- **URL:** https://www.linkedin.com/jobs/view/4456269253
- **Verdict rationale:** The card is live, fresh, and in Dresden, but the published `Onsite` mode is not evidenced; it describes project inspections and travel. Under the strict gate, mode cannot be inferred.
- **Method 1 — direct LinkedIn guest API:** `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4456269253` returned the direct card. Evidence: title `Senior QA/QC Engineer - Electrical (m/f/d)`, location `Dresden, Saxony, Germany`, age `1 week ago`; description requires electrical inspections, functional tests and travel **“within Germany”** for project assignments.
- **Method 2 — independent page extraction:** `web_extract` of the direct LinkedIn URL returned the same title, Dresden location, age and project-inspection description.
- **Failure:** No exact evidence says the role is `Onsite`; “Willingness to travel within Germany” and project-assignment work do not establish Onsite. The linked source shown by the card is the unrelated `Exyte` developer domain, whose attempted legal pages did not provide the asserted **Exyte Germany GmbH** entity evidence. Per SPEC §2.5–2.7, missing/ambiguous work mode is not guessed.
- **Gate:** QA/test role and Dresden location are plausible/confirmed, freshness is current, but strict work-mode and provenance requirements are not met.

### ID 26 — PASS
- **Vacancy:** QA Engineer (Mid Level), Talon.One
- **URL:** https://de.linkedin.com/jobs/view/qa-engineer-mid-level-at-talon-one-4465625914
- **Verdict rationale:** Fresh direct QA vacancy in Berlin; Berlin office plus home-office arrangement is an acceptable Berlin Hybrid route.
- **Method 1 — direct LinkedIn guest API:** `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4465625914` returned the card. Evidence: title `QA Engineer (Mid Level)`, location `Berlin, Berlin, Germany`, age `2 weeks ago`; QA evidence includes test strategy, end-to-end automated tests and Cypress; benefits explicitly mention **“Home office setup budget, a monthly home office allowance”** and **“our dog-friendly Berlin office”**.
- **Method 2 — independent page extraction:** `web_extract` returned the same title, Berlin location, **“Vor 2 Wochen”**, and QA test-strategy/automation text.
- **DE-entity evidence:** `https://www.talon.one/legal/imprint` states **Talon.One GmbH, Wiener Str. 10, 10999 Berlin**, HRB 172085 B, VAT DE303400336.
- **Gate:** QA role **confirmed**; freshness **≤30 days**; German entity **confirmed**; Berlin Hybrid **confirmed**; direct card live.

### ID 28 — REJECT
- **Vacancy:** Software QA Engineer (m/w/d), Instaffo / Bite AG
- **URL:** https://de.linkedin.com/jobs/view/software-qa-engineer-m-w-d-at-instaffo-4465078731
- **Verdict rationale:** The old master’s `Germany (remote)` mode is not supported. The current direct card places the job in Bonlanden, and no Germany-wide remote wording was found.
- **Method 1 — direct LinkedIn guest API:** `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4465078731` returned the direct card. Evidence: title `Software QA Engineer (m/w/d)`, company `Instaffo`, exact location **“Bonlanden, Baden-Württemberg, Germany”**, age `2 weeks ago`; description identifies the hiring company as **Bite AG** and asks for German work authorization.
- **Method 2 — independent page extraction:** `web_extract` returned the same Bonlanden location and `Vor 2 Wochen`; the extracted duties are QA/test planning and automation, but no explicit Germany-wide remote mode appears.
- **DE-entity evidence:** official pages confirm `Instaffo GmbH`, Römerstraße 135, 69126 Heidelberg, HRB 720838; `https://www.bite.de/impressum/` confirms `Bite AG`, Im Köller 3, 70794 Filderstadt, HRB 225217.
- **Gate:** Role, freshness and German entities are confirmed, but `Onsite` in Bonlanden is outside Berlin/Leipzig/Dresden and Remote lacks explicit Germany-wide eligibility. **REJECT.**

### ID 29 — PASS
- **Vacancy:** Senior QA Engineer (w/m/d) mit Fokus auf Mobile Testing, Zasta
- **URL:** https://de.linkedin.com/jobs/view/senior-qa-engineer-w-m-d-mit-fokus-auf-mobile-testing-at-zasta-4458636126
- **Verdict rationale:** Fresh direct QA vacancy in Berlin with explicit recurring office days and remote work on other days; therefore valid Berlin Hybrid.
- **Method 1 — direct LinkedIn guest API:** `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4458636126` returned the card. Evidence: title, employer `Zasta`, location `Berlin, Germany`, age `2 weeks ago`; work-mode evidence: **two days per week in the office** (Wednesday/Thursday in Berlin), with the remaining days worked from a location of the employee’s choice.
- **Method 2 — independent page extraction:** `web_extract` returned the same title, Berlin, `Vor 2 Wochen`, Playwright/Cypress/Selenium test-automation duties and the two-office-days arrangement.
- **DE-entity evidence:** official `https://assets.zasta.de/legal/imprint_legal_content.json` states **Zasta GmbH, Kurt-Dunkelmann-Str. 2, 18057 Rostock**, Amtsgericht Rostock HRB 14586, VAT DE313684890.
- **Gate:** QA role **confirmed**; freshness **≤30 days**; German entity **confirmed**; explicit Berlin Hybrid **confirmed**; direct card live.

### ID 33 — PASS
- **Vacancy:** QA-Engineer (w/m/d), SupplyOn
- **URL:** https://www.linkedin.com/jobs/view/4462956289
- **Verdict rationale:** Fresh direct software-QA vacancy explicitly for Dresden with explicit Hybrid wording; SupplyOn GmbH is independently confirmed.
- **Method 1 — direct LinkedIn guest API:** `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4462956289` returned the card. Evidence: title `QA-Engineer (w/m/d)`, employer `SupplyOn`, location `Dresden, Saxony, Germany`, age `2 weeks ago`; description explicitly requests a QA engineer for the company’s **“Standort in Dresden (hybrid)”**; duties include manual and automated software tests and test strategies.
- **Method 2 — independent page extraction:** `web_extract` returned the same title, Dresden location, **“2 weeks ago”**, QA duties and explicit **“Dresden (hybrid)”** wording.
- **DE-entity evidence:** official `https://www.supplyon.com/en/imprint/` identifies **SupplyOn GmbH, Ludwigstrasse 49, 85399 Hallbergmoos, Germany** and phone +49 811 99997-0.
- **Gate:** QA role **confirmed**; freshness **≤30 days**; German entity **confirmed**; Dresden Hybrid **confirmed**; direct card live.

### ID 34 — PASS
- **Vacancy:** QA-Engineer (w/m/d), SupplyOn — alternate LinkedIn hostname/path for the same vacancy
- **URL:** https://de.linkedin.com/jobs/view/qa-engineer-w-m-d-at-supplyon-4462956289
- **Verdict rationale:** This is a duplicate representation of ID 33, but it independently resolves to the same live, current Dresden Hybrid vacancy and passes every gate. It should not be counted twice during final deduplication.
- **Method 1 — direct LinkedIn guest API:** `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4462956289` returned the direct card with title, SupplyOn, Dresden, `2 weeks ago`, software-QA duties and the description phrase **“Standort in Dresden (hybrid)”**.
- **Method 2 — independent page extraction:** `web_extract` of this exact alternate URL returned the same content: title `QA-Engineer (w/m/d)`, Dresden, **“Vor 2 Wochen”**, manual/automated testing and **“Dresden (hybrid)”**.
- **DE-entity evidence:** official `https://www.supplyon.com/en/imprint/` identifies **SupplyOn GmbH, Ludwigstrasse 49, 85399 Hallbergmoos, Germany**.
- **Gate:** all fields pass; **PASS as URL, but REJECT for publication as a second row because it duplicates ID 33** (semantic dedupe rule).

## Outcome notes

- Every rechecked row was accessed through at least two methods: direct LinkedIn guest API plus independent `web_extract`; no verdict relies on a bare curl 403.
- IDs 33 and 34 are the same vacancy and therefore must collapse to one logical vacancy in any accepted master.
- The master file was not read for modification and no project master was changed.
