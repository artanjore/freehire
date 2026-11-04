# Personal job board (non-commercial)

This optional, independent integration uses FreeHire's existing public API. It does **not** start FreeHire's Go crawlers, PostgreSQL, Redis, or Meilisearch.

## Scheduled refresh

GitHub Actions runs `fetch_jobs.py` every three hours (UTC) and on manual dispatch. Each run requests the newest US jobs matching five product/business roles, deduplicates them, and uploads a JSON artifact retained for seven days. GitHub Actions cron runs can be delayed; the schedule is not an exact SLA. The artifact is **not** committed to this public repository or published to GitHub Pages.

Go to **Actions → Personal job board refresh → Run workflow** to test. Download the `personal-job-matches` artifact from a successful run. No API key or paid hosting is needed for this personal-use integration, subject to GitHub Actions limits and FreeHire API usage terms.

## Local test

```bash
python3 personal-job-board/fetch_jobs.py
```

The output is written to `personal-job-board/jobs.json` (ignored by git; do not publish third-party job data without verifying licensing). Change `ROLES` and search parameters in the script to customize the feed. `open_within_days=14` means first observed by FreeHire within 14 days, rather than trusting reposted dates.

## Hosting / dashboard

This PR adds the cloud scheduled data integration, **not a publicly hosted dashboard**. GitHub Actions artifacts are intended for private download by a repository collaborator, not public site hosting. A subsequent deployment can use a compliant backend with authenticated access or fetch the public API live in a browser. Do not redistribute the FreeHire API dataset as a public product without checking its API/data licensing.
