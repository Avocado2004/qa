#!/usr/bin/env python3
import json, time
from pathlib import Path

root = Path('/opt/data/results/cycles/2026-09-24_cycle-3')
state_path = root / 'state.json'
active_path = Path('/tmp/qa-vacancy-daily-controller.active.json')
last = None
started = time.time()
while time.time() - started < 86400:
    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
    except Exception:
        time.sleep(10)
        continue
    snapshot = {
        'cycle_id': state.get('cycle_id'),
        'stage': state.get('stage'),
        'status': state.get('status'),
        'publication_allowed': state.get('publication_allowed'),
        'worker_pool': state.get('worker_pool'),
        'unresolved_workers': state.get('unresolved_workers'),
        'blocked_reason': state.get('blocked_reason'),
    }
    if snapshot != last:
        print(json.dumps({'event': 'state_change', **snapshot}, ensure_ascii=False), flush=True)
        last = snapshot
    if state.get('stage') == 'PUBLISHED' or state.get('status') in {'COMPLETE', 'BLOCKED', 'FAILED'}:
        if not active_path.exists() or json.loads(active_path.read_text()).get('cycle_id') != '2026-09-24_cycle-3':
            print(json.dumps({'event': 'terminal', 'final': snapshot}, ensure_ascii=False), flush=True)
            raise SystemExit(0)
    time.sleep(15)
print(json.dumps({'event': 'monitor_timeout', 'final': last}, ensure_ascii=False), flush=True)
raise SystemExit(2)
