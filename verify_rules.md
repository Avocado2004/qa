# Verification 3 — acceptance-rule consistency

## Scope

Compared:

- `qa-vacancy-project/SPEC.md`
- `QA_VACANCY_WORKER_PROMPT.md`
- `skills/qa-vacancy-search-de/SKILL.md`

The skill was read only and was not modified.

## Result

The worker's location/work-mode gate is the strongest and internally consistent of the three documents. The skill mostly preserves that gate and describes archiving and repeat/stop behavior. `SPEC.md` is materially incomplete: it collapses Remote into a geography clause, does not constrain Hybrid/Onsite to the three target cities, does not reject generic `Germany` without remote wording, and omits archiving and repeated-pass requirements.

## Confirmed consistent rules

- **Hybrid:** allowed only in Berlin, Leipzig, or Dresden in the worker prompt (`QA_VACANCY_WORKER_PROMPT.md:13-18, 65-67, 82-85`) and skill (`skills/qa-vacancy-search-de/SKILL.md`, Step 1 hard filters, Steps 4–5 and final-validation/checklist rules).
- **Onsite:** allowed only in Berlin, Leipzig, or Dresden in the worker prompt (`QA_VACANCY_WORKER_PROMPT.md:16-18, 66, 83`) and skill (Step 1 hard filters, location gate, checklist).
- **Remote:** worker prompt requires explicit Germany-wide eligibility and rejects generic `Germany`/`Deutschland` without an explicit remote mode (`QA_VACANCY_WORKER_PROMPT.md:14-16, 67-68, 84`). The skill likewise requires explicit Germany-wide Remote/Home Office/100% Remote evidence.

## Contradictions and omissions

### 1. Critical — SPEC allows non-target-city Onsite/Hybrid

`SPEC.md:9` says only:

> `Leipzig, Berlin, Dresden, OR another German city with explicit remote/Home-Office/100% Remote wording.`

Read literally, this says Berlin/Leipzig/Dresden qualify without any work-mode restriction, while another German city qualifies if remote is offered. It therefore does not enforce the required disjunction:

> `(Onsite OR Hybrid in Berlin/Leipzig/Dresden) OR (Remote with explicit Germany-wide eligibility)`

It also fails to say that Hybrid and Onsite outside the three cities are rejected.

**Exact replacement in `SPEC.md:9`:**

```markdown
- Accept exactly one location/work-mode combination:
  1. `Onsite` or `Hybrid` in Berlin, Leipzig, or Dresden; or
  2. `Remote` with explicit Germany-wide eligibility (`bundesweit`, `Deutschland`, `Germany`, `remote in Germany`, `100% Remote`, or `Home Office` with explicit availability across Germany).
  Reject every `Hybrid` and every `Onsite` vacancy outside Berlin, Leipzig, and Dresden. Reject generic `Germany`/`Deutschland` location text without an explicit remote mode.
```

### 2. Critical — SPEC does not state that Germany/DE must be tied to Remote

`SPEC.md:9` permits "another German city with explicit remote ... wording", but does not explicitly require Germany-wide eligibility rather than a generic country label. The worker prompt and skill do require explicit Germany-wide Remote eligibility.

**Exact addition after the replacement above in `SPEC.md:9`:**

```markdown
- A location containing only `Germany`, `DE`, or `Deutschland` is insufficient unless the same vacancy explicitly confirms Germany-wide remote eligibility.
```

### 3. Major — SPEC omits archiving requirements

Neither `SPEC.md` nor `QA_VACANCY_WORKER_PROMPT.md` describes the required archive-before-replacement behavior. The skill does require archiving the previous published master and preserving existing dated archives. `About.md:49-55` gives the project-specific archive rule.

This is an omission rather than a worker duty: the worker should write a pass result, while the orchestrator/publisher performs final-master archiving. To avoid ambiguity, add a non-worker output/publish section to SPEC or state explicitly that the orchestrator owns it.

**Exact addition to `SPEC.md` after the hard-filters section:**

```markdown
## 7. Archive and publication rule

Before replacing the canonical published master, the orchestrator must archive the previous published file as `/opt/data/qa-vacancy-project/qa_vacancies_master_YYYY-MM-DD.md`. Never overwrite or delete an existing dated archive. Workers do not replace the canonical master; they submit only their pass outputs and provenance.
```

### 4. Major — SPEC omits repeated-pass stop condition and known-URL comparison

`SPEC.md` has no repeat-pass rule. The skill says two consecutive **daily runs** with zero new vacancies stop the pipeline, but does not explicitly mention an accumulated known-URL database. `About.md:55` requires both the database and two consecutive complete passes with the same acceptance gate.

**Exact addition to `SPEC.md` after the proposed archive section:**

```markdown
## 8. Repeat-pass rule

Maintain an accumulated known-URL database and compare every accepted URL against it. Continue full passes, using the same acceptance gate, until two consecutive complete passes produce zero new unique accepted vacancies. A pass is complete only after all configured worker scopes, provenance checks, deduplication, and final acceptance validation have finished.
```

### 5. Major — Skill does not explicitly require the known-URL database

The skill's stop condition is present, and archive behavior is present, but its stop condition does not say that newness is measured against a persistent known-URL database. This is weaker than `About.md:45,55` and leaves the implementation of “zero new” ambiguous across runs.

**Exact addition near the skill's `## Stop Condition` (recommended; not applied):**

```markdown
Maintain a persistent known-URL database across runs and define a new vacancy as an accepted URL absent from that database before the pass. Count semantic duplicates already present in the known dataset as not new. Stop only after two consecutive complete passes, using the same acceptance gate, each produce zero new unique accepted vacancies.
```

### 6. Minor — Skill's final Markdown example can violate its Remote gate

In the skill's final output example, a row uses `Berlin | Remote` while the Remote gate requires explicit Germany-wide eligibility in the location/title/vacancy evidence. A city alone is not proof that the role is remote across Germany. This example may be understood as illustrative rather than accepted data, but it weakens the rule.

**Exact correction in the skill (recommended; not applied):** either change the example mode to `Onsite`, or change the location/evidence to an explicit form such as `Berlin | 100% Remote (bundesweit)` only if the source actually confirms it. Do not invent eligibility merely to fit the example.

## Count summary

- Documents compared: **3**
- High-severity contradictions/omissions: **4** (SPEC location gate, SPEC Germany-wide Remote condition, SPEC archive omission, SPEC repeat-pass omission)
- Medium-severity gaps: **2** (skill known-URL persistence, skill example ambiguity)
- Confirmed core rule sets: **3/3** (Hybrid-only target cities, Onsite-only target cities, Remote-only explicit Germany-wide)
- Documents fully aligned on all requested rules: **0/3**
- Skill modifications made: **0**
- Report files created: **1**
