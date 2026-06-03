# Next Phase Architecture

## Channel Responsibilities

### Telegram

Telegram is only for field data intake and automatic daily report delivery.

Allowed Telegram inputs:

- Attendance updates
- Material received/consumed updates
- Site expenses
- Progress updates
- Site notes

Not allowed through Telegram:

- Payroll changes
- Salary/wage edits
- Payment approvals
- Contractor-only database questions
- Confidential financial analysis

Natural Telegram text is stored in `telegram_data_submissions` with `PENDING_LLM` status. The LLM extraction phase will read that text, choose a backend tool, and write to business tables only through tool functions.

### Website

The website should have three separated areas:

1. Operations dashboard
   - Attendance overview
   - Inventory overview
   - Site workflow/progress
   - Upcoming planned work
   - Non-confidential alerts

2. Secure payroll section
   - Contractor/accountant-only access
   - Worker rates
   - Payroll runs
   - Payment status
   - Manual corrections with audit logs

3. Contractor AI assistant
   - Contractor-only access
   - Full database retrieval
   - Natural-language insights
   - Daily/weekly/monthly reports
   - Spreadsheet export

## Tool Calling Design

LLMs must not directly write SQL.

The insertion assistant can only call approved insertion tools:

- `mark_attendance`
- `record_material_received`
- `record_material_consumed`
- `record_site_expense`
- `record_progress_update`

The website retrieval assistant can call read-only analytics tools:

- `get_site_summary`
- `get_attendance_summary`
- `get_inventory_summary`
- `get_budget_summary`
- `get_progress_summary`
- `generate_daily_report`
- `export_report_sheet`

Payroll tools must be separate and gated by role:

- `calculate_payroll`
- `preview_payroll_run`
- `approve_payroll_run`
- `record_worker_payment`
- `update_worker_rate`

## Data Safety Rules

- Telegram can create operational records, but never payroll records.
- Payroll writes require website login and a privileged role.
- LLMs call typed backend tools, never direct SQL.
- All tool calls should be logged with user, channel, raw input, extracted payload, result, and timestamp.
- For risky writes, the insertion assistant should return a confirmation request before committing.
- Worker matching by name should detect ambiguity and ask for clarification.

## Credentials Needed

Minimum for LLM insertion:

```env
LLM_INSERTION_PROVIDER=
LLM_INSERTION_API_KEY=
LLM_INSERTION_MODEL=
```

Recommended free-first providers to test:

- Groq for fast tool calling
- Cerebras for fast inference fallback
- OpenRouter for model routing and fallback
- Mistral for structured/tool-call experiments

For the website:

```env
JWT_SECRET=
APP_BASE_URL=
```

For reports/export:

```env
REPORT_EXPORT_STORAGE=local
```

Later, if using cloud file storage:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

## Immediate Build Order

1. Add LLM insertion processor for pending Telegram submissions.
2. Add confirmation flow before committing extracted tool calls.
3. Add website auth and roles.
4. Add dashboard read APIs with confidential fields excluded.
5. Add payroll section with role checks and audit logs.
6. Add contractor-only retrieval assistant with read-only tools.
7. Add daily report generator and spreadsheet export.
