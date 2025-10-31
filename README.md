# huproof — Human-in-the-Loop ZK Auth (PoC)

Privacy-preserving, unlinkable liveness proof at enrollment/login using keystroke dynamics.

- Biometrics stay on-device; server stores only commitments and verifies ZK proofs
- Proofs are bound to nonce/time/origin; replay-resistant and unlinkable across sites

## Quickstart with uv

1) Install Python >= 3.11 and uv (`https://github.com/astral-sh/uv`).
2) Copy env file: `cp env.example .env`
3) Create venv and install deps from `pyproject.toml`:
   - `uv sync --all-extras`
4) Run the API:
   - `uv run uvicorn huproof.app:app --reload`

The API serves on `http://127.0.0.1:8000`.

## Web demo

1) Build circuits (see `circuits/README.md`).
2) Copy artifacts into web public directory (so Vite can serve them):
   - `cp -r circuits/build web/public/artifacts`
3) Install web deps and run dev server:
   - `cd web && npm install && npm run dev`
4) Open the Vite URL (default `http://localhost:5173`).

Notes:
- During early development, set `BYPASS_ZK_VERIFY=1` in `.env` to skip proof verification.
- The demo enrolls a user and stores the template locally; then runs a login with that template.

## Configuration

- `APP_SECRET` — JWT signing secret (required)
- `DB_URL` — database URL (default: `sqlite:///./dev.db`)
- `NONCE_TTL_S` — seconds nonces are valid (default: `120`)
- `TAU_DEFAULT` — default threshold for distance check (default: `400`)
- `ORIGIN` — expected web origin during development (default: `http://localhost:5173`)

## Repo layout

- `huproof/` — Python package (FastAPI app, config, core)
- `circuits/` — Circom circuits and build artifacts (PoC)
- `web/` — Web client (TypeScript) for keystroke capture and proving (PoC)
- `tests/` — pytest suite
- `scripts/` — helper scripts

## Status

This is a PoC scaffold. API endpoints are stubbed; circuits and browser proving are implemented in later tasks.

## License

MIT

## Development notes

- Use `BYPASS_ZK_VERIFY=1` during early development to skip proof verification.
- See `circuits/README.md` for building the Groth16 artifacts (`verification_key.json`).
- Endpoints:
  - `GET /api/enroll/start` → `{ challenge, nonce, origin_hash, tau, timestamp }`
  - `POST /api/enroll/finish` → `{ success, user_id }`
  - `GET /api/login/start?user_id=...` → `{ challenge, nonce, origin_hash, tau, timestamp, commitment }`
  - `POST /api/login/finish` → `{ success, token }`
