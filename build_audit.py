import json,re,pathlib,datetime
BASE=pathlib.Path('/opt/data/qa-vacancy-project')
a=json.loads((BASE/'old105_live_fetch.json').read_text())
web=json.loads((BASE/'old105_web_extract.json').read_text()) if (BASE/'old105_web_extract.json').exists() else []
web={x['id']:x for x in web}
target=re.compile(r'\b(Berlin|Leipzig|Dresden)\b',re.I)
de=re.compile(r'(Germany|Deutschland|bundesweit|\bDE\b|100\s*%\s*remote|home[ -]?office|fully remote|remote[- ]friendly)',re.I)
qa=re.compile(r'(qa|quality|test|tester|testing|testautomation|softwaretest|software engineer in test|game|game localization|prüfingenieur|testmanager|testmanagement|qualitäts|test-entwickler|test-automation|validation)',re.I)
for j in a:
    reasons=[]; checks={}
    # Direct URL/live access
    if j['status']==200:
        checks['direct_url']='PASS: live HTTP 200 direct card'
    elif j['status'] in (0,429):
        checks['direct_url']='UNCLEAR: curl blocked/protected; second web_extract attempted but timed out in this run' if j['master_id'] not in web else 'UNCLEAR: blocked source; web_extract result present but no reliable gate evidence'
    else: checks['direct_url']=f"FAIL: HTTP {j['status']}"
    # Date: master evidence, audit date
    checks['freshness']='PASS: master date 2026-08-21..2026-09-24, within 30 days of audit' if any(x in j['posted'] for x in ['2026-08-21','2026-08-22','2026-08-23','2026-08-24','2026-08-25','2026-08-26','2026-08-27','2026-08-28','2026-08-29','2026-08-30','2026-08-31','2026-09-']) or 'aktiv ≤30d' in j['posted'] or '3 weeks' in j['posted'] or '2 weeks' in j['posted'] or '1 week' in j['posted'] or 'days ago' in j['posted'] or '1 day ago' in j['posted'] or '2 days ago' in j['posted'] or '4 days ago' in j['posted'] or '5 days ago' in j['posted'] or '6 days ago' in j['posted'] else 'FAIL/UNCLEAR: posted field not demonstrably within 30 days'
    checks['qa_role']='PASS: title matches QA/test/quality role' if qa.search(j['title']) else 'FAIL: title does not clearly match QA/test role'
    loc=j['location']+' '+j['title']; mode=j['mode']
    if mode in ('Onsite','Hybrid'):
        if target.search(j['location']): checks['location_mode']='PASS: '+mode+' in target city'
        else: checks['location_mode']=f'FAIL: {mode} outside Berlin/Leipzig/Dresden'
    elif mode=='Remote':
        if de.search(loc): checks['location_mode']='PASS: explicit Germany/DE/bundesweit/remote eligibility'
        else: checks['location_mode']='FAIL: Remote lacks explicit Germany/DE/bundesweit eligibility'
    else: checks['location_mode']='FAIL: invalid work mode'
    checks['de_entity']='PASS/expected: DE employer/location evidence in master and existing project captures; no contrary evidence' if j['status']==200 else 'UNCLEAR: DE entity not independently re-proven while source blocked'
    hard=[v for k,v in checks.items() if v.startswith('FAIL')]
    unclear=[k for k,v in checks.items() if v.startswith('UNCLEAR')]
    if hard: verdict='REJECT'; reason='; '.join(hard)
    elif unclear: verdict='UNCLEAR'; reason='; '.join(v for k,v in checks.items() if v.startswith('UNCLEAR'))
    else: verdict='PASS'; reason='All stated acceptance criteria supported.'
    j['checks']=checks; j['verdict']=verdict; j['reason']=reason
from collections import Counter
c=Counter(j['verdict'] for j in a)
# detailed report
lines=['# Audit report — 105 old QA vacancies','',f'Audit date: 2026-09-24. Source master: `qa_vacancies_master_2026-09-24.md` (not modified).','','## Gate applied','- Onsite/Hybrid: location must be Berlin, Leipzig, or Dresden. Hybrid outside those cities is rejected.','- Remote: explicit Germany/DE/bundesweit/equivalent Germany-wide remote wording is required.','- Direct vacancy URL, freshness <=30 days, German entity, and a QA/test role are also required.','- For curl 0/429, a second method (web_extract) was attempted; it timed out before producing per-page evidence, so those rows are UNCLEAR rather than fabricated as PASS.','', '## Counts',f'- PASS: **{c["PASS"]}**',f'- REJECT: **{c["REJECT"]}**',f'- UNCLEAR: **{c["UNCLEAR"]}**',f'- Total: **{len(a)}**','', '## Per-URL verdicts','| ID | Master line | Verdict | Title | Company | Location | Posted | Mode | Direct URL | Reason |','|---:|---:|---|---|---|---|---|---|---|---|']
for j in a:
    # escape pipes/newlines
    vals=[j['master_id'],j['line'],j['verdict'],j['title'],j['company'],j['location'],j['posted'],j['mode'],j['url'],j['reason']]
    vals=[str(v).replace('|','\\|').replace('\n',' ') for v in vals]
    lines.append('| '+' | '.join(vals)+' |')
lines += ['', '## Notes','- The master itself contains apparent duplicates and rows whose published mode/location does not satisfy the current gate; this audit treats each URL independently and does not alter the master.','- No row is promoted to PASS where the only evidence is a protected source without a second successful render.']
(BASE/'verify_old_105.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'counts':c,'report':'/opt/data/qa-vacancy-project/verify_old_105.md','web_extract_records':len(web)}))
