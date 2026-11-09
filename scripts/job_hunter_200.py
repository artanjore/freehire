#!/usr/bin/env python3
"""Job Hunter 200: read-only discovery from freehire public API.
Produces a CSV artifact; does not submit applications or commit private tracking data.
"""
import csv, datetime as dt, json, os, re, urllib.parse, urllib.request
from pathlib import Path

API = os.getenv("JOB_HUNTER_API", "https://freehire.me/api/v1/jobs")
TERMS = ["product manager", "ai product manager", "product owner", "business analyst", "program manager", "product analyst", "forward deployed"]
SIGNALS = ["llm", "ai agent", "voice agent", "langsmith", "a/b testing", "experimentation", "fintech", "roadmap", "stakeholder", "agile", "sql", "product analytics", "generative ai", "prompt engineering"]
BLOCK = ["no sponsorship", "not sponsor", "cannot sponsor", "unable to sponsor", "no visa sponsorship", "not eligible for sponsorship", "will not sponsor", "no h-1b", "no h1b"]
FIELDS = ["found_at", "posted_at", "company", "title", "location", "source", "url", "match_score", "matched_keywords", "resume_customization_suggestion", "visa_status", "application_status"]

def fetch(query):
    params = urllib.parse.urlencode({"q": query, "limit": 100})
    req = urllib.request.Request(API + ("&" if "?" in API else "?") + params, headers={"User-Agent": "JobHunter200/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def extract(payload):
    data = payload.get("data", []) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        for key in ("jobs", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
        return []
    return data if isinstance(data, list) else []

def field(obj, *names):
    for name in names:
        val = obj.get(name)
        if isinstance(val, dict):
            val = val.get("name") or val.get("title") or val.get("url")
        if val:
            return str(val)
    return ""

def normalize(job):
    title = field(job, "title", "job_title", "name")
    company = field(job, "company_name", "company", "organization")
    url = field(job, "apply_url", "application_url", "url", "job_url")
    description = field(job, "description", "description_text", "body", "summary")
    location = field(job, "location", "location_name", "city")
    source = field(job, "source", "provider", "ats")
    return title, company, url, description, location, source

def posting_date(job):
    """Only accept dated postings; first-seen and updated dates are not proof."""
    raw = field(job, "posted_at", "published_at", "date_posted", "publication_date", "postedAt", "publishedAt")
    if not raw:
        return None
    try:
        if raw.isdigit():
            date = dt.datetime.fromtimestamp(int(raw) / (1000 if len(raw) >= 13 else 1), tz=dt.timezone.utc)
        else:
            date = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if date.tzinfo is None:
                date = date.replace(tzinfo=dt.timezone.utc)
        return date.astimezone(dt.timezone.utc)
    except (ValueError, OverflowError):
        return None

def main():
    seen, rows, errors = set(), [], []
    for term in TERMS:
        try:
            jobs = extract(fetch(term))
        except Exception as exc:
            errors.append(f"{term}: {exc}")
            continue
        for job in jobs:
            if not isinstance(job, dict):
                continue
            posted = posting_date(job)
            now = dt.datetime.now(dt.timezone.utc)
            if posted is None or posted > now or now - posted > dt.timedelta(hours=72):
                continue
            title, company, url, desc, location, source = normalize(job)
            if not title or not company or not url:
                continue
            if not any(x in title.lower() for x in ("product", "program", "business analyst", "forward deployed")):
                continue
            if not any(x in (location + " " + desc).lower() for x in ("united states", "usa", "remote", "new york", "new jersey", "california", "texas", "virginia", "washington", "massachusetts", "illinois", "arizona", "colorado", "pennsylvania", "connecticut", "florida", "georgia", "north carolina")):
                continue
            key = (company.lower(), title.lower(), location.lower(), url.split("?")[0])
            if key in seen:
                continue
            seen.add(key)
            content = (title + " " + desc).lower()
            if any(x in content for x in BLOCK):
                continue
            matched = [x for x in SIGNALS if x in content]
            score = min(100, 45 + len(matched) * 7)
            if score < 66:
                continue
            rows.append({
                "found_at": now.isoformat(), "posted_at": posted.isoformat(),
                "company": company, "title": title, "location": location, "source": source, "url": url,
                "match_score": score, "matched_keywords": "; ".join(matched),
                "resume_customization_suggestion": "Emphasize verified experience with: " + ", ".join(matched[:5]),
                "visa_status": "Unverified — employer and position-specific transfer eligibility must be checked",
                "application_status": "Research only — not applied",
            })
    rows.sort(key=lambda x: -x["match_score"])
    out = Path("job-hunter-output")
    out.mkdir(exist_ok=True)
    with (out / "high_fit_jobs.csv").open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows[:200])
    (out / "run_summary.json").write_text(json.dumps({"qualified": len(rows), "exported": min(200,len(rows)), "errors": errors}, indent=2))
    if errors and len(errors) == len(TERMS):
        raise RuntimeError("All job API queries failed; inspect run_summary.json")

if __name__ == "__main__":
    main()
