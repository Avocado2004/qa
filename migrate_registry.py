#!/usr/bin/env python3
"""Migrate the legacy source registry to the controller's schema-2 contract.

The source file is backed up before any write. Historical evidence is retained;
legacy fields remain available under `legacy` so no audit data is lost.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REG = ROOT / "source_registry.json"
SCHEMA = 2

LISTING = {
    "linkedin.com": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=QA&location=Germany&f_TPR=r2592000&start=0",
    "arbeitsagentur.de": "https://www.arbeitsagentur.de/jobsuche/",
    "stepstone.de": "https://www.stepstone.de/jobs/qa-test/in-berlin.html",
    "xing.com": "https://www.xing.com/jobs/search",
    "hitmarker.net": "https://hitmarker.net/jobs",
    "remotive.com": "https://remotive.com/api/remote-jobs?search=QA",
    "arbeitnow.com": "https://www.arbeitnow.com/api/job-board-api",
    "germantechjobs.de": "https://germantechjobs.de/rss",
    "eurotechjobs.com": "https://www.eurotechjobs.com/jobs/test_analyst",
    "adzuna.de": "https://www.adzuna.de/search?q=QA&loc=587664",
}
ADAPTERS = {
    "linkedin.com": "linkedin_v1", "arbeitsagentur.de": "arbeitsagentur_v1",
    "stepstone.de": "stepstone_v1", "xing.com": "xing_v1", "hitmarker.net": "hitmarker_v1",
    "remotive.com": "remotive_v1", "arbeitnow.com": "arbeitnow_v1",
    "germantechjobs.de": "rss_v1", "eurotechjobs.com": "html_v1", "adzuna.de": "adzuna_v1",
}

def atomic(path: Path, data):
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def main():
    old = json.loads(REG.read_text(encoding="utf-8"))
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / f"source_registry.schema1.{stamp}.json"
    shutil.copy2(REG, backup)
    sources=[]
    for item in old.get("sources", []):
        domain=item.get("domain") or item.get("name")
        if domain not in LISTING:
            continue
        sources.append({
            "id": domain, "name": item.get("name", domain), "domain": domain,
            "type": item.get("type", "unknown"), "status": item.get("status", "active"),
            "adapter": ADAPTERS[domain], "adapter_version": 1,
            "listing_url": LISTING[domain],
            "detail_url_pattern": item.get("query_or_url_pattern"),
            "preferred_methods": item.get("access_methods", ["http"]),
            "fallback_methods": item.get("access_methods", ["http"]),
            "direct_card_domains": [domain], "config": {},
            "evidence": {"first_seen": item.get("first_seen"), "last_verified": item.get("last_verified"),
                          "last_preflight": None, "last_success": None, "url": item.get("evidence_url")},
            "legacy": item,
        })
    if len(sources) != len(LISTING):
        raise SystemExit(f"migration refused: expected {len(LISTING)} sources, got {len(sources)}")
    data={"schema_version":SCHEMA, "registry_revision":1, "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
          "sources":sources, "retired_sources":old.get("retired_sources",[]), "history":old.get("scout_history",[]),
          "migration":{"from_schema":old.get("schema_version"), "backup":str(backup)}}
    atomic(REG, data)
    print(json.dumps({"status":"MIGRATED","sources":len(sources),"backup":str(backup)}))
if __name__ == "__main__": main()
