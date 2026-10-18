# ID Audit Specification — 107 historical vacancy URLs

**Audit date:** 2026-09-24  
**Canonical input:** `/opt/data/qa-vacancy-project/github_history_urls.json` → `unique_urls`  
**Scope:** exactly 107 unique historical URLs, indexed **1–107**  
**Output target:** an audit dataset and, after reconciliation, a rebuilt master with one row per semantically unique accepted vacancy and a stable `ID` column.

This document is the authority for this audit. Existing audit files are evidence inputs only, not verdicts. They are known to use inconsistent indexing and incompatible PASS/REJECT rules.

## 1. Canonical identity and indexing

1. Load `unique_urls` in stored order.
2. Assign `url_index` as **1-based position**: `url_index = array_position + 1`.
3. The tuple `(url_index, original_url)` is the canonical audit key.
4. Never use a historical Markdown table row number, a commit-local `#`, a filename range, a semantic title, or an array slice as identity.
5. `github_history_urls.json` says there are 107 unique URLs. The audit must stop with an error if this count differs.
6. URL normalization may be used only to detect aliases. Preserve the original URL string in the audit.
7. Normalization for alias detection:
   - lowercase scheme and host;
   - remove fragment;
   - remove tracking parameters (`utm_*`, `trk`, `source`, `lipi`, `ref`, `originalSubdomain` and equivalent);
   - normalize `www.` only for comparison, not for publication;
   - decode redundant URL encoding where safe;
   - preserve path and source job IDs;
   - never synthesize a URL or add parameters to make it unique.
8. Join all legacy reports to this audit by **exact canonical URL or a documented normalized alias**, then by stable source job ID. Convert legacy references to the canonical `url_index` only after the URL match is proven. If a legacy range or label remains ambiguous, record `legacy_claim` and do not use its count or verdict.
9. The current eight-row public master is known to be incomplete and is not the universe for this audit. Rebuild the master from the reconciled 107-URL audit, not by appending rows to that master.

## 2. Hard acceptance gate

A URL is publishable only if the current identity behind the URL passes **all six hard gates** below. Historical labels, old snippets and old status flags are not current evidence.

### G1 — Role

The current vacancy must be one of:

- Manual WEB QA / manual software testing;
- Software Test / Test Automation / Software Engineer in Test / Quality Engineering whose duties include software testing;
- Gamedev QA / game QA / game testing / game localization testing.

Reject hardware-only testing, wafer/chip testing, product/manufacturing quality, facility/electrical inspection, general compliance and QA-management roles without a qualifying testing duty. Seniority, intern, freelancer and Werkstudent status do not exclude a role if the QA/testing duties are substantive.

### G2 — Posting date

The posting date must be:

```text
2026-08-25 <= posted_date <= 2026-09-24
```

Use this precedence:

1. official JobPosting JSON-LD `datePosted`;
2. official ATS/employer displayed publication date;
3. direct job-board structured date;
4. relative board text resolved against 2026-09-24.

Relative text is permitted only when it resolves unambiguously to a date inside the window. A future date, a relative date spanning the boundary, `aktiv`, `aktuell`, `heute` without a derivable age, or an absent date is not PASS. A date after 2026-09-24 is invalid, not merely fresh.

### G3 — German legal entity

The **employer named by the vacancy** must be linked to a German legal entity. Accept:

- a German `GmbH`, `AG`, `SE`, `GmbH & Co. KG`, etc. named in the vacancy and confirmed by an official imprint/legal page; or
- a portal/brand explicitly linked by an official company page to its hiring German legal entity.

A German job location, German-language page, `.de` domain, address, phone number or group membership alone is insufficient. Evidence for a group parent or subsidiary does not automatically prove the named hiring entity. The evidence must identify the employing legal entity and retain the exact source URL and quoted text.

### G4 — Direct current vacancy card

The URL must resolve to a live direct card for the same vacancy. Search pages, category pages, homepages, expired landing pages, unrelated retargeted cards and reused source IDs fail G4. A portal-hosted direct card is allowed. A `404`, `410`, “no longer available”, or a current card whose employer/title/location is incompatible with the historical identity is a rejection, not a replacement vacancy.

Access failure alone (`403`, `429`, timeout, bot wall) is not proof that the vacancy is dead.

### G5 — Location/work mode

Exactly one accepted route must be evidenced:

```text
(Onsite OR Hybrid) AND location in {Berlin, Leipzig, Dresden}
OR
Remote AND explicit Germany-wide eligibility
```

Rules:

- **Onsite:** require explicit current evidence such as `Vor Ort`, `on-site`, `onsite`, or an equivalent unambiguous marker. Historical “Onsite” text is not enough.
- **Hybrid:** require explicit `Hybrid` or a concrete split arrangement, such as named recurring office days plus work from another location. The office location must be exactly Berlin, Leipzig or Dresden.
- **Remote:** require both explicit remote mode and Germany-wide eligibility in the same vacancy evidence: for example `Remote — Deutschland`, `100 % remote`, `remote in Germany`, or `bundesweit` plus an explicit remote arrangement.
- Generic `Germany`, `DE` or `Deutschland` without an explicit remote mode is insufficient.
- Generic `Homeoffice`, `mobile working`, `flexible working`, or a home-office benefit alone is insufficient unless the current vacancy defines a concrete Hybrid split or explicit Germany-wide Remote eligibility.
- `Radeberg (bei Dresden)`, `Hamburg`, `Munich`, `Stuttgart`, and every other city are not Berlin, Leipzig or Dresden.
- For a multi-city card, acceptance is possible only if Berlin, Leipzig or Dresden is an explicit current option with an explicit accepted mode. Do not infer a mode for the selected city.

### G6 — Evidence completeness and identity consistency

Every accepted verdict must have current evidence for G1–G5 plus a direct-card identity match. Store an evidence excerpt and source URL for every gate. Two independent access paths are required for `PASS`, where technically feasible: for example direct HTTP plus rendered extraction, LinkedIn guest API plus page extraction, or ATS page plus official legal page. Two copies of the same failed HTTP response do not count.

If current sources conflict, do not average or vote. The verdict is `UNCLEAR` until the conflict is resolved by a higher-authority current source.

## 3. Reproducible URL-level verdict schema

Use one JSON object per canonical URL in `historical_url_audit.jsonl`. Field order in the file is `url_index` ascending.

```json
{
  "url_index": 1,
  "original_url": "https://…",
  "normalized_url": "https://…",
  "source_key": "linkedin:4457769285",
  "access": {
    "attempted_methods": ["http", "render"],
    "http_status": 200,
    "final_url": "https://…",
    "current_card": true,
    "blocked": false,
    "notes": ""
  },
  "current_identity": {
    "title": "…",
    "employer_display": "…",
    "employer_legal_name": "…",
    "employer_entity_id": "DE:HRB:…",
    "location": "…",
    "work_mode": "Onsite|Hybrid|Remote|UNKNOWN",
    "germany_wide": true,
    "posted_date": "2026-09-07",
    "identity_match": "MATCH|MISMATCH|UNKNOWN"
  },
  "gates": {
    "role": {"result": "PASS|FAIL|UNKNOWN", "value": "", "evidence": [{"url": "", "quote": "", "method": ""}]},
    "date": {"result": "PASS|FAIL|UNKNOWN", "value": "", "evidence": [{"url": "", "quote": "", "method": ""}]},
    "de_entity": {"result": "PASS|FAIL|UNKNOWN", "value": "", "evidence": [{"url": "", "quote": "", "method": ""}]},
    "direct_current_card": {"result": "PASS|FAIL|UNKNOWN", "value": "", "evidence": [{"url": "", "quote": "", "method": ""}]},
    "location_mode": {"result": "PASS|FAIL|UNKNOWN", "value": "", "evidence": [{"url": "", "quote": "", "method": ""}]},
    "evidence_identity": {"result": "PASS|FAIL|UNKNOWN", "value": "", "evidence": [{"url": "", "quote": "", "method": ""}]}
  },
  "verdict": "PASS|PARTIAL|UNCLEAR|REJECT",
  "reason_code": "…",
  "reason": "…",
  "semantic_group_key": "…|null",
  "duplicate_of_url_index": null,
  "legacy_reports": [{"file": "", "legacy_position": "", "legacy_verdict": "", "match_method": "exact_url|normalized_alias|source_job_id"}],
  "reviewed_at": "2026-09-24T00:00:00Z"
}
```

### Gate results

- `PASS`: affirmative current evidence exists and supports the gate.
- `FAIL`: current evidence affirmatively fails the gate.
- `UNKNOWN`: required current evidence is missing, blocked, ambiguous, contradictory or only historical.

### URL verdicts

1. `PASS`: all six gates are `PASS`.
2. `REJECT`: any gate is an affirmatively supported `FAIL` (wrong/dead card, stale date, non-qualifying role, confirmed non-DE hiring entity, confirmed disallowed city/mode, or incompatible current identity). If several gates fail, choose the most fundamental reason: identity/direct card, role, entity, date, then location/mode.
3. `PARTIAL`: no gate is `FAIL`, but one or more gates are `UNKNOWN` and the missing evidence is specifically retrievable (for example a live card lacks structured date or explicit mode). This is a review state, not publication.
4. `UNCLEAR`: current identity cannot be established, or two current sources materially conflict, or bot/access barriers prevent verification after the prescribed fallback attempts. This is a review state, not publication.

Only `PASS` is eligible for the final master. `PARTIAL` and `UNCLEAR` remain in the audit dataset and are excluded until rechecked. The strict final gate therefore does not contradict the existence of diagnostic `PARTIAL`/`UNCLEAR` states.

## 4. Reconciliation of split legacy audits

Do not merge verdict labels by majority. Merge evidence, then apply this deterministic policy per URL:

1. Ignore legacy `PASS`/`FAIL` status labels as authoritative conclusions.
2. Preserve each legacy claim, access result and evidence quote in `legacy_reports`.
3. Re-evaluate G1–G6 against current evidence and the rules above.
4. If a legacy report used zero-based and another used one-based positions, first match exact URLs. Never copy a verdict by numeric position.
5. If exact normalized URL and stable source job ID cannot prove which report entry is being reconciled, set `UNCLEAR` with reason `LEGACY_IDENTITY_AMBIGUOUS`; do not guess.
6. A current wrong-page/retarget observation overrides an old pass. An old successful observation does not override a current `404/410` or identity mismatch.
7. If one report says a gate passes and another says unknown, aggregate the cited evidence and re-evaluate. `PASS` is allowed only if the combined evidence independently proves every gate.
8. If reports disagree on substantive current facts and neither source dominates by the date/evidence precedence above, use `UNCLEAR` with `CONFLICTING_CURRENT_EVIDENCE`.
9. The historical `PARTIAL` state is never silently converted to publication acceptance. A later complete recheck may change the URL verdict to `PASS` only by supplying all missing current evidence.

## 5. Semantic vacancy identity and duplicate grouping

Deduplication occurs **after** URL verdicts and before ID generation.

### 5.1 Vacancy identity hierarchy

For each PASS URL, build a canonical employer entity key:

1. official German registry identifier when available (`HRB/HRR/HRA + court`);
2. otherwise normalized legal name plus official registered address/court evidence.

Then build `semantic_group_key` in this order:

1. **Official requisition identity:** `<employer_entity_id>|<official_requisition_id>` when the employer/ATS exposes the same requisition or job ID.
2. **Confirmed cross-source identity:** if two portal URLs demonstrably represent the same official requisition, map both to that official identity.
3. **Evidence-backed semantic identity when no requisition ID exists:**  
   `<employer_entity_id>|<role_core>|<seniority>|<eligibility_scope>`  
   where:
   - `role_core` is a controlled normalized role, e.g. `software-qa-engineer`, `test-automation-engineer`, `manual-web-qa`, `game-qa`; remove gender tokens, `(m/w/d)`, locations, percentages and marketing suffixes;
   - `seniority` is one of `intern`, `junior`, `mid`, `senior`, `staff`, `lead`, `principal`, `unspecified`;
   - `eligibility_scope` is `berlin`, `leipzig`, `dresden`, or `remote-de` according to the accepted current route.
4. If a proposed fingerprint matches multiple genuinely distinct openings, add a stable discriminator: official requisition ID if present; otherwise the smallest verified source-native job ID, prefixed `source:`. Never add a posting date or a new URL parameter.

Employer identity is required. Two different legal employers are never duplicates merely because title and location match. The same employer with two different official requisition IDs is not a duplicate. The same role family in two separately evidenced target-city openings is not a duplicate unless the source proves one multi-location requisition.

### 5.2 Duplicate policy

- Alias URLs such as LinkedIn long/short host/path variants collapse into one vacancy.
- One source may have a replacement URL, but the historical URL must still resolve to the same identity for G4 PASS; a new replacement URL does not retroactively make a retargeted historical URL valid.
- For a duplicate group, retain every URL index and source URL in the audit.
- The final master contains exactly one row for each group.
- Do not delete rejected or unclear aliases from the audit; they are not representatives of a PASS group.
- Do not group on title alone.

## 6. Stable semantic ID

Generate IDs only for accepted semantic groups.

Canonical serialized key:

```text
<semantic_group_key>
```

If the official requisition key is available:

```text
<employer_entity_id>|req:<normalized_official_requisition_id>
```

Otherwise use the final semantic group key without a source-specific display prefix.

Normalization for hashing:

1. Unicode NFKC.
2. Lowercase ASCII/latin text.
3. Replace legal-form punctuation and `&` consistently; preserve `gmbh`, `ag`, `se`, `gmbh-co-kg` as legal-form tokens.
4. Collapse whitespace to one hyphen; strip accents only after preserving the legal evidence in fields.
5. Remove non-semantic URL/path text.
6. Do not include posting date, current work-mode prose beyond the canonical eligibility scope, source domain, source URL or audit `url_index`.

ID formula:

```text
QADE-<first 12 uppercase hex characters of SHA-256(canonical_serialized_key)>
```

Example only:

```text
QADE-8F21A0C93D74
```

If two different verified canonical keys produce the same 12-character prefix, retain SHA-256 for both and disambiguate deterministically by appending `-01`, `-02`, etc. in ascending order of the full 64-character hash. This collision suffix is exceptionally rare; never resolve it by renaming one vacancy to match a similar title.

### Stability rules

- Persist the generated ID in the final master and an ID registry file.
- The ID must remain unchanged if a preferred source URL changes.
- The ID may change only if a documented correction changes the actual employer entity or official requisition identity. Record `previous_id`, `new_id` and reason; never recycle the old ID for another vacancy.
- Never derive the ID from row number, display title, current date, category, audit range, or sort order.
- Sort accepted rows by `posted_date` descending, then `id` ascending for deterministic ties.

## 7. Final outputs and validation

### Audit artifacts

- `historical_url_audit.jsonl`: exactly 107 objects, one per canonical URL index.
- `semantic_groups.json`: all accepted groups with member URL indexes, chosen URL and stable ID.
- `id_registry.json`: `id → semantic_group_key → member URL indexes`; one ID per semantic group.
- evidence captures and timestamps referenced by the audit.

### Rebuilt master

The public table has **seven** columns:

```markdown
| ID | Position | Company | Location | Posted | Work mode | URL index |
|---|---|---|---|---|---|---:|
```

- `ID` is the stable semantic ID above.
- `Position` is a clickable Markdown link to the chosen direct current vacancy card.
- `Location` is the canonical accepted scope, e.g. `Berlin`, `Leipzig`, `Dresden`, or `Germany (Remote)`.
- `Work mode` is exactly `Onsite`, `Hybrid` or `Remote`.
- `URL index` lists all canonical historical audit indices belonging to the group, ascending. This field is for traceability and is not a row number.

Chosen URL precedence:

1. live official employer/ATS card;
2. official government direct card;
3. direct portal card with complete current fields;
4. among equals, earliest canonical `url_index`.

Do not choose a rejected, unclear, retargeted or non-direct URL as the representative.

### Required validations

Fail publication if any check fails:

1. source has exactly 107 URL objects and indices 1–107 occur once;
2. every verdict uses only `PASS`, `PARTIAL`, `UNCLEAR`, `REJECT`;
3. every PASS has six gate results equal to PASS and non-empty evidence;
4. no PARTIAL/UNCLEAR/REJECT appears as a final master row;
5. every final row has exactly seven table columns;
6. every final ID is unique and matches `^QADE-[0-9A-F]{12}(?:-[0-9]{2})?$`;
7. every final ID maps to one and only one `semantic_group_key`;
8. no two final rows have the same semantic group;
9. every final location/mode passes G5;
10. all final dates are in the inclusive 2026-08-25…2026-09-24 window;
11. every final URL is a direct current card;
12. every final representative URL belongs to a PASS audit entry;
13. all member URL indexes exist in the 107-row audit;
14. IDs are unchanged from the persisted registry unless an explicit correction record exists;
15. Markdown table parsing succeeds and the reported final row count equals the number of accepted semantic groups.

## 8. Exact worker prompt

Copy the following prompt verbatim for the worker that performs the 107-URL audit:

```text
You are the sole reconciliation worker for a complete audit of exactly 107 historical QA-vacancy URLs.

AUTHORITATIVE INPUT
- /opt/data/qa-vacancy-project/github_history_urls.json, array `unique_urls`
- /opt/data/qa-vacancy-project/ID_AUDIT_SPEC.md
- Existing audit/recheck files in /opt/data/qa-vacancy-project may be read only as evidence inputs. They are not authoritative verdicts.

SCOPE
Audit every URL in `unique_urls` exactly once. Stop with an error if the array length is not 107. Assign `url_index` as 1-based array position. Never use old Markdown row numbers, commit-local # values, filename ranges or legacy ID labels as identity. Join legacy reports to canonical rows by exact URL, normalized alias or stable source job ID; never reconcile a verdict merely by position.

HARD GATES — ALL SIX MUST PASS
1. Role: substantive Manual WEB QA, Software Test/Test Automation/Software Engineer in Test, or Gamedev QA/game QA/game localization testing. Reject hardware-only, wafer/chip, product/manufacturing, facility/electrical inspection, compliance and management-only roles.
2. Date: current posting date must satisfy 2026-08-25 <= posted_date <= 2026-09-24. Use JSON-LD, official ATS date, direct board structured date, then unambiguous relative text resolved on 2026-09-24. Future dates fail.
3. German legal entity: link the named hiring employer to the exact German legal entity through an official vacancy/legal/imprint source. A German location, .de domain, address, phone or group membership alone is insufficient.
4. Direct current card: the URL must resolve to the same live vacancy. Search/home/category pages, 404/410, expired cards, wrong redirects, retargeted IDs and unrelated current cards fail. 403/429/timeout alone is not deadness.
5. Location/mode: accept only (Onsite OR Hybrid) in exactly Berlin, Leipzig or Dresden, OR Remote with explicit Germany-wide eligibility. Require explicit Onsite evidence; explicit Hybrid or concrete split-office evidence; explicit Remote plus Germany-wide evidence. Generic Homeoffice/mobile work/Germany text is insufficient. Radeberg (bei Dresden) is not Dresden.
6. Evidence/identity: store current evidence for every gate and prove current URL identity. For PASS, use two independent evidence paths where feasible (for example HTTP + render, LinkedIn guest API + extraction, ATS + official legal page). If current evidence conflicts and cannot be resolved by source precedence, use UNCLEAR.

VERDICTS
- PASS: all six gates PASS.
- REJECT: at least one gate has affirmative current evidence of failure.
- PARTIAL: no gate FAIL, but one or more gates UNKNOWN and the missing evidence is specifically retrievable.
- UNCLEAR: current identity cannot be established, current evidence materially conflicts, or verification remains blocked after fallback methods.
Only PASS can enter the final master. PARTIAL and UNCLEAR are review states and must not be promoted without new evidence.

LEGACY RECONCILIATION
Ignore old PASS/FAIL labels. Preserve each old claim and cited evidence. Re-evaluate from current evidence. A current wrong-page/retarget/dead result overrides an old pass. If two current reports conflict and neither dominates, use UNCLEAR. Never majority-vote.

OUTPUT
Create these artifacts without modifying the current public master:
1. /opt/data/qa-vacancy-project/historical_url_audit.jsonl — exactly 107 records in url_index order, following the complete JSON schema and controlled enums in ID_AUDIT_SPEC.md.
2. /opt/data/qa-vacancy-project/semantic_groups.json — accepted semantic groups, all member URL indexes, chosen direct URL, and stable ID.
3. /opt/data/qa-vacancy-project/id_registry.json — stable ID to semantic_group_key and member URL indexes.
4. A rebuild candidate master, but do not publish it.

SEMANTIC ID
Group only semantically identical vacancies. Prefer exact German legal entity + official requisition ID. Otherwise require the same exact legal entity + normalized role core + seniority + canonical eligibility scope, with a stable discriminator only when separately evidenced distinct openings would otherwise collide. Different legal entities are never duplicates. Different official requisition IDs are not duplicates. Never use posting date, source domain, URL or audit index as a semantic duplicate discriminator.
Generate ID as QADE- plus the first 12 uppercase hex characters of SHA-256(canonical semantic key). Resolve the exceptionally rare hash-prefix collision by appending -01, -02 in ascending full-hash order. IDs must not change when the chosen URL changes.

QUALITY RULES
No fabrication. Store exact evidence URLs and short verbatim quotes. Preserve blocked status honestly. Do not treat an unrelated replacement card as the historical vacancy. Do not modify existing source/audit/master files. Stop and report a structured error rather than silently skipping any URL. Before finishing, run all validations in section 7 of ID_AUDIT_SPEC.md and report counts by verdict, accepted semantic groups, duplicate groups, PARTIAL/UNCLEAR items still needing evidence, hash collisions, and every validation failure.
```

## 9. Definition of done

The audit is complete only when all 107 canonical URLs have exactly one current verdict, all legacy report rows are joined by URL identity, every accepted vacancy has one semantic group and one persisted stable ID, the eight-row public master has been replaced by a separately validated rebuild candidate, and no publication occurs while `PARTIAL`, `UNCLEAR`, identity ambiguity or validation failure remains unresolved.
