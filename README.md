# Financial GPS

A humorous financial decision simulator for Canadian professionals. Combines a transaction-based budget tracker with a Canadian FIRE planning engine in one unified Streamlit app.

## Stack

- Python · Streamlit · SQLite (PostgreSQL in v2)
- Three-layer architecture: `fire_engine/` (L1) → services (L2) → Streamlit UI (L3)

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501), register an account, and explore the sidebar navigation.

## Project Structure

```
financial_gps/
├── app.py              # Streamlit entry point
├── auth/               # Register + login
├── pages/              # UI screens (L3)
├── budget/             # Budget services (L2)
├── bridge/             # CSV → FIRE data bridge (L2)
├── fire_engine/        # Pure Python FIRE engine (L1)
├── shared/             # Database, models, utils
└── tests/
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect the repo, set main file to `app.py`
4. Deploy

## Deployment Notes

- The current app uses SQLite, which is fine for local development and lightweight demos.
- For shared testing with persistent multi-user data, move storage to a hosted database such as PostgreSQL or Supabase.
- A browser refresh resets Streamlit session state, but database-backed data remains.

## Build Status

**Phase 0 — Foundation** ✓
- Database schema (budget + FIRE tables)
- Auth (email/password with bcrypt)
- Sidebar navigation skeleton
- CRA 2026 parameters + loader

**Current:** Phase 7 — Onboarding, polish, settings expansion, and deploy-readiness cleanup

See `financial_gps_unified_spec.md` for the full product spec and build plan.
