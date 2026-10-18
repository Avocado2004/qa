# Спецификация задачи

## Исходный запрос (дословно)

> # QA Vacancy Search Project — About
>
> ## Goal
>
> Maintain a daily-updated markdown list of unique, verified QA/test vacancies in Germany.
>
> ## Acceptance criteria
>
> A vacancy is included only if all conditions are met:
>
> - Role is QA/test-related: Manual WEB QA, Software Test, Test Automation, Gamedev QA, Game QA, QA Localization or a semantically equivalent testing role.
> - The employer has a German legal entity, verified through Impressum, Handelsregister or an official company legal page.
> - The direct vacancy card is available; search pages, category pages and homepages are forbidden.
> - The vacancy was posted no more than 30 days before the run date.
> - The location/work-mode combination is accepted:
>   - `Onsite` in **Berlin, Leipzig or Dresden**;
>   - `Hybrid` in **Berlin, Leipzig or Dresden**;
>   - `Remote` only with explicit Germany-wide eligibility (`Germany`, `DE`, `Deutschland`, `bundesweit`, `100% Remote`, or equivalent).
> - `Onsite` or `Hybrid` in any other city is rejected.
> - Hybrid is rejected outside Berlin, Leipzig and Dresden.
> - A generic `Germany` location without explicit remote eligibility is rejected.
> - Unclear or unverifiable work mode, location, date or employer is rejected.
> - Vacancies are deduplicated by URL and by normalized `company + title`.
>
> ## Output format
>
> The master table has exactly six columns:
>
> | # | Position | Company | Location | Posted | Work mode |
> |---:|---|---|---|---|---|
>
> - `Position` is a clickable Markdown link to the direct vacancy card.
> - No separate `Link` column is used.
> - `Work mode` is one of `Remote`, `Onsite` or `Hybrid`.
> - Hybrid is allowed only in Berlin, Leipzig and Dresden.
> - Rows inside every category are sorted by posting date descending, newest first.
> - All accepted rows require row-level provenance covering role, date, location, work mode, German legal entity and verification method.
>
> ## Daily pipeline
>
> 1. Create or update `SPEC.md` with the hard acceptance gate.
> 2. Run parallel workers for Berlin, Leipzig, Dresden and Germany-wide Remote scopes.
> 3. Require workers to submit only accepted rows; rejected and near-miss candidates stay in rejected logs.
> 4. Parse, validate, deduplicate and independently verify every candidate.
> 5. Compare URLs with the accumulated known-URL database.
> 6. Archive the previous published master before replacing it.
> 7. Write the new master and `result.md`, then publish to GitHub.
>
> ## Archive and repeat rule
>
> Before replacing the canonical master, save the previous published file as:
>
> `/opt/data/qa-vacancy-project/qa_vacancies_master_YYYY-MM-DD.md`
>
> Never overwrite an existing dated archive. Keep an accumulated known-URL database and continue full passes until two consecutive complete passes find zero new unique accepted vacancies. Each pass must use the same acceptance gate.
>
> ## Search and verification requirements
>
> - Search queries and vacancy extraction should use German terms such as `Softwaretester`, `QA Engineer`, `Test Engineer`, `Qualitätssicherung`, `Spiele-Tester`, `Manuelle Tests`, `Test Automation` and `Game QA`.
> - Use multiple working sources: LinkedIn Jobs, Arbeitsagentur, StepStone, XING, hitmarker and direct company ATS pages.
> - Try at least two access methods for blocked sources.
> - For every URL use `curl -L` or browser/web extraction and record the verification method.
> - Verify the posting date from JSON-LD or visible source text.
> - Verify the German legal entity from Impressum/Handelsregister/legal page.
> - If evidence is ambiguous, reject the row instead of guessing.
>
> ## Sources
>
> | Source | Method | Notes |
> |---|---|---|
> | LinkedIn Jobs | Guest API/browser | Good coverage; use `f_TPR=r2592000`, remote filters when available |
> | Arbeitsagentur | Public API/JSON-LD/browser | Reliable dates and German locations |
> | StepStone | Browser/Camofox | Cloudflare may block curl; browser verification is acceptable |
> | XING | Browser | Use last-month filters |
> | hitmarker | Browser/web_extract | Gamedev-specific source |
> | Company ATS | Browser/web_extract | Prefer direct employer cards |
>
> ## Pipeline schedule and maintenance
>
> - Daily cron runs the full pipeline and stores a dated run log.
> - A run is complete only after the final master passes the location/work-mode gate, link checks, deduplication, date checks and table validation.
> - Published files must be synchronized between the project master, `result.md` and GitHub `README.md`.
> - Keep dated historical masters; do not delete them.
>
> ## Verification checklist
>
> - [ ] SPEC exists and contains the exact acceptance gate.
> - [ ] All five worker scopes completed.
> - [ ] Every accepted row has a clickable direct URL.
> - [ ] Every row has six columns.
> - [ ] `Hybrid` appears only in Berlin, Leipzig or Dresden.
> - [ ] `Onsite` appears only in Berlin, Leipzig or Dresden.
> - [ ] Remote rows have explicit Germany-wide eligibility.
> - [ ] All rows are posted within 30 days.
> - [ ] German legal entity is evidenced.
> - [ ] URLs and semantic duplicates are verified.
> - [ ] Row-level provenance coverage is 100%.
> - [ ] Previous master is archived before replacement.
> - [ ] Final master, result.md and GitHub README are synchronized.
> - [ ] Search continues until two consecutive complete passes produce zero new unique vacancies.

## Цель

Поддерживать ежедневно обновляемый markdown-список уникальных, проверенных вакансий QA/test в Германии.

## Критерии готовности

1. Вакансия включена только при выполнении всех условий acceptance criteria из исходного запроса.
2. Роль относится к QA/test: Manual WEB QA, Software Test, Test Automation, Gamedev QA, Game QA, QA Localization или семантически эквивалентная тестовая роль.
3. У работодателя подтверждено наличие германского юридического лица через Impressum, Handelsregister или официальную страницу компании о юридических данных.
4. Доступна прямая карточка вакансии; страницы поиска, категорий и главные страницы не используются.
5. Дата публикации — не более чем за 30 дней до даты запуска.
6. Для `Onsite` приняты только Berlin, Leipzig или Dresden.
7. Для `Hybrid` приняты только Berlin, Leipzig или Dresden.
8. Для `Remote` принято только явное соответствие условию Germany-wide eligibility из исходного запроса.
9. `Onsite` или `Hybrid` в любом другом городе отклоняются.
10. Hybrid вне Berlin, Leipzig и Dresden отклоняется.
11. Общее указание Germany без явной remote eligibility отклоняется.
12. Неясные или непроверяемые work mode, location, date или employer отклоняются.
13. Вакансии дедуплицируются по URL и по нормализованным `company + title`.
14. Мастер-таблица содержит ровно шесть колонок: `#`, `Position`, `Company`, `Location`, `Posted`, `Work mode`.
15. `Position` является кликабельной Markdown-ссылкой на прямую карточку вакансии.
16. Отдельная колонка `Link` не используется.
17. `Work mode` имеет одно из значений `Remote`, `Onsite` или `Hybrid`.
18. Hybrid разрешён только в Berlin, Leipzig и Dresden.
19. Строки внутри каждой категории отсортированы по дате публикации по убыванию, новые первыми.
20. Для всех принятых строк есть row-level provenance по роли, дате, location, work mode, германскому юридическому лицу и методу верификации.
21. Создан или обновлён `SPEC.md` с hard acceptance gate.
22. Запущены параллельные workers для указанных scope Berlin, Leipzig, Dresden и Germany-wide Remote.
23. Workers предоставляют только принятые строки; отклонённые и near-miss кандидаты остаются в rejected logs.
24. Каждый кандидат разобран, проверен, дедуплицирован и независимо верифицирован.
25. URL сравниваются с накопленной known-URL database.
26. Предыдущий опубликованный master архивируется до замены.
27. Новый master и `result.md` записываются и публикуются в GitHub.
28. Архивы имеют формат `/opt/data/qa-vacancy-project/qa_vacancies_master_YYYY-MM-DD.md`; существующий архив не перезаписывается.
29. Накапливается known-URL database и выполняются полные проходы до двух последовательных полных проходов с нулевым количеством новых уникальных принятых вакансий, с неизменным acceptance gate на каждом проходе.
30. Для поиска и извлечения вакансий используются немецкие термины, перечисленные в исходном запросе.
31. Используются перечисленные в исходном запросе рабочие источники, а для заблокированных источников предпринимаются не менее двух способов доступа.
32. Для каждого URL используется `curl -L` или browser/web extraction, а метод верификации фиксируется.
33. Дата публикации проверяется по JSON-LD или видимому тексту источника.
34. Германское юридическое лицо проверяется по Impressum/Handelsregister/legal page.
35. При неоднозначных доказательствах строка отклоняется, а не угадывается.
36. Запускается daily cron полного pipeline с сохранением dated run log.
37. Запуск считается завершённым только после прохождения финальным master проверок location/work-mode gate, link checks, deduplication, date checks и table validation.
38. Опубликованные файлы синхронизируются между project master, `result.md` и GitHub `README.md`.
39. Dated historical masters сохраняются.
40. Выполняется verification checklist из исходного запроса.

## Границы

- Поисковые страницы, страницы категорий и главные страницы запрещены как ссылки на вакансию.
- `Onsite` и `Hybrid` разрешены только в Berlin, Leipzig и Dresden; Hybrid вне этих городов отклоняется.
- `Remote` допускается только при явной Germany-wide eligibility, перечисленной в исходном запросе.
- Общее `Germany` без explicit remote eligibility не принимается.
- Неясные или непроверяемые сведения отклоняются.
- Существующий dated archive нельзя перезаписывать; исторические masters нельзя удалять.
- Принятые строки должны иметь прямые URL и row-level provenance; отдельная колонка Link запрещена.
- Worker-предложения ограничены принятыми строками, а rejected и near-miss кандидаты сохраняются в rejected logs.

## Формат итогового результата

Результат проекта — ежедневно обновляемый markdown master и синхронизированные с ним `result.md` и GitHub `README.md`. Master-таблица каждой категории должна иметь ровно шесть колонок в указанном порядке: `#`, `Position`, `Company`, `Location`, `Posted`, `Work mode`. Position оформляется кликабельной Markdown-ссылкой на direct vacancy card. Work mode принимает только `Remote`, `Onsite` или `Hybrid`; hybrid допустим только в Berlin, Leipzig и Dresden. Строки сортируются по posting date descending, newest first. Для каждой принятой строки требуется row-level provenance, включающий role, date, location, work mode, German legal entity и verification method. Перед заменой canonical master сохраняется как `/opt/data/qa-vacancy-project/qa_vacancies_master_YYYY-MM-DD.md` без перезаписи существующего архива. Daily cron stores a dated run log.

## Допущения

- **Гипотеза:** Термин «категория» в исходном запросе означает scope/группу строк Berlin, Leipzig, Dresden и Germany-wide Remote; это допущение не добавляет новый acceptance criterion.
- **Гипотеза:** «даже без перезаписи существующего архива» означает, что при совпадении имени даты существующий файл должен быть сохранён, а дальнейшая запись под тем же именем — отклонена или разрешена только после явного разрешения пользователя.
- **Гипотеза:** «две последовательные complete passes» означает два последовательных полных прохода с одинаковым acceptance gate, каждый из которых даёт ноль новых уникальных принятых вакансий; это непосредственно следует из repeat rule и не задаёт дополнительные критерии проверки.
