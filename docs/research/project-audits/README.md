# External Project Audits

These documents preserve research conducted against external budgeting and financial-planning projects. They are reference material, not Financial GPS specifications. Product requirements and implementation work remain tracked in the active project documentation and GitHub Issues.

## Audit index

| Audit | Primary use for Financial GPS | Reuse boundary |
|---|---|---|
| [Actual Budget](Actual_Budget_Code_Audit.md) | Transactions, payees, rules, reconciliation, present-day budgeting, imports, synchronization, and mobile workflow patterns | Primarily MIT, with package-level metadata and third-party licenses requiring verification before direct reuse |
| [ProjectionLab reconstruction research](ProjectionLab_Reconstruction_Research.md) | Clean-room planning workflows, current-finance separation, milestones, ordered flows, scenario comparison, and validation cases | Product-behaviour reference only; use original implementation, wording, branding, and assets |
| [Retire, Eh?](Retire_Eh_Code_Audit.md) | Compact deterministic calculation boundaries, local execution, import/export, and calculation testing | MIT; verify source commit and notices before adapting code |
| [Ignidash](Ignidash_Code_Audit.md) | Plan schemas, snapshots, simulation reproducibility, historical testing, Monte Carlo, and validation architecture | AGPL-3.0-only; treat as an architectural reference unless an explicit compatible licensing decision is made |

## How to use this research

When an audit informs a decision or GitHub issue:

1. State the Financial GPS problem independently.
2. Link the relevant audit section as supporting research.
3. Record the chosen design and rejected alternatives.
4. Implement original code suited to the existing Python and Streamlit architecture.
5. Add Financial GPS-specific tests and documentation.

Do not silently treat an external project's behaviour as authoritative financial logic. Canadian calculations must continue to be implemented and verified from authoritative public sources.

## Current high-value mappings

* Actual Budget informs transaction reconciliation, unmatched transfers, goals and allocations, deterministic rules, and narrow transaction-review workflows.
* ProjectionLab research informs forecast/scenario information architecture, composable plan events, ordered cash flows, and Canadian planning input UX.
* Ignidash informs current-finance and plan snapshots, reproducible simulation runs, runtime validation, and future probabilistic analysis.
* Retire, Eh? informs small deterministic engine boundaries and transparent calculation tests; its audited calculation engine is not a complete Canadian retirement engine.

The cross-project conclusions should be distilled into Financial GPS decision records and issue requirements before implementation. The audit files themselves remain unchanged research artifacts.
