# Beta Data and Storage Policy

**Approved:** July 22, 2026  
**Applies to:** First external Financial GPS testing round

## Approved boundary

The first external beta is a small, invited, **synthetic-data-only** product-validation test using one Streamlit application instance and SQLite.

Testers may use the synthetic CSV files in [`csv samples`](../csv%20samples/README.md), manually entered fictional transactions, and fictional profile, income, account, goal, or scenario values. They must not enter or upload real banking, credit-card, tax, investment, identity, account-number, credential, or other personal financial information.

SQLite is approved for local development, short-lived demonstrations, and this restricted synthetic beta. It is not approved for persistent external testing with real financial data. Managed PostgreSQL is required before that boundary changes.

## Persistence, recovery, and retention

The SQLite beta is demo-grade and non-durable:

* Data may be reset or lost during deployment, container replacement, corruption, or platform maintenance.
* Financial GPS is not a system of record, and no recovery-time or recovery-point guarantee is offered.
* The database file must never be committed to Git or shared through an unsecured link.
* When preserving a test state is useful, stop the app and copy the database to protected storage before deployment or a schema change.
* Restore the matching database copy together with its matching application revision; otherwise start with an empty synthetic database.
* Delete inactive tester accounts after 90 days and all beta data no later than 30 days after this synthetic beta ends. Honour earlier deletion requests where practical.
* Do not persistently retain uploaded CSV files after processing. Financial GPS processes uploads in memory and stores the filename metadata and parsed transaction records, not a copy of the source file.

Backups follow the same synthetic-only restriction and retention schedule. The maintainer may delete all beta data at any time.

## Concurrency, authentication, and isolation

The SQLite beta is limited to one application instance and a small invited group. Every tester must use a separate account.

All access to transactions, imports, accounts, preferences, categories, goals, FIRE profiles, forecasts, and scenarios must remain scoped to the authenticated user ID. Synthetic data does not remove the need for isolation because credentials, behavior, and notes may still be private.

Set `FINANCIAL_GPS_ENV=production` in the deployed environment. Keep `FINANCIAL_GPS_TEST_LOGIN` unset; production mode also rejects the development shortcut if it is accidentally set.

## Secrets

Store deployment secrets in the hosting provider's secret-management system, never in source files, sample configuration, logs, screenshots, or the repository. Restrict secrets to the application runtime and rotate any exposed value immediately.

A future PostgreSQL connection string must be supplied through a protected secret such as `DATABASE_URL`, with encrypted connections enabled.

## Required tester notice

Use this notice in tester invitations, registration or first run, beside CSV upload, and in beta documentation:

> Financial GPS is an early beta for synthetic sample data only. Do not upload real banking, credit-card, tax, account, or other personal financial information. Beta data may be deleted or reset without notice and has no backup or recovery guarantee. Financial GPS is not a system of record or a substitute for financial, tax, or investment advice.

Operational language and procedures are maintained in the [Synthetic Beta Tester Guide](BETA_TESTER_GUIDE.md) and [Synthetic Beta Retention Runbook](BETA_RETENTION_RUNBOOK.md).

## PostgreSQL migration trigger

Migration to managed PostgreSQL is mandatory before any of the following:

* Testers may upload real transaction exports or enter real financial data.
* The beta becomes public, paid, or part of a commercial pilot.
* Persistent data or reliable recovery is promised.
* More than one application instance is used.
* Account-level recovery or automated backups are required.
* SQLite locking or deployment persistence causes failed writes or data loss.

## Requirements before real-data testing

The real-data beta must not launch until follow-up issues deliver:

* PostgreSQL-compatible configuration while retaining useful local SQLite support.
* Repeatable, versioned schema migrations.
* A managed database in an approved region with encrypted connections and protected credentials.
* Automated backups with documented retention and a successful restore test.
* Verified ownership constraints and automated multi-user isolation tests.
* Tested simultaneous imports and writes.
* Reviewed logs that exclude transaction descriptions, credentials, and connection strings.
* Data deletion and export procedures, updated privacy notices, and a deployment/rollback runbook.

Because this phase contains synthetic data only, the preferred cutover is a clean PostgreSQL database. Preserving disposable SQLite beta data is optional; avoid building a complex one-time migration unless a real need emerges.
