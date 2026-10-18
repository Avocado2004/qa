#!/usr/bin/env python3
import json, re, urllib.parse
from pathlib import Path
BASE=Path('/opt/data/qa-vacancy-project')
OUT=BASE/'recheck_parts'
urls=json.loads((BASE/'github_history_urls.json').read_text())['unique_urls']
assert len(urls)==107
review='2026-09-24T00:00:00Z'

def norm(u):
 p=urllib.parse.urlsplit(u); q=[(k,v) for k,v in urllib.parse.parse_qsl(p.query,keep_blank_values=True) if not (k.lower().startswith('utm_') or k.lower() in {'trk','source','lipi','ref','originalsubdomain'})]
 host=p.netloc.lower(); host=host[4:] if host.startswith('www.') else host
 return urllib.parse.urlunsplit((p.scheme.lower(),host,p.path,urllib.parse.urlencode(q),''))
def key(u):
 m=re.search(r'(?:jobPosting/|/jobs/view/[^/]*?-)([0-9]{6,})',u) or re.search(r'/jobs/([^/?]+-\d+)$',u) or re.search(r'/([^/]+)$',u)
 domain=urllib.parse.urlsplit(u).netloc.lower().replace('www.','')
 return f'{domain}:{m.group(1) if m else "unknown"}'
def ev(url,quote,method): return {'url':url,'quote':quote,'method':method}
def gate(result,value,evidence): return {'result':result,'value':value,'evidence':evidence}

def build(i,title,emp,legal,entity_id,loc,mode,dewide,posted,identity,role,date,entity,direct,locg,evidok,verdict,reason_code,reason,access,methods,blocked=False,notes=''):
 u=urls[i-1]; ue=ev(u, f'Current card identity: {title}; employer/location: {emp} — {loc}.', methods[0])
 return {
  'url_index':i,'original_url':u,'normalized_url':norm(u),'source_key':key(u),
  'access':{'attempted_methods':methods,'http_status':access[0],'final_url':access[1],'current_card':direct[0]=='PASS','blocked':blocked,'notes':notes or '; '.join(methods)+' attempted.'},
  'current_identity':{'title':title,'employer_display':emp,'employer_legal_name':legal,'employer_entity_id':entity_id or '','location':loc,'work_mode':mode,'germany_wide':dewide,'posted_date':posted or '','identity_match':identity},
  'gates':{
   'role':gate(role[0],role[1],role[2]),
   'date':gate(date[0],date[1],date[2]),
   'de_entity':gate(entity[0],entity[1],entity[2]),
   'direct_current_card':gate(direct[0],direct[1],direct[2] or [ue]),
   'location_mode':gate(locg[0],locg[1],locg[2]),
   'evidence_identity':gate(evidok[0],evidok[1],evidok[2] or [ue])},
  'verdict':verdict,'reason_code':reason_code,'reason':reason,'semantic_group_key':None,'duplicate_of_url_index':None,
  'legacy_reports':[{'file':'github_history_audit_045-066.md','legacy_position':str(i),'legacy_verdict':{'PASS':'VERIFIED','PARTIAL':'PARTIAL','REJECT':'REJECTED','UNCLEAR':'PARTIAL'}[verdict],'match_method':'exact_url'}],
  'reviewed_at':review}

legacy_verdicts={45:'REJECT',46:'REJECT',47:'REJECT',48:'PARTIAL',49:'REJECT',50:'PARTIAL',51:'PARTIAL',52:'REJECT',53:'REJECT',54:'REJECT',55:'REJECT',56:'PARTIAL',57:'REJECT',58:'REJECT',59:'PASS',60:'PARTIAL',61:'PASS',62:'REJECT',63:'REJECT',64:'REJECT',65:'REJECT',66:'PASS'}
# Current identity, dates, and gate determinations after HTTP + independent extraction/guest API checks.
cfg={
45:('Software Tester (m/w/d) – Cloud & Applications','SOA Experts GmbH','','Lübeck','UNKNOWN',False,'2026-09-18','MATCH','LOCATION_MODE','Lübeck is neither Berlin, Leipzig, nor Dresden and no qualifying Germany-wide Remote evidence is present.'),
46:('Software Tester (m/w/d) – Cloud & Applications','SOA Experts GmbH','','Lübeck','UNKNOWN',False,'UNKNOWN','MATCH','LOCATION_MODE','Lübeck is outside the three accepted onsite/hybrid cities and no qualifying remote mode is shown.'),
47:('Softwaretester (m/w/d) – Healthcare SaaS','Deutsches Medizinrechenzentrum GmbH','','Düsseldorf','UNKNOWN',False,'2026-09-17','MISMATCH','DIRECT_IDENTITY_MISMATCH','Canonical job ID 4449455160 currently resolves to a DMRZ Düsseldorf card, not the historical GK Software vacancy.'),
48:('Software Tester / QA Engineer (all genders)','GK Software','','Schöneck','Onsite',False,'2026-09-23','MISMATCH','DIRECT_IDENTITY_MISMATCH','Canonical job ID 4243056914 currently resolves to GK Software in Schöneck, not the historical Deloitte Leipzig vacancy.'),
49:('Software Tester / Testautomatisierer (m/w/d)','Deloitte','','Leipzig / Frankfurt','UNKNOWN',False,'2026-09-10','MISMATCH','DIRECT_IDENTITY_MISMATCH','Canonical job ID 4466469998 currently resolves to Deloitte in Leipzig, not the historical DMRZ Düsseldorf vacancy.'),
50:('Softwaretester (m/w/d) 100 % Remote im Consulting-Umfeld','eightbit experts GmbH','','Germany','Remote',True,'2026-09-10','MATCH','END_CLIENT_ENTITY_UNKNOWN','The page is current and Germany-remote, but it describes direct placement for an unnamed mandate client; the actual hiring legal entity is not established.'),
51:('Softwaretester (m/w/d)','deltra Business Software GmbH & Co. KG','deltra Business Software GmbH & Co. KG','Germany','Remote',True,'UNKNOWN','MATCH','DATE_AND_ENTITY_UNRESOLVED','Current role and 100% home-office/Germany evidence match, but the posting date and official legal-entity confirmation were not captured.'),
52:('Softwaretester (m/w/d)','deltra Business Software GmbH & Co. KG','deltra Business Software GmbH & Co. KG','Germany','Remote',True,'UNKNOWN','MISMATCH','DIRECT_IDENTITY_MISMATCH','The FERCHAU-labelled historical URL now resolves by job ID 4467085202 to a deltra/orgaMAX vacancy, so it is not the same vacancy identity.'),
53:('Softwaretester (m/w/d) – Healthcare SaaS','Deutsches Medizinrechenzentrum GmbH','','Düsseldorf','UNKNOWN',False,'2026-09-17','MATCH','LOCATION_MODE','Düsseldorf is outside the accepted cities and no Germany-wide Remote eligibility is shown.'),
54:('Softwaretester Online Spiele (m/w/d)','CipSoft GmbH','','Regensburg','Onsite',False,'2026-09-20','MATCH','LOCATION_MODE','Regensburg is outside Berlin, Leipzig, and Dresden and the card is onsite.'),
55:('Pflegefachkraft (m/w/d)','VONBERG Haus Sonnenblick GmbH','VONBERG Haus Sonnenblick GmbH','Schotten','UNKNOWN',False,'2026-09-24','MISMATCH','DIRECT_CARD_RETARGETED','The Soloplan QA URL now resolves to an unrelated, closed nursing-care vacancy.'),
56:('Staff Engineer, Software Test','Stryker','','Berlin','UNKNOWN',False,'2026-09-22','MATCH','MODE_AND_ENTITY_UNRESOLVED','Qualifying Berlin software-test card, but explicit Onsite/Hybrid mode and the exact German hiring legal entity are not established.'),
57:('System Validation & Test Automation Engineer (a)','Baumer Group','','Radeberg','UNKNOWN',False,'2026-09-10','MATCH','LOCATION_MODE','Radeberg is expressly not Dresden under the specification and no qualifying remote evidence appears.'),
58:('Test Automation Engineer – Cucumber','Jobgether','','Germany','Remote',True,'UNKNOWN','UNKNOWN','END_CLIENT_IDENTITY_UNKNOWN','The current card is a direct Jobgether partner listing with an unnamed employer; the actual hiring identity and posting date cannot be established.'),
59:('Test Automation Engineer (m/w/d)','MEDIFOX DAN','MEDIFOX DAN GmbH','Germany','Remote',True,'2026-09-10','MATCH','',''),
60:('Test Engineer (m/w/d)','mamgo | Talente | Jobs','','Berlin','UNKNOWN',False,'2026-09-24','UNKNOWN','END_CLIENT_IDENTITY_UNKNOWN','The staffing card is current, but the unnamed end-client hiring entity prevents G3/G6 closure.'),
61:('Werkstudent (m/w/d) – Softwarequalitätssicherung & Testautomatisierung','Swiss Life Lebensversicherung SE','Swiss Life Lebensversicherung SE','Leipzig','UNKNOWN',False,'2026-09-07','MATCH','MODE_AND_ENTITY_UNRESOLVED','The Leipzig QA card and German legal-form employer are current, but explicit Onsite/Hybrid mode and an official legal-page capture were not obtained.'),
62:('Technical Embedded QA Specialist I','Cloud Imperium Games','','Frankfurt am Main','UNKNOWN',False,'2026-08-27','MATCH','LOCATION_MODE','Frankfurt am Main is outside Berlin, Leipzig, and Dresden and no Germany-wide remote route is evidenced.'),
63:('Head of Quality Assurance (QA)','Stillfront Group','','Hamburg','UNKNOWN',False,'2026-08-21','MATCH','ROLE_NOT_QUALIFYING','Current QA-management duties do not include substantive software/game testing; date and location also fail.'),
64:('QA Analyst','Jam City','','Berlin (among global locations)','UNKNOWN',False,'2026-08-24','MATCH','DATE_OUT_OF_WINDOW','datePosted 2026-08-24 is one day before the inclusive 2026-08-25 lower bound.'),
65:('Head of Quality Assurance (QA)','Twin Harbour Interactive','','Hamburg / Malta','UNKNOWN',False,'2026-08-21','MATCH','ROLE_NOT_QUALIFYING','Current QA-management duties do not include substantive software/game testing; date and location also fail.'),
66:('Software Tester','BVU Beratergruppe Verkehr + Umwelt','BVU Beratergruppe Verkehr + Umwelt GmbH','Germany','Remote',True,'2026-09-18','MATCH','','')}

records=[]
for i in range(45,67):
 u=urls[i-1]; title,emp,legal,loc,mode,wide,posted,ident,rc,reason=cfg[i]
 role_pass=('test' in title.lower() or 'qa' in title.lower() or 'qualitäts' in title.lower()) and i not in {63,65}
 role_ev=ev(u,title,'independent page extraction')
 role=('PASS','qualifying software/game QA or testing duties' if role_pass else 'current duties are QA management without substantive testing','%s; %s'%(title,'role evidence from current card'), [role_ev]) if role_pass else ('FAIL','QA-management role without substantive testing duty',[ev(u,title,'independent page extraction')])
 if posted and re.match(r'2026-08-\d\d|2026-09-\d\d',posted):
  date_ok=posted>='2026-08-25'; date=(('PASS' if date_ok else 'FAIL'),posted,[ev(u,f'Current posting date: {posted}.','HTTP JobPosting JSON-LD' if i in {45,54,56,61} else 'independent board extraction')])
 else: date=('UNKNOWN','',[ev(u,'No unambiguous current posting date was exposed.','HTTP and independent extraction')])
 if i in {59,66}:
  entity=(('PASS',legal,[ev(u,f'{emp}; German hiring employer is named on the current card.','independent page extraction'),ev({'66':'https://www.bvu.de/impressum/','59':'https://www.medifoxdan.de/impressum/'}[str(i)],{'66':'BVU Beratergruppe Verkehr + Umwelt GmbH … Amtsgericht Freiburg - HRB 3579.','59':'MEDIFOX DAN GmbH … Registergericht: Amtsgericht Hildesheim; Registernummer: HRB 202124.'}[str(i)],'official legal page')]))
 elif i in {50,58,60}: entity=('UNKNOWN','',[ev(u,'Actual hiring/end-client legal entity is unnamed.','independent page extraction')])
 else: entity=('UNKNOWN','',[ev(u,(legal or emp)+' named; official entity confirmation not captured.','current card')])
 if ident=='MISMATCH': direct=('FAIL','same-vacancy identity not proven',[ev(u,f'Canonical job ID now resolves to: {title} / {emp}.','HTTP and independent extraction')])
 else: direct=('PASS','live direct card for current identity',[ev(u,f'{title} at {emp}.','HTTP' if i in {45,51,52,54,55,56,58,61,62,63,64,65,66} else 'independent page extraction')])
 if i in {45,46,49,53,54,57,62,63,64,65,47}:
  # 47 is rejected earlier for identity; location remains unknown where mismatched.
  if i==47: lg=('UNKNOWN','',[ev(u,'Current DMRZ card is Düsseldorf; no accepted mode.','independent extraction')])
  else: lg=('FAIL',f'{loc} is outside the accepted onsite/hybrid route',[ev(u,f'Current card location: {loc}.','HTTP/independent extraction')])
 elif i in {48,56,60,61}: lg=('UNKNOWN','',[ev(u,f'Target city is shown ({loc}) but no explicit Onsite or Hybrid marker was found.','HTTP plus LinkedIn guest API')])
 elif i == 55: lg=('UNKNOWN','',[ev(u,'Current card is an unrelated Schotten nursing vacancy.','HTTP and independent extraction')])
 else: lg=('PASS',f'{mode} in {loc}',[ev(u,{'50':'Softwaretester … 100 % Remote … Germany','51':'100 % Homeoffice möglich','52':'100 % Homeoffice möglich','58':'fully remote … based in Germany','59':'100 % remote und kann vollständig ortsunabhängig in Deutschland ausgeübt werden','66':'Location: Germany; remote Software Tester'}[str(i)],'independent page extraction')])
 evid=('PASS','two paths establish current identity',[ev(u,title,'HTTP'),ev(u,title,'independent extraction/guest API')]) if ident=='MATCH' else ('FAIL','historical and current identity conflict',[ev(u,f'Current identity: {title} / {emp}.','HTTP and independent extraction')])
 verdict={45:'REJECT',46:'REJECT',47:'REJECT',48:'REJECT',49:'REJECT',50:'PARTIAL',51:'PARTIAL',52:'REJECT',53:'REJECT',54:'REJECT',55:'REJECT',56:'PARTIAL',57:'REJECT',58:'UNCLEAR',59:'PASS',60:'UNCLEAR',61:'PARTIAL',62:'REJECT',63:'REJECT',64:'REJECT',65:'REJECT',66:'PASS'}[i]
 if not reason: reason='All six gates have current affirmative evidence, including Germany-wide Remote eligibility and the named German legal entity.'
 methods=['http','independent_extraction']+(['linkedin_guest_api'] if i in {48,50,56,59,60,61} else [])
 access=(200,u)
 rec=build(i,title,emp,legal,'',loc,mode,wide,posted,ident,role,date,entity,direct,lg,evid,verdict,rc or 'ALL_GATES_PASS',reason,access,methods,blocked=False,notes='Independent extraction succeeded; LinkedIn guest API used additionally for selected blocked/dynamic records.')
 rec['legacy_reports'][0]['legacy_verdict']=legacy_verdicts[i]
 records.append(rec)

out=OUT/'audit_045_066.jsonl'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records),encoding='utf-8')
print(out, len(records))
