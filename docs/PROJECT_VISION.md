# Financial GPS Project Vision

## Purpose

Financial GPS helps Canadian professionals understand where their money is going and how today's choices affect long-term financial independence. It combines transaction-based spending insight with an explainable Canadian FIRE planning engine in one Streamlit application.

The product should answer two connected questions:

1. Where is my money going now?
2. When could I become financially independent, and what changes that outcome?

## Target users

The primary audience is Canadian professionals who want more guidance than a transaction ledger but do not want an opaque financial model. The current beta is Ontario-first and designed for one user managing their own finances.

## Problems the product solves

* Convert bank CSV exports into understandable spending activity.
* Reduce manual categorization through rules while keeping users in control.
* Prevent transfers and credit-card payments from distorting spending.
* Connect observed income and spending to forward-looking forecasts.
* Explain Canadian accounts and benefits such as TFSA, RRSP, FHSA, CPP, OAS, and GIS.
* Let users compare the financial consequences of life decisions.
* Surface missing or uncertain inputs rather than presenting false precision.

## Differentiation

Financial GPS connects day-to-day spending with Canadian retirement planning. Transaction data can seed FIRE assumptions, while users can review and override those values. Forecast output should remain traceable to inputs, rules, taxes, benefits, and account activity.

Products such as Monarch Money and YNAB are useful references for transaction clarity and money organization. ProjectionLab is a useful reference for scenario planning and long-term visualization. Financial GPS should learn from those interaction patterns without copying them or losing its Canadian focus.

## Product principles

### Explain consequences

Show why a result changed and which assumption or transaction caused it. Do not present an unexplained recommendation as fact.

### Financial correctness before polish

Tax, transfer, categorization, isolation, and reporting correctness take priority over visual refinement.

### Users remain in control

Imported and derived values must be reviewable. Manual overrides should be clearly identified and reversible where practical.

### Preserve an audit trail

Raw transactions remain visible. Exclusions, rules, offsets, and forecast assumptions should be understandable rather than silently rewriting history.

### Use cautious language

Forecasts are estimates, not guarantees. Missing data and unsupported assumptions must be visible.

### Keep the beta maintainable

Use stable Streamlit components and shared helpers. Avoid fragile CSS and unnecessary custom frontend behavior.

### Protect user data

All user-owned data remains isolated. Development shortcuts fail closed in production. Synthetic data should be used before real financial data.

## Long-term possibilities

Later versions may include managed PostgreSQL storage, account reconciliation, bank synchronization, transaction-linked goals, composable scenarios, additional provinces, couples planning, Monte Carlo projections, notifications, mobile experiences, and CRA or Service Canada integrations.

These possibilities belong in the [roadmap](ROADMAP.md). Actionable work is tracked in [GitHub Issues](https://github.com/nicholashorsky/financial-gps/issues) and the [Financial GPS Development project](https://github.com/users/nicholashorsky/projects/1).
