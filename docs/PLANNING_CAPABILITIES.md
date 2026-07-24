# Planning Capability Status

**Updated:** July 24, 2026  
**Reference:** Clean-room product research in [ProjectionLab Reconstruction Research](research/project-audits/ProjectionLab_Reconstruction_Research.md)

Financial GPS uses ProjectionLab as a workflow and information-architecture reference while retaining original code, language, visual design, and Canadian calculations. The objective is not proprietary feature parity; it is an explainable Canadian planning journey that connects current finances to testable future plans.

## Current planning foundation

The implemented Plans workspace currently provides:

* Multiple user-isolated plans with immutable revisions.
* Creation from a reviewed current-finance snapshot or a profile-prefilled blank plan.
* Plan duplication, selection, renaming, archiving, and confirmed permanent deletion.
* Selective refresh from current finances without writing plan edits back to source records.
* Guided inputs for profile, income timing, CPP/OAS elections, categorized expenses, account balances, expected returns, retirement year, spending target, inflation, and projection horizon.
* Optional mean or median expense suggestions from categorized transaction history.
* Deterministic Canadian projections with federal and Ontario tax, CPP, OAS, GIS, OAS recovery, RRSP-to-RRIF conversion, minimum withdrawals, and tax-aware decumulation.
* Chart views for net worth, change in net worth, stacked account balances, total income, government benefits, spending, taxes, effective tax rate, withdrawals, annual surplus, and savings rate.
* Full-plan, 10-year, 20-year, and through-retirement views with year or age axes.
* Annual cash-flow and tax/benefit tables.
* Comparison of up to three independent plans.

The current interface and recent usability improvements are awaiting manual approval under [Issue #8](https://github.com/nicholashorsky/financial-gps/issues/8).

## Important gaps

The major remaining ProjectionLab-inspired capabilities are:

1. **Timeline and plan events:** generalized milestones, one-time events, recurring start/end conditions, financial-independence conditions, and visible timeline markers.
2. **Ordered cash flows:** configurable priorities for expenses, debt payments, account contributions, target balances, surplus destinations, and drawdown permissions.
3. **Richer expenses:** recurrence, payment source, milestone timing, and flexibility classes that change calculation behaviour.
4. **Debts and real assets:** mortgages, loans, homes, vehicles, appreciation, financing, purchase/sale events, ownership costs, and liquid-versus-total net worth.
5. **Portfolio allocation:** stocks, bonds, cash, dividends, account tax treatment, rebalancing, and allocation changes over time.
6. **Interactive What-If mode:** temporary modifications over a dashed baseline, change lists, milestone deltas, and keep/discard actions.
7. **Withdrawal choices and reports:** user-selectable strategies, RRSP-meltdown analysis, depletion timing, lifetime income/tax reports, and estate outcomes.
8. **Chance of success:** versioned historical testing followed by reproducible Monte Carlo simulation.
9. **Couples and collaboration:** a second person, ownership, joint assumptions, survivor rules, pension splitting, secure invitations, permissions, and revocation.

## Delivery sequence

| Stage | Outcome | Prerequisite |
|---|---|---|
| Current review | Approve and deploy the chart-led Plans workspace | Manual desktop review |
| Planning V2 | Timeline milestones and dated income/expense events | Versioned payload design |
| Planning V3 | Ordered contribution, debt-payment, and surplus flows | Event model |
| Planning V4 | Debts, real assets, and liquid net worth | Flow model |
| Planning V5 | Interactive What-If changes and comparison | Events, flows, assets |
| Planning V6 | Reports and selectable withdrawal strategies | Stable deterministic engine |
| Planning V7 | Historical testing, then Monte Carlo | Reproducible run metadata and validated datasets |
| Collaboration | Couple plans and secure invitations | PostgreSQL, migrations, backup, and isolation gates |

## Implementation rules

* Complete and approve the current Plans workspace before expanding the calculation model.
* Preserve deterministic engine tests while adding each new entity or event.
* Implement timeline events before ordered flows, and ordered flows before real assets or interactive scenarios.
* Add historical success testing before Monte Carlo.
* Do not implement shared couple plans on the current SQLite deployment.
* Keep contribution-room tracking outside the plan builder; users enter the balance available to each plan account.
* Continue using authoritative public sources for Canadian tax and benefit calculations.
