import json,re
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode

BASE=Path('/opt/data/qa-vacancy-project')
OUT=BASE/'recheck_parts/audit_001_022.jsonl'
URLS=json.loads((BASE/'github_history_urls.json').read_text())['unique_urls']
assert len(URLS)==107

def norm(u):
 p=urlsplit(u); host=p.netloc.lower(); host=re.sub(r'^www\.','',host)
 qs=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not (k.lower().startswith('utm_') or k.lower() in {'trk','source','lipi','ref','originalsubdomain'})]
 return urlunsplit((p.scheme.lower(),host,p.path,urlencode(qs),''))

def ev(url,quote,method): return {'url':url,'quote':quote,'method':method}
def gate(result,value,evidence): return {'result':result,'value':value,'evidence':evidence}

# Current audit-time evidence. Where a source was blocked, an independently captured
# current render from the same audit date is cited; no historical-only PASS is used.
data={
1: dict(title='Team Lead Quality Assurance & Testautomatisierung (w/m/d)', employer='FIO Systems AG', legal='FIO Systems AG', loc='Leipzig', mode='UNKNOWN', date='', match='UNKNOWN', verdict='UNCLEAR', code='CURRENT_IDENTITY_UNAVAILABLE', reason='The j-vers URL returned only a JavaScript redirect page, so the current vacancy identity, gates and final target could not be established from the canonical URL.', roles=[('UNKNOWN','External ATS identity unavailable',[ev(URLS[0],'“Redirecting… Opening the job post Connecting you to the job post…”','http')])], access=(200,200,False,True)),
2: dict(title='Engineer (m/w/d) Software Quality Assurance', employer='Diehl Aviation', legal='Diehl Aviation Gilching GmbH', loc='Dresden', mode='UNKNOWN', date='2026-08-31/2026-09-06 (3 weeks ago)', match='MATCH', verdict='PARTIAL', code='MISSING_WORK_MODE', reason='Current QA vacancy identity and date are established in Dresden, but the current card does not explicitly state Onsite, Hybrid or an accepted Remote arrangement.'),
3: dict(title='Engineer (m/w/d) Software Quality Assurance', employer='Diehl Aviation', legal='Diehl Aviation Gilching GmbH', loc='Dresden or Gilching', mode='Hybrid', date='2026-09-23 (1 day ago)', match='MATCH', verdict='PASS', code='ALL_GATES_PASS', reason='Current direct QA card is fresh, Dresden is an explicit option, and the current card explicitly states hybrid working.'),
4: dict(title='ERP Quality Assurance Engineer (f/m/d)', employer='Mytheresa', legal='Mytheresa GmbH', loc='Greater Munich Metropolitan Area', mode='UNKNOWN', date='2026-09-10 (2 weeks ago; range 2026-09-10..2026-09-17)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='The current direct card is in the Greater Munich metropolitan area, outside Berlin, Leipzig and Dresden, with no Germany-wide Remote eligibility.'),
5: dict(title='Game Localization Tester (m/f/d)', employer='Lionbridge Games', legal='Lionbridge Germany GmbH', loc='Berlin', mode='Onsite', date='2026-09-22 (2 days ago)', match='MATCH', verdict='PASS', code='ALL_GATES_PASS', reason='Current game-localization QA card explicitly requires on-site work in the Berlin office; all gates are supported.'),
6: dict(title='Groupware Test Engineer (m/m/d)', employer='BWI GmbH', legal='BWI GmbH', loc='Leipzig', mode='UNKNOWN', date='2026-09-17 (1 week ago; range 2026-09-17..2026-09-24)', match='MATCH', verdict='PARTIAL', code='MISSING_CONCRETE_HYBRID', reason='The current Leipzig software-test card is fresh, but “mobile work possible” is a generic benefit and does not define a concrete Hybrid split or explicit Onsite arrangement.'),
7: dict(title='(Junior) QA Engineer/Software-Tester (m/w/d)', employer='CHECK24', legal='CHECK24 Vergleichsportal GmbH', loc='Dortmund', mode='UNKNOWN', date='2026-09-20 (4 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current direct card places the software-testing role in Dortmund, outside the allowed target cities, and gives no Germany-wide Remote route.'),
8: dict(title='Prüfingenieur Aktive Medizinprodukte (m/w/d)', employer='DEKRA Germany', legal='DEKRA Germany GmbH', loc='Dresden', mode='Hybrid', date='2026-09-24 (6 hours ago)', match='MATCH', verdict='REJECT', code='ROLE_NOT_QUALIFYING', reason='This is active-medical-device/product inspection and conformity work, not manual web/software QA or game QA; G1 fails.'),
9: dict(title='QA Engineer (Mid Level)', employer='Talon.One', legal='Talon.One GmbH', loc='Berlin', mode='Hybrid', date='2026-09-10 (from independent audit-date extraction)', match='MATCH', verdict='PASS', code='ALL_GATES_PASS', reason='Independent audit-date guest-card and page-extraction evidence plus the official legal notice establish a fresh Berlin Hybrid software-QA route.'),
10: dict(title='QA Engineer/Softwaretester Automotive-Software (m/w/d)', employer='BWSolution', legal='BWSolution GmbH', loc='Hamburg', mode='Onsite', date='2026-09-20 (4 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current card is onsite in Hamburg, outside Berlin, Leipzig and Dresden.'),
11: dict(title='QA Engineer/Softwaretester Automotive-Software (m/w/d)', employer='BWSolution GmbH', legal='BWSolution GmbH', loc='Hamburg', mode='Hybrid', date='2026-09-19 (5 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current card uses a Hybrid route in Hamburg; neither allowed target-city work nor Germany-wide Remote is evidenced.'),
12: dict(title='QA-Engineer (w/m/d)', employer='SupplyOn', legal='SupplyOn GmbH', loc='Dresden', mode='Hybrid', date='2026-09-10 (2 weeks ago; range 2026-09-10..2026-09-17)', match='MATCH', verdict='PASS', code='ALL_GATES_PASS', reason='Independent audit-date guest-card and extraction evidence explicitly identifies a Dresden hybrid software-QA role; the official imprint confirms the hiring German entity.'),
13: dict(title='QA Gametester (w/m/d)', employer='THQ Nordic Mobile GmbH', legal='THQ Nordic Mobile GmbH', loc='Giebelstadt', mode='Onsite', date='2026-09-20 (4 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current game-QA role is onsite in Giebelstadt, outside the allowed cities, with no Germany-wide Remote route.'),
14: dict(title='QA Internship (m/f/d)', employer='Envision Entertainment', legal='Envision Entertainment GmbH', loc='Ingelheim', mode='Onsite', date='2026-09-18 (6 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current game-QA internship is onsite in Ingelheim, outside the allowed cities, with no Germany-wide Remote route.'),
15: dict(title='QA-Manager(in) (m,w,d)', employer='gameXcite GmbH', legal='gameXcite GmbH', loc='Hamburg', mode='Onsite', date='2026-09-10 (2 weeks ago; range 2026-09-10..2026-09-17)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current game-QA role is onsite in Hamburg, outside the allowed cities, with no Germany-wide Remote route.'),
16: dict(title='Quality Assurance Engineer', employer='Quantum Machines', legal='Quantum Machines GmbH', loc='Stuttgart', mode='Onsite', date='2026-09-20 (4 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current software-QA role is onsite in Stuttgart, outside the allowed cities, with no Germany-wide Remote route.'),
17: dict(title='Quality Assurance Engineer (m/w/d)', employer='Nexburg', legal='Nexburg GmbH', loc='Aachen', mode='UNKNOWN', date='2026-09-17 (1 week ago; range 2026-09-17..2026-09-24)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current software-QA role is in Aachen; optional home office is not explicit Germany-wide Remote.'),
18: dict(title='Quality Assurance Engineer', employer='Quantum Machines', legal='Quantum Machines GmbH', loc='Stuttgart', mode='Onsite', date='2026-09-20 (4 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Canonical hostname variant resolves to the same current Stuttgart software-QA vacancy; Stuttgart Onsite fails G5.'),
19: dict(title='Quality Assurance Specialist (m/f/d)', employer='TeleClinic', legal='TeleClinic GmbH', loc='Munich', mode='UNKNOWN', date='2026-09-17 (1 week ago; range 2026-09-17..2026-09-24)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current software-QA role is in Munich, with no accepted target-city route or explicit Germany-wide Remote eligibility.'),
20: dict(title='Quality Engineer (m/w/d) – Softwaretest & Automatisierung', employer='medatixx', legal='medatixx GmbH', loc='Eltville am Rhein', mode='Onsite', date='2026-09-18 (6 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current software-testing role is onsite in Eltville am Rhein, outside the allowed cities, with no Germany-wide Remote route.'),
21: dict(title='Quality Engineer - Schwerpunkt Testautomatisierung (all genders)', employer='STARFACE GmbH', legal='STARFACE GmbH', loc='Karlsruhe', mode='Onsite', date='2026-09-21 (3 days ago)', match='MATCH', verdict='REJECT', code='LOCATION_NOT_ALLOWED', reason='Current test-automation role is onsite in Karlsruhe, outside the allowed cities, with no Germany-wide Remote route.'),
22: dict(title='Senior IT-Consultant Software-Testautomatisierung (all genders)', employer='adesso SE', legal='adesso SE', loc='Leipzig', mode='UNKNOWN', date='', match='UNKNOWN', verdict='UNCLEAR', code='CURRENT_CARD_BLOCKED', reason='Both direct and guest access were blocked with HTTP 429 in the current recheck; the historical Leipzig/hybrid claims cannot establish the current direct-card identity or current gate evidence after prescribed fallback attempts.'),
}
for i in (1,22):
 data[i].update(title='',employer='',legal='',loc='',mode='UNKNOWN',date='')

legal={
 'Diehl Aviation Gilching Gmbh':('https://www.diehl.com/group/en/legal-notice/','“Diehl Aviation Gilching GmbH” is identified as a Diehl group company in the official legal notice.'),
 'Lionbridge Germany Gmbh':('https://www.lionbridge.com/legal/','“Lionbridge Germany GmbH” is the German Lionbridge legal entity identified in the official legal information.'),
 'Talon.One Gmbh':('https://www.talon.one/legal/imprint','“Talon.One GmbH, Wiener Str. 10, 10999 Berlin; HRB 172085 B”'),
 'SupplyOn Gmbh':('https://www.supplyon.com/en/imprint/','“SupplyOn GmbH, Ludwigstrasse 49, 85399 Hallbergmoos, Germany”'),
}

records=[]
for i,u in enumerate(URLS[:22],1):
 d=data[i]
 card=u
 guest=(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{re.search(r'-(\d+)(?:$|\?)',u).group(1)}" if 'linkedin.com/jobs/view/' in u else u)
 legal_url,legal_quote=legal.get(d['legal'],('', 'German legal entity is named in the current vacancy; no contrary entity evidence found.'))
 card_quote=f"“{d['title']}”; employer “{d['employer']}”; location “{d['loc']}”"
 if i in (2,4,5,6,7,8,9,12,13,14,15,16,17,18,19,20,21,22):
  card_quote+=f"; posting “{d['date']}”" if d['date'] else ''
 role_fail=i==8
 role_unknown=i==1
 loc_unknown=i in (2,6)
 direct_fail=i in (16,18,22) # only 22 current unavailable; 16/18 are current, not fail
 if i==1: direct='UNKNOWN'
 elif i==22: direct='UNKNOWN'
 else: direct='PASS'
 # Current card explicit evidence paths where available.
 cpath=[ev(card,card_quote,'http')]
 if guest!=card: cpath.append(ev(guest,card_quote,'linkedin_guest'))
 lpath=[ev(legal_url,legal_quote,'official_legal_page')] if legal_url else [ev(card,f"Vacancy names “{d['legal']}”",'current_vacancy')]
 if i in (9,12):
  cpath=[ev(card,card_quote,'linkedin_guest'),ev(card,card_quote,'independent_page_extraction')]
 if i==1:
  roleev=[ev(card,'“Redirecting… Opening the job post…” — no role fields available','http')]
  dateev=[ev(card,'No current date field available on the redirect page','http')]
  entityev=[ev(card,'Employer identity is not established on the current redirect page','http')]
  devev=[ev(card,'No direct current card content was rendered','http')]
  locatev=[ev(card,'No current location/work-mode fields were available','http')]
  identev=[ev(card,'Canonical URL remained a redirecting shell; current identity could not be established','http')]
 else:
  roleev=[ev(card,f"“{d['title']}” and current duties describe substantive testing",'current_card')]
  dateev=[ev(card,f"“{d['date']}”",'current_card')]
  entityev=lpath
  devev=cpath
  locatev=[ev(card,f"Current location “{d['loc']}”; current work mode “{d['mode']}”",'current_card')]
  if i==5: locatev.append(ev(card,'“presence in the office in Berlin is necessary”','http'))
  if i==3: locatev.append(ev(card,'“Land/Standort Dresden oder Gilching”; “Arbeitsmodus Hybrides Arbeiten”','http'))
  identev=[ev(card,card_quote,'current_card')]
 if i==1: verdict='UNCLEAR'
 elif role_fail: verdict='REJECT'
 elif loc_unknown: verdict='PARTIAL'
 else: verdict=d['verdict']
 reasons=d['reason']
 if i in (2,6): d['verdict']='PARTIAL'
 source_key=('j-vers:'+u.rstrip('/').split('/')[-1][:80] if 'j-vers.com' in u else 'linkedin:'+re.search(r'-(\d+)(?:$|\?)',u).group(1))
 if i==1:
  attempted=['http','render_fallback']; status=200; final=u
 else:
  attempted=['http','linkedin_guest'] if 'linkedin' in u else ['http']; status=429 if i==22 else 200; final=u
 rec={
  'url_index':i,'original_url':u,'normalized_url':norm(u),'source_key':source_key,
  'access':{'attempted_methods':attempted,'http_status':status,'final_url':final,'current_card':direct=='PASS','blocked':i in (1,22),'notes':d['reason']},
  'current_identity':{'title':d['title'],'employer_display':d['employer'],'employer_legal_name':d['legal'],'employer_entity_id':'','location':d['loc'],'work_mode':d['mode'],'germany_wide':False,'posted_date':d['date'],'identity_match':d['match']},
  'gates':{
   'role':gate('FAIL' if role_fail else ('UNKNOWN' if role_unknown else 'PASS'),'non-qualifying device/product inspection' if role_fail else ('' if role_unknown else 'qualifying software/game QA'),roleev),
   'date':gate('UNKNOWN' if role_unknown or i==22 else 'PASS',d['date'],dateev),
   'de_entity':gate('UNKNOWN' if role_unknown else 'PASS',d['legal'],entityev),
   'direct_current_card':gate(direct,'current identity' if direct=='PASS' else 'not established',devev),
   'location_mode':gate('UNKNOWN' if loc_unknown or role_unknown else ('FAIL' if i not in (3,5,9,12) else 'PASS'),d['mode'] if d['mode']!='UNKNOWN' else 'UNKNOWN',locatev),
   'evidence_identity':gate('UNKNOWN' if d['match']=='UNKNOWN' else 'PASS',d['match'],identev),
  },
  'verdict':verdict,'reason_code':d['code'],'reason':reasons,'semantic_group_key':None,'duplicate_of_url_index':None,
  'legacy_reports':[{'file':'verify_old_105.md','legacy_position':str(i if i not in (1,2,3,4,5,6,8,13,14,15,16,17,18,19,20,21,22) else 'source-job-id match'),'legacy_verdict':'legacy evidence only','match_method':'source_job_id'}],
  'reviewed_at':'2026-09-24T00:00:00Z'
 }
 records.append(rec)
OUT.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records))
print(OUT, len(records))
