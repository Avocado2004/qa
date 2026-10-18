import json, os
ROOT='/opt/data/qa-vacancy-project'
u=json.load(open(f'{ROOT}/github_history_urls.json'))['unique_urls']
assert len(u)==107
# current card facts observed on 2026-09-24; dates resolved only from unambiguous relative current-card text
rows=[
('QA Engineer (m/w/d)','AZUR SPACE Solar Power GmbH','AZUR SPACE Solar Power GmbH','','Heilbronn','UNKNOWN',False,'2026-09-23','MATCH','NON_QUALIFYING_ROLE','Manufacturing/product quality duties are outside accepted software/game QA; Heilbronn is also disallowed.'),
('Qualitätsingenieur KI-Fokus / Quality Engineer (AI-augmented) (m/w/d) IT-Consulting','PTA GmbH','PTA GmbH','','Berlin, Dresden and other cities','UNKNOWN',False,'2026-09-22','MATCH','CURRENT_EVIDENCE_INCOMPLETE','Qualifying role and fresh matching card, but generic Homeoffice möglich does not establish Hybrid or Germany-wide Remote.'),
('Senior QA Engineer (m/w/d)','adp MERKUR GmbH','adp MERKUR GmbH','','Lübbecke','UNKNOWN',False,'2026-09-19','MISMATCH','WRONG_CURRENT_CARD','Historical igus URL currently renders the adp MERKUR vacancy.'),
('Senior Test Engineer (m/w/d) Erprobung und Validierung','Falk Defence','Falk Defence','','Leipzig','UNKNOWN',False,'2026-09-17','MISMATCH','WRONG_CURRENT_CARD','Historical adp MERKUR URL currently renders the Falk Defence vacancy.'),
('QA Engineer (m/w/d)','AZUR SPACE Solar Power GmbH','AZUR SPACE Solar Power GmbH','','Heilbronn','UNKNOWN',False,'2026-09-23','MISMATCH','WRONG_CURRENT_CARD','Historical Falk Defence URL currently renders the AZUR SPACE vacancy.'),
('Software QA Test Engineer (m/w/d)','Aveyara Software GmbH','Aveyara Software GmbH','','Stuttgart','UNKNOWN',False,'2026-08-04','MATCH','POSTING_DATE_OUTSIDE_WINDOW','Qualifying role, but the current card says “Erschienen: vor 3 Wochen,” resolving to 2026-08-04 before the audit window; Stuttgart plus generic homeoffice also fails the location route.'),
('Software Quality Engineer (m/w/d)','WERTGARANTIE Group','','','Hannover','UNKNOWN',False,'2026-09-18','MATCH','DISALLOWED_LOCATION_MODE','Qualifying role, but Hannover plus partial homeoffice is not an accepted route; exact legal entity is not named.'),
('Software & Quality Engineer (m/w/d)','Bedifol GmbH','Bedifol GmbH','','Konstanz','UNKNOWN',False,'2026-09-17','MATCH','DISALLOWED_LOCATION_MODE','Qualifying role, but Konstanz plus up to two homeoffice days is not an accepted route.'),
('Software-Tester (w/m/d) Schwerpunkt manuelle Tests','seca GmbH & Co. KG','seca GmbH & Co. KG','','Hamburg','UNKNOWN',False,'2026-09-19','MISMATCH','WRONG_CURRENT_CARD','Historical secupay URL currently renders the seca manual software tester vacancy.'),
('Software Quality Engineer (m/w/d)','secupay AG','secupay AG','','Pulsnitz','UNKNOWN',False,'2026-09-19','MISMATCH','WRONG_CURRENT_CARD','Historical seca URL currently renders the secupay vacancy.'),
('System Validation & Test Automation Engineer (a)','Baumer Optronic GmbH','Baumer Optronic GmbH','','Radeberg (bei Dresden)','UNKNOWN',False,'2026-09-18','MATCH','DISALLOWED_LOCATION_MODE','Radeberg is not Dresden and no explicit Germany-wide remote route is evidenced.'),
('Test Automation Engineer (all genders)','msg systems ag','msg systems ag','','Berlin and other listed cities','UNKNOWN',False,'','MATCH','CURRENT_EVIDENCE_INCOMPLETE','Qualifying Berlin option, but generic homeoffice is not an explicit Hybrid split and current posting date is absent.'),
('Test Automation Engineer (m/w/d)','secunet Security Networks AG','secunet Security Networks AG','','Dresden, Essen','UNKNOWN',False,'','MISMATCH','WRONG_CURRENT_CARD','Historical Materna URL currently renders the secunet vacancy.'),
('Test Automation Engineer (m/w/d)','Materna Information & Communications SE','Materna Information & Communications SE','','multiple cities including Dresden','UNKNOWN',False,'','MISMATCH','WRONG_CURRENT_CARD','Historical secunet URL currently renders the Materna vacancy.'),
('Test-Entwickler (m/w/d) Satellitenkommunikation','NEOSAT GmbH','NEOSAT GmbH','','Dresden','UNKNOWN',False,'2026-09-10','MATCH','CURRENT_EVIDENCE_INCOMPLETE','Qualifying Dresden software-test role, but generic homeoffice does not establish Hybrid.'),
('Testautomatisierer (m/w/d)','Sopra Steria','','','bundesweit, Berlin, Leipzig and other cities','UNKNOWN',False,'2026-09-17','MATCH','CURRENT_EVIDENCE_INCOMPLETE','Current card combines bundesweit with generic homeoffice, but explicit remote arrangement and exact German hiring entity are not evidenced.'),
('Testmanager / IT-Consultant Testmanagement (m/w/d)','PTA GmbH','PTA GmbH','','Berlin, Dresden and other cities','UNKNOWN',False,'','MATCH','CURRENT_EVIDENCE_INCOMPLETE','Qualifying Berlin/Dresden card, but generic homeoffice does not establish Hybrid and current posting date is absent.'),
('Freelance QA Tester / Software-Tester (m/w/d)','SEDIWORK','',' ','Leipzig','UNKNOWN',False,'','MATCH','CURRENT_EVIDENCE_INCOMPLETE','Qualifying Leipzig card, but current posting date, explicit accepted mode, and exact German employing legal entity are not evidenced.'),
('Test Automation Engineer (m/w/d)','GEOMAGIC','GEOMAGIC GmbH','','Leipzig','Onsite',False,'','MATCH','CURRENT_EVIDENCE_INCOMPLETE','Current XING card explicitly says Vor Ort in Leipzig, but current posting date is absent; ab sofort is not a posting date.')]
legacy={89:'REJECT',90:'PASS',91:'REJECT',92:'REJECT',93:'REJECT',94:'REJECT',95:'REJECT',96:'REJECT',97:'PASS',98:'REJECT',99:'REJECT',100:'PASS',101:'PASS',102:'PASS',103:'PASS',104:'PASS',105:'PASS',106:'REJECT',107:'PASS'}
quote_map={89:'QA Engineer (m/w/d); AZUR SPACE Solar Power GmbH; Heilbronn; Homeoffice möglich; Erschienen: vor 1 Tag',90:'PTA GmbH; Berlin, Dresden and other cities; Homeoffice möglich; Erschienen: vor 2 Tagen; software testing/test automation duties',91:'Senior QA Engineer (m/w/d); adp MERKUR GmbH; Lübbecke; Erschienen: vor 5 Tagen',92:'Senior Test Engineer (m/w/d) Erprobung und Validierung; Falk Defence; Leipzig; Erschienen: vor 1 Woche',93:'QA Engineer (m/w/d); AZUR SPACE Solar Power GmbH; Heilbronn; Erschienen: vor 1 Tag',94:'Software QA Test Engineer (m/w/d); Aveyara Software GmbH; Stuttgart; Homeoffice möglich; Erschienen: vor 3 Wochen',95:'Software Quality Engineer (m/w/d); WERTGARANTIE Group; Hannover; Erschienen: vor 1 Tag',96:'Software & Quality Engineer (m/w/d); Bedifol GmbH; Standort Konstanz; bis zu 2 Tage Homeoffice pro Woche',97:'Software-Tester (w/m/d) Schwerpunkt manuelle Tests; seca GmbH & Co. KG; Hamburg',98:'Software Quality Engineer (m/w/d); secupay AG; Pulsnitz',99:'System Validation & Test Automation Engineer (a); Baumer Optronic GmbH; Radeberg (bei Dresden); Erschienen: vor 6 Tagen',100:'Test Automation Engineer (all genders); msg systems ag; Berlin and other listed cities',101:'Test Automation Engineer (m/w/d); secunet Security Networks AG; Dresden, Essen',102:'Test Automation Engineer (m/w/d); Materna Information & Communications SE; multiple cities including Dresden',103:'Test-Entwickler (m/w/d) Satellitenkommunikation; NEOSAT GmbH; Dresden; Homeoffice möglich; Erschienen: vor 2 Wochen',104:'Testautomatisierer (m/w/d); Sopra Steria; bundesweit, Berlin, Leipzig and other cities; Homeoffice möglich; Erschienen: vor 1 Woche',105:'Testmanager / IT-Consultant Testmanagement (m/w/d); PTA GmbH; Berlin, Dresden and other cities',106:'Freelance QA Tester / Software-Tester (m/w/d); SEDIWORK; Leipzig; Home-Office',107:'Test Automation Engineer (m/w/d) - GEOMAGIC; GEOMAGIC; Leipzig; Vor Ort; Aktiv auf der Suche; ab sofort'}

def evidence(url,quote,method='web_extract'): return {'url':url,'quote':quote,'method':method}
def g(result,value,ev): return {'result':result,'value':value,'evidence':ev}
recs=[]
for n,row in enumerate(rows,89):
    title,ed,legal,eid,loc,mode,dewide,date,match,code,reason=row; url=u[n-1]
    q=quote_map[n]; paths=[evidence(url,q)]
    if n in (106,107): paths.append(evidence(url, f'HTTP capture title: {title} | XING Jobs', 'http'))
    # G1 role on the current card; wrong identity prevents affirmative acceptance of the historical vacancy.
    role='UNKNOWN' if match=='MISMATCH' else 'PASS'
    if n==89: role='FAIL'
    dateknown=bool(date); dateres='UNKNOWN' if not dateknown else ('FAIL' if date<'2026-08-25' or date>'2026-09-24' else 'PASS')
    if n==95: entity='UNKNOWN'
    elif n==104: entity='UNKNOWN'
    elif n==106: entity='UNKNOWN'
    elif n==107: entity='PASS'
    else: entity='PASS'
    dcard='FAIL' if match=='MISMATCH' else 'PASS'
    lm='FAIL' if n in (89,94,95,96,99) else ('PASS' if n==107 else 'UNKNOWN')
    ident='FAIL' if match=='MISMATCH' else ('UNKNOWN' if n in (90,100,103,104,105,106) else 'PASS')
    verdict='REJECT' if dcard=='FAIL' or role=='FAIL' or lm=='FAIL' or dateres=='FAIL' else 'PARTIAL'
    legacy_reports=[{'file':'github_history_audit_089-107.md','legacy_position':str(n),'legacy_verdict':legacy[n],'match_method':'exact_url'}]
    if n in (93,97,101,102,107): legacy_reports.append({'file':'github_history_audit_023-044.md','legacy_position':'legacy-local-position','legacy_verdict':'legacy claim preserved; verdict ignored','match_method':'exact_url'})
    rec={'url_index':n,'original_url':url,'normalized_url':url.replace('https://www.','https://').lower().split('#')[0],
      'source_key':(('stepstone:'+url.split('--')[-1].replace('-inline.html','')) if 'stepstone' in url else 'xing:'+url.split('/')[-1].split('-')[-1]),
      'access':{'attempted_methods':['http','web_extract'],'http_status':200 if 'xing' in url else 0,'final_url':url,'current_card':match=='MATCH','blocked':'stepstone' in url,'notes':('StepStone HTTP/2 stream failed; independent extraction succeeded' if 'stepstone' in url else 'Direct HTTP 200 and independent extraction succeeded')},
      'current_identity':{'title':title,'employer_display':ed,'employer_legal_name':legal.strip(),'employer_entity_id':eid,'location':loc,'work_mode':mode,'germany_wide':dewide,'posted_date':date,'identity_match':match},
      'gates':{'role':g(role,'qualifying software/game QA' if role=='PASS' else ('non-qualifying manufacturing/product QA' if role=='FAIL' else 'current card does not match historical vacancy'),paths),
        'date':g(dateres,date,paths if dateknown else [evidence(url,'Current extracted card exposes no posting date; historical date is not current evidence.')]),
        'de_entity':g(entity,legal.strip() or ed,paths),'direct_current_card':g(dcard,'matching current card' if dcard=='PASS' else 'current card has a different source identity',paths),
        'location_mode':g(lm,mode,paths),'evidence_identity':g(ident,'same canonical identity' if ident=='PASS' else ('retargeted current card' if ident=='FAIL' else 'accepted identity not fully proven'),paths)},
      'verdict':verdict,'reason_code':code,'reason':reason,'semantic_group_key':None,'duplicate_of_url_index':None,'legacy_reports':legacy_reports,'reviewed_at':'2026-09-24T00:00:00Z'}
    recs.append(rec)
out=f'{ROOT}/recheck_parts/audit_089_107.jsonl'; os.makedirs(os.path.dirname(out),exist_ok=True)
with open(out,'w') as f:
    for r in recs: f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
print(out,len(recs))
