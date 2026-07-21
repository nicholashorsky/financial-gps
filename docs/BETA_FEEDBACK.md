# Financial GPS Beta Feedback

This document records hands-on beta observations that should remain visible during future polish work.

## Transaction Review — Addressed in P0

- Merchant rule suggestions must remove bank/reference and location noise. Example: `LCBO/RAO #0495 GUELPH ON` should suggest `lcbo`, not `lcbo rao`.
- Generic transaction-type labels must not become part of merchant rule text. Example: `Transfer — WWW TRANSFER - 4793` should suggest `www transfer`, allowing it to match other reference-number variants.
- Rule matching must ignore punctuation consistently in previews, bulk application, and future imports. Example: `paypal microsoft` must match `PAYPAL *MICROSOFT 4029357733 ON`.
- A separate "I reviewed this rule preview" checkbox adds unnecessary friction. Showing the preview followed by an explicit Create Rule action is sufficient confirmation.
- Review progress must count the complete matching queue rather than only the first 50 transactions.
- Quick Review should not be fixed to three cards. Users can select 10, 25, 50, 100, or all remaining transactions.

## Rules and Categories — Addressed in P5

- User-created categorization rules are editable from Settings, not only listed or deleted.
- Users can disable system categorization rules for their own account.
- Categories can be managed from Settings.
- The original category set remains the default for new users.
- Category and system-rule preferences are user-specific and covered by isolation tests.

## Spending Reporting — Addressed During P0 Review

- Transfer no longer appears as spending in the Spending Snapshot because moving money between accounts is not an expense.
- Transfer transactions remain visible in transaction activity but are excluded from spending totals, income totals, category breakdowns, and summary cash-flow metrics.

## Accounts and Transfer Reconciliation — Future Development

- Some transfers involve accounts that have not been imported or configured yet, such as a transfer from savings to an investment account.
- Future investment-account support should allow these transactions to be reconciled without treating them as spending.
- The application should distinguish unmatched transfers from genuine expenses while the destination account is unavailable.

## Scope Note

The Settings observations were intentionally left out of P0 and were completed in P5. Investment-account support and reconciliation of transfers involving accounts that have not yet been imported remain future work.

## Beta Exit Validation — In Progress

- The primary Streamlit workflow now has an automated smoke test using a disposable database.
- The smoke test covers development login, onboarding, the checked-in RBC sample import, transfer matching, and every primary sidebar page.
- The next validation work is clean-environment deployment testing, followed by production database migration and operational readiness.
