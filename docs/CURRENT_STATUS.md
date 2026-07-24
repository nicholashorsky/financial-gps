# Financial GPS Current Status

**Updated:** July 23, 2026
**Current branch:** `main`  
**Current phase:** Invited synthetic-data beta
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
* Added tester-facing synthetic-data notices, documented retention operations, and implemented self-service beta account deletion.
* Hardened FIRE projections with explicit parameter-year handling, RRIF minimum withdrawals, a validated annual cash-flow contract, and incremental tax-aware decumulation.
* Added a user-scoped Service Canada CPP estimate override with separate start-age modeling and visible source guidance.
* Added neutral Lean, Coast, Barista, and Fat FIRE guidance while preserving existing saved selections.
* Reorganized Settings into horizontal Profile, Assumptions, Rules, Categories, and Account & data tabs with persistent confirmations.
* Completed the narrow-viewport audit with compact mobile typography, spacing, metrics, and spending-chart presentation.
* Added a clean-room, ProjectionLab-inspired Plans workspace with independent versioned plans, guided setup, deterministic projections, cash-flow and tax views, and three-plan comparison.

## Current focus

The beta-exit backlog is complete. The immediate focus is operating a controlled invited beta:

1. Keep testing limited to synthetic financial data.
2. Gather structured tester feedback through GitHub Issues.
3. Refine mobile presentation later where testing identifies meaningful usability problems.
4. Prepare the PostgreSQL, migration, backup, and isolation work required before real-data testing.
5. Complete manual review of the new Plans workflow before resolving Issue #8.

## Release readiness

The deployed fresh-account path, synthetic-data storage boundary, and narrow-viewport audit are approved. The invited synthetic-data beta is feature-complete, with further mobile refinement intentionally deferred rather than treated as a beta blocker. Ready work is visible in the [project board](https://github.com/users/nicholashorsky/projects/1).

## Blockers and undecided questions

* The first external beta is synthetic-only. Managed PostgreSQL is required before accepting real financial data; see the [Beta Data and Storage Policy](BETA_DATA_POLICY.md).
* SQLite passed normal refresh persistence but remains non-durable across restarts and redeployments; the synthetic-only restriction remains in force.

## Validation baseline

Current automated and deployment validation:

* 97 automated tests pass.
* 18 Streamlit navigation subtests pass.
* Ruff reports no issues.
* The original sample import creates 118 transactions across four accounts in an isolated smoke test.
* Eight additional synthetic personas parse to their documented 1,463 total transactions with no invalid rows or parser warnings.
* The deployed fresh-account workflow completed without application errors; see the [deployment smoke-test record](DEPLOYMENT_SMOKE_TEST_2026-07-22.md).

## Tracking rules

* GitHub Issues are the actionable backlog.
* The project board records workflow state, priority, phase, effort, and target release.
* This file records only the current phase, focus, blockers, and next tasks.
* Product purpose belongs in [PROJECT_VISION.md](PROJECT_VISION.md).
* Release-level direction belongs in [ROADMAP.md](ROADMAP.md).
* Durable choices belong in [DECISIONS.md](DECISIONS.md).
