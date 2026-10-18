# Pass 2 verification — QA vacancies (run date 2026-09-24)

Проверены Pass 2-файлы и локальные raw captures. Acceptance gate сверен с `/opt/data/SPEC.md` и `/opt/data/QA_VACANCY_WORKER_PROMPT.md`: нужны direct card, QA/test-роль, дата ≤30 дней, немецкое юрлицо, ровно один допустимый маршрут, подтверждённый work mode, рабочий URL и полный provenance.

| Verdict | Вакансия | Причина | URL | Доказательства |
|---|---|---|---|---|
| **REJECT** | Software Test Engineer* Secure Communication (SDR), Valentum Engineering GmbH, Dresden | **Work mode не доказан как Hybrid по стандарту.** Provenance пишет «Home Office: bis zu 60%» и классифицирует это как Hybrid, но это лишь ограниченный home-office формат; в объявлении нет явного `Hybrid`. По gate нельзя выводить Hybrid из догадки, а Hybrid без явного режима — `UNCLEAR`/reject. Другие поля подтверждены, но этого достаточно для REJECT. | https://www.stellenanzeigen.de/job/software-test-engineer-secure-communication-sdr-dresden-jim-363087/ | `raw/valentum-stellenanzeigen.html`: JobPosting JSON-LD `datePosted=2026-09-16`, `jobLocation= Dresden, DE`; описание явно содержит создание/ведение тест-кейсов и автоматизацию тестов; `raw/valentum-impressum.html`: Valentum Engineering GmbH, адрес в Regensburg, AG Regensburg HRB 12938. Live HTTP status 200. Provenance полный, но work-mode evidence недостаточен для Hybrid. |
| **ACCEPT** | Software Tester, BVU Beratergruppe Verkehr + Umwelt GmbH, Germany (Remote) | Все поля acceptance gate подтверждены. | https://remotive.com/remote/jobs/qa/software-tester-5925120 | `raw/bvu_capture.txt`: JobPosting `jobLocationType=TELECOMMUTE`, `datePosted=2026-09-18 18:18:56`, QA role text (test case creation/automation, test results/reports), header `Remote Location Germany`; `raw/bvu_legal_capture.txt`: BVU GmbH, Wentzingerstraße 19, D-79106 Freiburg, Amtsgericht Freiburg HRB 3579. `raw/bvu_http_status.txt`: HTTP 200. Provenance JSON/MD содержит direct URL, capture, role/date/location/work-mode/entity evidence. |
| **ACCEPT** | Software Tester, QA Analyst – Smart Grid Platform, Venios GmbH, Germany (Remote) | Все поля acceptance gate подтверждены. | https://www.remotery.co/job/remote-software-tester-qa-analyst-smart-grid-platform-at-venios-gmbh-in-germany-full-time-7c36a7 | `raw/venios_capture.txt`: JobPosting JSON-LD `jobLocationType=TELECOMMUTE`, `datePosted=2026-09-15T01:27:52.676Z`, `applicantLocationRequirements` Germany/Austria; текст: “fully remote position, open to applicants in Germany”, а также test cases/regression/release testing/QA. `raw/venios_legal_capture.txt`: Venios GmbH, Schumannstraße 34b, 60325 Frankfurt, Amtsgericht Frankfurt am Main HRB 99796. `raw/venios_http_status.txt`: HTTP 200. Provenance JSON/MD полный. |

## Counts

- **ACCEPT: 2** (BVU Germany-wide Remote; Venios Germany-wide Remote)
- **REJECT: 1** (Dresden Valentum: неподтверждённый Hybrid)
- **Проверено всего: 3**
- Provenance coverage для трёх записей: **3/3 (100%)**, но coverage не отменяет failure acceptance gate.
- Все три URL независимо вернули HTTP 200; master не изменялся.
