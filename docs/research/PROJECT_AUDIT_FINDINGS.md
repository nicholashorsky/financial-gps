# External Project Audit Findings

**Reviewed:** July 22, 2026

## Executive recommendation

Financial GPS should remain an independent Python and Streamlit application. The audited projects provide useful architecture, workflow, and testing patterns, but none is an appropriate replacement for the current codebase:

* [Actual Budget](project-audits/Actual_Budget_Code_Audit.md) is the strongest reference for present-day financial records and transaction operations.
* [ProjectionLab research](project-audits/ProjectionLab_Reconstruction_Research.md) is the strongest clean-room reference for planning workflows and information architecture.
* [Ignidash](project-audits/Ignidash_Code_Audit.md) is the strongest reference for plan snapshots and simulation reproducibility.
* [Retire, Eh?](project-audits/Retire_Eh_Code_Audit.md) is a useful reference for small deterministic calculation boundaries and local execution.

These findings do not authorize copying external code, wording, branding, assets, or financial formulas. Financial GPS requirements remain in its own documentation and GitHub Issues.

## Reference boundaries

### Actual Budget

Concepts worth adapting independently:

* Preserve raw imported transaction data alongside user-facing merchant information.
* Use explicit transfer links, import identifiers, cleared status, and reconciliation records.
* Keep transaction rules deterministic, ordered, previewable, and explainable.
* Separate short-term allocation and budgeting from long-term projections.
* Test transaction totals, splits, transfers, and reconciliation as financial invariants.

Do not adopt its full application or synchronization architecture during the current Streamlit beta. A fork or API integration would be a separate future decision with substantial product and technology consequences.

### ProjectionLab research

Concepts worth adapting through clean-room implementation:

* Separate current finances from future plans.
* Build plans from milestones, income, expenses, assets, debts, and ordered cash flows.
* Use progressive navigation from current position to forecast, plan, scenarios, and comparison.
* Keep Canadian benefit inputs understandable, including a user-provided CPP estimate at age 65.
* Validate projections with small controlled scenarios before adding advanced analytics.

Do not reproduce proprietary branding, unique copy, assets, hidden behaviour, or inaccessible calculations. Public product behaviour is research evidence, not an implementation specification.

### Ignidash

Concepts worth studying and reimplementing independently:

* Keep current finances separate from plan configuration.
* Snapshot plans so simulation inputs are reproducible and comparable.
* Associate results with engine, assumptions, tax-data, market-data, and seed versions.
* Validate serialized plan inputs and test conservation-of-cash and balance invariants.
* Run future historical or probabilistic simulations behind a clear calculation boundary.

Ignidash is AGPL-3.0-only. Its code must not be incorporated unless Financial GPS first makes an explicit compatible licensing decision.

### Retire, Eh?

Concepts worth adapting where useful:

* Keep calculation code independent from the UI.
* Use typed inputs and deterministic outputs at the engine boundary.
* Support local calculation, import/export, and transparent formula tests.
* Prefer small golden scenarios over opaque end-to-end financial assertions.

Its audited engine is an accumulation calculator rather than a complete Canadian retirement engine. Financial GPS already implements broader tax, benefit, RRIF, and decumulation behaviour, so its formulas are not a replacement foundation.

## Existing issue mappings

The audits inform—but do not change—the following GitHub issues:

| Issue | Audit-derived guidance |
|---|---|
| [#6 — Transaction-linked goals and money buckets](https://github.com/nicholashorsky/financial-gps/issues/6) | Separate historical balances, present-day allocations, and projected contributions. Treat bucket funding as allocation or transfer rather than new income. |
| [#8 — Forecast and scenario information architecture](https://github.com/nicholashorsky/financial-gps/issues/8) | A versioned Plans workspace now implements the progressive current-finances → plan → projection → comparison journey and is awaiting manual review. |
| [#9 — Reconciliation and unmatched transfers](https://github.com/nicholashorsky/financial-gps/issues/9) | Use linked transfer pairs, cleared and reconciliation state, imported identifiers, and placeholder or off-budget destinations. |
| [#11 — Compound scenarios](https://github.com/nicholashorsky/financial-gps/issues/11) | Compose scenarios from independently timed income, expense, asset, debt, milestone, and flow events. |
| [#12 — Reimbursements and designated funds](https://github.com/nicholashorsky/financial-gps/issues/12) | Preserve raw transactions, use explicit links and splits, and distinguish reporting classification from cash movement. |
| [#14 — Narrow-viewport audit](https://github.com/nicholashorsky/financial-gps/issues/14) | Prioritize core workflows, native responsive primitives, horizontally navigable tabs where appropriate, readable controls, and adequate touch targets. |
| [#20 — Versioned database migrations](https://github.com/nicholashorsky/financial-gps/issues/20) | Treat backward-compatible schema evolution and upgrade testing as required persistence infrastructure. |
| [#24 — Multi-user isolation audit](https://github.com/nicholashorsky/financial-gps/issues/24) | Verify ownership on every entity and access path; consider concurrency and immutable snapshots when planning data becomes collaborative or long-lived. |

No acceptance criteria or project-board state were changed as part of this synthesis.

## Recommendations requiring later design

The following are not approved architecture or active implementation work. Each requires a dedicated design and migration review before becoming a decision or GitHub issue.

### Simulation-run metadata

Current-finance snapshots and immutable plan revisions are implemented. Before historical or Monte Carlo analysis, saved simulation results must additionally record engine, assumptions, tax-data, market-data, timestamp, dataset, and random-seed versions.

### Exact monetary representation

Evaluate migration from SQLite `REAL` and Python floating-point values to integer minor units for accounting records and decimal arithmetic for rates and tax calculations. The migration must address existing data, imports, projections, formatting, and compatibility.

### Richer payees and categorization rules

Evaluate separating raw imported description, normalized merchant identity, user-facing payee, institution import ID, and rule execution trace. Consider rule stages, specificity, conflict previews, and optional application to previous matches.

### Financial-engine invariants

Expand regression coverage around transfers netting to zero, splits reconciling to their parent, cash sources equalling uses, tax reconciliation, non-negative account constraints, snapshot immutability, and deterministic repeatability.

## Accepted decisions versus recommendations

| Status | Conclusion |
|---|---|
| Accepted | Financial GPS remains the primary Python and Streamlit codebase. |
| Accepted | External audits are research references, not product specifications or runtime dependencies. |
| Accepted | ProjectionLab is used only through clean-room product research. |
| Accepted | Ignidash code is excluded unless an explicit AGPL-compatible licensing decision is made. |
| Accepted | Canadian calculations continue to be implemented from authoritative public sources. |
| Accepted | Plans use independent current-finance snapshots and immutable revisions; plan edits do not write back to source records. |
| Recommendation | Evaluate exact monetary storage before accepting real financial data. |
| Recommendation | Expand payee and deterministic-rule modeling. |
| Recommendation | Add reproducibility metadata and broader financial invariants before probabilistic simulation. |

## Next use

The beta-exit backlog is complete. Issue #8 is the active manual-review gate for the first Plans workspace. Subsequent clean-room planning work follows [Planning Capability Status](../PLANNING_CAPABILITIES.md), beginning with timeline events and ordered cash flows.
