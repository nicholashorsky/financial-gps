# Financial GPS Decisions

This log records durable product and technical decisions. Open questions belong in GitHub Issues.

## 2026-07-21 — GitHub is the actionable work system

**Decision:** Features, bugs, research, testing, and technical debt are tracked in [GitHub Issues](https://github.com/nicholashorsky/financial-gps/issues) and the [Financial GPS Development project](https://github.com/users/nicholashorsky/projects/1). Markdown files retain product knowledge, current status, roadmap outcomes, and decision history.

**Reasoning:** Multiple note files had overlapping, stale, and contradictory task lists.

**Tradeoffs:** Maintaining the board requires deliberate triage, but it provides ownership, workflow state, and testable completion criteria.

**Reconsider when:** GitHub no longer supports the project's collaboration or reporting needs.

## 2026-07-21 — Streamlit remains the beta interface

**Decision:** Continue using Streamlit for the beta. Match design references through hierarchy and interaction rather than pixel-perfect styling.

**Reasoning:** The application already has substantial Streamlit functionality, and beta value depends more on correctness and cohesion than a frontend rewrite.

**Tradeoffs:** Some responsive and interaction patterns will remain less flexible than a custom frontend.

**Reconsider when:** Validated user needs cannot be met reliably with stable Streamlit primitives.

## 2026-07-21 — Avoid fragile CSS

**Decision:** Prefer native Streamlit components, shared helpers, and limited stable CSS. Do not depend heavily on undocumented generated class names.

**Reasoning:** Streamlit internals may change and brittle overrides increase maintenance risk.

**Tradeoffs:** The interface will approximate rather than exactly reproduce design mockups.

**Reconsider when:** Streamlit provides a stable theming API or a frontend migration is approved.

## 2026-07-21 — Financial correctness precedes visual polish

**Decision:** Prioritize tax, transfer, reporting, import, authentication, and user-isolation correctness ahead of additional visual refinement.

**Reasoning:** Incorrect financial output causes more harm than an imperfect layout.

**Tradeoffs:** Some visual and mobile improvements remain queued during correctness work.

**Reconsider when:** Beta correctness and deployment acceptance criteria are consistently passing.

## 2026-07-21 — Ontario and verified 2026 parameters are the current baseline

**Decision:** Treat Ontario and verified 2026 CRA parameters as the supported calculation baseline. Unsupported years and provinces must be disclosed rather than implied to be verified.

**Reasoning:** Silent reuse of tax parameters creates false precision.

**Tradeoffs:** Long-term projections require an explicit flat-parameter assumption until additional verified data exists.

**Reconsider when:** Verified yearly or provincial parameter modules and regression cases are available.

## 2026-07-21 — FIRE engine remains independent of Streamlit

**Decision:** Pure financial calculation code must not import Streamlit. UI pages access engine behavior through service-layer functions.

**Reasoning:** This keeps financial logic independently testable and makes future interfaces possible.

**Tradeoffs:** Some UI features require additional service-layer plumbing.

**Reconsider when:** Only if the application architecture is intentionally replaced.

## 2026-07-22 — First external beta is synthetic-only on SQLite

**Decision:** Use one SQLite-backed Streamlit instance for a small, invited, synthetic-data-only external beta. Do not accept real personal financial data. Migrate to managed PostgreSQL before real-data, public, persistent, multi-instance, paid, or recovery-guaranteed testing.

**Reasoning:** SQLite supports disposable product validation but does not provide the concurrency, durable hosted persistence, automated backup, point-in-time recovery, or database-level controls expected for real financial data.

**Tradeoffs:** Testers must use fictional personas, data may be reset without recovery, and the beta must remain small and single-instance. PostgreSQL compatibility, migrations, operations, and isolation work are deferred until the real-data gate.

**Reconsider when:** Any trigger in the [Beta Data and Storage Policy](BETA_DATA_POLICY.md) is reached.

## 2026-07-21 — Development login fails closed

**Decision:** The development login shortcut is explicitly enabled only for synthetic development use and remains disabled in production mode even if its flag is accidentally present.

**Reasoning:** Convenience must not introduce predictable production access.

**Tradeoffs:** Production-like manual testing requires normal registration and login.

**Reconsider when:** Authentication is replaced with a managed identity provider.

## 2026-07-21 — Transfers remain visible but do not count as spending

**Decision:** Confirmed transfers remain visible in activity but are excluded from spending, income, category breakdowns, and summary cash-flow metrics.

**Reasoning:** Moving money between owned accounts does not create an expense or income.

**Tradeoffs:** Transfers involving unavailable destination accounts require a separate reconciliation design.

**Reconsider when:** The reconciliation model in [Issue #9](https://github.com/nicholashorsky/financial-gps/issues/9) is implemented.

## 2026-07-21 — User preferences remain isolated

**Decision:** User rules, system-rule settings, and category preferences are stored and applied per user. Existing categories remain defaults for new users.

**Reasoning:** One user's categorization choices must not affect another user's financial data.

**Tradeoffs:** Preference management requires user-scoped queries and additional isolation tests.

**Reconsider when:** Shared household behavior is explicitly designed.
