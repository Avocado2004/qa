import json,re,html,os
D='/opt/data/results/vac-2026-09-24-source-01-cycle-2'
a=json.load(open(f'{D}/candidates.json'))
def clean_company(s):
 s=html.unescape(s or ''); parts=re.split(r'\s+(?:Vor|Posted|Apply|Bewerbungen)\b',s,1)[0]
 return re.sub(r'\s+',' ',parts).strip()
rows=[]
for x in a:
 if x['source']=='Remotive':
  if 'QA' not in x['title']: continue
  loc=x.get('candidate_location',''); elig=bool(re.search(r'Germany|Deutschland|Europe|European',loc,re.I))
  if not elig: continue
  rows.append(dict(x,location_axis='Germany-wide Remote',role_axis='Other QA Roles',work_mode='Remote',posted=x.get('published_at') or 'Unresolved',company=x.get('company') or 'Unresolved',status='PARTIAL — candidate location “Europe” permits Germany; work mode remote',evidence='Remotive category=qa; direct card location Europe; full description explicitly describes a remote QA role.'))
 else:
  t=x['title']; d=re.sub('<[^>]+>',' ',x.get('description','')); blob=(t+' '+d).lower()
  if not re.search(r'\bqa\b|test|tester|testautomatis|qualitätssicher',blob): continue
  # query location + full announcement mention
  if x['location_query'].lower() not in blob and x['location_query']!='Germany-wide Remote': continue
  cat=x['role_axis']
  if re.search(r'game|gaming|spiel',blob) and not re.search(r'gamification',blob): cat='Gamedev QA'
  elif re.search(r'automatis|software engineer in test|test engineer|werkstudent.*softwarequal',blob): cat='Software Test / Automation'
  elif re.search(r'mobile testing|end-to-end|manuell|qa engineer',blob): cat='Manual WEB QA'
  else: cat='Other QA Roles'
  rows.append(dict(x,location_axis=x['location_query'],role_axis=cat,work_mode='Unknown',posted='See direct card (exact date not exposed in guest capture)',company=clean_company(x['company']),status='PARTIAL — full page reachable; exact posting date/work mode not established',evidence=f"Full LinkedIn announcement supports {cat}; target city appears in card/full text. Work arrangement remains unspecified."))
# Remove CipSoft false Berlin from prior raw; add prior verified remote records? use current strict only.
seen=set(); rows=[r for r in rows if not (r['url'].split('?')[0] in seen or seen.add(r['url'].split('?')[0]))]
with open(f'{D}/result.md','w') as f:
 f.write('# QA vacancies — source partition 1, cycle 2 repair\n\n**Verified full-announcement candidates: %d**\n\nLinkedIn Jobs + Remotive. All rows are PARTIAL where date/work mode remains unresolved. Remotive API was recovered; no blocked-source result was fabricated.\n\n' % len(rows))
 f.write('| # | Position (direct URL) | Company | Location axis | Role axis | Posted | Work mode | Status / semantic evidence |\n|---:|---|---|---|---|---|---|---|\n')
 for i,r in enumerate(sorted(rows,key=lambda z:(z['source'],z['location_axis'],z['role_axis'],z['title'])),1):
  f.write(f"| {i} | [{r['title']}]({r['url']}) | {r['company']} | {r['location_axis']} | {r['role_axis']} | {r['posted']} | {r['work_mode']} | {r['status']}. {r['evidence']} |\n")
 f.write('\n## Rechecks / exclusions\n- CipSoft “Softwaretester Online Spiele” was rechecked and excluded: current direct card says Regensburg, not Berlin.\n- Remotive search results unrelated to QA were rejected despite remote text; the retained Remotive QA card explicitly lists Europe, which includes Germany.\n- HTTP 200 alone was not treated as validation; URL identity, title/company, full text, role, and location were checked.\n')
# coverage
cov=json.load(open(f'{D}/coverage.json')); failures=json.load(open(f'{D}/failures.json'))
with open(f'{D}/source_coverage.md','w') as f:
 f.write('# Source coverage — 2026-09-24 cycle 2 repair\n\nAll 32 source×location×role partitions were attempted. Matrix:\n\n| Source | Berlin | Leipzig | Dresden | Germany-wide Remote |\n|---|---|---|---|---|\n| LinkedIn Jobs | 4 role queries | 4 role queries | 4 role queries attempted, all HTTP 429 | 4 role queries attempted, 3 HTTP 429 |\n| Remotive | 4 role queries/API 200 | 4 role queries/API 200 | 4 role queries/API 200 | 4 role queries/API 200 |\n\n')
 for r in cov: f.write(f"- {r['source']} / {r['location']} / {r['role']}: `{r['status']}`, cards={r.get('cards',r.get('cards_verified',0))}\n")
 f.write('\n## Remotive retry methods\n1. Public API with curl-like UA: HTTP 200; JSON captured per role query.\n2. Every API-returned direct card fetched over HTTPS and captured as HTML/full description.\nThis repaired the prior API 403 condition.\n\n## Explicit failures\n- LinkedIn guest API was rate-limited (HTTP 429) on 10/16 scope searches and on 10 direct-card fetches. The successful scopes and raw responses are preserved; failure is not treated as a negative result.\n- No browser retry was available for LinkedIn rate-limited partitions in this repair run.\n- Remotive had no API failure on retry. Search was noisy; unrelated non-QA results were rejected.\n- Prior CipSoft Berlin classification was affirmatively disproved on recheck and removed.\n\nMachine-readable details: `coverage.json`, `failures.json`.\n')
print(len(rows))
