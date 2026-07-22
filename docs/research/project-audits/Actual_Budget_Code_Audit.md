# Actual Budget — Repository Audit

**Repository:** `actualbudget/actual`  
**Audited commit:** `71d802e91f5d5533b684fe7642e4506ebb31c8b5`  
**Default branch:** `master`  
**Audit date:** 2026-07-22  
**Repository license:** MIT  
**Current core/server package version observed:** `26.7.0`  
**Purpose:** Evaluate Actual Budget as a technical and product foundation for a personal-finance application, especially transaction categorization, account tracking, automation rules, budgeting, local-first storage, multi-device synchronization, and integration with a ProjectionLab-inspired financial-planning product.

---

# 1. Executive Assessment

Actual Budget is a mature, actively maintained, local-first personal-finance system. It is substantially more complete than a typical open-source budgeting prototype and contains production-grade implementations of:

- Local SQLite financial storage
- Browser and desktop application support
- Offline-first operation
- Multi-device synchronization
- Conflict-resistant change replication
- Optional end-to-end encryption
- Transaction importing
- Bank synchronization
- Envelope budgeting
- Rules-based transaction automation
- Automatic payee cleanup and category learning
- Split transactions
- Transfers
- Scheduled transactions
- Reconciliation workflows
- Reporting
- A Node.js integration API
- Desktop packaging through Electron
- Browser deployment
- Self-hosted synchronization
- Mobile-responsive interfaces
- Extensive unit, end-to-end, and visual-regression testing
- Internationalization
- A reusable component library

Actual is especially relevant to the proposed financial application because it can provide or inspire nearly the entire **historical-finance and transaction-management layer**, while ProjectionLab-style functionality can form a separate **forward-looking planning layer**.

## Overall recommendation

Actual is the strongest of the audited projects for direct reuse.

Use it as a foundation or source for:

- Accounts
- Transactions
- Payees
- Categories
- Rules
- Recurring schedules
- Imports
- Reconciliation
- Local-first persistence
- Multi-device sync
- Data encryption
- Reporting
- Public APIs
- Desktop and browser distribution

Do not use it as the main source for:

- Long-term retirement projections
- Monte Carlo simulations
- Canadian tax planning
- RRSP/TFSA contribution-room projections
- CPP/OAS forecasting
- Scenario comparison
- Future milestones
- Estate modelling
- ProjectionLab-style ordered savings flows

Those capabilities should be built as a separate planning module that consumes Actual’s current financial data.

### Overall score as a reusable foundation: **9/10**

The primary concerns are:

- Large repository and significant complexity
- Mature internal abstractions that require onboarding
- Sync and local-first logic are difficult to modify safely
- Some packages report differing license metadata
- Combining upstream Actual with a highly customized product may make upgrades difficult
- Budgeting concepts and planning concepts should remain cleanly separated

---

# 2. Product Positioning

Actual describes itself as:

> A local-first personal finance tool with synchronization across devices.

Its product philosophy is meaningfully different from typical cloud-first SaaS applications:

- Every device maintains a complete local copy.
- The application functions offline.
- A chosen synchronization server replicates changes.
- The server is not required for day-to-day calculations.
- Users can self-host the server.
- Optional end-to-end encryption prevents the server from reading budget contents.
- Local data remains directly accessible to the user.

This architecture is highly aligned with a privacy-focused personal financial application.

---

# 3. Repository State and Activity

The audited commit was:

```text
71d802e91f5d5533b684fe7642e4506ebb31c8b5
```

The most recent observed commit message at audit time addressed scoped error boundaries on mobile schedules, payees, and bank-sync screens. Other recent changes included:

- Continued TypeScript migration
- Reduced-motion accessibility support
- Dependency updates
- Per-budget bank-sync provider selection
- Pluggy integration improvements

This indicates:

- Active development
- Ongoing mobile investment
- Continued modernization
- Multiple supported bank providers
- Strong maintenance momentum

Because Actual changes frequently, any implementation based on it should pin a commit or release and maintain an explicit upgrade strategy.

---

# 4. Licensing

## Repository-level license

The root repository declares the MIT License.

MIT permits broad use, modification, distribution, sublicensing, and commercial use, provided the copyright and permission notice are retained in copies or substantial portions.

## Package-level metadata

Most audited packages declare MIT, including:

- `@actual-app/crdt`
- `@actual-app/sync-server`

The `@actual-app/core` package metadata declares `ISC`, while the root repository is MIT. MIT and ISC are both permissive, but this discrepancy should be documented and reviewed before redistributing individual packages independently.

## Practical implications

Compared with Ignidash’s AGPL license, Actual is much easier to:

- Fork
- Modify
- Embed
- Self-host
- Use commercially
- Combine with proprietary code

Recommended actions:

1. Preserve the root MIT copyright notice.
2. Preserve any package-level notices.
3. Maintain a third-party notices file.
4. Review licenses for bundled icons, fonts, bank SDKs, and other assets.
5. Track copied versus independently written modules.

This section is not legal advice.

---

# 5. Monorepo Architecture

Actual uses:

- Yarn 4 workspaces
- Lage task orchestration
- TypeScript
- React
- Vite
- Electron
- Node.js
- SQLite
- Vitest
- Playwright
- Visual-regression testing

The root package requires approximately:

```text
Node >= 22.18
Yarn 4.9+
```

The main workspaces are organized under:

```text
packages/*
```

## Core packages

### `packages/loot-core`

The platform-independent application core.

Responsibilities include:

- Business logic
- Database access
- Budget calculations
- Transaction processing
- Rules
- Schedules
- Synchronization client logic
- Import/export
- Reports and queries
- Encryption
- Platform abstraction

### `packages/desktop-client`

The React UI used for browser and desktop deployments.

Responsibilities include:

- Desktop interface
- Mobile-responsive interface
- Transaction tables
- Budget screens
- Reports
- Rules editor
- Settings
- Bank-sync controls
- Onboarding
- Playwright tests
- Visual-regression tests

The workspace alias is:

```text
@actual-app/web
```

### `packages/desktop-electron`

The Electron wrapper.

Responsibilities include:

- Native window management
- Desktop operating-system integration
- Packaging
- Electron-specific test coverage

### `packages/sync-server`

The self-hosted synchronization and bank-integration server.

Responsibilities include:

- Authentication
- Budget-file registration
- Mutation synchronization
- Multi-user/server functionality
- Server-side storage
- Bank-provider integrations
- OpenID support
- Password management
- Health checks
- Database migrations

### `packages/crdt`

The conflict-resistant synchronization layer.

Responsibilities include:

- Change representation
- Change ordering
- Conflict handling
- Protocol Buffer serialization
- Stable IDs
- Hashing
- Cross-device replication primitives

### `packages/api`

The public Node.js API.

Responsibilities include:

- Programmatic access
- Integrations
- Automation
- Budget download and loading
- Account, transaction, category, rule, and schedule methods

### `packages/component-library`

The shared UI system.

Responsibilities include:

- Buttons
- Inputs
- Menus
- Layout components
- Design tokens
- Themes
- Hundreds of icons
- Storybook documentation

### `packages/plugins-service`

A plugin and extension service.

### `packages/docs`

A Docusaurus documentation site stored in the same repository.

### `packages/eslint-plugin-actual`

Custom rules that enforce:

- Internationalization
- Logging conventions
- Typography
- Preferred code styles

---

# 6. Architectural Boundaries

Actual’s strongest architectural decision is separating:

```text
UI
↓
Client connection and commands
↓
loot-core business logic
↓
SQLite and sync mutation layer
↓
optional synchronization server
```

The UI is not intended to directly own financial rules or database mechanics.

## Platform abstraction

`loot-core` uses conditional package exports for:

- Browser
- Electron
- Node API

Examples include platform-specific implementations for:

- SQLite
- File systems
- Network requests
- Memory
- Connections
- Async storage
- Encryption internals

This allows one business-logic package to run in:

- A browser worker
- An Electron process
- A Node.js API process

## Relevance to the proposed project

This is an excellent model for separating:

- Historical finance engine
- Planning engine
- Web UI
- Desktop wrapper
- API
- Sync server

The planning engine should be a peer to `loot-core`, not embedded throughout UI components.

---

# 7. Local-First Storage Architecture

Actual stores a complete budget database locally on each client.

## Desktop

Desktop deployments use:

```text
better-sqlite3
```

## Browser

Browser deployments use:

- SQL.js
- Absurd SQL
- IndexedDB-backed storage

This produces SQLite-like behaviour in the browser rather than using a simpler key-value store.

## Benefits

- Offline operation
- Fast local queries
- User-controlled data
- Straightforward backups
- Mature relational semantics
- Rich reporting queries
- Reduced dependency on server availability
- Easier API and import/export consistency

## Costs

- Browser SQLite integration is complex
- Migrations must work across all platforms
- Large files and mutation logs need maintenance
- Sync must reconcile relational changes
- Browser-storage limits and eviction need consideration
- Schema changes require rigorous backward compatibility

---

# 8. Core Financial Data Model

The public API documentation and code paths establish a model centred around:

```text
Budget File
├── Accounts
├── Transactions
├── Payees
├── Category Groups
├── Categories
├── Rules
├── Schedules
├── Budget Values
├── Reports
├── Preferences
└── Sync Metadata
```

## 8.1 IDs

Entities generally use UUID strings.

## 8.2 Monetary values

Money is represented as integers in the smallest currency unit.

Example:

```text
$120.30 → 12030
```

This is an important and correct financial design decision.

### Benefits

- Avoids binary floating-point errors
- Supports exact summation
- Simplifies reconciliation
- Produces stable deterministic sync values

### Recommendation

Use integer minor units throughout both historical and planning layers.

For projections involving percentages, use:

- Decimal/fixed-point arithmetic
- Explicit rounding rules
- Currency-specific precision

---

# 9. Accounts

The API account object includes:

```text
id
name
offbudget
closed
balance_current
```

## On-budget accounts

These participate in envelope budgeting and available-cash calculations.

Examples:

- Chequing
- Savings
- Cash
- Credit card accounts

## Off-budget accounts

These are tracked but excluded from the envelope budget.

Examples:

- Investments
- Mortgages
- Property
- Retirement accounts
- Other net-worth accounts

## Relevance to financial planning

Actual’s on-budget/off-budget distinction can map into a planning model as:

```text
spendable cash
budget reserve
investment asset
registered account
debt
real asset
```

However, the planning application will need more explicit account types, such as:

- TFSA
- RRSP
- FHSA
- RRIF
- Taxable brokerage
- Cash
- Employer retirement plan
- RESP
- Mortgage
- Loan
- Property

Actual account records may need an extension table or metadata layer rather than changing core assumptions everywhere.

---

# 10. Transactions

The documented transaction model includes:

```text
id
account
date
amount
payee
payee_name
imported_payee
category
notes
imported_id
transfer_id
cleared
subtransactions[]
```

## Strong design elements

### Raw imported description

`imported_payee` preserves the original bank description after the user cleans up the display payee.

This is essential for:

- Debugging imports
- Writing categorization rules
- Avoiding loss of source data
- Reprocessing transactions

### Imported transaction ID

`imported_id` is intended for duplicate prevention.

### Transfers

Transfers use paired transactions, linked by `transfer_id`.

### Split transactions

A parent transaction can contain subtransactions, each with its own category and amount.

### Cleared status

Transactions can be marked cleared or uncleared to support reconciliation.

## Recommended reuse

The transaction schema is highly suitable for the user’s financial application.

Potential additions:

```text
merchant
normalized_description
source_provider
source_account_id
pending
posted_date
transaction_type
currency
exchange_rate
rule_trace
review_status
user_verified
planning_tag
```

---

# 11. Payees and Categories

## Payees

Payees provide a normalized user-facing identity for raw imported merchants.

Key use cases:

- Clean transaction display
- Category learning
- Rule matching
- Transfers
- Reporting

## Categories

Categories belong to category groups.

Documented category fields include:

```text
id
name
group_id
is_income
```

Category groups can contain categories and can be marked as income groups.

## Relevance

This model provides the foundation for:

- Spending analysis
- Budgeting
- Cash-flow forecasting
- Merchant behaviour
- Rule automation
- Projection-plan expense baselines

A ProjectionLab-inspired planning tool could convert historical category data into suggested future expense events.

Example:

```text
Historical category: Groceries
12-month average: CA$620/month
→ Suggested plan expense: Groceries, CA$620/month, inflation-adjusted
```

---

# 12. Transaction Rule Engine

Actual’s transaction rules are one of its most valuable reusable systems.

## Rule lifecycle

When transactions are imported or synchronized:

1. Transactions are evaluated against rules.
2. Rules execute in visible order.
3. Every matching rule runs once.
4. Actions mutate the transaction.
5. The modified transaction continues through later rules.
6. If two rules modify the same field, the later rule wins.

## Rule stages

Rules execute in three stages:

```text
pre
default
post
```

Within each stage, rules are ranked by specificity.

This permits:

- Early payee cleanup
- Normal categorization
- Forced final overrides

## Specificity ranking

More exact rules run after broader rules.

Example:

```text
contains "cat" → Pets
is "Catan" → Games
```

The exact match wins because it runs later.

## Condition operators

Observed condition types:

- is
- is not
- contains
- does not contain
- matches regular expression
- one of
- not one of

## Condition fields

Rules can inspect:

- Imported payee
- Payee
- Account
- Category
- Date
- Notes
- Amount
- Inflow amount
- Outflow amount

String matching is case-insensitive.

## Actions

Rules can set:

- Category
- Payee
- Notes
- Cleared status
- Account
- Date
- Amount

Rules can also:

- Prepend notes
- Append notes
- Create transfers
- Use experimental formula values

## Automatic rule learning

Actual can automatically create or update rules when users:

- Rename imported payees
- Repeatedly categorize a payee

Payee cleanup rules are placed in the `pre` stage.

Category rules are placed in the default stage.

Users can:

- Edit learned rules
- Disable learning for individual payees
- Disable learning globally
- Add post-stage overrides

## Rule editor as batch processor

The rule editor:

- Previews matching transactions
- Allows users to select matches
- Applies actions to existing transactions
- Functions as a sophisticated batch-editing interface

## Relevance to the user’s transaction-categorization screen

This directly supports the desired workflow:

```text
Show one transaction
→ choose category
→ optionally create a future rule
→ save
→ continue
```

A simplified categorization inbox can sit on top of Actual’s existing rule engine.

## Recommended enhancements

Add:

- Rule confidence
- Rule explanation
- Rule simulation before save
- Conflict warnings
- Rule execution trace
- Suggested rules without automatic activation
- “Apply to previous matches” count
- User approval status
- ML suggestions as a separate layer from deterministic rules

---

# 13. Rules and Formula Mode

Actual includes an experimental Excel-style formula mode for certain rule actions.

This suggests the rule engine can support calculated values rather than only constants.

Potential planning use cases:

- Add a note based on account or date
- Calculate allocations
- Assign categories based on amount bands
- Normalize merchant descriptions
- Compute internal tags

## Caution

Formula execution increases:

- Complexity
- Security risk
- Debugging difficulty
- User confusion
- Migration surface

For an MVP, deterministic field actions are sufficient.

---

# 14. Schedules

Schedules represent recurring or expected transactions.

The API model includes:

```text
id
name
rule
next_date
completed
posts_transaction
```

Each schedule is backed by a rule.

This unifies:

- Recurrence detection
- Expected transaction matching
- Optional transaction creation
- Forecasting

## Potential schedule types

Actual supports recurring concepts such as:

- Monthly bills
- Income
- Subscriptions
- Loan payments
- Irregular recurrence patterns

## Relevance to financial planning

Schedules can bridge present-day budgeting and future planning.

Example:

```text
Actual schedule: Rent, monthly
→ Plan expense event: Rent, monthly until move milestone
```

The planning engine should not directly reuse schedule semantics for long-range events, but schedules are an excellent source of suggested recurring inputs.

---

# 15. Envelope Budgeting

Actual is fundamentally an envelope-budgeting application.

The budgeting model assigns available money to categories.

Core concepts include:

- Income available to budget
- Category allocations
- Category spending
- Remaining balances
- Rollover between months
- Overspending
- Category groups
- Budget templates and automation

## Strengths

- Cash-aware
- Explicit allocation
- Strong behavioural feedback
- Prevents budgeting money that does not exist
- Works well for short-term financial control

## Difference from projection planning

Envelope budgeting answers:

> What should this money do this month?

Projection planning answers:

> How might finances evolve over decades?

These should remain separate engines.

## Recommended integration

Use Actual to produce:

- Current account balances
- Historical expenses
- Recurring obligations
- Average savings
- Category trends
- Debt payments
- Income patterns

Feed those into the planning engine as suggested assumptions.

Do not make long-term projections depend on mutable envelope-budget internals.

---

# 16. Reporting and Query Engine

`loot-core` includes:

- Client query helpers
- Reports
- Data hooks
- Spreadsheet provider
- HyperFormula dependency
- AQL query system

This implies a powerful reporting and calculated-data layer beyond fixed SQL screens.

Potential benefits:

- Custom dashboards
- Spending reports
- Net-worth reports
- Cash-flow summaries
- Savings rates
- Category comparisons
- User-defined report formulas

## Relevance

Actual’s reporting architecture can support the historical side of a combined financial application.

The projection engine should expose a similarly queryable output model:

```text
yearly balances
income
expenses
taxes
contributions
withdrawals
milestones
net worth
liquid net worth
```

---

# 17. Synchronization Architecture

Actual uses a local-first synchronization model.

Every device keeps:

- A full local budget database
- A mutation/change history
- A synchronization ID
- Knowledge of synchronized changes

The synchronization server:

- Registers budget files
- Stores changes
- Passes changes between devices
- Supports backups and re-downloads
- Can operate without reading encrypted budget contents

## CRDT package

The CRDT workspace uses:

- Protocol Buffers
- UUIDs
- MurmurHash
- Conflict-resistant replication logic

The package is independently versioned and MIT licensed.

## Benefits

- Offline edits
- Multi-device support
- Low-latency local UI
- No central calculation dependency
- Conflict handling
- Self-hosting
- Privacy

## Challenges

- Sync bugs are difficult to diagnose
- Migrations interact with historical mutations
- Concurrent edits to the same fields can surprise users
- Mutation logs grow over time
- Reset workflows must be carefully designed
- Encryption complicates sync recovery

---

# 18. Sync Reset and Compaction

Actual documents a “reset sync” process.

Resetting sync:

1. Clears synchronized history on the server.
2. Treats one chosen local file as authoritative.
3. Uploads that version.
4. Generates a new sync ID.
5. Requires other devices to revert and re-download.

It also significantly reduces file size because historical mutations are compacted into a new base state.

## Important product lesson

A local-first application needs first-class recovery tools.

Recommended features:

- Sync health indicator
- Last successful sync
- Device list
- Conflict information
- Download backup
- Reset sync
- Restore from backup
- Authoritative-device warning
- Local unsynced-change count

---

# 19. End-to-End Encryption

Actual supports optional end-to-end encryption for budget data.

## Behaviour

- The user chooses a second encryption password.
- A key is derived locally.
- Data is encrypted before leaving the client.
- The synchronization server passes encrypted changes.
- Other devices require the encryption password once to derive the key.
- The encryption password cannot be recovered.
- Enabling encryption is effectively one-way without export/restore.
- Local device data remains unencrypted unless the device uses disk encryption.

## Important exception

Bank-sync tokens are stored separately on the server and are not covered by budget-file end-to-end encryption.

This means a server administrator may be able to read:

- SimpleFIN credentials
- GoCardless tokens
- Pluggy credentials
- Other bank-provider tokens

## Implications

For a privacy-focused financial app:

- Self-hosting should be recommended for bank-sync users.
- Bank tokens should be encrypted at rest separately.
- Secrets should use a dedicated key-management design.
- Users should clearly understand what E2EE covers.
- Local database encryption could be considered separately.

---

# 20. Multi-User and Concurrent Editing

Actual permits the same budget file to be opened and edited in multiple browsers, including by different people.

The documentation warns that simultaneous conflicting edits should be avoided.

This suggests the sync system handles many concurrent changes but does not attempt collaborative-document semantics at the UI level.

## Recommendation

For a shared household:

- Allow multiple users
- Track actor/device IDs
- Show recently modified records
- Avoid simultaneous editing of the same transaction
- Consider optimistic locking for complex plan objects
- Use immutable plan snapshots for comparisons

---

# 21. Sync Server

The sync server is an Express 5 application.

Dependencies and features include:

- SQLite via `better-sqlite3`
- Argon2
- Bcrypt
- CORS
- Rate limiting
- OpenID Connect
- Logging via Winston
- Health checks
- Database migrations
- Multiple bank-provider SDKs

## Observed bank providers

Code paths and dependencies indicate support for integrations including:

- GoCardless
- SimpleFIN
- Pluggy
- Enable Banking
- Akahu

Recent development also added per-budget provider selection.

## Server scripts

The package provides operations for:

- Start
- Development monitoring
- Build
- Type checking
- Tests
- Database migration
- Migration rollback
- Password reset
- OpenID disablement
- Health check

## Recommendation

For a personal homelab deployment, the existing sync server is more mature than building synchronization from scratch.

---

# 22. Public API

Actual includes a public Node API designed for automation and integrations.

The API supports concepts including:

- Server initialization
- Budget download
- Budget loading
- Accounts
- Transactions
- Categories
- Category groups
- Rules
- Schedules
- Data export
- Sync

## Strong API design choices

- Transactions preserve raw imported payees.
- Amounts use integer minor units.
- Imported IDs support deduplication.
- Transfers are explicit linked transactions.
- Split transactions are represented structurally.
- Budget files are cached locally by the API.

## Potential uses for the proposed application

- Pull current account balances
- Read transactions
- Generate historical spending summaries
- Create or update categories
- Create transaction rules
- Import bank transactions
- Feed current finances into projection plans
- Export plan recommendations back as budget targets

---

# 23. Desktop and Browser Delivery

Actual supports:

- Browser deployment
- Electron desktop applications
- Local-only desktop use
- Self-hosted web use

## Benefits

- Broad platform reach
- Offline desktop usage
- Easier local file access
- Reusable React interface
- Shared core business logic

## Cost

Maintaining browser and Electron platforms requires:

- Conditional platform code
- Native dependency rebuilding
- Electron security reviews
- Separate E2E coverage
- Packaging infrastructure

For an MVP, a responsive browser application may be enough.

---

# 24. UI Architecture and Component Library

The component library includes:

- Reusable inputs
- Buttons
- Menus
- Themes
- Design tokens
- Over 375 icons
- Storybook

The React codebase follows:

- Functional components
- Declarative patterns
- React Compiler
- TypeScript
- Shared hooks
- Internationalized user-facing text
- Financial typography utilities

## Relevance

Actual can provide a mature base for:

- Transaction tables
- Categorization forms
- Account screens
- Reports
- Settings
- Mobile layouts
- Dialog patterns
- Keyboard interaction
- Accessibility

A custom product should still establish distinct branding and design rather than appearing to be an unmodified Actual deployment.

---

# 25. Mobile Support

The repository actively maintains mobile-specific components for:

- Transactions
- Schedules
- Payees
- Rules
- Bank sync
- Error boundaries

This is a major advantage over desktop-only financial tools.

## Recommendation

Reuse mobile information architecture where practical, but prioritize the user’s core workflows:

1. Review uncategorized transaction
2. Select category
3. Save
4. Create optional rule
5. Continue
6. View spending
7. Review current financial position
8. Open long-term plan

---

# 26. Testing and Quality Engineering

Actual uses several layers of testing.

## Unit tests

- Vitest
- Node environment
- Browser environment
- Package-specific suites
- Property-testing dependencies such as `fast-check`

## End-to-end tests

- Playwright for browser UI
- Electron E2E tests

## Visual-regression tests

- Dedicated VRT commands
- Docker-based consistent rendering

## Static quality

- Type checking
- Strict TypeScript plugin
- Oxfmt
- Oxlint
- Custom ESLint rules
- Knip unused-code analysis
- Pre-commit hooks
- Workspace dependency checks

## Task orchestration

Lage provides:

- Parallel test execution
- Caching
- Dependency-aware ordering
- Continue-on-error behaviour

## Financial application benefits

Recommended invariants to add for a combined product:

- Transaction totals equal account-balance changes
- Split totals equal parent amount
- Transfers net to zero
- Category totals reconcile to transaction totals
- Projection cash sources equal uses
- No unauthorized negative account balances
- Tax calculations reconcile by year
- Sync replay produces identical database state
- Simulation runs are deterministic with a fixed seed

---

# 27. Internationalization and Currency

Actual enforces internationalization through:

- Translated strings
- Custom lint rules
- Weblate
- Locale-aware interfaces

Money is represented generically in minor units, which supports multiple currencies.

## Remaining concerns for a combined application

Long-term planning introduces:

- Currency conversion
- Multiple currencies per household
- Historical exchange rates
- Tax residency
- Province/country assumptions
- Currency-specific inflation
- Foreign-account reporting

These should not be inferred from Actual’s budgeting model alone.

---

# 28. Security Assessment

## Positive controls

- Local-first architecture
- Optional E2EE
- Argon2
- Bcrypt
- Rate limiting
- OpenID Connect
- Self-hosting
- Offline operation
- Server health checks
- Separation of budget content and bank tokens

## Risks

- Local databases are not encrypted by Actual itself
- Bank tokens are outside budget E2EE
- Browser local storage may be vulnerable to device compromise
- Electron adds a desktop attack surface
- Plugins and imported files create trust boundaries
- A self-hosted server requires updates and secure configuration
- E2EE password loss can make data unrecoverable
- Multi-user concurrent edits may produce unexpected conflict results

## Recommended additions

- Encrypt bank tokens at rest
- Optional local database encryption
- Device/session management
- Audit log for sensitive operations
- Secret rotation
- Content-security-policy review
- Plugin permissions
- Signed update verification
- Secure backup key export

---

# 29. Performance and Scalability

Actual’s local SQLite model is well suited to personal finance.

Expected strengths:

- Fast transaction querying
- Efficient aggregation
- Good offline performance
- Predictable single-household workloads

Potential bottlenecks:

- Very large transaction histories
- Browser SQLite and IndexedDB performance
- Mutation-log growth
- Complex reports
- Rule evaluation across large imports
- Multiple historical budgets
- Large projection trial datasets

## Recommendation

Keep long-term simulation outputs in a separate database or compressed result store rather than adding millions of Monte Carlo rows to the operational transaction database.

---

# 30. Reuse Assessment by Module

| Module | Reuse recommendation |
|---|---|
| Accounts | Reuse/adapt |
| Transactions | Strongly reuse/adapt |
| Payees | Strongly reuse |
| Categories | Strongly reuse |
| Category groups | Strongly reuse |
| Split transactions | Strongly reuse |
| Transfers | Strongly reuse |
| Cleared/reconciliation status | Strongly reuse |
| Imports | Strongly reuse |
| Bank sync | Reuse if provider coverage fits |
| Transaction rules | Strongly reuse |
| Automatic categorization learning | Strongly reuse/adapt |
| Schedules | Strongly reuse |
| Envelope budget | Reuse as current-budget module |
| Reports | Reuse/adapt |
| SQLite core | Strongly reuse |
| CRDT sync | Strongly reuse unless simplifying scope |
| E2EE sync | Strongly reuse |
| Sync server | Strongly reuse for self-hosted product |
| Node API | Strongly reuse |
| Electron wrapper | Optional |
| Component library | Reuse/adapt |
| Projection engine | Build separately |
| Canadian tax planner | Build separately |
| Monte Carlo | Study Ignidash or build |
| Historical retirement testing | Build separately |
| Plan milestones | Build separately |
| Scenario comparison | Build separately |

---

# 31. Fit with the Proposed Financial Application

The proposed product appears to need two major domains.

## Domain A: Financial GPS / present-day finances

Actual provides most of this domain:

```text
Accounts
Transactions
Categories
Rules
Budgets
Schedules
Cash flow
Reports
Net worth
Imports
Sync
```

## Domain B: Long-term planning

ProjectionLab-inspired functionality provides:

```text
Current-finance snapshot
Plans
Milestones
Income events
Expense events
Savings flows
Investment assumptions
Tax assumptions
Historical trials
Monte Carlo
What-if comparison
Estate outcomes
```

## Recommended system boundary

```text
Actual-derived finance module
        ↓ snapshot/export
Planning input normalization
        ↓
Long-term simulation engine
        ↓
Projection reports and recommendations
```

Do not make the projection engine directly query mutable transaction tables during a run.

Instead:

1. Create a dated current-finance snapshot.
2. Convert historical patterns into proposed assumptions.
3. Let the user approve or modify them.
4. Save an immutable plan snapshot.
5. Run simulations against that snapshot.

---

# 32. Suggested Combined Data Model

## Historical finance

```text
Person
Household
Account
Transaction
Subtransaction
Payee
CategoryGroup
Category
Rule
Schedule
BudgetMonth
BudgetCategoryValue
BankConnection
ImportBatch
Reconciliation
```

## Planning

```text
CurrentFinanceSnapshot
Plan
PlanSnapshot
Milestone
IncomeEvent
ExpenseEvent
Flow
PlanAccount
Debt
RealAsset
MarketAssumption
TaxSetting
SimulationSetting
SimulationRun
YearlyResult
TrialResult
```

## Bridge tables

```text
HistoricalCategoryToPlanExpense
ActualAccountToPlanAccount
ScheduleToPlanEvent
BudgetTargetToPlanExpense
PlanRecommendation
```

---

# 33. Recommended Implementation Paths

## Option 1: Fork Actual and add planning

### Advantages

- Fastest route to a complete finance application
- Immediate transaction-management maturity
- Existing sync
- Existing rules
- Existing API
- Existing UI
- Existing imports

### Disadvantages

- Significant merge/upstream maintenance
- Planning features may feel bolted on
- Large codebase learning curve
- Product branding and navigation need substantial work
- Core changes can complicate upstream updates

## Option 2: Use Actual as a service and API

Create a separate planning application that connects through the Actual API.

### Advantages

- Clean separation
- Easier upstream upgrades
- Lower risk to transaction data
- Independent planning architecture
- Can support standard Actual installations

### Disadvantages

- Two applications
- Authentication and API setup
- Harder seamless UX
- Some data may require API expansion
- Cross-application navigation

## Option 3: Reuse selected packages

Reuse or adapt:

- Core models
- Rule engine
- CRDT
- Sync server
- API concepts

Build a new UI and planning engine.

### Advantages

- Original product experience
- Selective complexity
- Strong technical foundation

### Disadvantages

- Hardest integration path
- Package boundaries may rely on monorepo assumptions
- Upstream changes harder to merge
- Requires deeper licensing and dependency review

## Recommended option

For a personal project:

> Start with an Actual fork or standard Actual deployment plus a separate planning prototype. Integrate through the API first. Only merge codebases after the planning model is stable.

---

# 34. Recommended First Integration Milestone

Build a planning-data exporter that reads from Actual:

```text
Account balances
Account classifications
12-month income
12-month category spending
Recurring schedules
Debt balances
Savings rate
Net worth
```

Produce a draft planning snapshot:

```json
{
  "asOfDate": "2026-07-22",
  "cash": 10000,
  "registeredAccounts": [],
  "taxableInvestments": [],
  "debts": [],
  "annualIncome": 58000,
  "annualExpensesByCategory": {},
  "recurringEvents": []
}
```

The user reviews and approves this snapshot before it enters the projection engine.

---

# 35. Risks of Direct Forking

## Upstream drift

Actual is actively developed. A heavily customized fork may become difficult to update.

## Schema coupling

Planning-specific fields added directly to account or transaction tables may conflict with future migrations.

## UI complexity

Adding long-term planning to an already feature-rich sidebar can overwhelm users.

## Sync compatibility

New synchronized entities need:

- Mutation handling
- CRDT semantics
- Encryption support
- Migrations
- API support
- Recovery paths

## Recommendation

Use separate planning tables and versioned schema boundaries.

---

# 36. High-Priority Source Areas for Deeper Review

Before implementing major changes, inspect these areas in more depth:

```text
packages/loot-core/src/server/db/
packages/loot-core/migrations/
packages/loot-core/src/server/rules/
packages/loot-core/src/server/transactions/
packages/loot-core/src/server/schedules/
packages/loot-core/src/server/sync/
packages/loot-core/src/server/encryption/
packages/loot-core/src/client/budgets/
packages/loot-core/src/client/reports.ts
packages/crdt/src/
packages/api/
packages/sync-server/src/app-sync/
packages/desktop-client/src/components/transactions/
packages/desktop-client/src/components/rules/
packages/desktop-client/src/components/reports/
```

Specific follow-up audits could trace:

1. A bank-imported transaction from provider to database.
2. Rule evaluation and automatic-rule creation.
3. Transfer creation and sync replay.
4. Envelope-budget calculations.
5. Schedule matching and transaction posting.
6. Encryption key derivation and mutation encryption.
7. CRDT conflict resolution.
8. Report query execution.
9. API budget loading and command execution.
10. Database migration strategy.

---

# 37. Comparison with Other Audited Projects

| Capability | Actual | Retire, Eh? | Ignidash | ProjectionLab |
|---|---|---|---|---|
| Accounts and transactions | Excellent | Minimal | Basic planning accounts | Current-finance accounts |
| Budgeting | Excellent | None | None | Limited |
| Rules and categorization | Excellent | None | None | None |
| Local-first | Excellent | Browser-local | Server-backed | Cloud/browser app |
| Multi-device sync | Excellent | None | Convex-backed | Proprietary |
| End-to-end encryption | Yes | Not established | Not established | Not established publicly |
| Canadian planning | No | Basic accumulation | No | Yes |
| Monte Carlo | No | No | Yes | Yes |
| Historical retirement trials | No | No | Yes | Yes |
| Long-term milestones | No | No | Roadmap/partial | Yes |
| Tax planning | No | No | US focused | Multi-country |
| License | MIT/ISC metadata | MIT | AGPL | Proprietary |
| Best use | Current finances | Small calculation reference | Simulation architecture | Product behaviour reference |

---

# 38. Final Verdict

Actual is the best available technical foundation for the **operational personal-finance half** of the project.

Its greatest strengths are:

- Mature financial data model
- Local-first SQLite architecture
- Deterministic transaction rules
- Automatic categorization learning
- Multi-device CRDT synchronization
- Optional E2EE
- Strong import and bank-sync support
- Public API
- Permissive licensing
- Extensive testing
- Desktop, browser, and mobile-responsive delivery

Its principal limitation is intentional:

> Actual helps users understand and control money they have now; it is not a long-term financial projection engine.

The strongest overall strategy is therefore:

```text
Actual for present-day financial truth
+
ProjectionLab-inspired planning UX
+
Independent Canadian projection and tax engine
+
Ignidash-inspired simulation architecture
+
Retire, Eh?-inspired local deterministic calculation modules
```

This combination provides a credible path to a privacy-focused, self-hostable “Financial GPS” application without recreating mature budgeting and synchronization infrastructure from scratch.

---

# 39. Audited Primary Sources

Repository files and documentation reviewed:

- `README.md`
- `LICENSE.txt`
- `package.json`
- `AGENTS.md`
- `packages/loot-core/package.json`
- `packages/crdt/package.json`
- `packages/sync-server/package.json`
- `packages/docs/docs/api/types.jsx`
- `packages/docs/docs/getting-started/sync.md`
- `packages/docs/docs/budgeting/rules/index.md`
- Recent commit metadata from `master`

Repository:

```text
https://github.com/actualbudget/actual
```
