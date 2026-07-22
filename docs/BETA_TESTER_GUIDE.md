# Financial GPS Synthetic Beta Tester Guide

## Invitation template

Use this text when inviting a tester:

> You are invited to test Financial GPS, an early Streamlit beta using fictional sample data only. Do not upload or enter real banking, credit-card, tax, investment, account, identity, or other personal financial information. Use one of the supplied synthetic personas. Beta data may be deleted or reset without notice and has no backup or recovery guarantee. Financial GPS is not a system of record or a substitute for financial, tax, or investment advice.

Provide the private Streamlit deployment link separately and grant the tester access through Streamlit Community Cloud. Each tester must register a separate Financial GPS account with a fictional email and a password not used elsewhere.

## Safe test path

1. Register and confirm the development-login shortcut is absent.
2. Import one persona from [`csv samples`](../csv%20samples/README.md) into a fresh account.
3. Do not combine personas unless the test specifically requires it.
4. Exercise onboarding, spending review, forecasts, goals, FIRE pages, Data Quality, and Settings.
5. Refresh and sign back in to verify normal-session persistence.

## Feedback and support

Report defects through [GitHub Issues](https://github.com/nicholashorsky/financial-gps/issues). Include the synthetic persona name, page, expected result, observed result, and reproduction steps.

Do not attach CSV files, screenshots containing credentials, database files, secrets, or any real personal information. For access or account-deletion help, contact the maintainer through the private invitation channel rather than posting credentials publicly.

Financial GPS stores the uploaded filename as import-history metadata and stores parsed transactions. It does not persist a copy of the uploaded source CSV.

## Account deletion

Testers can open **Settings → Delete beta account**, enter their account email, acknowledge the warning, and permanently delete the account. Foreign-key cascades remove associated test records from the active database.

Deletion from the active database does not promise immediate removal from an existing protected backup. Backups follow the retention limits in the [Beta Data and Storage Policy](BETA_DATA_POLICY.md).

## Before changing the synthetic-only notice

The notice must not be weakened or removed until the real-data gate is approved. At minimum, Issues #20–#25 must be complete, backup restoration and user isolation must be verified, privacy/support material must be reviewed, and the Beta Data and Storage Policy must be replaced by an approved real-data policy.
