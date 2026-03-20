# Clinical Trial Monitoring System — CLAUDE.md
Protocol NVX-1218.22 | NovaPlex-450 in Advanced NSCLC | Sponsor: NexaVance Therapeutics Inc.

## CRITICAL RULES — Read First

1. **Always edit files in the main repo** (`clinical-trial-data-layer/`), never in the worktree (`.claude/worktrees/brave-joliot/`). The worktree is a Claude-internal branch — edits there don't deploy.
2. **Never query the worktree DB** — it is always 0 bytes. The real DB is `clinical_trial.db` at the main repo root (2.9MB+).
3. **Deploy = push to master** → Railway auto-deploys in ~3–5 min. Never push to the worktree branch.
4. **Frontend edits must be copied to main repo** if edited in worktree — use `cp` then commit from main repo.

## Architecture

| Layer | File/Dir | Notes |
|---|---|---|
| Backend | `api_sqlite.py` | FastAPI, ~2,700 lines, 50+ endpoints, port 8001 |
| Frontend | `frontend/src/App.jsx` | React/Vite, ~3,000 lines, port 3000 |
| CSS | `frontend/src/App.css` | Full CSS custom property system |
| DB (main) | `clinical_trial.db` | SQLite, 2.9MB, 101 subjects, 5 sites — re-seeded on deploy |
| DB (logs) | `access_logs.db` / `/data/access_logs.db` | Persistent across deploys via Railway Volume |
| Rules engine | `rules_engine/` | Hybrid LLM + deterministic, YAML configs in `rule_configs/` |
| Rule configs | `rule_configs/*.yaml` | 6 files: exclusion, inclusion, lab_safety, ae_rules, deviation, endpoint |
| Dockerfile | `Dockerfile` | Used by Railway (not nixpacks) |
| Railway config | `railway.toml` | Volume mount at `/data` for persistent logs |

## Local Dev

```bash
# Backend (from main repo root — not worktree)
cd C:/Users/Sandya/Downloads/ProjectsAI/clinical-trial-data-layer
uvicorn api_sqlite:app --port 8001

# Frontend
cd frontend && npm run dev   # port 3000, proxies /api → localhost:8001
npm run build                # verify build before committing
```

## Deploy Flow

```bash
cd /c/Users/Sandya/Downloads/ProjectsAI/clinical-trial-data-layer
git add <files>
git commit -m "message"
git push origin master       # triggers Railway auto-deploy
```

- **Live URL:** https://web-production-b4df.up.railway.app
- **GitHub:** https://github.com/virupakshb/TrialMonitor (master branch)
- **Railway project:** exemplary-curiosity

## Current Data State

- **101 subjects** (100 generated + 1 manual: subject 101-901)
- **5 sites:** site_101 (Memorial Cancer Center, US) through site_105 (Singapore Medical Research)
- **Subject 101-901** — Safety case added 2026-02-21. Female, 61, Asian, Site 101, Discontinued due to immune myocarditis/cardiac arrest (G5 SAE). Has 4 visits, 30 labs, 4 AEs.

## Key API Endpoints

- `GET /api/statistics` — dashboard summary
- `GET /api/subjects` — subject list
- `GET /api/ctms/sites-overview` — all sites with risk/TMF/findings
- `GET /api/ctms/site/{site_id}` — site detail + monitoring visits
- `POST /api/chat` — CRA Copilot (intent-routed, RAG-gated)
- `GET /api/admin/access-logs` — who accessed, when, what questions asked
- `GET /api/usage` — Anthropic token usage this session

## CRA Copilot — Token Optimisation (implemented 2026-02-26)

The `/api/chat` endpoint uses intent-based routing to cut input tokens ~60-70%:
- **Intent detection:** keyword matching classifies as `_is_data_q` or `_is_protocol_q`
- **RAG (voyage-3 embed):** only called for protocol questions, skipped for data/findings
- **Protocol body:** only included for protocol questions
- **All-sites summary:** only in study-wide mode (no site selected)
- **History:** last 3 messages (was 6)
- **Timeouts:** LLM=25s, RAG embed=8s, max_tokens=800

## UX Design System

Enterprise Veeva/Medidata-inspired. All edits must follow these conventions:

- **Font:** Inter (Google Fonts, loaded in `frontend/index.html`)
- **Layout:** Fixed left sidebar (220px, `--color-navy`) + 48px topbar + breadcrumbs
- **Key CSS tokens:**
  - `--color-navy: #0A2540` (sidebar, banners)
  - `--color-blue: #2D6BE4` (primary action, links)
  - `--color-blue-dk: #1A56D6`
  - `--color-surface: #F4F6F9` (page background)
  - `--color-critical: #C0392B` / `--color-major: #C96A00` / `--color-minor: #1E7E4A`
  - `--color-text: #1A2332` / `--color-muted: #6B7A8D` / `--color-border: #DDE2EA`
- **No emoji** in nav, banners, or data tables — use text indicators with semantic color
- **No purple** — `#667eea`, `#764ba2`, `#8b5cf6` are banned
- **Banners:** solid `var(--color-navy)` + `borderLeft: 4px solid var(--color-blue)`, never gradients
- **Badges:** `.badge-critical/.badge-major/.badge-minor/.badge-info/.badge-neutral`

## Nav Views

Dashboard | Subjects | Rules | Execute | Results | Violations | My Sites | Copilot (sidebar)

## Access Logging

- Middleware logs every request to `usage_logs` table in `access_logs.db`
- Logs: IP (from X-Forwarded-For), user agent, endpoint, method, status, response_ms, Copilot questions, timestamp
- View at: `/api/admin/access-logs`
- **Railway Volume** (`/data`) must be created manually in Railway dashboard for persistence across redeploys

## Known Gotchas

- `frontend/dist/` is gitignored — Railway builds from source. Never commit dist files.
- Railway Volume for `/data` not yet created — access logs reset on each deploy until done
- worktree `clinical_trial.db` is always empty (0 bytes) — never use for queries
- Copilot may timeout on Railway if RAG + LLM > 25s — timeouts are now set
- `api/rules_api.py` is the OLD backend — always use `api_sqlite.py`
- When editing `App.jsx` in worktree, must `cp` to main repo before committing
