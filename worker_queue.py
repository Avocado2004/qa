#!/usr/bin/env python3
"""Atomic file-backed queue for durable vacancy worker sessions."""
from __future__ import annotations
import argparse, contextlib, fcntl, json, os, tempfile
from pathlib import Path

def atomic(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(FileNotFoundError): os.unlink(tmp)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('queue'); ap.add_argument('worker_id'); ap.add_argument('action', choices=['claim','heartbeat','complete','fail','reclaim','scale','retry'])
    ap.add_argument('--error', default=''); ap.add_argument('--count', type=int); a=ap.parse_args()
    if a.worker_id == 'controller' and a.action not in {'reclaim', 'scale'}:
        raise SystemExit('controller may only use reclaim or scale')
    qpath=Path(a.queue); lockpath=qpath.with_suffix('.lock')
    with lockpath.open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q=json.loads(qpath.read_text())
        now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        if a.action == 'scale':
            if a.count is None or not 1 <= a.count <= 16:
                raise SystemExit('--count must be between 1 and 16')
            q['desired_workers'] = a.count
            atomic(qpath,q); print(json.dumps(q)); return
        if a.action == 'reclaim':
            for j in q['jobs']:
                if j.get('state') == 'claimed' and j.get('pid') and not Path(f'/proc/{j["pid"]}').exists():
                    j.update(state='pending', owner=None, pid=None, next_action='resume_checkpoint', reclaimed_at=now)
            atomic(qpath,q); print(json.dumps(q)); return
        if a.action == 'claim':
            for j in q['jobs']:
                if j.get('state') == 'pending':
                    j.update(state='claimed', owner=a.worker_id, pid=None, claimed_at=now,
                             heartbeat_at=now, next_action='process_from_checkpoint')
                    atomic(qpath,q); print(json.dumps(j, ensure_ascii=False)); return
            print(json.dumps({'state':'empty'})); return
        if a.action == 'retry':
            cur=next((j for j in q['jobs'] if j.get('source_id') == a.worker_id and j.get('state') == 'failed'), None)
            if cur is None: print(json.dumps({'state':'not_retryable'})); return
            cur.update(state='claimed', owner='recovery', pid=None, claimed_at=now, heartbeat_at=now,
                       next_action='resume_checkpoint', error=None, recovery_owner='recovery')
            atomic(qpath,q); print(json.dumps(cur, ensure_ascii=False)); return
        cur=next((j for j in q['jobs'] if j.get('owner') == a.worker_id and j.get('state') == 'claimed'), None)
        if cur is None: print(json.dumps({'state':'not_owned'})); return
        if a.action == 'heartbeat': cur['heartbeat_at']=now
        elif a.action == 'complete': cur.update(state='complete', finished_at=now, next_action=None)
        elif a.action == 'fail': cur.update(state='failed', error=a.error, finished_at=now, next_action='resume_checkpoint')
        atomic(qpath,q); print(json.dumps(cur, ensure_ascii=False))
if __name__ == '__main__': main()
