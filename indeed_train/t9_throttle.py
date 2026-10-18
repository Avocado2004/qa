"""Train step 9: how long does the throttle last, and what is the safe cadence?

Burst probing got this IP throttled completely -- even the homepage answers 403
now. Before tuning anything else the duration has to be measured, otherwise any
cadence I pick is a guess. Log one probe every N minutes until access returns.

Run detached; it writes a line per probe to throttle.log.
"""
import sys
import time

sys.path.insert(0, "/opt/data/qa-vacancy-project")
from indeed_client import Indeed

MINUTES = 20
PROBE_URL = "https://de.indeed.com/jobs?q=QA+Engineer&l=Berlin&start=0"


def main():
    cli = Indeed(lo=1.0, hi=1.0)
    log = open("throttle.log", "a", buffering=1, encoding="utf-8")
    log.write(f"\n=== измерение троттлинга, старт {time.strftime('%H:%M:%S')} ===\n")
    for attempt in range(1, 40):
        st, html = cli.get(PROBE_URL, attempts=1)
        size = len(html) // 1024
        line = (f"{time.strftime('%H:%M:%S')}  попытка {attempt:2d}  "
                f"HTTP {st:3d}  {size:5d}KB  cookies={len(list(cli.jar))}")
        print(line, flush=True)
        log.write(line + "\n")
        if st == 200 and size > 100:
            log.write("ДОСТУП ВОССТАНОВЛЕН\n")
            log.close()
            return 0
        time.sleep(MINUTES * 60)
    log.write("не восстановился за отведённое время\n")
    log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
