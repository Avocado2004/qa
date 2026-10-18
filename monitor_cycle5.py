#!/usr/bin/env python3
import json,time
from pathlib import Path
root=Path('/opt/data/results/cycles/2026-09-24_cycle-5'); sp=root/'state.json'
last=None
for _ in range(120):
    try:
        s=json.loads(sp.read_text())
        view={k:s.get(k) for k in ('cycle_id','stage','status','publication_allowed','blocked_reason')}
        if view != last:
            print(json.dumps({'event':'state_change',**view},ensure_ascii=False),flush=True); last=view
        if s.get('status') not in {'RUNNING','BLOCKED'}:
            break
    except Exception as e:
        print(json.dumps({'event':'monitor_error','error':str(e)}),flush=True)
    time.sleep(5)
print(json.dumps({'event':'monitor_end','last':last},ensure_ascii=False),flush=True)
