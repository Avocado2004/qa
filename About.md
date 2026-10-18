# QA Vacancy Search Project — About

## Goal

Maintain a daily-updated Markdown list of unique QA/test vacancies in Germany. The canonical result is `qa_vacancies_master.md`, published to GitHub as `README.md` when it changes.

## Confirmed daily order

The single scheduled job launches one detached Python controller. It does not create Hermes chat sessions, Kanban tasks, or additional cron jobs.

1. Recheck every row in the currently published master, including `PARTIAL`, `Unclear`, and `Unverified` rows.
2. Run daily source discovery and maintain the persistent source registry.
3. Preflight every active source, in parallel, with at most 10 workers.
4. Run one vacancy worker per confirmed source, in parallel, with at most 10 workers.
5. Analyze the complete announcement text, validate criteria, deduplicate semantically, and synthesize the candidate master.
6. Run an independent final verifier.
7. Publish only if the master changes. Otherwise finish with `NO_CHANGE` and do not replace or push an unchanged master.
8. Notify only when the master changes or the run fails.

## Acceptance and retention rules

A vacancy is retained or classified as unresolved using affirmative evidence from the complete announcement:

- Role is Manual WEB QA, Software Test/Test Automation, Gamedev/Game QA, QA Localization, or a semantically equivalent testing role.
- The employer is a German legal entity or a German branch/representation of an international company, verified through Impressum, Handelsregister, or an official legal page. Unresolved employer evidence remains `PARTIAL`/`Unclear`.
- The direct vacancy card is required; search, category, and homepage URLs are not vacancy cards.
- The posting is no older than 30 days. If the current date is known, use it. If the current page has no date but the old master has one, retain the old date. If no date exists, retain `Unknown`, record `first_seen_in_master`, and remove the row 30 days after first appearance.
- A previously known date older than 30 days is stale and is removed.
- Berlin, Leipzig, and Dresden vacancies may have `Remote`, `Hybrid`, `Onsite`, or `Unknown` work mode. A city vacancy with unknown mode is retained.
- Outside the three target cities, only explicit Germany-wide Remote is eligible: `Germany`, `DE`, `Deutschland`, `bundesweit`, `100% Remote`, or equivalent. Generic `Germany` without explicit remote eligibility is not sufficient.
- A temporary inability to open or read a page is `Unverified`, not proof that the vacancy is closed or ineligible.
- Remove only when stale, explicitly closed, demonstrably ineligible, or otherwise affirmatively disproved. `PARTIAL` and `Unclear` are retained in a separate master block and rechecked daily.
- Deduplicate by the complete announcement text and vacancy identity, not by URL alone. If the same vacancy is found at multiple URLs, keep the first-found URL in the public master and discard the other duplicate URLs from the master; retain the deduplication evidence internally.

## Master format

Each category table uses:

| # | Position | Company | Location | Posted | Work mode | Verification |
|---:|---|---|---|---|---|---|

`Position` is a clickable direct vacancy URL. `Verification` is one of `Current`, `Current / Partial`, `Unverified`, or `Unclear`. The master ends with:

```markdown
## Sources
| Source | Status | Last checked | Last successful use | Reason |
```

Source status is `Used`, `Not used`, or `Unavailable`. A skipped source is not treated as zero vacancies and remains active for future runs.

## Source discovery and access

- Search sources daily using German QA/testing terms.
- A source is usable only after a full preflight: discovery/listing route, two distinct analyzable cards, first detail page, return to results, and second detail page.
- If the first access method fails, try a second independent method. If both fail, mark the source `Not used` for the run, continue with other sources, and record the reason in the master.
- Process every source's pages/cards sequentially. Never access one source from two workers simultaneously.

## Durable workers and recovery

Use JSON with atomic temp-file + `fsync` + `os.replace`, `fcntl`, schema versions, and explicit generation/lease tokens. Preserve these artifacts per source:

```text
queue.json
manifest.json
checkpoint.json
failures.json
plan.json
completed/
raw/
```

The controller may run at most 10 workers. A worker claims one source, updates its checkpoint after each bounded page/card operation, writes a durable receipt before marking the operation complete, and heartbeats the queue. The controller must detect a dead PID, or a live worker with both heartbeat and checkpoint older than 5 minutes. It stops the old worker gracefully, force-kills after 30 seconds if necessary, increments the attempt, issues a new lease token, and resumes the same job from the first unfinished receipt. A stale process must be unable to write after its lease is replaced.

Allow 3 automatic restart attempts with backoff 5 seconds, 30 seconds, and 120 seconds. After exhaustion, mark the job `failed`/`Not used`, record the error, continue other sources, and retry from durable state on the next run. `state.json` is cycle-level status; recovery uses queue, manifest, checkpoint, failures, and completion receipts.

## Publication

Before replacing a changed master, save the previous published master as `/opt/data/qa-vacancy-project/qa_vacancies_master_YYYY-MM-DD.md` without overwriting an existing archive. Publish the project master, `result.md`, and GitHub `README.md` only after final verification. If the candidate is byte-identical to the published master, do not create a new publication commit or push.

## Verification checklist

- [ ] One cron job launches one detached controller.
- [ ] No Hermes chat sessions, Kanban tasks, or extra cron jobs are created.
- [ ] Master recheck happens before new discovery/search.
- [ ] Daily source discovery ran.
- [ ] Source preflight covered every active source, including the two-card detail flow.
- [ ] Confirmed sources were processed with no more than 10 workers.
- [ ] Every source/page/card has durable recovery state.
- [ ] Every master row has a direct URL and provenance.
- [ ] Date, location, work-mode, role, and German employer rules pass.
- [ ] `PARTIAL`/`Unclear`/`Unverified` rows remain in the dedicated block.
- [ ] Duplicate announcement text is deduplicated and the first URL is retained.
- [ ] Final verification passed.
- [ ] Changed master is archived, synchronized, committed, and pushed; unchanged master yields `NO_CHANGE`.
- [ ] Notification was sent only on master change or controller error.
