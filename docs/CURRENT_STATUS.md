# Financial GPS Current Status

**Updated:** July 21, 2026  
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

## Current focus

The immediate focus is beta-exit validation and FIRE forecast correctness:

1. [Complete a deployed fresh-account beta smoke test](https://github.com/nicholashorsky/financial-gps/issues/19).
2. [Define and validate the FIRE projection cash-flow and tax contract](https://github.com/nicholashorsky/financial-gps/issues/18).
3. [Make CRA parameter-year assumptions explicit](https://github.com/nicholashorsky/financial-gps/issues/15).

## Work in progress

No implementation Issue is currently marked In Progress. Ready work is visible in the [project board](https://github.com/users/nicholashorsky/projects/1).

## Blockers and undecided questions

* Whether the early-tester release is synthetic/demo-only or requires managed PostgreSQL: [#3](https://github.com/nicholashorsky/financial-gps/issues/3).
* The projection cash-flow contract must be corrected before RRIF and optimized decumulation work can be trusted: [#18](https://github.com/nicholashorsky/financial-gps/issues/18).
* Unsupported future tax years currently require an explicit product assumption: [#15](https://github.com/nicholashorsky/financial-gps/issues/15).

## Validation baseline

At the time of the documentation migration:

* 52 automated tests pass.
* 13 Streamlit navigation subtests pass.
* Ruff reports no issues.
* The sample import creates 118 transactions across four accounts in an isolated smoke test.

## Tracking rules

* GitHub Issues are the actionable backlog.
* The project board records workflow state, priority, phase, effort, and target release.
* This file records only the current phase, focus, blockers, and next tasks.
* Product purpose belongs in [PROJECT_VISION.md](PROJECT_VISION.md).
* Release-level direction belongs in [ROADMAP.md](ROADMAP.md).
* Durable choices belong in [DECISIONS.md](DECISIONS.md).
