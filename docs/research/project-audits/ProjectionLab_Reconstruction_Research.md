# ProjectionLab Reconstruction Research

## Purpose

This document consolidates the research, observations, and inferred product requirements gathered from:

- ProjectionLab's public website, help centre, changelog, founder posts, and public feature descriptions
- Public screenshots and product documentation
- Open-source financial-planning projects used as architectural references
- Three screen recordings covering:
  - The introductory product tour
  - The accessible application areas and settings
  - The complete new-plan walkthrough

The goal is to support a **clean-room, ProjectionLab-inspired personal financial-planning application**. The project should reproduce useful workflows and planning concepts using original code, branding, wording, assets, and implementation decisions.

---

# 1. Executive Summary

The recordings and public research provide enough information to begin building a functional MVP with:

- Account onboarding and sandbox personas
- A fixed desktop application shell
- Current-finances tracking
- Canadian account types
- Net-worth and projection dashboards
- Plan creation through a multi-stage wizard
- Milestones and conditional milestones
- Income, expenses, real assets, and ordered cash-flow flows
- Interactive financial charts
- Historical success testing
- Return, inflation, dividend, bond, and tax settings
- Basic Canadian retirement-income modelling
- Saved plans and scenario navigation

The largest remaining uncertainties are not the overall interface. They are:

- Exact calculation order
- Exact Canadian tax calculations
- TFSA contribution-room handling
- RRSP/RRIF logic
- CPP, OAS, and GIS calculations
- Capital-gain and adjusted-cost-base handling
- Historical-return dataset selection and normalization
- Exact withdrawal and drawdown sequencing
- Several advanced editor options hidden behind expandable sections
- Premium-only analytics and optimizers

No additional broad walkthrough is required to begin development.

---

# 2. Legal and Product Boundaries

## Appropriate clean-room approach

The safest implementation approach is to recreate:

- General planning concepts
- Workflow structure
- Financial models based on public rules
- Similar categories of charts and reports
- Comparable user experiences

The project should avoid copying:

- ProjectionLab branding
- Logos
- Proprietary illustrations
- Unique written copy
- Exact premium report language
- Private API endpoints
- Authentication credentials
- Hidden implementation details
- Server-side code
- Copyrighted assets

The result should be an independently coded financial-planning application inspired by the observed functionality.

---

# 3. What Can and Cannot Be Observed

## Available through the browser and recordings

The following can be documented:

- Screen layout
- User workflows
- Form labels
- Dropdown choices shown in recordings
- Chart behaviour
- Navigation structure
- Publicly exposed settings
- Public help-centre explanations
- Visible account types
- User-facing calculation assumptions
- Public plugin behaviour
- Public export/import descriptions
- Visible premium boundaries

## Not directly available

The following remain inaccessible without source-code access:

- Server-side source code
- Database schema
- Private APIs
- Internal cloud configuration
- Proprietary tax-engine implementation
- Environment variables
- Secrets and credentials
- Internal historical datasets
- Exact simulation sequencing when not publicly documented
- Hidden error-handling logic
- Premium-only screens that cannot be opened

---

# 4. Publicly Documented Product Model

ProjectionLab publicly describes a planning system built around:

1. Individual or couple profile
2. Current financial position
3. One or more future plans
4. Milestones
5. Income
6. Expenses
7. Cash-flow priorities
8. Real assets
9. Taxes
10. Investment growth assumptions
11. Historical or probabilistic success analysis
12. Scenario comparison
13. Reports and estate outcomes

The Canadian configuration includes support for concepts such as:

- Canadian currency
- Province-based tax settings
- RRSP
- TFSA
- CPP
- OAS
- GIS eligibility
- RRSP-to-RRIF conversion
- Canadian dividend categories
- Canadian tax estimates
- Capital-gain handling
- Contribution and drawdown strategies

---

# 5. Publicly Described Technical Architecture

Public founder commentary has described a frontend stack involving:

- Vue 3
- Vite
- Vuetify 3
- Pinia
- Vitest
- Firebase modular APIs
- Increasing use of TypeScript

Public security and product documentation indicate that account data is stored using Google Cloud Platform and Firebase, encrypted at rest and in transit.

ProjectionLab also exposes a plugin ecosystem used by integrations with services such as:

- Lunch Money
- YNAB
- Monarch Money

The plugin system suggests that top-level plan and account data can be read and updated through supported browser-side APIs.

---

# 6. Open-Source Reference Projects

## Ignidash

Ignidash is an open-source ProjectionLab alternative that includes:

- Long-term financial projections
- Monte Carlo simulation
- Historical backtesting
- Assets and debts
- US tax estimation
- Modern web application architecture

Its stack includes:

- Next.js
- React
- TypeScript
- Tailwind
- Convex

Important note: Ignidash uses the AGPL-3.0 license. Incorporating its code may impose reciprocal licensing obligations.

## Retire, Eh?

Retire, Eh? is a Canadian retirement-planning project with:

- RRSP modelling
- TFSA modelling
- CPP modelling
- Canadian retirement projections
- Deterministic calculations

Its architecture includes:

- React
- TypeScript
- Tailwind
- Rust
- WebAssembly

It uses the MIT license, making it potentially easier to use as a technical reference, subject to its license requirements.

---

# 7. Recording Inventory

## Recording 1: Introductory tour

Approximate duration: **1 minute 59 seconds**

It documented:

- First-run setup
- Sandbox persona selection
- Main navigation
- Dashboard
- Current Finances summary
- Progress premium lock
- Main Plan workspace
- Chart hovering
- Plan tabs
- Visible income and expense cards

## Recording 2: Accessible areas and settings

Approximate duration: **5 minutes 41 seconds**

It documented:

- Current Finances forms
- Investment and asset account types
- Debt structures
- About You settings
- Chart metric options
- Chance of Success
- Plan settings
- Milestones
- Rates
- Dividends
- Bonds
- Tax settings
- Premium boundaries

## Recording 3: New-plan walkthrough

Approximate duration: **6 minutes 57 seconds**

It documented:

- New-plan creation
- Milestones
- Income
- CPP and OAS setup
- Ordered cash-flow priorities
- Expenses
- Expense flexibility
- Real assets
- Final plan creation
- Reusable form-section patterns

---

# 8. Onboarding and Sandbox Experience

The setup begins with a centred modal offering two main paths:

- Normal walkthrough
- Sandbox mode

The visible estimates were approximately:

- Normal walkthrough: 5–10 minutes
- Sandbox mode: about 1 minute

Visible sandbox personas included examples such as:

- High School Student
- Recent Grad, Single
- Early Career, Married
- Mid Career, High Debt
- Mid Career, Married
- Late Career, Single
- Early Career, UK
- Mid Career, UK
- Late Career, CA
- Early Career, AU

The Canadian late-career persona is described as approaching retirement with existing RRSP and TFSA assets.

## Recommended implementation

A personal project could offer:

- Start from scratch
- Canadian early-career sandbox
- Canadian mid-career sandbox
- Canadian retirement sandbox
- Couple sandbox
- High-debt sandbox

Each sandbox should contain fictional data only.

---

# 9. Main Navigation

The desktop sidebar includes:

- Upgrade
- Dashboard
- Current Finances
- Progress
- Plans
  - Current Projections
  - New Plan
- Help Center
- Gift a Subscription
- Resources
- Support
- More Info

Observed behaviour:

- Fixed left sidebar
- Expandable Plans section
- Current page highlighting
- Dark theme
- Compact toolbar
- Contextual walkthrough tooltips

## Plan-level navigation

Inside a plan, the upper navigation includes:

- Plan
- Cash Flow
- Tax Analytics
- Chance of Success
- Compare
- Optimize
- Reports
- Estate
- Settings

---

# 10. Dashboard

The Dashboard includes:

- Large net-worth or progress visualization
- Premium upgrade overlay for historical progress
- Plans for the Future section
- Existing plan-preview cards
- Add Plan card
- Plan-mode dropdown
- Miniature projection graph
- Three-dot plan menu

The plan card in the recording showed:

- Plan name
- Mini projection preview
- Full Plan selector
- Context menu

The Dashboard is primarily a summary and navigation screen.

---

# 11. Current Finances

Current Finances acts as the master financial-state layer from which plans are initialized or linked.

Top-level sections:

- Net Worth
- Savings
- Investments
- Real Assets
- Unsecured Debts
- About You

The Canadian sandbox summary displayed approximately:

- Net Worth: CA$852K
- Savings: CA$65K
- Investments: CA$528K
- Real Assets / Equity: CA$259K
- Unsecured Debts: CA$0

## Savings

Observed fields and behaviour:

- Account name
- Current balance
- Owner
- Add Savings
- Rename
- Reorder
- Remove
- Individual or partner ownership
- Summary visualization

## Investments

Visible investment categories included:

- Taxable investment account
- TFSA
- RRSP
- Pension
- Other tax-free account
- Cryptocurrency
- Country-specific account types

Observed fields:

- Account name
- Balance
- Owner
- Taxable account cost basis
- Notes
- Reorder
- Delete

The Add Investment dialog changes options based on the selected country, suggesting a country-template system.

## Real Assets

Observed fields:

- Name
- Purchase price
- Current value
- Owner
- Ownership or financing status

Visible asset types:

- House
- Car
- Rental property
- Commercial property
- Land
- Building
- Motorcycle
- Boat
- Jewelry
- Precious metals
- Furniture
- Instrument
- Machinery
- Custom asset

## Unsecured Debts

Visible debt categories:

- General debt
- Student loan
- Medical debt
- Credit-card debt

Observed debt fields:

- Name
- Current balance
- Interest rate
- Owner
- Interest or compounding method
- Payment frequency
- Recurring payment amount

## About You

Observed fields:

- Individual or couple
- Person name
- Birth month
- Birth year
- Country
- Province or region
- Planning currency
- Locale or language

---

# 12. Progress

Progress is a separate primary section.

Observed:

- Net-worth history graph
- Lower summary tables
- Premium upgrade lock in the free experience
- Current Finances updates appear to generate progress points

A future MVP can omit historical progress or implement a simpler monthly snapshot feature.

---

# 13. New Plan Wizard

The new-plan sequence is:

1. Create Plan
2. Milestones
3. Income
4. Flows
5. Expenses
6. Real Assets
7. Completed Plan

A progress indicator remains visible near the top, and live preview charts appear on the right.

---

# 14. Create Plan Stage

Observed fields:

- Plan name
- Plan or source dropdown
- Notes
- Cancel
- Create Plan

The source dropdown was not opened, but it likely supports creating from:

- Current Finances
- Existing plan
- Blank plan
- Template

The completed implementation should confirm the final desired choices independently.

---

# 15. Milestones

Default milestones:

- Retirement
- Life Expectancy
- Financial Independence

## Milestone conditions

Milestones can be date-based or condition-based.

Observed examples:

- Retirement at a specified date or year
- Life expectancy at a specified year
- Financial independence when net worth reaches a multiple of spending

The visible financial-independence rule was effectively:

```text
Net Worth >= 25 × Annual Spending
```

Conditions can be joined with **AND**.

Potential condition inputs shown or inferred:

- Date
- Year
- Age
- Savings rate
- Net worth
- Savings balance
- Taxable investment balance
- TFSA balance
- RRSP balance
- Account-specific metrics

## Milestone templates

Visible templates:

- Custom Milestone
- Move
- Financial Independence
- FIRE
- LeanFIRE
- FatFIRE
- CoastFIRE
- Debt Free
- Start School
- Graduate
- Gap Year
- New Job
- Get Married
- Kid

Templates appear to define:

- Name
- Icon
- Colour
- Default rule
- Suggested timing

---

# 16. Income

Canadian plans automatically include:

- OAS
- CPP

## OAS form

Observed fields:

- Name
- Claiming age
- Full Canadian residency toggle
- Estimated annual OAS
- Include GIS when eligible
- Expandable explanation
- Save
- Cancel

The estimated benefit updates when claiming age changes.

## CPP form

Observed fields:

- Name
- Estimated monthly CPP benefit at age 65
- Service Canada reference
- Claiming age
- Estimated annual benefit
- Expandable explanation
- Save
- Cancel

CPP appears to rely on a user-entered age-65 estimate rather than reconstructing the user's full contribution history.

## Income templates

Visible types:

- Salary
- Hourly Wage
- RSU Grant
- Inheritance
- Side Hustle
- Tax Credit
- Tax Deduction
- Pension Income
- Custom Income

## Common income form structure

Common sections:

- Name
- Amount
- Frequency
- Time Range
- Change Over Time
- Tax Handling
- Send To
- Recurrence
- More Options

## Hourly Wage

Observed fields:

- Hourly rate
- Hours per week
- Tax type
- Withholding
- Tax-exempt toggle

## Side Hustle

Observed fields:

- Starting amount
- Frequency
- Self-employment tax classification
- Withholding
- Passive-income treatment
- Tax-exempt toggle

## Inheritance

Observed concepts:

- One-time amount
- Timing
- Advanced options
- Destination account or default cash-flow handling

## Custom Income

Observed concepts:

- Time range
- Growth rule
- Tax handling
- Destination
- Recurrence

## Send To

Income can:

- Follow normal cash-flow rules
- Potentially be sent directly to a chosen account or destination

---

# 17. Cash-Flow Flows

Flows are ordered priorities for allocating available income.

The interface explains that income is processed from top to bottom.

Example:

```text
#1 Taxable Investments
#2 Student Loan Payments
Save anything left over
```

This ordering is central to the application's cash-flow engine.

## Flow tabs

The New Flow dialog contains:

- Existing Accounts
- Add Account

## Visible flow destinations

- Cash
- Taxable Investments
- RRSP
- TFSA
- Debt
- Transfer — premium

## Investment flow

Observed fields:

- Flow name
- Destination account
- Goal section
- Contribution method
- Amount or percentage

Visible method:

```text
% of Remaining Income
```

## Cash presets

Visible presets:

- Emergency Fund
- Cash Reserves

## Funding and spending controls

Funding:

- Fund with Income

Spending:

- Avoid Drawdown
- Allow Drawdown

Interpretation:

- Avoid Drawdown protects the balance and uses it only as a last resort
- Allow Drawdown makes the balance available to fund shortfalls

## Leftover handling

The bottom priority can be:

```text
Save anything left over
```

This acts as a catch-all after explicit flows are processed.

---

# 18. Expenses

Visible expense templates:

- Living Expenses
- Rent
- Debt
- Student Loans
- Dependent
- Education
- Health Care
- Vacation
- Wedding
- Charity
- Travel
- Medical Expenses
- Emergency
- Custom Expense

## Common expense structure

- Name
- Starting Amount
- Frequency
- Time Range
- Change Over Time
- Tax Options
- Pay From
- Flexibility
- More Options

The Living Expenses form links to an external cost-of-living estimator.

## Expense flexibility

Observed classes:

### Essential

Required spending.

### Discretionary

Spending that can be eliminated.

### Hybrid

Only a specified percentage is discretionary.

### Not Spending

The item remains an expense but is excluded from the application's Spending metric.

These classifications likely influence:

- Flexible-spending optimization
- Failure analysis
- Historical success
- Spending metrics

---

# 19. Real Assets in Plans

Current assets can be imported and marked:

```text
Linked to Current Finances
```

This indicates plan assets may reference master assets rather than duplicate them.

## Real-asset templates

- House
- Car
- Rental Property
- Commercial Property
- Land
- Building
- Motorcycle
- Boat
- Jewelry
- Precious Metals
- Furniture
- Instrument
- Machinery
- Custom Asset

Rental and commercial property appeared premium-gated.

## Common real-asset structure

- Name
- Purchase
- Change Over Time
- Taxes
- Expenses
- Sale
- Recurrence
- More Options

## Linked car example

Observed:

- Purchase price
- Annual depreciation
- Taxes
- Ownership expenses
- Maintenance
- Never sold
- Optional recurrence

## Machinery example

Observed default concepts:

- Purchased now
- Negative annual appreciation or depreciation
- Property-tax percentage
- Insurance percentage
- Maintenance percentage
- Never sold
- Recurrence off

A real asset should therefore support:

- Acquisition
- Financing
- Appreciation or depreciation
- Annual ownership costs
- Taxes
- Sale
- Recurrence or replacement

---

# 20. Main Plan Workspace

The main plan screen includes:

- Large interactive projection chart
- Metric dropdown
- Age and year horizontal axis
- Currency vertical axis
- Milestone markers
- Current-age marker
- Net Worth
- Liquid Net Worth
- Portfolio Allocations
- Display Options
- Lower data sections

Lower plan sections:

- Accounts
- Income
- Expenses
- Real Assets
- Flows

---

# 21. Chart Behaviour

Observed interactions:

- Hovering reveals year
- Hovering reveals age
- Hovering reveals metric value
- Vertical crosshair follows the selected year
- Milestones appear as coloured icons
- Charts update after input changes
- Alternative chart modes include stacked account balances

Visible or publicly described chart metrics include:

- Net Worth
- Change in Net Worth
- Liquid Net Worth
- Income
- Taxable Income
- Taxes
- Effective Tax Rate
- Spending
- Expenses
- Savings Rate
- Contributions
- Transfers
- Tax Balance
- Portfolio Allocation
- Income metrics

Display Options control:

- Time range
- Chart appearance
- Other display preferences

A separate toolbar allows quick experimentation with retirement age and other plan variables.

---

# 22. Visible Canadian Sandbox Examples

## Income cards

### My Job

```text
CA$170K
Before Current Year → Retirement
Increased to match inflation
25% withholding
```

### OAS — You

```text
CA$8.91K
Feb 2031
```

### CPP — You

```text
CA$0
Feb 2031
```

## Expense cards

### Living Expenses

```text
CA$35K
Before Current Year → End of Plan
+6% per year up to CA$40K
```

### Vacation

```text
CA$2.5K
Before Current Year → End of Plan -10
Increased to match inflation
```

### Health Care

```text
CA$8K
Retirement → End of Plan
Increased to match inflation
```

### Medical Expenses

```text
CA$20K
End of Plan -10 → End of Plan
Increased to match inflation
```

These examples confirm support for:

- Milestone-relative dates
- End-of-plan offsets
- Inflation indexing
- Custom annual growth
- Growth caps
- Withholding assumptions
- Ownership

---

# 23. Chance of Success

The free version runs approximately 196 historical trials.

Observed presentation:

- Circular success percentage
- Outcome bands
- Number and percentage of trials per band

Visible categories:

- Large Surplus
- Comfortable
- Barely Made It
- Almost Made It

Premium-gated details include:

- Deeper outcome distributions
- Detailed failure analysis
- Additional scenario diagnostics

## Likely implementation

A clean-room version can use:

- Historical rolling return sequences
- Fixed-length retirement trials
- Inflation-adjusted spending
- End-balance classification
- Shortfall detection
- Outcome bands

The exact ProjectionLab historical dataset is not known.

---

# 24. Plan Settings

## Milestones

Settings include:

- Retirement milestone
- Life-expectancy milestone
- Financial-independence milestone
- User-created milestones

Milestones can be:

- Date-based
- Age-based
- Year-based
- Formula-based

## Rates

Three modes:

- Fixed
- Historical
- Advanced

Historical mode includes:

- Historical sequence selection
- Inflation
- Stock returns
- Bond returns

Advanced mode allows separate rate paths by year for:

- Inflation
- Stock growth
- Stock dividend yield
- Bond returns

## Dividends

Canadian stock dividends are divided into:

- Eligible Canadian dividends
- Non-eligible Canadian dividends
- Foreign dividends

Visible example:

- 25% eligible
- 0% non-eligible
- 75% foreign

Dividend reinvestment can be controlled globally, with account-level overrides.

## Bonds

Bond allocation can be:

- None
- Based on portfolio allocation

Accounts can also have individual bond percentages.

## Tax

Observed settings:

- Automatic tax estimation
- Custom tax configuration
- Country template
- Province template
- Apply Canadian tax template
- Withholding assumptions
- Tax-deferred withdrawals
- Taxable withdrawals
- Account conversions
- Global income-tax modifier
- Restore defaults

## Simulation-year alignment

The application supports different simulation-year alignment options, including calendar-year alignment and per-plan overrides.

---

# 25. Scenario Comparison

Public documentation describes What-If mode as:

- Keeping the original plan as a dashed baseline
- Overlaying a changed plan
- Updating milestone outcomes
- Listing modifications
- Comparing summary metrics
- Supporting plan-to-plan comparison

Potential compared metrics include:

- Cash flow
- Savings
- Net worth
- Milestone timing
- Success rate

---

# 26. Withdrawal Strategies

Public documentation identifies strategies such as:

- Initial Percentage
- Ratcheting Safe Withdrawal Rate
- Variable Percentage Withdrawal
- Guyton-Klinger

These modes begin at a selected year or milestone and can override normal plan logic.

Without a selected withdrawal strategy, the application appears to calculate withdrawals based on the obligations that need to be funded.

---

# 27. Premium Boundaries

Observed premium or partially premium areas:

- Progress history
- Cash Flow Sankey
- Tax Analytics
- Advanced Chance of Success
- Compare
- Advanced tax optimization
- Flexible-spending optimization
- Drawdown optimization
- Gain harvesting
- Estate planning
- Some report functionality
- Transfers between accounts
- Certain property types
- Historical data or advanced projections

The MVP does not need to reproduce every premium area.

---

# 28. Inferred Simulation Engine

Public documentation indicates that ProjectionLab simulates each full year and reports year-end results.

A plausible clean-room annual sequence is:

```text
Opening balances
→ Process milestone state
→ Process income
→ Apply withholding
→ Process government benefits
→ Process mandatory account activity
→ Process expenses
→ Process debt payments
→ Apply ordered contribution flows
→ Cover shortfalls using drawdown rules
→ Calculate taxes
→ Process taxes due or refunds
→ Apply dividends and investment returns
→ Apply asset appreciation or depreciation
→ Update debts
→ Store closing balances
```

The exact order must be independently chosen and documented.

## Important sequencing questions

- Are returns applied before or after withdrawals?
- Are contributions invested immediately?
- Are taxes paid in the current year or following year?
- Are dividends treated separately from price growth?
- Are debt payments processed before savings flows?
- Are essential expenses covered before all contributions?
- How are negative balances prevented?
- How are tax refunds handled?
- How are account conversions represented?

---

# 29. Recommended Clean Data Model

## Entity overview

```text
User
├── People
├── Current Finances
│   ├── Savings Accounts
│   ├── Investment Accounts
│   ├── Real Assets
│   └── Debts
└── Plans
    ├── Milestones
    ├── Accounts
    ├── Income
    ├── Expenses
    ├── Real Assets
    ├── Flows
    ├── Assumptions
    ├── Tax Settings
    └── Simulation Results
```

## Person

```text
id
name
birthMonth
birthYear
country
province
currency
locale
relationshipRole
```

## Account

```text
id
name
ownerId
accountType
currency
balance
costBasis
taxTreatment
portfolioAllocation
dividendTreatment
drawdownRule
linkedCurrentFinanceId
notes
```

## Debt

```text
id
name
ownerId
debtType
balance
interestRate
compoundingMethod
paymentFrequency
paymentAmount
startDate
endDate
```

## Milestone

```text
id
planId
name
templateType
icon
colour
conditionJoinType
conditions[]
```

## Milestone Condition

```text
metric
operator
value
unit
relativeMilestoneId
offset
```

## Income

```text
id
planId
ownerId
incomeType
name
amount
frequency
startRule
endRule
growthRule
taxTreatment
withholdingRate
destinationRule
recurrenceRule
advancedOptions
```

## Expense

```text
id
planId
ownerId
expenseType
name
amount
frequency
startRule
endRule
growthRule
taxTreatment
paymentSource
flexibilityType
discretionaryPercentage
recurrenceRule
advancedOptions
```

## Flow

```text
id
planId
priority
name
destinationType
destinationAccountId
fundingMethod
amount
percentage
targetBalance
drawdownRule
isCatchAll
```

## Real Asset

```text
id
planId
ownerId
assetType
name
purchaseRule
purchasePrice
currentValue
appreciationRule
taxRule
expenseRules
financingRule
saleRule
recurrenceRule
linkedCurrentFinanceId
```

## Assumptions

```text
mode
inflationRate
stockGrowthRate
stockDividendYield
bondReturnRate
historicalSequence
advancedRateCurves
dividendMix
reinvestmentDefault
simulationYearAlignment
```

## Tax Settings

```text
country
province
automaticEstimation
templateVersion
withholdingRules
deferredWithdrawalRules
taxableWithdrawalRules
conversionRules
globalTaxModifier
```

---

# 30. Reusable Form Components

The recordings show a strongly componentized form architecture.

Reusable components should include:

- Name field
- Amount field
- Currency field
- Frequency selector
- Owner selector
- Time Range
- Change Over Time
- Tax Handling
- Pay From
- Send To
- Flexibility
- Recurrence
- More Options
- Account selector
- Milestone selector
- Relative-date selector
- Growth cap
- Percentage or fixed-amount selector
- Save and Cancel footer

This approach will simplify implementation across income, expenses, flows, and assets.

---

# 31. Recommended MVP Scope

## Phase 1: Application shell

- Authentication or local-only user
- Dark theme
- Fixed sidebar
- Dashboard
- Current Finances
- Plans list
- New-plan wizard

## Phase 2: Current Finances

- Individual or couple
- Savings
- Taxable investments
- TFSA
- RRSP
- Real assets
- Debts
- Net-worth summary

## Phase 3: Plan builder

- Retirement milestone
- Life expectancy
- Financial independence
- Salary
- CPP
- OAS
- Recurring expenses
- Ordered flows
- Real assets
- Basic assumptions

## Phase 4: Projection engine

- Annual deterministic simulation
- Income
- Expenses
- Contributions
- Withdrawals
- Returns
- Inflation
- Debts
- Basic taxes
- Net worth
- Liquid net worth

## Phase 5: Historical success

- Historical rolling trials
- Success percentage
- Outcome bands
- End-balance distribution
- Failure-year display

## Phase 6: Canadian improvements

- Province-specific tax estimates
- RRSP deductions
- RRSP withdrawals
- RRIF conversion
- TFSA room
- CPP
- OAS
- GIS
- Eligible dividends
- Non-eligible dividends
- Foreign dividends
- Capital gains

## Phase 7: Scenario tools

- What-If comparison
- Duplicate plan
- Baseline overlay
- Retirement-age slider
- Spending adjustment
- Return adjustment

---

# 32. Remaining Interface Unknowns

Narrow gaps remain in:

- Complete Time Range options
- Complete Change Over Time methods
- Complete Tax Options
- Complete Pay From choices
- Full Recurrence settings
- Contents of More Options
- Full Salary form
- RSU Grant form
- Tax Credit form
- Tax Deduction form
- Pension Income form
- Detailed home and mortgage form
- Every flow-goal option
- Plan-source dropdown
- Portfolio-allocation editor
- Metrics settings
- Reports contents
- Form validation
- Error states
- Mobile behaviour
- Light theme
- Delete confirmations

These gaps do not block MVP development.

---

# 33. Remaining Calculation Unknowns

The most important unresolved questions are:

- Exact annual transaction order
- Exact Canadian federal tax implementation
- Exact provincial tax implementation
- RRSP deduction timing
- RRSP withdrawal withholding
- RRIF conversion timing
- RRIF minimum withdrawals
- TFSA contribution-room carryforward
- TFSA withdrawal room restoration
- CPP benefit adjustment by claiming age
- OAS adjustment by claiming age
- OAS recovery tax
- GIS eligibility
- Dividend tax credits
- Capital-gain inclusion
- Adjusted cost base
- Realized versus unrealized gains
- Principal-residence exemption
- Spousal ownership
- Death of one spouse
- Estate tax treatment
- Withdrawal ordering
- Account shortfall logic
- Historical market-data source
- Sequence start and end conventions

These should be implemented from official Canadian sources and transparently documented.

---

# 34. Recommended Validation Scenarios

Use simple controlled scenarios.

## Scenario 1: Salary and cash

- One person
- CA$100,000 salary
- No investments
- CA$40,000 expenses
- Fixed tax rate
- Confirm annual surplus

## Scenario 2: RRSP contribution

- Salary
- RRSP contribution flow
- Confirm contribution amount
- Confirm deduction
- Confirm tax change
- Confirm RRSP balance

## Scenario 3: TFSA

- Annual TFSA contribution
- Withdrawal
- Contribution-room restoration next year
- Growth

## Scenario 4: Retirement drawdown

- Salary ends at retirement
- Expenses continue
- Withdraw from cash
- Then taxable account
- Then RRSP
- Verify shortfall logic

## Scenario 5: CPP and OAS

- Compare claiming ages
- Confirm annual benefit differences
- Test OAS recovery tax

## Scenario 6: Historical trial

- Fixed retirement age
- Fixed spending
- Historical stock and bond returns
- Confirm end balances across rolling periods

## Scenario 7: Real asset

- Purchase a house
- Mortgage
- Appreciation
- Maintenance
- Sale
- Verify net-worth impact

---

# 35. Additional Recording Guidance

No further broad recording is needed.

A future targeted recording would only be useful for:

- Portfolio allocation editor
- Metrics settings
- Reports
- Advanced Salary options
- Advanced Tax Options
- Advanced Pay From options
- Mortgage setup
- Recurrence
- More Options
- Form validation and error states

These should be captured only when needed for close field-by-field replication.

---

# 36. Safe Capture Practices

When recording or exporting:

- Use sandbox personas
- Use dummy accounts
- Avoid real names
- Avoid real balances
- Hide email addresses
- Do not expose cookies
- Do not expose authorization headers
- Do not share bearer tokens
- Do not share plugin API keys
- Do not share session IDs
- Do not upload HAR files without sanitizing
- Use fictional financial data

---

# 37. Source References

Public resources referenced during research included:

- ProjectionLab Help Centre  
  https://projectionlab.com/help/

- ProjectionLab Canada information  
  https://projectionlab.com/canada

- ProjectionLab Changelog  
  https://projectionlab.com/changelog

- ProjectionLab plugin documentation  
  https://projectionlab.com/help/plugins

- ProjectionLab getting-started documentation  
  https://projectionlab.com/help/how-to-get-started

- ProjectionLab simulation-engine documentation  
  https://projectionlab.com/help/simulation-engine

- ProjectionLab What-If documentation  
  https://projectionlab.com/help/using-what-if

- ProjectionLab withdrawal-strategy documentation  
  https://projectionlab.com/help/withdrawal-strategy-mode

- ProjectionLab RRSP-meltdown documentation  
  https://projectionlab.com/help/rrsp-meltdown

- Ignidash  
  https://github.com/schelskedevco/ignidash

- Retire, Eh?  
  https://github.com/halfguru/retire-eh

These links should be rechecked during implementation because product documentation and feature availability may change.

---

# 38. Final Assessment

The available research is sufficient to move from product discovery into:

- Formal requirements
- Wireframes
- Database design
- Simulation-engine design
- MVP implementation
- Canadian tax research
- Validation testing

The recommended next artifact is a technical specification containing:

- Final MVP scope
- Page-by-page requirements
- Database schema
- Simulation sequence
- Canadian calculation modules
- API contracts
- Component library
- Development milestones
- Test cases
