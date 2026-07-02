# RawLead

AI-assisted lead intelligence for freelancers: multi-source ingest, skill match scoring, and fast response workflow.

Live product: [rawlead.ru](https://rawlead.ru)

## Product Summary

RawLead aggregates opportunities from FL/Kwork/Telegram, filters noise, scores relevance by stack, and helps users react faster.

Core value:
- one feed instead of multiple source tabs
- compatibility score per lead
- tiered access flow (trial -> feed -> pro)
- faster outreach workflow with AI-assisted draft path

## What Is Implemented

- Multi-source ingest pipeline (web + Telegram)
- FastAPI backend with subscription/tier logic
- Next.js frontend (`/lenta`, `/pricing`, `/cabinet`)
- Paywall and checkout integration
- Match push notifications in Telegram
- Operational deploy scripts and smoke check flow

## Architecture (High-Level)

- **Frontend:** Next.js static export (`rawlead-next/`)
- **Backend:** FastAPI (`src/`)
- **Data:** Postgres
- **Automation:** Python workers/parsers
- **Infra:** VPS + systemd + nginx
- **Messaging:** Telegram bot + Telethon accounts

## My Engineering Focus (Interview Context)

- designed safe rollout strategy (feature flags, smoke-first deploys)
- implemented paywall/tier behavior and edge-case handling
- hardened flow for anon vs expired-trial states
- connected product UX decisions to backend access control
- maintained deploy reliability and rollback readiness

## Repository Map

- `src/` - backend logic and domain services
- `rawlead-next/` - web app
- `scripts/` - deploy/ops tooling
- `tests/` - automated checks
- `docs/` - product and engineering documentation

Primary docs:
- docs index: [`docs/README.md`](docs/README.md)
- product vision: [`docs/team/product/PRODUCT_VISION.md`](docs/team/product/PRODUCT_VISION.md)
- roadmap: [`docs/team/architect/ROADMAP.md`](docs/team/architect/ROADMAP.md)
- current prod facts: [`docs/team/common/PROD_FACTS.md`](docs/team/common/PROD_FACTS.md)

## Quick Start (Local)

```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
.venv\Scripts\python.exe src/main.py
```

Frontend local:

```powershell
cd rawlead-next
npm install
npm run dev
```

## Interviewer Notes

This repository includes both product code and internal operational docs.
For technical review, start with:

1. `src/` (core backend flows)
2. `rawlead-next/` (user-facing behavior)
3. `tests/` (edge-case coverage)
4. `docs/team/common/PROD_FACTS.md` (live state snapshot)
