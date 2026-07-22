# Ignidash — Code Audit

**Repository:** `schelskedevco/ignidash`  
**Audit date:** 2026-07-22  
**Default branch:** `main`  
**Version in audited package metadata:** `0.2.0`  
**License:** AGPL-3.0-only  
**Audit purpose:** Evaluate Ignidash as an architectural and simulation reference for a Canadian, ProjectionLab-inspired financial-planning application.

---

## 1. Executive Assessment

Ignidash is a significantly broader and more production-oriented application than Retire, Eh?. It provides:

- Persisted financial plans
- Plan snapshots
- Assets and liabilities
- Income and expenses
- Accounts
- Contribution rules
- Market assumptions
- Tax settings
- Simulation settings
- Glide paths
- Monte Carlo simulation
- Historical backtesting
- US tax estimation
- AI chat and generated insights
- Authentication
- Billing
- Analytics
- Docker self-hosting
- Unit and end-to-end testing

Its architecture is highly relevant to a ProjectionLab-inspired application.

However, it has three major constraints:

1. **AGPL-3.0 licensing**
2. **US-centric tax and retirement logic**
3. **A larger SaaS stack than a personal MVP requires**

### Recommendation

Use Ignidash primarily as:

- A simulation architecture reference
- A schema and validation reference
- A testing reference
- A historical-backtesting and Monte Carlo reference
- A source of UI and state-management ideas
- A reference for worker-based simulation processing

Avoid directly copying substantial code unless the project is intentionally AGPL-compatible and its source-disclosure obligations are acceptable.

---

## 2. Product Scope

Ignidash describes itself as a web-based long-term financial and retirement planner rather than a budgeting application.

Documented current capabilities:

- Monte Carlo simulations
- Historical backtesting
- US tax estimation
- AI plan chat
- AI educational insights
- Debts
- Physical assets

Documented roadmap items include:

- Configurable drawdown order
- State and local taxes
- IRMAA
- Roth conversions
- SEPP
- Custom goals and milestones
- Couple planning
- Net-worth tracking from market data
- Plan comparison

This indicates the application is actively evolving and some ProjectionLab-like features remain incomplete.

---

## 3. Technology Stack

### Application

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4

### Persistence and backend

- Convex database
- Convex server functions
- Convex agents
- Convex migrations
- Convex rate limiting
- Convex Resend integration

### Authentication and billing

- Better Auth
- Google OAuth
- Stripe

### AI

- Azure OpenAI
- OpenAI SDK
- Convex agent tooling

### UI and visualization

- Recharts
- Headless UI
- Radix Tooltip and Scroll Area
- Heroicons
- Lucide
- Framer Motion
- Embla Carousel
- DnD Kit

### Forms and validation

- React Hook Form
- Zod
- Number formatting

### State and data access

- Zustand
- SWR
- Immer
- Convex reactive queries

### Simulation processing

- Comlink is included, suggesting worker-mediated computation
- Browser or worker calculation architecture should be inspected before reuse

### Quality and operations

- Vitest
- Playwright
- ESLint
- Prettier
- Husky
- lint-staged
- Docker Compose
- Self-host scripts
- PostHog
- Vercel Analytics

---

## 4. Repository Scale and Complexity

Ignidash is a full SaaS application, not merely a calculator.

Its dependency graph includes:

- Database
- Authentication
- Billing
- Email
- AI
- Product analytics
- Multiple UI libraries
- Simulation code
- End-to-end tests
- Self-hosting tooling

### Implication

Adopting the entire application would import substantial operational complexity.

For a personal application, many components are unnecessary:

- Stripe
- Google OAuth
- Azure OpenAI
- Resend
- PostHog
- Vercel Analytics
- Multi-tenant Convex infrastructure

The simulation and domain modules should be evaluated separately from the SaaS shell.

---

## 5. Audited Persisted Schema

The top-level Convex schema includes these tables:

```text
plans
planSnapshots
finances
conversations
messages
userFeedback
insights
onboarding
```

## 5.1 Plans

Each plan stores:

```text
userId
name
isDefault
timeline
incomes[]
expenses[]
debts[]
physicalAssets[]
accounts[]
glidePath
contributionRules[]
baseContributionRule
marketAssumptions
taxSettings
privacySettings
simulationSettings
```

This is a strong domain decomposition for a financial-planning application.

## 5.2 Plan snapshots

Snapshots contain the same plan-data fields plus:

```text
planId
userId
```

This supports:

- Historical plan versions
- Scenario reproducibility
- Comparison
- Simulation consistency
- Auditability

## 5.3 Finances

Current finances are stored separately from plans:

```text
userId
assets[]
liabilities[]
```

This mirrors the useful ProjectionLab distinction between:

- Current financial position
- Future plan configuration

## 5.4 AI conversations

Stored fields include:

```text
userId
planId
title
updatedAt
systemPrompt
includeSimData
```

Messages store:

```text
userId
conversationId
author
body
usage
updatedAt
duration
loading state
```

## 5.5 Insights

Generated insights are plan-linked and store:

- Content
- Prompt
- Token usage
- Timing
- Loading state

## 5.6 Onboarding

Onboarding state is persisted separately:

```text
userId
onboardingDialogCompleted
```

---

## 6. Domain Model Assessment

The audited `planDataFields` module validates the following domains independently:

- Timeline
- Income
- Expenses
- Debt
- Physical assets
- Accounts
- Glide path
- Contribution rules
- Base contribution rule
- Market assumptions
- Tax settings
- Privacy settings
- Simulation settings

### Strengths

- Clear separation of concerns
- Shared schema between plans and snapshots
- Runtime validation
- Optional migration path for newer domains
- Easy plan serialization
- Simulation inputs are explicit

### Relevance to our project

This is very close to the top-level schema needed for a ProjectionLab-inspired product.

Potential adapted model:

```text
Plan
├── timeline and milestones
├── people
├── accounts
├── incomes
├── expenses
├── debts
├── physical assets
├── flows and contribution rules
├── portfolio glide path
├── market assumptions
├── tax settings
├── simulation settings
└── snapshots
```

---

## 7. Current-Finances Separation

Ignidash stores `finances` independently from `plans`.

This is strategically important.

### Benefits

- A user's real balance sheet can be updated independently
- Multiple plans can start from one financial state
- Plans can snapshot balances without mutating the source
- Current financial tracking does not become entangled with scenario assumptions
- Plan comparison becomes simpler

### Recommendation

Adopt this concept directly in the clean-room design:

```text
CurrentFinances
Plan
PlanSnapshot
SimulationRun
```

A plan should reference or copy a versioned current-finances snapshot.

---

## 8. Simulation Capability

The README confirms two major simulation modes:

### Monte Carlo

- Hundreds of trials
- Probability-of-success calculation
- Risk identification
- Variable return paths

### Historical backtesting

- Uses actual historical market data
- Tests a plan across historical starting periods
- Exposes sequence-of-returns risk

### Why this matters

ProjectionLab's Chance of Success feature is conceptually closer to Ignidash than to Retire, Eh?.

### Areas that require deeper code-level validation before reuse

- Random-return distribution
- Correlation assumptions
- Inflation modelling
- Stock/bond return decomposition
- Trial count
- Rebalancing
- Fees
- Return timing
- Withdrawal timing
- Historical data sources
- Failure definition
- Success threshold
- End-of-plan classification
- Deterministic seeding
- Worker architecture

These details should be independently documented before treating results as financially credible.

---

## 9. Tax Architecture

Ignidash currently emphasizes US tax estimation.

Documented or roadmap-related topics include:

- Federal income taxes
- RMDs
- Roth conversions
- Asset location
- Withdrawal strategies
- State and local taxes
- IRMAA
- SEPP

### Implication for a Canadian application

The tax framework and interface patterns may be reusable, but the calculations are not.

Canadian replacements would need:

- Federal tax brackets
- Provincial tax brackets
- Basic personal amount
- Age amount
- Pension credit
- CPP and EI treatment
- RRSP deductions
- RRSP/RRIF withdrawals
- TFSA room
- Eligible dividends
- Non-eligible dividends
- Foreign dividends
- Capital gains
- OAS recovery tax
- GIS
- RRIF minimums
- Spousal and survivor rules

### Recommendation

Reuse architecture, not formulas.

---

## 10. Contribution Rules and Glide Paths

The schema includes:

- Multiple contribution rules
- One base contribution rule
- Glide path
- Accounts
- Market assumptions

This suggests a more flexible planning engine than Retire, Eh?.

Likely supported concepts include:

- Contribution routing
- Account-specific funding
- Rule prioritization
- Portfolio allocation changes over time
- Account-specific retirement handling

These concepts align well with ProjectionLab's ordered flows and portfolio-allocation controls.

### Clean-room adaptation

Convert contribution rules into explicit ordered cash-flow rules:

```text
priority
source
destination
condition
method
amount
percentage
target
start rule
end rule
drawdown policy
```

---

## 11. Snapshots and Reproducibility

Plan snapshots are one of Ignidash's strongest architectural choices.

A simulation result should be tied to:

- Plan snapshot ID
- Engine version
- Tax-data version
- Market-data version
- Random seed
- Simulation settings
- Run timestamp

This makes simulation outputs:

- Reproducible
- Auditable
- Comparable
- Easier to debug

### Recommendation

Adopt snapshots early rather than adding them later.

---

## 12. AI Features

Ignidash includes:

- Plan-aware chat
- Generated educational insights
- Optional inclusion of simulation data
- Token and latency tracking
- Stored conversations

### Value

- Explaining financial outcomes
- Guiding users through assumptions
- Summarizing risks
- Educational context

### Risks

- Privacy
- Hallucinations
- Financial-advice boundaries
- Token cost
- Prompt injection
- Sensitive plan data leaving the local environment
- Need to distinguish calculations from generated explanations

### Recommendation

AI should not be part of the MVP calculation engine.

If added later:

- Use AI only to explain deterministic outputs
- Never let AI calculate authoritative figures
- Show underlying numeric sources
- Make inclusion of plan data explicit
- Provide a no-AI local mode

---

## 13. Authentication, Billing, and Analytics

Ignidash includes a commercial SaaS shell:

- Better Auth
- Google OAuth
- Stripe
- Resend
- PostHog
- Vercel Analytics

For a personal project, these should be excluded initially.

### Simpler alternatives

- Local-only mode
- Single-user password
- Self-hosted account
- SQLite/PostgreSQL
- No billing
- No telemetry by default

---

## 14. Testing and Quality

The package defines:

- Vitest unit tests
- Coverage reporting
- Playwright end-to-end tests
- Type checking
- ESLint
- Prettier
- Husky hooks
- lint-staged

### Strong practices to adopt

- Unit tests for formulas
- Validator tests
- Golden simulation fixtures
- E2E plan-creation tests
- Migration tests
- Snapshot reproducibility tests
- Tax-year regression fixtures
- Historical-data integrity tests

### Financial-engine-specific additions

- Deterministic random seeds
- Conservation-of-cash checks
- Balance-sheet identity checks
- No-negative-account invariant unless explicitly allowed
- Tax reconciliation checks
- Contribution-limit checks
- Historical sequence boundary tests

---

## 15. Deployment and Self-Hosting

Ignidash supports:

- Next.js development
- Convex local backend
- Docker Compose
- Self-host scripts
- Environment synchronization
- Separate frontend and backend services

### Advantages

- Production-style architecture
- Multi-user capabilities
- Reactive backend
- Hosted and self-hosted paths

### Costs

- Operational complexity
- More secrets
- More services
- More upgrade risk
- Convex-specific coupling
- Larger attack surface

For a personal homelab project, a simpler stack may be preferable:

```text
Next.js or React
PostgreSQL or SQLite
Background worker
Local simulation engine
Docker Compose
```

---

## 16. License Audit

Ignidash declares:

```text
AGPL-3.0-only
```

The GNU Affero General Public License is materially different from MIT.

### Practical concern

When modified AGPL software is made available to users over a network, users generally must be offered the corresponding source code under the AGPL.

### Implications

Directly incorporating substantial Ignidash code may require:

- Licensing the combined covered work under AGPL
- Publishing corresponding source
- Preserving notices
- Providing network users access to source
- Tracking modifications

### Recommendation

Before direct code reuse, decide whether the final project will be:

- Private and used only locally
- Open-source under AGPL-compatible terms
- Publicly hosted
- Commercial

For a proprietary or closed hosted product, treat Ignidash as a reference and independently reimplement concepts.

This is not legal advice.

---

## 17. Reusability Matrix

| Area | Recommendation |
|---|---|
| Top-level plan schema | Strong reference |
| Plan snapshots | Adopt concept |
| Current-finances separation | Adopt concept |
| Runtime validators | Adopt concept |
| Monte Carlo architecture | Study and reimplement |
| Historical backtesting | Study and reimplement |
| Simulation workers | Study |
| Contribution rules | Adapt concept |
| Glide paths | Adapt concept |
| US tax formulas | Do not reuse for Canada |
| SaaS authentication | Optional |
| Stripe integration | Exclude from MVP |
| AI chat | Exclude from MVP |
| Analytics | Exclude by default |
| UI components | Reference, license-sensitive |
| Convex backend | Optional |
| Tests | Strong reference |
| Direct code reuse | Only with AGPL decision |

---

## 18. Comparison with ProjectionLab Requirements

| ProjectionLab-inspired capability | Ignidash status |
|---|---|
| Current finances | Present |
| Multiple plans | Present |
| Plan snapshots | Present |
| Income | Present |
| Expenses | Present |
| Accounts | Present |
| Debts | Present |
| Physical assets | Present |
| Contribution rules | Present |
| Market assumptions | Present |
| Tax settings | Present, US-focused |
| Simulation settings | Present |
| Monte Carlo | Present |
| Historical trials | Present |
| Milestones | Roadmap or incomplete |
| Couple planning | Roadmap or incomplete |
| Compare plans | Coming soon |
| Canadian tax | Missing |
| CPP/OAS/GIS | Missing |
| RRSP/TFSA/RRIF | Missing as Canadian wrappers |
| Ordered ProjectionLab-style flows | Similar concept, requires adaptation |
| Estate modelling | Not established in audited files |
| Advanced optimizers | Partial or roadmap |

---

## 19. Recommended Clean-Room Extraction Plan

### Study from Ignidash

1. Plan schema
2. Plan snapshot lifecycle
3. Simulation input normalization
4. Worker boundaries
5. Historical-data loading
6. Monte Carlo trial execution
7. Aggregation of trial results
8. Success/failure definitions
9. Chart data transformations
10. Validator design
11. Simulation tests
12. Migration strategy

### Reimplement independently

- Canadian domain types
- Canadian tax engine
- Canadian account rules
- ProjectionLab-style milestones
- Ordered flow engine
- UI and branding
- Calculation explanations

---

## 20. Suggested Architecture for Our Project

```text
Web UI
├── Current Finances
├── Plan Builder
├── Projection Viewer
├── Chance of Success
└── Compare

Application API
├── Current finance service
├── Plan service
├── Snapshot service
├── Simulation service
└── Export/import service

Calculation Engine
├── Annual ledger
├── Tax engine
├── Account rules
├── Market return engine
├── Historical trials
├── Monte Carlo
└── Result aggregation

Persistence
├── People
├── Current finances
├── Plans
├── Plan snapshots
├── Simulation runs
└── Versioned assumptions
```

This retains the strongest Ignidash concepts without importing its entire SaaS stack.

---

## 21. Risks

### Technical

- Simulation complexity
- Performance with many trials
- Tax-year data updates
- Market-data quality
- Reproducibility
- Migration complexity
- Coupling between UI and engine

### Product

- Financial outputs may appear more precise than they are
- Users may misunderstand Monte Carlo probability
- Historical success is not a forecast
- Tax estimates may become stale
- AI explanations may overstate certainty

### Licensing

- Accidental copying of AGPL-covered code
- Mixing AGPL code with closed-source modules
- Incomplete attribution
- Hosting without source-offer compliance

---

## 22. Final Verdict

### Overall score as a direct code foundation: 5/10

This score is limited primarily by:

- AGPL implications
- US-centric logic
- Stack complexity

### Overall score as an architectural and simulation reference: 9/10

Ignidash is the stronger reference for:

- Plan persistence
- Simulation settings
- Historical testing
- Monte Carlo
- Snapshots
- Testing
- Full application architecture

Its best contribution to the new project is:

> A mature blueprint for structuring plans, simulations, snapshots, and a financial-planning SaaS—not a Canadian calculation engine.

---

## 23. Audited Primary Files

- `README.md`
- `package.json`
- `convex/schema.ts`
- `convex/validators/plan_data_fields.ts`

Repository:  
https://github.com/schelskedevco/ignidash
