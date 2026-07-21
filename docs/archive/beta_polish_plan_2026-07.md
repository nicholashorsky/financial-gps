# Financial GPS Beta Polish Plan

## Overall Assessment

Financial GPS is functionally ahead of its visual polish.

The core workflow is already substantial and includes:

* Authentication
* User onboarding
* CSV transaction imports
* Account tracking
* Transaction review
* Transaction categorization
* Categorization rules
* Spending summaries
* Cash-flow forecasting
* Financial goals
* FIRE planning

The project is no longer an early prototype. It is in a beta-hardening phase.

The recommended approach is:

> Complete one focused beta-polish and reliability sprint, then move to the next phase. Do not spend excessive time trying to make Streamlit pixel-perfect.

The design mockups should be treated as layout and interaction targets rather than exact visual specifications.

A successful Streamlit implementation should resemble the mockups in:

* Information hierarchy
* Screen structure
* Primary actions
* User flow
* Visual consistency
* Relative emphasis of components

It does not need to reproduce every exact shadow, border radius, animation, hover effect, or spacing measurement.

## Progress Snapshot — July 21, 2026

The focused P0–P5 beta-polish work has been implemented and manually reviewed. The application remains a Streamlit application and the polish work deliberately favors stable native components and small shared helpers over fragile, page-specific CSS.

Completed outcomes include:

* **Transaction review (P0):** explicit category saving, full-queue progress, configurable review batch sizes, skip guidance, rule previews, and normalized merchant matching.
* **Spending overview and reporting:** a clearer overview hierarchy, period selection and comparison, readable account/category/transaction presentation, corrected monthly chart labels, and transfers excluded from spending and income summaries.
* **Shared presentation:** centralized currency and date formatting plus reusable theme and UI helpers.
* **Import reliability and recovery:** duplicate-safe imports, updated-export handling, invalid-row reporting, import batch history, user-isolated undo, and clear import results.
* **Settings and preferences (P5):** user-created rule editing, per-user system-rule controls, and user-specific category management with the existing categories retained as defaults.
* **Development and deployment safeguards:** Ruff development tooling, documented environment flags, a convenient development launcher, and production-safe development-login behavior.
* **Automated beta workflow:** an isolated Streamlit smoke test exercises development login, the RBC sample import, transfer matching, and all primary sidebar pages without touching the developer's normal database.

Current automated verification: **52 tests and 13 Streamlit navigation subtests pass; Ruff reports no issues.**

The next work is beta-exit validation rather than another UI-polish phase. Remaining items include clean-environment deployment verification, production database migration and migration tooling, backup/restore and rollback procedures, and final multi-user security validation before real financial data is accepted.

---

# 1. Spending Overview Review

## Intended Screen Hierarchy

The Spending screen should follow this general structure:

1. Page title and import action
2. Prominent transaction-review alert
3. Accounts and spending overview
4. Recent transactions
5. Secondary reporting and import functionality

The current implementation contains most of the required features, but the experience is divided across several tabs and currently feels more like an internal Streamlit tool than a polished consumer application.

The goal should be to make the Overview tab function as the primary dashboard while retaining deeper tabs for users who need additional detail.

## Recommended Spending Overview Layout

### Header

Use a two-column header.

The left side should include:

* Page title
* Short description of the screen
* Current reporting period

The right side should include:

* Import CSV button
* Optional date-range selector

The import button should take the user directly to the import workflow or open an import dialog.

### Transaction Review Banner

Display one consistent review banner when transactions require attention.

The banner should include:

* Number of transactions requiring review
* A short explanation
* A clear Review Transactions button
* Optional progress information

Avoid showing multiple warnings for the same review queue.

Example:

> **18 transactions need your attention**
> Review uncategorized or uncertain transactions to improve your spending insights.
> **Review transactions**

### Accounts Panel

The Accounts panel should display more than only the account name and net flow.

Each account row should include:

* Account name
* Account type
* Last updated date
* Number of imported transactions
* Current balance or net-flow value
* Included or excluded status
* Account icon or initials

The user should be able to quickly understand which accounts are connected, how current their data is, and whether they are included in spending calculations.

### Spending Overview Panel

The spending summary should visually emphasize the most important information.

Include:

* Total spending for the selected period
* Change compared with the previous period
* Total income
* Net cash flow
* Top spending categories
* Percentage of total spending by category

Use horizontal progress bars or category rows rather than relying only on a dataframe.

A suitable layout would show the top three to five categories, followed by a View All Categories action.

### Recent Transactions

Recent transactions should appear as readable transaction rows rather than primarily as a spreadsheet-style dataframe.

Each row should include:

* Merchant or transaction description
* Date
* Account
* Category
* Amount
* Review status, when applicable

Amounts should be right-aligned and formatted consistently.

The section should end with a View All Transactions control.

---

# 2. Transaction Review Screen

## Current Strengths

The current transaction-review workflow already supports important functionality, including:

* Category filtering
* Account filtering
* Search
* Quick review
* Detailed review
* Category assignment
* Skipping transactions
* Rule creation
* Applying rules to existing transactions
* Recurring merchant suggestions

The functionality is strong. The main opportunity is improving presentation, predictability, and user flow.

## Recommended Transaction Review Changes

### Show Multiple Transactions

Display approximately three transaction cards at once rather than showing only one transaction per screen.

Each card should include:

* Merchant name
* Transaction date
* Account
* Amount
* Current category
* Suggested category, if available
* Save Category button
* Skip button
* Create Rule option

This will make the review process feel like a manageable queue rather than a sequence of isolated page reloads.

### Require Explicit Saving

Selecting a category should not immediately save the transaction.

Instead:

1. The user selects a category.
2. The user clicks Save Category.
3. The transaction is updated.
4. The queue advances.

This reduces accidental changes and makes the interaction more predictable.

### Place Suggestions With the Relevant Transaction

Suggestions should appear inside the transaction card they relate to.

Example:

> **Suggested rule**
> When the merchant contains “Spotify,” categorize the transaction as Entertainment.
> This rule would apply to three existing transactions.

The user should then be able to:

* Apply only to this transaction
* Create the rule
* Apply the rule to existing matching transactions
* Dismiss the suggestion

Avoid displaying unrelated suggestions inside the first transaction card.

### Add Review Progress

Display queue progress near the top of the review screen.

Include:

* Total transactions in the review session
* Transactions completed
* Transactions remaining
* Transactions skipped
* Progress bar

Example:

> 22 of 40 transactions reviewed
> 18 remaining

### Explain Skip Behavior

Users should understand what happens when a transaction is skipped.

Suggested explanation:

> Skipped transactions remain uncategorized and can be reviewed later. Skipping does not delete or exclude the transaction.

### Rule Preview

Before applying a rule to existing transactions, show:

* Merchant text that will be matched
* Category that will be assigned
* Number of matching transactions
* Accounts affected
* Whether already categorized transactions will be changed

The user should confirm the action before the rule is applied broadly.

---

# 3. Streamlit Design Guidance

Streamlit can reproduce the overall structure and workflow of the mockups, but it should not be forced into behaving like a fully custom frontend.

## Reasonable to Reproduce

The following elements are practical in Streamlit:

* Wide page layouts
* Two-column sections
* Bordered cards
* Metrics
* Progress bars
* Tabs
* Category selectors
* Review banners
* Transaction rows
* Consistent spacing
* Primary and secondary buttons
* Purple brand styling
* Clear empty states

## Not Worth Perfecting During Beta

Do not spend significant beta-development time reproducing:

* Exact card shadows
* Pixel-perfect border radiuses
* Complex hover animations
* Fixed-position elements
* Highly customized responsive layouts
* Mobile-perfect navigation
* Complex page transitions
* Extensive custom JavaScript
* CSS that depends heavily on undocumented Streamlit class names

Streamlit’s generated page structure can change between versions. Excessive CSS overrides may become fragile and difficult to maintain.

The beta should prioritize a clean and coherent interface rather than exact visual duplication.

---

# 4. Beta Reliability Priorities

Reliability and financial correctness are more important than visual polish.

## Automated Tests

Add tests for the most important financial and data-handling behavior.

At minimum, cover:

* Duplicate CSV imports
* Re-importing the same file
* Importing an updated bank export
* Empty CSV files
* Malformed CSV files
* Invalid dates
* Invalid amounts
* Positive and negative amount handling
* Transfer identification
* Transfer matching
* Categorization rules
* Applying rules to existing transactions
* Excluded transactions
* Monthly reporting boundaries
* Account ownership
* User data isolation
* Empty database states

Recommended development dependencies:

```text
pytest
pytest-cov
ruff
```

These may be placed in a separate development requirements file such as:

```text
requirements-dev.txt
```

## User Data Isolation

Every database query, update, and delete operation involving user data must be constrained by the authenticated user’s ID.

This applies to:

* Accounts
* Transactions
* Imports
* Categories
* Rules
* Goals
* Forecasts
* Settings

User isolation should be validated with automated tests rather than assumed from manual code review.

## Test Login and Development Shortcuts

Development login features must be disabled in production unless explicitly enabled.

Production deployments should have:

* No default passwords
* No predictable test credentials
* No sample user with access to real data
* Secrets stored outside the repository
* Secure session handling
* Development-only features disabled by default

The application should fail closed when security-related environment variables are missing.

## Database Choice

SQLite is suitable for:

* Local development
* Personal testing
* Demonstrations using synthetic data
* Early prototypes
* Temporary single-user testing

SQLite should not be used as the long-term database for a multi-user beta containing real financial data.

Before inviting multiple users to upload real data, migrate to a managed relational database such as:

* PostgreSQL
* Supabase
* Neon
* Another managed PostgreSQL provider

The migration should include:

* Schema migrations
* Database backups
* Connection security
* User-level data isolation
* Recovery procedures
* Environment-specific configuration

---

# 5. User-Flow Polish Priorities

Complete the following before moving to the next major phase:

* Create one primary Spending Overview screen
* Add a clear Import CSV action
* Add a clear Review Transactions action
* Remove duplicate warnings and status messages
* Require explicit category saving
* Add review progress
* Add rule previews
* Add import confirmation
* Show duplicate-import results
* Provide clear empty states
* Use consistent currency formatting
* Use consistent account naming
* Add clear success and error messages
* Explain excluded and skipped transactions
* Provide a recovery path for incorrect imports

---

# 6. Shared UI Components

Create a centralized UI or theme module instead of adding unrelated styling separately to each page.

Suggested structure:

```text
shared/
├── ui.py
├── theme.py
└── formatting.py
```

Centralize reusable elements such as:

* Page headers
* Review banners
* Card containers
* Metric formatting
* Currency formatting
* Date formatting
* Status badges
* Empty states
* Confirmation messages
* Button conventions
* Category labels

This will create more consistency than individually polishing each screen.

---

# 7. Beta Completion Criteria

Remain in beta hardening until the following conditions are met.

## Onboarding and Import

* A new user can register without assistance.
* A new user can complete onboarding.
* A new user can import the sample CSV.
* The app clearly reports successful and unsuccessful rows.
* Duplicate imports do not create duplicate totals.
* The user can understand which account received the imported data.

## Transaction Review

* A user can review a transaction.
* A user can assign a category.
* A user can skip a transaction.
* A user can create a rule.
* A user can preview a rule before applying it.
* A user can return to skipped transactions.
* Review progress is understandable.

## Financial Correctness

* Spending totals remain correct after categorization.
* Spending totals remain correct after exclusions.
* Transfers are not incorrectly counted as spending.
* Date filters return the expected reporting periods.
* Account-level totals reconcile with transaction-level totals.

## Security

* One user cannot access another user’s data.
* Test-login behavior is disabled in production.
* Secrets are not stored in the repository.
* Real user data is not committed to Git.
* Production data is not stored in a public Codespace or repository.

## Deployment

* The application can be deployed from a clean environment.
* Dependencies are reproducible.
* Database setup is documented.
* Environment variables are documented.
* The main workflow has automated smoke tests.
* A failed deployment can be rolled back.

Once these conditions pass, move to the next phase even if the Streamlit interface is only approximately 75–85% visually similar to the mockups.

---

# 8. Laptop Versus GitHub Codespaces

## Recommendation

Use a hybrid development setup.

The laptop should remain the primary development environment.

GitHub Codespaces should be used as:

* A clean-environment test
* A portability check
* An occasional remote development environment
* A pull-request review environment
* A way to reproduce dependency issues

## Laptop Suitability

The current laptop is suitable for this project.

Relevant specifications include:

* Intel Core i5-7200U
* Two physical CPU cores
* Four logical threads
* 8 GB RAM
* 256 GB SSD
* Linux Mint based on Ubuntu 24.04
* Python 3.12
* Integrated Intel graphics

Financial GPS currently uses a relatively lightweight stack:

* Python
* Streamlit
* pandas
* SQLite
* Plotly
* bcrypt

This workload does not require a powerful GPU or high-end processor.

The older CPU may make some operations slower, but it should be sufficient for:

* Running Streamlit
* Editing Python files
* Running tests
* Working with moderate CSV files
* Running SQLite
* Using Git
* Running a browser and VS Code

## Use the Laptop For

* Daily development
* Streamlit UI iteration
* Local database testing
* Fast edit-refresh cycles
* Git commits
* Working offline
* Synthetic-data testing
* Avoiding Codespaces usage limits

## Use Codespaces For

* Verifying that the repository works from a clean environment
* Testing the dev container
* Working temporarily from another computer
* Reviewing pull requests
* Reproducing environment-specific bugs
* Confirming dependency installation
* Demonstrating a development branch

## Do Not Use Codespaces As Production Hosting

Codespaces should not be treated as a permanent beta-hosting service.

Do not use a Codespace to:

* Store permanent user financial data
* Host the public beta long-term
* Replace a production database
* Expose unauthenticated Streamlit ports publicly
* Store production secrets unnecessarily
* Act as the only copy of the application database

A Codespace is a development environment, not a production platform.

---

# 9. Dev Container Improvements

The existing dev container is useful, but it should remain minimal and reproducible.

Recommended improvements include:

* Remove unnecessary full operating-system upgrades during creation
* Install only explicitly required system packages
* Pin important dependency versions
* Avoid disabling security features by default
* Document required environment variables
* Add development dependencies
* Run tests as part of verification
* Ensure Streamlit starts on port 8501
* Keep production configuration separate from development configuration

Avoid disabling CORS or XSRF protections unless there is a confirmed technical reason.

Development convenience should not create insecure defaults for a financial application.

---

# 10. Recommended Development Workflow

```text
Laptop
├── Primary coding environment
├── Local Python virtual environment
├── Local Streamlit development
├── Synthetic financial data
└── Fast UI iteration

GitHub
├── Main branch
├── Feature branches
├── Pull requests
├── Issue tracking
└── Automated tests

GitHub Codespaces
├── Clean environment verification
├── Dev-container testing
├── Occasional remote development
└── Pre-merge smoke testing

Hosted Beta
├── Streamlit-compatible hosting
├── Managed PostgreSQL database
├── Environment secrets
├── Authentication enabled
└── Private user financial data
```

---

# 11. Recommended Implementation Order

The implementation phases below are retained as the original plan. Their current status is:

| Original phase | Status | Result |
| --- | --- | --- |
| Phase 1: Spending Overview | Complete | Overview hierarchy, reporting periods, account/category summaries, transaction presentation, and transfer-safe totals are implemented. |
| Phase 2: Transaction Review | Complete | The P0 review workflow and subsequent merchant-rule corrections are implemented and approved. |
| Phase 3: Shared UI | Complete | Shared formatting, theme, and UI helpers are in use without extensive fragile CSS. |
| Phase 4: Reliability | Complete for current SQLite beta scope | Import, isolation, categorization, reporting-boundary, transfer, and recovery tests are present. |
| Phase 5: Deployment Readiness | In progress | Login safeguards, environment documentation, dev-container improvements, and the primary workflow smoke test are present; managed PostgreSQL, migrations, backups, and deployment rollback verification remain. |

## Phase 1: Spending Overview

* Rebuild the Overview tab around the mockup hierarchy.
* Add the header and Import CSV action.
* Consolidate the transaction-review warning.
* Improve account cards.
* Add category progress rows.
* Improve recent transaction rows.

## Phase 2: Transaction Review

* Display multiple transaction cards.
* Require explicit saving.
* Add review progress.
* Place suggestions inside relevant cards.
* Add rule previews.
* Explain skip behavior.

## Phase 3: Shared UI

* Create shared card and banner components.
* Centralize currency formatting.
* Centralize date formatting.
* Centralize empty states.
* Reduce duplicated page-specific CSS.

## Phase 4: Reliability

* Add automated tests.
* Test duplicate imports.
* Test user isolation.
* Test rule application.
* Test transfers and exclusions.
* Test date boundaries.

## Phase 5: Deployment Readiness

* Disable test login by default.
* Document secrets.
* Move multi-user data away from SQLite.
* Add database migrations.
* Verify deployment from a clean environment.
* Run a full smoke test.

---

# Final Recommendation

Financial GPS should remain in beta hardening for one more focused sprint.

The next work should prioritize:

1. Improving the Spending Overview hierarchy
2. Improving the Transaction Review workflow
3. Testing financial correctness
4. Testing user data isolation
5. Preparing a safe multi-user database
6. Establishing a repeatable deployment process

Do not delay the next project phase in pursuit of pixel-perfect Streamlit styling.

The beta is ready to move forward once it is:

* Clear
* Reliable
* Secure
* Testable
* Deployable
* Consistent

The current laptop is sufficient as the main development machine.

Use GitHub Codespaces selectively for clean-environment testing and remote development rather than as the primary development environment or production host.
