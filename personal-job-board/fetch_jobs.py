#!/usr/bin/env python3
"""Personal, non-commercial FreeHire API snapshot. No credentials required."""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://freehire.me/api/v1/jobs/search"
ROLES = ["Product Manager", "AI Product Manager", "Program Manager", "Business Analyst", "Product Analyst"]
OUT = Path(os.environ.get("JOB_SNAPSHOT_PATH", "personal-job-board/jobs.json"))

def fetch(role):
    params = urllib.parse.urlencode({
        "q": role, "countries": "US", "open_within_days": "14",
        "sort": "posted_at", "order": "desc", "limit": "50",
    })
    req = urllib.request.Request(BASE + "?" + params, headers={
        "Accept": "application/json", "User-Agent": "personal-freehire-board/1.0"
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                payload = json.load(response)
            if not isinstance(payload.get("data"), list):
                raise ValueError("Unexpected FreeHire response")
            ignored = (payload.get("meta") or {}).get("ignored_params") or []
            if ignored:
                print(f"Warning: ignored API parameters for {role}: {ignored}", file=sys.stderr)
            return payload["data"]
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt == 2:
                raise RuntimeError(f"API request failed for {role}: {exc}") from exc
            time.sleep(2 ** attempt)
    return []

def main():
    unique = {}
    for role in ROLES:
        for job in fetch(role):
            if not isinstance(job, dict):
                continue
            key = job.get("public_slug") or job.get("url")
            if key:
                unique[key] = job
    jobs = sorted(unique.values(), key=lambda j: j.get("posted_at") or "", reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "FreeHire public API; personal non-commercial use only",
        "count": len(jobs), "jobs": jobs,
    }, ensure_ascii=False), encoding="utf-8")
    tmp.replace(OUT)
    print(f"Fetched {len(jobs)} unique jobs into {OUT}")

if __name__ == "__main__":
    main()
