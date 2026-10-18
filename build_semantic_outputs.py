#!/usr/bin/env python3
import json, re, hashlib, unicodedata
from pathlib import Path
from datetime import date

ROOT = Path('/opt/data/qa-vacancy-project')
AUDIT = ROOT / 'historical_url_audit.jsonl'
START, END = date(2026,8,25), date(2026,9,24)

# Controlled mappings are based on the accepted current identity in the audit.
# A distinct PASS record gets a distinct semantic identity unless an official
# requisition key is explicitly present in the accepted audit.
ROLE = {
  1: ('test-automation-engineer', 'lead', 'remote-de'),
  3: ('software-qa-engineer', 'unspecified', 'dresden'),
  5: ('game-localization-qa', 'unspecified', 'berlin'),
  9: ('software-qa-engineer', 'mid', 'berlin'),
  12: ('software-qa-engineer', 'unspecified', 'dresden'),
  59: ('test-automation-engineer', 'unspecified', 'remote-de'),
  66: ('software-qa-engineer', 'unspecified', 'remote-de'),
  73: ('software-qa-engineer', 'unspecified', 'dresden'),
  85: ('software-test-engineer', 'unspecified', 'dresden'),
  105: ('test-management-consultant', 'unspecified', 'berlin'),
  107: ('test-automation-engineer', 'unspecified', 'leipzig'),
}
EMPLOYER = {
  1: 'fio-systems-ag', 3: 'diehl-aviation-gilching-gmbh', 5: 'lionbridge-germany-gmbh',
  9: 'talon-one-gmbh', 12: 'supplyon-gmbh', 59: 'medifox-dan-gmbh',
  66: 'bvu-beratergruppe-verkehr-und-umwelt-gmbh', 73: 'robotron-datenbank-software-gmbh',
  85: 'k-tronik-gmbh', 105: 'pta-programmier-technische-arbeiten-gmbh', 107: 'geomagic-gmbh',
}
SCOPE = {3:'Dresden',5:'Berlin',9:'Berlin',12:'Dresden',59:'Germany (Remote)',66:'Germany (Remote)',73:'Dresden',85:'Dresden',105:'Berlin',107:'Leipzig',1:'Germany (Remote)'}
OFFICIAL_REQUISITION = {}

def norm_legal(s):
    s = unicodedata.normalize('NFKC', s).casefold().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s

def semantic_key(r):
    i=r['url_index']
    if i in OFFICIAL_REQUISITION:
        return f"{EMPLOYER[i]}|req:{OFFICIAL_REQUISITION[i].casefold()}"
    role, seniority, scope = ROLE[i]
    return f"{EMPLOYER[i]}|{role}|{seniority}|{scope}"

def iso_date(s):
    m=re.match(r'(\d{4}-\d{2}-\d{2})', s or '')
    return m.group(1) if m else None

rows=[json.loads(line) for line in AUDIT.read_text().splitlines() if line.strip()]
byidx={r['url_index']:r for r in rows}
passes=[r for r in rows if r['verdict']=='PASS']
assert len(rows)==107 and sorted(byidx)==list(range(1,108))
assert len(passes)==11 and set(ROLE)=={r['url_index'] for r in passes}

# One row per proven semantic group. No PASS records in this audit share the
# same legal-employer + requisition identity, hence no duplicate group is claimed.
groups=[]
for r in passes:
    i=r['url_index']; ci=r['current_identity']
    key=semantic_key(r)
    groups.append({
      'semantic_group_key': key,
      'member_url_indexes': [i],
      'member_urls': [r['original_url']],
      'chosen_url_index': i,
      'chosen_url': r['original_url'],
      'stable_id': None,
      'position': ci['title'],
      'company': ci['employer_legal_name'] or ci['employer_display'],
      'location': SCOPE[i], 'posted_date': iso_date(ci['posted_date']),
      'work_mode': ci['work_mode'],
      'deduplication_basis': 'official requisition identity' if i in OFFICIAL_REQUISITION else 'single accepted PASS; no evidence of another identical opening'
    })
# Defensive semantic merge (currently no merges), with member traceability.
merged=[]
for g in groups:
    old=next((x for x in merged if x['semantic_group_key']==g['semantic_group_key']),None)
    if old:
        for k in ('member_url_indexes','member_urls'): old[k].extend(g[k])
        old['member_url_indexes'].sort(); old['member_urls']=[byidx[x]['original_url'] for x in old['member_url_indexes']]
        old['chosen_url_index']=min(old['member_url_indexes']); old['chosen_url']=byidx[old['chosen_url_index']]['original_url']
    else: merged.append(g)
groups=merged
# hash and collision resolution by full hash
hashed=[]
for g in groups: hashed.append((hashlib.sha256(g['semantic_group_key'].encode()).hexdigest().upper(),g))
for digest,g in hashed: g['stable_id']='QADE-'+digest[:12]
from collections import defaultdict
by_prefix=defaultdict(list)
for digest,g in hashed: by_prefix[digest[:12]].append((digest,g))
for prefix, vals in by_prefix.items():
    if len(vals)>1:
        for n,(digest,g) in enumerate(sorted(vals),1): g['stable_id']=f'QADE-{prefix}-{n:02d}'

groups.sort(key=lambda g:(g['posted_date'],g['stable_id']), reverse=True)
registry={g['stable_id']:{'semantic_group_key':g['semantic_group_key'],'member_url_indexes':g['member_url_indexes']} for g in groups}
(ROOT/'semantic_groups.json').write_text(json.dumps({'audit_date':'2026-09-24','accepted_verdict':'PASS','group_count':len(groups),'groups':groups},ensure_ascii=False,indent=2)+'\n')
(ROOT/'id_registry.json').write_text(json.dumps({'algorithm':'SHA-256 first 12 uppercase hex; deterministic -NN collision suffix by full hash','groups':registry},ensure_ascii=False,indent=2)+'\n')

headers=['ID','Position','Company','Location','Posted','Work mode','URL index']
md=['# QA Vacancies — Rebuilt Master Candidate','',f'Accepted semantic groups: **{len(groups)}** (PASS only).','',
    '| '+' | '.join(headers)+' |','|'+'|'.join(['---']*6+['---:'])+'|']
for g in groups:
    vals=[g['stable_id'],f"[{g['position']}]({g['chosen_url']})",g['company'],g['location'],g['posted_date'],g['work_mode'],', '.join(map(str,g['member_url_indexes']))]
    vals=[str(v).replace('|','\\|') for v in vals]
    md.append('| '+' | '.join(vals)+' |')
(ROOT/'qa_vacancies_master_rebuilt.md').write_text('\n'.join(md)+'\n')

# Section 7 validations.
checks={}
checks['1_exactly_107_unique_indices']=len(rows)==107 and sorted(byidx)==list(range(1,108))
checks['2_controlled_verdicts']=all(r['verdict'] in {'PASS','PARTIAL','UNCLEAR','REJECT'} for r in rows)
gate_names={'role','date','de_entity','direct_current_card','location_mode','evidence_identity'}
checks['3_pass_six_gates_and_evidence']=all(all(r['gates'].get(g,{}).get('result')=='PASS' and bool(r['gates'].get(g,{}).get('evidence')) for g in gate_names) for r in passes)
checks['4_only_pass_in_master']=all(r['verdict']=='PASS' for g in groups for i in g['member_url_indexes'] for r in [byidx[i]])
parsed=[]
for line in md:
    if line.startswith('| QADE-'):
        # Parse only unescaped column separators; display fields are already pipe-escaped.
        cells=[]; current=[]; escaped=False
        for ch in line.strip()[1:-1]:
            if ch=='|' and not escaped:
                cells.append(''.join(current).strip()); current=[]
            else:
                current.append(ch)
            escaped=(ch=='\\' and not escaped)
            if ch!='\\': escaped=False
        cells.append(''.join(current).strip()); parsed.append(cells)
checks['5_seven_columns']=len(parsed)==len(groups) and all(len(x)==7 for x in parsed)
checks['6_unique_valid_ids']=len({g['stable_id'] for g in groups})==len(groups) and all(re.fullmatch(r'QADE-[0-9A-F]{12}(?:-[0-9]{2})?',g['stable_id']) for g in groups)
checks['7_id_maps_one_key']=all(registry[g['stable_id']]['semantic_group_key']==g['semantic_group_key'] for g in groups)
checks['8_unique_semantic_groups']=len({g['semantic_group_key'] for g in groups})==len(groups)
checks['9_final_location_mode_g5']=all((g['work_mode'] in {'Onsite','Hybrid'} and g['location'] in {'Berlin','Leipzig','Dresden'}) or (g['work_mode']=='Remote' and g['location']=='Germany (Remote)') for g in groups)
checks['10_dates_in_window']=all(START<=date.fromisoformat(g['posted_date'])<=END for g in groups)
checks['11_final_urls_direct_cards']=all(byidx[g['chosen_url_index']]['gates']['direct_current_card']['result']=='PASS' and byidx[g['chosen_url_index']]['access']['current_card'] for g in groups)
checks['12_representative_pass']=all(byidx[g['chosen_url_index']]['verdict']=='PASS' for g in groups)
checks['13_member_indexes_exist']=all(i in byidx for g in groups for i in g['member_url_indexes'])
checks['14_registry_stability']=all(registry[g['stable_id']]['member_url_indexes']==g['member_url_indexes'] for g in groups)
checks['15_markdown_row_count']=len(parsed)==len(groups)
print(json.dumps({'verdict_counts':{v:sum(r['verdict']==v for r in rows) for v in ['PASS','PARTIAL','UNCLEAR','REJECT']},'accepted_groups':len(groups),'duplicate_groups':sum(len(g['member_url_indexes'])>1 for g in groups),'validations':checks,'all_passed':all(checks.values())},indent=2))
if not all(checks.values()): raise SystemExit(1)
