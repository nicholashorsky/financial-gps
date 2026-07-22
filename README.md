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

## Development Test Login

For beta testing, you can enable a login shortcut that creates/uses `test@financialgps.local`.

On Linux or macOS, run the development launcher from the project directory:

```bash
./start_dev_app.sh
```

The launcher uses `.venv`, enables the beta test login for that process, starts Streamlit, and opens the app in your browser. Press `Ctrl+C` in the terminal to stop it.

On Windows, double-click the launcher:

```text
start_dev_app.bat
```

Local PowerShell:

```powershell
$env:FINANCIAL_GPS_TEST_LOGIN="1"
streamlit run app.py
```

Streamlit Community Cloud secrets:

```toml
[dev]
allow_test_login = true
```

Do not enable this shortcut for a real public test with personal financial data.

### Environment variables

| Variable | Development | Production |
| --- | --- | --- |
| `FINANCIAL_GPS_ENV` | `development` (default) | Set to `production` |
| `FINANCIAL_GPS_TEST_LOGIN` | Set to `1` only for synthetic local testing | Must be unset; production mode ignores it |

Production deployments should store secrets in the hosting provider rather than the repository. When `FINANCIAL_GPS_ENV=production`, the Beta Tester shortcut remains disabled even if its development flag is accidentally present.

## Development Tools

Install application and development dependencies into the project virtual environment:

```bash
.venv/bin/pip install -r requirements-dev.txt
```

Run Ruff to check the Python source:

```bash
.venv/bin/ruff check .
```

Run tests and coverage:

```bash
.venv/bin/pytest
.venv/bin/pytest --cov=. --cov-report=term-missing
```

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

## Beta Test With Sample Data

The repo includes the original RBC-style sample plus eight fictional personas documented in [`csv samples/README.md`](csv%20samples/README.md). All are synthetic and intended for product validation.

> **Synthetic-data beta:** Do not upload real bank exports or enter real personal financial information. Beta data may be reset without notice and has no recovery guarantee. See the [Beta Data and Storage Policy](docs/BETA_DATA_POLICY.md).

Suggested beta smoke path:

1. Register a fresh test account
2. Open Spending
3. Upload `csv samples/RBC SAMPLE CSV.csv`
4. Import transactions
5. Check Home, Spending, Forecast, Goals, FIRE Profile, FIRE Forecast, and Data Quality

Import one persona per fresh test account so histories remain isolated and results are easier to compare.

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect the repo, set main file to `app.py`
4. Deploy

## Deployment Notes

- The current SQLite deployment is approved only for local use, demos, and the invited synthetic-data beta described in the [Beta Data and Storage Policy](docs/BETA_DATA_POLICY.md).
- Managed PostgreSQL, versioned migrations, verified isolation, and tested backup/restore are required before accepting real financial data.
- A browser refresh resets Streamlit session state, but database-backed data remains.
- Set `FINANCIAL_GPS_ENV=production` in the deployment environment.
- Keep Streamlit's CORS and XSRF protections enabled.
- Back up the database before deployment and before schema changes. For SQLite, stop the app and copy `financial_gps.db` to protected storage.
- Roll back by restoring the previous application release and its matching database backup.
- Run `python -m unittest discover -s tests -p 'test*.py'` or `pytest` before deployment.

## Build Status

**Phase 0 — Foundation** ✓
- Database schema (budget + FIRE tables)
- Auth (email/password with bcrypt)
- Sidebar navigation skeleton
- CRA 2026 parameters + loader

**Current:** Phase 8 — Final beta usability work and invited synthetic-data testing

The deployed fresh-account smoke path has passed. One beta-targeted usability issue remains before the invited synthetic-data beta is considered feature-complete; current details are maintained in [Current status](docs/CURRENT_STATUS.md).

Project documentation:

- [Project vision](docs/PROJECT_VISION.md)
- [Current status](docs/CURRENT_STATUS.md)
- [Roadmap](docs/ROADMAP.md)
- [Decision log](docs/DECISIONS.md)
- [Beta data and storage policy](docs/BETA_DATA_POLICY.md)
- [Synthetic beta tester guide](docs/BETA_TESTER_GUIDE.md)
- [Synthetic beta retention runbook](docs/BETA_RETENTION_RUNBOOK.md)
- [GitHub Issues](https://github.com/nicholashorsky/financial-gps/issues)
- [Financial GPS Development project](https://github.com/users/nicholashorsky/projects/1)

Historical specifications and beta notes are preserved in `docs/archive/`.
