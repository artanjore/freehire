# Personal Cloudflare Pages job dashboard

A static, mobile-friendly job search dashboard that queries FreeHire's public search API directly. It is isolated from the upstream Go/SvelteKit application and requires no server, API key, or build tooling.

## Features

- US-based searches for Product Manager, AI Product Manager, Program Manager, Business Analyst, and Product Analyst
- Search, role and work-style filters; 14-day first-seen freshness window
- Save jobs and track Applied / Interviewing / Rejected / Offer in browser localStorage
- Three-hour browser cache and manual refresh
- Accessible responsive layout and safe outbound application links

## Deploy to Cloudflare Pages

1. In Cloudflare, open **Workers & Pages → Create → Pages → Connect to Git**.
2. Authorize GitHub and select `artanjore/freehire`.
3. Set production branch to `main`.
4. Build command: `exit 0` (or leave blank if Cloudflare permits).
5. Build output directory: `personal-job-board/dashboard`.
6. Deploy and open the assigned `*.pages.dev` URL.

The repository contains a larger upstream application, but Pages will publish only this static subdirectory. No secrets are needed.

**Important:** The existing GitHub Actions collector creates downloadable workflow artifacts, not a public JSON endpoint. This dashboard intentionally fetches FreeHire's API from the browser instead of exposing workflow artifacts. The dashboard cache is refreshed when visited after three hours; it does not perform background browser polling while closed. The independent GitHub Actions collector continues to run every three hours. API availability, browser CORS, and usage limits apply. The public FreeHire API is licensed for personal, non-commercial use; check the provider's data licensing before offering a public product to other users.

Saved jobs and statuses stay in the current browser only. They are not backed up or synced between devices. If you need account-based sync, add an authenticated database in a follow-up change.

## Test locally

```bash
cd personal-job-board/dashboard
python3 -m http.server 8000
```

Visit http://localhost:8000 and test search, saving, and refresh. This PR does not provision a Cloudflare account or deploy the site automatically.
