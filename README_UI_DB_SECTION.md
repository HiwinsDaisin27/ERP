# TheSecond Construction ERP — UI & Database Design

> Site-centric construction management platform. Telegram handles field input. Web handles intelligence.

---

## Table of Contents

- [ER Diagram](#er-diagram)
- [Database Schema](#database-schema)
- [UI Wireframe Design](#ui-wireframe-design)
  - [Design System](#design-system)
  - [Login Page](#login-page)
  - [Operations Dashboard](#operations-dashboard)
  - [Payroll Workbook](#payroll-workbook)
  - [Navigation & Role Flow](#navigation--role-flow)
- [Frontend Environment Setup](#frontend-environment-setup)

---

## ER Diagram

Classic Chen notation — rectangles are entities, diamonds are relationships, ovals are attributes.

![ER Diagram](er_diagram.svg)

| Symbol | Meaning |
|--------|---------|
| 🟧 Rectangle (orange border) | Core entity (Sites, Users) |
| 🟥 Rectangle (red border) | Admin-only entity (Payroll, Budgets) |
| 🟩 Rectangle (green border) | Operational entity (Attendance, Materials) |
| ◇ Diamond | Relationship between entities |
| ○ Oval | Attribute of an entity |
| `1 — M` | One-to-many cardinality |
| Dashed line | Cross-module foreign key reference |

**Key relationships at a glance:**

- `SITES` is the central hub — every operational table has a `site_id` FK
- `WORKERS` → `ATTENDANCE_RECORDS` → `PAYROLL_LINE_ITEMS` is the attendance-to-payroll chain
- `MATERIAL_RECEIPTS` and `MATERIAL_CONSUMPTION` are both connected to `SITES` + `MATERIALS`
- `PAYROLL_RUNS`, `SITE_BUDGETS`, `WORKER_ADVANCES` are admin-only (red border)
- `AUDIT_LOGS` is a cross-cutting system table — not shown with a parent entity

---

## Database Schema

### Module Overview

| Module | Tables | Access |
|--------|--------|--------|
| Core | `sites`, `users`, `site_user_assignments` | All roles |
| Workforce | `workers`, `skill_categories`, `site_worker_allocations` | Supervisor (Telegram), Manager (Web) |
| Attendance | `attendance_records` | Supervisor (Telegram) |
| Inventory | `materials`, `suppliers`, `material_receipts`, `material_consumption` | Supervisor (Telegram) |
| Expenses & Budget | `expense_categories`, `site_expenses`, `site_budgets` | Supervisor (ops), Admin (budgets) |
| Progress | `site_milestones`, `site_progress_logs` | Supervisor (Telegram) |
| Payroll | `payroll_runs`, `payroll_line_items`, `worker_advances` | ⚠ Admin only |
| Audit | `audit_logs` | System only |

### Design Conventions

- **UUID** primary keys on all tables — safe for concurrent writes from Telegram + Web
- **`source ENUM(telegram, web)`** on all operational tables — tracks which channel created each record
- **`TIMESTAMPTZ`** on all timestamp columns — timezone-aware for field operations
- Payroll figures are never stored as running totals — always derived from line items at query time
- Current stock = `SUM(material_receipts.quantity) - SUM(material_consumption.quantity)` per site+material

### Full SQL Schema

<details>
<summary>Click to expand — Core entities</summary>

```sql
-- ─── SITES ────────────────────────────────────────────────────
CREATE TABLE sites (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(150) NOT NULL,
    location          TEXT,
    status            VARCHAR(20) NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'completed', 'on_hold')),
    start_date        DATE,
    expected_end_date DATE,
    actual_end_date   DATE,
    created_by        UUID REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── USERS ────────────────────────────────────────────────────
CREATE TABLE users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(120) NOT NULL,
    phone            VARCHAR(20) UNIQUE,
    telegram_chat_id BIGINT UNIQUE,
    role             VARCHAR(20) NOT NULL DEFAULT 'supervisor'
                     CHECK (role IN ('admin', 'manager', 'supervisor')),
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── SITE_USER_ASSIGNMENTS ────────────────────────────────────
CREATE TABLE site_user_assignments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id     UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at  TIMESTAMPTZ,
    UNIQUE (site_id, user_id)
);
```

</details>

<details>
<summary>Click to expand — Workforce</summary>

```sql
-- ─── SKILL_CATEGORIES ─────────────────────────────────────────
CREATE TABLE skill_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(80) NOT NULL UNIQUE,
    description TEXT
);

-- ─── WORKERS ──────────────────────────────────────────────────
CREATE TABLE workers (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(120) NOT NULL,
    phone             VARCHAR(20) UNIQUE,
    skill_category_id UUID REFERENCES skill_categories(id),
    daily_wage_rate   NUMERIC(10,2) NOT NULL DEFAULT 0,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at         DATE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workers_name ON workers(name);

-- ─── SITE_WORKER_ALLOCATIONS ──────────────────────────────────
CREATE TABLE site_worker_allocations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id      UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    worker_id    UUID NOT NULL REFERENCES workers(id),
    allocated_by UUID REFERENCES users(id),
    start_date   DATE NOT NULL,
    end_date     DATE,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

</details>

<details>
<summary>Click to expand — Attendance</summary>

```sql
-- ─── ATTENDANCE_RECORDS ───────────────────────────────────────
CREATE TABLE attendance_records (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id        UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    worker_id      UUID NOT NULL REFERENCES workers(id),
    date           DATE NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'present'
                   CHECK (status IN ('present', 'absent', 'half_day', 'holiday')),
    check_in_time  TIME,
    check_out_time TIME,
    overtime_hours NUMERIC(4,2) NOT NULL DEFAULT 0,
    recorded_by    UUID REFERENCES users(id),
    source         VARCHAR(10) NOT NULL DEFAULT 'telegram'
                   CHECK (source IN ('telegram', 'web')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (site_id, worker_id, date)
);

CREATE INDEX idx_attendance_date ON attendance_records(date);
CREATE INDEX idx_attendance_site ON attendance_records(site_id);
```

</details>

<details>
<summary>Click to expand — Inventory & Materials</summary>

```sql
-- ─── MATERIALS ────────────────────────────────────────────────
CREATE TABLE materials (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(120) NOT NULL,
    unit       VARCHAR(30) NOT NULL,
    category   VARCHAR(60),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_materials_name ON materials(name);

-- ─── SUPPLIERS ────────────────────────────────────────────────
CREATE TABLE suppliers (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(150) NOT NULL,
    phone      VARCHAR(20),
    address    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── MATERIAL_RECEIPTS ────────────────────────────────────────
CREATE TABLE material_receipts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id       UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    material_id   UUID NOT NULL REFERENCES materials(id),
    supplier_id   UUID REFERENCES suppliers(id),
    quantity      NUMERIC(12,3) NOT NULL,
    unit_price    NUMERIC(10,2),
    total_amount  NUMERIC(12,2),
    received_date DATE NOT NULL DEFAULT CURRENT_DATE,
    received_by   UUID REFERENCES users(id),
    invoice_ref   VARCHAR(80),
    source        VARCHAR(10) NOT NULL DEFAULT 'telegram'
                  CHECK (source IN ('telegram', 'web')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_receipts_site_date ON material_receipts(site_id, received_date);

-- ─── MATERIAL_CONSUMPTION ─────────────────────────────────────
CREATE TABLE material_consumption (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id              UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    material_id          UUID NOT NULL REFERENCES materials(id),
    quantity             NUMERIC(12,3) NOT NULL,
    consumed_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    activity_description TEXT,
    recorded_by          UUID REFERENCES users(id),
    source               VARCHAR(10) NOT NULL DEFAULT 'telegram'
                         CHECK (source IN ('telegram', 'web')),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_consumption_site_date ON material_consumption(site_id, consumed_date);
```

</details>

<details>
<summary>Click to expand — Expenses & Budget</summary>

```sql
-- ─── EXPENSE_CATEGORIES ───────────────────────────────────────
CREATE TABLE expense_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(80) NOT NULL UNIQUE,
    description TEXT
);

-- ─── SITE_EXPENSES ────────────────────────────────────────────
CREATE TABLE site_expenses (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id      UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    category_id  UUID REFERENCES expense_categories(id),
    amount       NUMERIC(12,2) NOT NULL,
    description  TEXT,
    expense_date DATE NOT NULL DEFAULT CURRENT_DATE,
    recorded_by  UUID REFERENCES users(id),
    receipt_ref  VARCHAR(80),
    source       VARCHAR(10) NOT NULL DEFAULT 'telegram'
                 CHECK (source IN ('telegram', 'web')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_expenses_site_date ON site_expenses(site_id, expense_date);

-- ─── SITE_BUDGETS (admin only) ────────────────────────────────
CREATE TABLE site_budgets (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id          UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    budget_type      VARCHAR(20) NOT NULL
                     CHECK (budget_type IN ('labour', 'material', 'overhead', 'total')),
    allocated_amount NUMERIC(14,2) NOT NULL,
    effective_from   DATE NOT NULL,
    effective_to     DATE,
    created_by       UUID REFERENCES users(id),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

</details>

<details>
<summary>Click to expand — Progress & Milestones</summary>

```sql
-- ─── SITE_MILESTONES ──────────────────────────────────────────
CREATE TABLE site_milestones (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id        UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    title          VARCHAR(200) NOT NULL,
    description    TEXT,
    target_date    DATE,
    completed_date DATE,
    status         VARCHAR(20) NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'in_progress', 'completed', 'delayed')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── SITE_PROGRESS_LOGS ───────────────────────────────────────
CREATE TABLE site_progress_logs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id           UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    log_date          DATE NOT NULL DEFAULT CURRENT_DATE,
    summary           TEXT NOT NULL,
    weather_condition VARCHAR(60),
    workers_present   SMALLINT,
    recorded_by       UUID REFERENCES users(id),
    source            VARCHAR(10) NOT NULL DEFAULT 'telegram'
                      CHECK (source IN ('telegram', 'web')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_progress_site_date ON site_progress_logs(site_id, log_date);
```

</details>

<details>
<summary>Click to expand — Payroll (⚠ Admin only)</summary>

```sql
-- ─── PAYROLL_RUNS ─────────────────────────────────────────────
CREATE TABLE payroll_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id      UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end   DATE NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'draft'
                 CHECK (status IN ('draft', 'finalised', 'paid')),
    total_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    generated_by UUID REFERENCES users(id),
    finalised_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── PAYROLL_LINE_ITEMS ───────────────────────────────────────
CREATE TABLE payroll_line_items (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_run_id    UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    worker_id         UUID NOT NULL REFERENCES workers(id),
    days_present      NUMERIC(5,1) NOT NULL DEFAULT 0,
    days_absent       NUMERIC(5,1) NOT NULL DEFAULT 0,
    overtime_hours    NUMERIC(5,2) NOT NULL DEFAULT 0,
    base_amount       NUMERIC(12,2) NOT NULL DEFAULT 0,
    overtime_amount   NUMERIC(12,2) NOT NULL DEFAULT 0,
    deductions        NUMERIC(12,2) NOT NULL DEFAULT 0,
    advances_adjusted NUMERIC(12,2) NOT NULL DEFAULT 0,
    net_amount        NUMERIC(12,2) NOT NULL DEFAULT 0,
    UNIQUE (payroll_run_id, worker_id)
);

-- ─── WORKER_ADVANCES ──────────────────────────────────────────
CREATE TABLE worker_advances (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id          UUID NOT NULL REFERENCES workers(id),
    site_id            UUID NOT NULL REFERENCES sites(id),
    amount             NUMERIC(12,2) NOT NULL,
    issued_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    adjusted_in_run_id UUID REFERENCES payroll_runs(id),
    created_by         UUID REFERENCES users(id),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── AUDIT_LOGS ───────────────────────────────────────────────
CREATE TABLE audit_logs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(80) NOT NULL,
    record_id  UUID,
    action     VARCHAR(10) NOT NULL CHECK (action IN ('insert', 'update', 'delete')),
    actor_id   UUID REFERENCES users(id),
    old_data   JSONB,
    new_data   JSONB,
    source     VARCHAR(10) CHECK (source IN ('telegram', 'web', 'system')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_table_record ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
```

</details>

---

## UI Wireframe Design

### Design System

The entire interface follows a consistent dark theme with a single amber accent. Below are the core design tokens used throughout.

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0d1117` | Page background |
| Surface | `#161b22` | Cards, sidebar, modals |
| Surface raised | `#1c2128` | Input fields, inner cards |
| Border | `#30363d` | Card borders, dividers |
| Text primary | `#f0f6fc` | Headings, values |
| Text secondary | `#8b949e` | Labels, descriptions |
| Text muted | `#6e7681` | Hints, placeholders |
| Accent amber | `#f7941d` | CTAs, active nav, brand |
| Success green | `#3fb950` | Status badges (ACTIVE) |
| Info blue | `#58a6ff` | Focus states, links |
| Danger red | `#f85149` | Alerts, admin badges |

**Typography:** System UI sans-serif for UI, monospace for code/credentials.  
**Border radius:** 8–12px on cards, 20px on pills/badges.  
**Spacing:** 16px base unit.

---

### Login Page

> Route: `/login` · Accessible to all roles before authentication

![Login Wireframe](wireframe_login.svg)

**Layout decisions:**
- Centered card on a dark background — no distractions for a management console
- Brand pill (`TS` in amber) establishes identity immediately
- Explanatory subtext clarifies the separation between Telegram (field) and Web (admin) — critical because the same contractor may use both
- Dev-mode credential hint box is shown only during development (`import.meta.env.DEV`)
- Email input has blue focus ring — distinguishes from the amber accent used on CTAs
- Single amber CTA button — `Sign in` — no secondary actions on this page

**Interaction states:**
- Email field: blue border on focus (`#58a6ff`)
- Password field: default border on focus
- Sign in button: amber on default, slight darken on hover, loading spinner on submit
- Error state: red inline message below the password field, no page reload

---

### Operations Dashboard

> Route: `/` · Manager and Admin roles

![Dashboard Wireframe](wireframe_dashboard.svg)

**Layout decisions:**
- Fixed sidebar (220px) with role-aware navigation — active item gets amber highlight + amber left border
- Top KPI strip: 5 metric cards in a responsive row — Active sites, Workers today, Attendance, Material moves, Expenses today
- Open payroll periods card is shown only when count > 0 in production (shown as `0` here indicating no pending runs)
- **Site overview** (left, ~60% width): one expandable card per active site — shows worker count, progress update count, budget utilisation bar
- **Alerts panel** (right, ~40% width): auto-generated smart alerts for low stock, missing attendance, budget threshold breaches
- Budget bar: thin progress bar inside each site card — amber fill against grey track

**Data freshness:**  
All KPI cards refresh on page load. Alerts are generated server-side based on rule engine (stock < threshold, no attendance by 10am, budget > 80%).

---

### Payroll Workbook

> Route: `/payroll` · ⚠ Admin role only

![Payroll Wireframe](wireframe_payroll.svg)

**Layout decisions:**
- Period selector dropdown at the top — shows run ID, date range, and status (DRAFT / FINALIZED / PAID)
- Date range picker + period type dropdown (Week / Fortnight / Month) + `New period` amber button
- Four summary cards below the period controls: Total gross, Total paid, Outstanding, Worker count
- Editable ledger table: one row per worker with columns for Present, Half, Absent, Rate/day, OT hrs, Advances, Deductions, Gross, Paid, Balance, Source
- `Src` column shows `AUTO` (synced from attendance) or `MANUAL` (admin overridden)
- Status bar at bottom: immutable finalization metadata
- Finalized runs are read-only — all input cells are disabled when `status = finalised`

**Access control note:**  
This route returns `403 Forbidden` for supervisor and manager roles. The sidebar item is not rendered for non-admin users.

---

### Navigation & Role Flow

![Navigation Flow](wireframe_nav_flow.svg)

**Role matrix:**

| Route | Supervisor | Manager | Admin |
|-------|-----------|---------|-------|
| Telegram bot | ✅ Primary | ❌ | ❌ |
| `/login` | ✅ | ✅ | ✅ |
| `/` Dashboard | ❌ | ✅ | ✅ |
| `/assistant` | ❌ | ✅ | ✅ |
| `/sites/:id` | ❌ | ✅ | ✅ |
| `/payroll` | ❌ | ❌ | ✅ |

Authentication is JWT-based. Token is issued on login, stored in `httpOnly` cookie, and verified on every API request. Route-level guards on the frontend redirect unauthorized access back to `/login`.

---

## Frontend Environment Setup

### Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + Vite |
| Language | TypeScript |
| Styling | Tailwind CSS (custom dark theme) |
| State | Zustand |
| Data fetching | TanStack Query (React Query) |
| Routing | React Router v6 |
| Charts | Recharts |
| HTTP client | Axios |

### Local Development

**Prerequisites:** Node.js 18+, npm 9+

```bash
# 1. Clone the repository
git clone https://github.com/your-org/thesecond-erp.git
cd thesecond-erp/frontend

# 2. Install dependencies
npm install

# 3. Set up environment variables
cp .env.example .env.local
# Edit .env.local and set:
# VITE_API_BASE_URL=http://localhost:8000
# VITE_ENV=development

# 4. Start development server
npm run dev
# → http://localhost:5173

# 5. Build for production
npm run build

# 6. Preview production build
npm run preview
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |
| `VITE_ENV` | Environment name | `development` |
| `VITE_SHOW_DEV_HINTS` | Show credential hints on login | `true` |

### Project Structure

```
frontend/
├── src/
│   ├── components/        # Shared UI components
│   │   ├── ui/            # Design system primitives (Button, Card, Badge)
│   │   ├── layout/        # Sidebar, Header, PageWrapper
│   │   └── charts/        # Recharts wrappers
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Assistant.tsx
│   │   ├── SiteDetail.tsx
│   │   └── PayrollWorkbook.tsx
│   ├── store/             # Zustand stores (auth, ui)
│   ├── hooks/             # TanStack Query hooks per domain
│   ├── api/               # Axios instance + endpoint functions
│   ├── utils/             # Formatters, date helpers, currency (₹)
│   └── main.tsx
├── public/
├── .env.example
├── tailwind.config.ts
├── vite.config.ts
└── tsconfig.json
```

### Design Review Checklist

Before shipping any UI change, verify:

- [ ] All new components use the design token colours — no hardcoded hex values
- [ ] Dark theme tested — no white backgrounds leaking through
- [ ] Amber accent used **only** for primary CTAs and active navigation state
- [ ] Admin-only pages have the `⚠ Admin` badge visible in the page header
- [ ] All currency values formatted with `₹` prefix and Indian number system (lakhs/crores)
- [ ] Loading states implemented on all data-fetching components
- [ ] Mobile: sidebar collapses to hamburger at < 768px
- [ ] Empty states designed for zero-data scenarios (new sites, no attendance yet)
- [ ] Error boundaries wrapping each major page
- [ ] No Telegram-style workflows on the web UI — they are intentionally separate

---

*Diagram files in this repo: `er_diagram.svg` · `wireframe_login.svg` · `wireframe_dashboard.svg` · `wireframe_payroll.svg` · `wireframe_nav_flow.svg`*
