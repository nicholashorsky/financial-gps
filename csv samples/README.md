# Financial GPS Synthetic RBC-Style Test Data

These files are deterministic, fictional datasets generated from the column structure and export conventions of `RBC SAMPLE CSV.csv`.

## Safety boundary

- Every person, employer, merchant, account identifier, amount, and transaction is synthetic.
- No source transaction rows or source account numbers were copied into the generated files.
- The files are suitable for application testing and demonstrations, not financial analysis.
- Account identifiers are deliberately fictional and must never be treated as real banking or payment-card numbers.

## Compatibility

Every dataset uses the exact source headers:

```text
Account Type,Account Number,Transaction Date,Cheque Number,Description 1,Description 2,CAD$,USD$
```

Dates use `M/D/YYYY`. Blank currency cells remain blank. Each row contains either a CAD amount or a USD amount, never both.

## Included datasets

### Steady professional

- File: `01_steady_professional.csv`
- Rows: 179
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: Stable biweekly salary, rent, recurring bills, moderate discretionary spending, and consistent savings.

### Family household

- File: `02_family_household.csv`
- Rows: 272
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: Two-income family with mortgage, childcare, utilities, groceries, fuel, household purchases, and an emergency fund.

### Freelancer

- File: `03_freelancer_irregular_income.csv`
- Rows: 195
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: Irregular client payments, business expenses, tax-reserve transfers, partial card payments, and a large equipment purchase.

### Student budget

- File: `04_student_budget.csv`
- Rows: 143
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: Part-time income, student aid, tuition, low-cost living, small savings transfers, and an NSF fee reversal edge case.

### FIRE-focused high saver

- File: `05_fire_focused_high_saver.csv`
- Rows: 186
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: High-income, low fixed costs, aggressive monthly savings, full card payments, and a bonus contribution.

### Cash-flow stress

- File: `06_cashflow_stress.csv`
- Rows: 189
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: Variable pay, high fixed costs, partial credit-card payments, emergency repair, savings withdrawal, fees, and a tax refund.

### Travel and mixed currency

- File: `07_travel_mixed_currency.csv`
- Rows: 174
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: Regular Canadian activity plus travel bookings, USD purchases in the USD$ column, and a foreign-transaction fee.

### Retiree

- File: `08_retiree_sparse_activity.csv`
- Rows: 125
- Accounts: Chequing, Savings, Visa
- Period: 2026-01-01 to 2026-06-30
- Test focus: Sparse activity with pension, CPP/OAS income, condo costs, healthcare purchases, and conservative savings.

## Suggested use

Import one file at a time into a newly created synthetic tester account. This keeps the persona histories isolated and makes expected behaviour easier to inspect.

The mixed-currency dataset deliberately includes rows where `CAD$` is blank and `USD$` is populated. Use it to verify currency handling rather than assuming every row is CAD.
