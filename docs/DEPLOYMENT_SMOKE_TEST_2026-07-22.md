# Deployed Beta Smoke Test — July 22, 2026

## Test target

* **Deployment:** <https://financial-gps-pcp4bappo3zkgbf8ct9m6p.streamlit.app/>
* **Git revision:** `99aa564`
* **Branch:** `main`
* **Data:** Synthetic `csv samples/RBC SAMPLE CSV.csv` only
* **Access:** Private Streamlit Community Cloud deployment requiring platform authentication

The public endpoint returned HTTP 303 to Streamlit platform authentication before Financial GPS loaded. This is acceptable for the invited beta only while every tester is explicitly granted access.

## Results

| Check | Result |
| --- | --- |
| Clean default-branch deployment starts | Pass |
| Production mode hides the development-login shortcut | Pass |
| Fresh user can register and reaches Onboarding | Pass |
| Registration and import show synthetic-data restrictions | Pass |
| Original sample imports 118 transactions into four accounts | Pass |
| Matched transfers remain visible but do not affect spending totals | Pass |
| Every primary sidebar page loads without an unexpected Streamlit exception | Pass |
| Imported data survives a normal browser refresh | Pass |
| Logging out and back in restores access to the same account data | Pass |
| No real personal financial data is used | Pass |

Pages checked: Home, Spending, Forecast, Scenarios, Goals, Financial Profile, Account Room Tracker, Benefits Workspace, FIRE Goal Setup, FIRE Forecast, FIRE Scenarios, Data Quality, and Settings.

## Persistence and rollback observations

Normal refresh and same-account login persistence passed during this test. This does not establish durable storage across application restarts, container replacement, redeployment, corruption, or platform maintenance.

The deployment remains subject to the [Beta Data and Storage Policy](BETA_DATA_POLICY.md):

* SQLite is approved only for this small synthetic-data beta.
* Test data may be deleted or reset without notice and has no recovery guarantee.
* Application rollback means redeploying a known-good Git revision.
* Data rollback requires a protected SQLite copy from the matching revision when one is available.
* Streamlit Community Cloud local storage must not be treated as durable or as a system of record.
* Managed PostgreSQL, versioned migrations, verified isolation, and tested backup/restore remain mandatory before real-data testing.

## Automated baseline

After the deployed manual pass, the local suite for the same application revision was rerun: 69 tests and 21 Streamlit subtests passed, Ruff reported no issues, and `git diff --check` passed.
