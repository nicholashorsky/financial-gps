# Financial GPS Roadmap

The roadmap describes release-level outcomes. Detailed requirements and active work belong in [GitHub Issues](https://github.com/nicholashorsky/financial-gps/issues) and the [Financial GPS Development project](https://github.com/users/nicholashorsky/projects/1).

## Phase 1 — Beta exit

**Status:** Complete.

### Goal

Deliver a stable, understandable Streamlit application suitable for controlled validation with synthetic data.

### Outcomes

* Complete the deployed fresh-account validation path.
* Remove unintended navigation and critical setup confusion.
* Make forecast configuration states understandable.
* Define the permitted storage boundary for early testing.
* Preserve automated financial, import, isolation, and workflow coverage.
* Correct high-impact FIRE cash-flow and tax assumptions.

The deployment smoke test, storage-boundary decision, FIRE correctness work, CPP estimate override, FIRE variant guidance, Settings reorganization, and narrow-viewport audit are complete.

## Phase 2 — Early tester release

**Status:** Synthetic-data-only invited testing is approved; broader or real-data testing is gated on Phase 4 persistence work.

### Goal

Invite a small group of users under an explicit data and support model.

### Outcomes

* Deploy with documented secrets, persistence, backup, recovery, and rollback behavior.
* Complete onboarding without developer assistance.
* Gather structured feedback through GitHub Issues rather than standalone notes.
* Resolve critical usability and correctness findings before widening access.

## Phase 3 — Financial intelligence hardening

### Goal

Make Canadian FIRE projections more accurate, explainable, and configurable.

### Outcomes

* Model taxable withdrawals through a validated annual cash-flow contract.
* Add verified RRIF conversion and minimum withdrawals.
* Replace fixed-order decumulation with tax-aware sequencing.
* Make parameter-year assumptions visible.
* Improve CPP estimate inputs and FIRE setup guidance.

## Phase 4 — Data and integrations

### Goal

Improve data durability, reconciliation, and safe automation.

### Outcomes

* Move shared real-user data to managed relational storage when required.
* Reconcile imported activity with account balances.
* Handle transfers to accounts that have not yet been configured.
* Research safe CRA, Service Canada, institution, and bank integrations.

## Phase 5 — Deeper planning

### Goal

Connect present-day money activity to richer goals and life scenarios.

### Outcomes

* Transaction-linked goals and designated money buckets.
* Reimbursement, rebate, and shared-expense handling.
* Compound scenarios with category-driven inputs.
* A versioned Plans workspace that replaces duplicate basic and FIRE forecast navigation.
* Independent current-finance snapshots, guided setup, deterministic projection, cash-flow and tax views, and plan comparison.

The first Plans workspace is implemented and awaiting manual review. The detailed capability sequence is maintained in [Planning Capability Status](PLANNING_CAPABILITIES.md): timeline events, ordered flows, debts and real assets, interactive What-If mode, reports and withdrawal strategies, and finally historical/probabilistic simulation.

## Later possibilities

* Additional provincial tax models and Quebec-native support.
* Couple plans, secure invitations to another Financial GPS user, shared household finances, and pension splitting.
* Monte Carlo and probability-based projections.
* Open banking and brokerage integrations.
* Notifications and achievement systems.
* Mobile-specific experiences or a native application.
* Natural-language financial exploration.
* Corporate and holdco planning.

Later possibilities should remain here until they are sufficiently defined and realistically approaching implementation.
