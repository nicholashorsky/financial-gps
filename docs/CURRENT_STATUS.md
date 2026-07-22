# Financial GPS Current Status

**Updated:** July 22, 2026
**Current branch:** `main`  
**Current phase:** Beta exit validation  
**Project board:** [Financial GPS Development](https://github.com/users/nicholashorsky/projects/1)

## Main objective

Produce a stable, cohesive Streamlit beta that can be tested safely by a small group of users. Financial correctness, clear setup, deployment safety, and repeatable validation take priority over additional feature breadth.

## Recently completed

* P0–P5 beta-polish work and manual review.
* Transaction-review progress, explicit saving, rule previews, normalized rule matching, and configurable queue size.
* Spending-period comparisons and corrected chart labels.
* Transfer-safe spending and income totals.
* Shared UI, date, and currency formatting helpers.
* Invalid-row reporting, duplicate-safe imports, import history, and user-isolated undo.
* Editable user rules, system-rule controls, and user-specific categories.
* Production-safe development login and documented local launch workflow.
* Automated Streamlit workflow coverage using a disposable database and the RBC sample CSV.
* Migration of actionable notes into GitHub Issues and the project board.
* Approved a synthetic-data-only SQLite boundary for the first external beta and added eight parser-validated fictional datasets.
* Completed the deployed fresh-account smoke test on Streamlit Community Cloud with the original 118-transaction sample.

## Current focus

The immediate focus is beta-exit validation:

1. Review the [deployed beta smoke-test record](DEPLOYMENT_SMOKE_TEST_2026-07-22.md) and close [Issue #19](https://github.com/nicholashorsky/financial-gps/issues/19).
2. Validate the expanded synthetic persona datasets in isolated tester accounts.
3. Keep real financial data outside the application until the PostgreSQL readiness work is complete.

## Work in progress

The storage-boundary decision in [Issue #3](https://github.com/nicholashorsky/financial-gps/issues/3) is being documented. Ready work is visible in the [project board](https://github.com/users/nicholashorsky/projects/1).

## Blockers and undecided questions

* The first external beta is synthetic-only. Managed PostgreSQL is required before accepting real financial data; see the [Beta Data and Storage Policy](BETA_DATA_POLICY.md).
* SQLite passed normal refresh persistence but remains non-durable across restarts and redeployments; the synthetic-only restriction remains in force.

## Validation baseline

At the time of the documentation migration:

* 68 automated tests pass.
* 13 Streamlit navigation subtests pass.
* Ruff reports no issues.
* The original sample import creates 118 transactions across four accounts in an isolated smoke test.
* Eight additional synthetic personas parse to their documented 1,463 total transactions with no invalid rows or parser warnings.

## Tracking rules

* GitHub Issues are the actionable backlog.
* The project board records workflow state, priority, phase, effort, and target release.
* This file records only the current phase, focus, blockers, and next tasks.
* Product purpose belongs in [PROJECT_VISION.md](PROJECT_VISION.md).
* Release-level direction belongs in [ROADMAP.md](ROADMAP.md).
* Durable choices belong in [DECISIONS.md](DECISIONS.md).
