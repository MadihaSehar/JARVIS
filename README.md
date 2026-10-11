# J.A.R.V.I.S.

**Joint AI Reconnaissance, Vulnerability Intelligence and Security**

A modular, AI-assisted cybersecurity workstation for authorized reconnaissance
and safe, evidence-based web security testing. Local-first: AI inference runs
on-device via Ollama by default, with every AI-proposed action re-validated
by deterministic, AI-independent policy logic before it can affect anything.

## Architecture

- **Backend:** FastAPI + SQLAlchemy 2.x + Alembic, SQLite by default
- **Frontend:** Next.js 16 (App Router) + React 19 + Tailwind v4
- **AI:** Ollama (local, default) or OpenAI/Anthropic (optional, disabled by
  default) behind a single provider interface
- **Real-time updates:** WebSocket event stream, backed by a persisted event
  log so a reconnecting client recovers full history, not just new events

### Safety model

Two things are true regardless of what the AI does or says:

1. **Scope enforcement is deterministic and AI-independent.** Every target is
   format-validated and checked against a hardcoded blocklist (private,
   loopback, link-local, reserved, multicast, and cloud metadata addresses)
   before anything is scanned -- a prompt can't talk its way around this.
2. **AI output is never trusted directly.** Every AI-proposed action passes
   through `app/orchestration/policy.py`'s hard rules (allowed action types,
   confidence range, scope membership, budget). If the AI is unreachable or
   returns unusable output, the system falls back to a fully deterministic
   ranking (`app/orchestration/fallback.py`) and says so in the event log.

## Running it

**Backend** (port 8001):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend** (port 3000):
```bash
cd frontend
npm run dev
```

Open `http://<this machine's LAN IP>:3000` from a browser on the same
network (the frontend resolves its API base URL from `window.location`, so
it works correctly from a host machine reaching into a VM).

### Configuration

All config lives in `backend/.env` (see `backend/.env.example`). Nothing
secret is ever returned by `/api/settings` -- API keys are reported only as
`*_api_key_configured: true/false`.

Key settings:
- `OLLAMA_BASE_URL`, `OLLAMA_DEFAULT_MODEL` -- local AI (default path)
- `ENABLE_CLOUD_AI` -- `false` by default; set `true` plus `CLOUD_AI_PROVIDER`
  (`openai` or `anthropic`) and the matching API key to use a cloud provider
  instead. Restart the backend after changing this.
- `ENABLED_SCANNERS` -- comma-separated list of active security scanners;
  empty/unset enables all registered scanners
- `ORCHESTRATION_BUDGET` -- max AI/fallback action proposals per scan

## Tests

```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt   # once
pytest tests/ -v
```

44 regression tests cover: scope enforcement (the safety-critical path),
the deterministic policy gate, the no-AI fallback, finding deduplication,
the scan lifecycle state machine, and report generation (including HTML
output escaping, verified against a deliberately malicious finding
observation). Tests run against an isolated SQLite file, never the real
`jarvis.db`.

Restart/recovery has been live-verified: stopping and restarting the
backend against real scan data (7 scans, 949 assets) preserved every scan,
its status, and its full asset/finding/event history exactly.

## What's implemented vs. what's a stub

Honestly labeled in the GUI itself (Tool Integrations, and the relevant
nav sections), but to summarize:

**Implemented:** DNS enumeration, passive subdomain discovery (crt.sh),
HTTP service probing, security header / cookie-flag checks, canary-based
reflected-input detection, AI-assisted + deterministic-fallback action
orchestration, report export (JSON/Markdown/HTML).

**Stubbed (honest "not yet implemented" pages, no fake data):** endpoint
discovery (crawling), directory/file brute-forcing, threat intelligence
enrichment. These were named in the original spec but would need
additional external tools (Katana, FFUF, a CVE/threat-intel source) and,
for brute-forcing specifically, careful rate-limiting work before they
belong in an authorized-testing tool.

**Named in spec, not integrated:** Subfinder, Amass, dnsx, the Go `httpx`,
Nuclei, OWASP ZAP. Current reconnaissance uses Python-native equivalents
(dnspython, crt.sh, httpx the Python library) instead.

## Known limitations

- `llama3.2:3b` (the default local model) does not reliably produce valid
  JSON for the orchestration prompt on this hardware; the deterministic
  fallback activates correctly when that happens and is clearly logged as
  such in the scan's event trail. A larger/instruction-tuned model would
  likely improve this.
- The WebSocket event stream is a 1-second DB-polling bridge, not true
  pub/sub -- fine at this scale, would need rework for many concurrent
  scans.
- Duplicate asset `value`s across different `asset_type`s (e.g. the same IP
  resolved as both a DNS A-record and a plain IP asset) can collide in the
  orchestrator's internal attribution map. Cosmetic only -- doesn't affect
  scope enforcement or findings.
- `HEAD` requests to the report export endpoint return 405 (FastAPI doesn't
  auto-generate `HEAD` for a custom `Response`-returning route); plain `GET`
  works correctly. Not fixed since nothing in the app issues `HEAD` requests.
- Cloud AI provider/model changes require editing `.env` and restarting the
  backend -- there's no in-app settings writer, by design (keeps secrets
  out of the database and out of git).
