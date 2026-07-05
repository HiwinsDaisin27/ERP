export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type User = {
  user_id: number;
  email: string;
  full_name: string;
  role: "OPERATIONS" | "MANAGEMENT" | "ADMIN";
  is_active: boolean;
};

export type DashboardOverview = {
  active_sites: number;
  workers_today: number;
  attendance_records_today: number;
  material_transactions_today: number;
  expenses_today: string;
  open_payroll_periods: number;
};

export type SiteCard = {
  site_id: number;
  site_name: string;
  status: string;
  workers_today: number;
  budget_allocated: string | null;
  budget_spent: string;
  budget_used_percent: number | null;
  progress_updates_count: number;
};

export type ChartSeries = {
  labels: string[];
  series: Array<{ name: string; data: number[] }>;
};

export type Alert = {
  alert_type: string;
  severity: string;
  message: string;
  site_id: number | null;
};

export type InventoryRow = {
  site_id: number;
  site_name: string;
  material_id: number;
  material_name: string;
  unit: string;
  stock_level: string;
  status: "OK" | "LOW" | "OUT";
};

export type Site = {
  site_id: number;
  site_name: string;
  location: string | null;
  supervisor_name: string | null;
  project_start_date: string | null;
  expected_end_date: string | null;
  project_budget: string | null;
  status: string;
};

export type Worker = {
  employee_id: number;
  full_name: string;
  phone_number: string | null;
  role: string | null;
  wage_type: string | null;
  daily_rate: string | null;
  weekly_rate: string | null;
  joining_date: string | null;
  image_url: string | null;
  status: string;
};

export type WorkerProfile = {
  worker: Worker;
  attendance: Array<{
    attendance_id: number;
    site_id: number;
    site_name: string;
    attendance_date: string;
    attendance_status: string;
    overtime_hours: string | null;
    remarks: string | null;
  }>;
  payroll: Array<{
    period_id: number;
    period_start: string;
    period_end: string;
    status: string;
    gross_wage: string;
    amount_paid: string;
    balance_due: string;
  }>;
};

export type ReportExport = {
  report_id: string;
  filename: string;
  format: string;
  download_url: string;
  row_count?: number;
  google_sheets_hint?: string;
};

export type AssistantMessage = {
  message_id: number;
  role: "user" | "assistant";
  text: string;
  tools_used?: string[] | null;
  exports: ReportExport[];
  created_at: string;
};

export type PayrollSummary = {
  total_gross: string;
  total_paid: string;
  total_outstanding: string;
  worker_count: number;
};

export type PayrollLine = {
  line_item_id: number;
  employee_id: number;
  employee_name: string;
  days_present: string;
  half_days: string;
  days_absent: string;
  daily_rate_override: string | null;
  effective_daily_rate: string;
  overtime_hours: string;
  overtime_rate: string | null;
  advances: string;
  deductions: string;
  gross_wage: string;
  amount_paid: string;
  balance_due: string;
  attendance_source: string;
  notes: string | null;
};

export type PayrollWorkbook = {
  period_id: number;
  period_type: string;
  period_start: string;
  period_end: string;
  site_id: number | null;
  status: string;
  finalized_at: string | null;
  summary: PayrollSummary;
  lines: PayrollLine[];
};

export type PayrollPeriodListItem = {
  period_id: number;
  period_type: string;
  period_start: string;
  period_end: string;
  site_id: number | null;
  status: string;
  total_outstanding: string;
};

async function request<T>(path: string, token: string | null, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.text();
    let message = body || `Request failed (${response.status})`;
    try {
      const parsed = JSON.parse(body) as { detail?: string | Array<{ msg?: string }> };
      if (typeof parsed.detail === "string") {
        message = parsed.detail;
      } else if (Array.isArray(parsed.detail)) {
        message = parsed.detail.map((item) => item.msg).filter(Boolean).join(", ");
      }
    } catch {
      // keep raw body
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", null, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) => request<User>("/auth/me", token),

  overview: (token: string) => request<DashboardOverview>("/dashboard/overview", token),
  sites: (token: string) => request<SiteCard[]>("/dashboard/sites", token),
  attendance: (token: string, days = 7) =>
    request<ChartSeries>(`/dashboard/attendance?days=${days}`, token),
  budget: (token: string) => request<ChartSeries>("/dashboard/budget", token),
  materialConsumption: (token: string, days = 30) =>
    request<ChartSeries>(`/dashboard/material-consumption?days=${days}`, token),
  alerts: (token: string) => request<Alert[]>("/dashboard/alerts", token),
  inventory: (token: string) => request<InventoryRow[]>("/dashboard/inventory", token),

  listSites: (token: string) => request<Site[]>("/operations/sites", token),
  createSite: (token: string, body: Record<string, string | number | null>) =>
    request<Site>("/operations/sites", token, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listWorkers: (token: string) => request<Worker[]>("/operations/workers", token),
  createWorker: (token: string, body: Record<string, string | number | null>) =>
    request<Worker>("/operations/workers", token, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  workerProfile: (token: string, employeeId: number) =>
    request<WorkerProfile>(`/operations/workers/${employeeId}`, token),

  listPayrollPeriods: (token: string) =>
    request<PayrollPeriodListItem[]>("/payroll/periods", token),

  createPayrollPeriod: (
    token: string,
    body: { period_type: string; period_start: string; period_end: string; site_id?: number },
  ) =>
    request<PayrollWorkbook>("/payroll/periods", token, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getWorkbook: (token: string, periodId: number) =>
    request<PayrollWorkbook>(`/payroll/periods/${periodId}/workbook`, token),

  recalculate: (token: string, periodId: number) =>
    request<PayrollWorkbook>(`/payroll/periods/${periodId}/recalculate?from_attendance=true`, token, {
      method: "POST",
    }),

  updateLine: (
    token: string,
    periodId: number,
    lineId: number,
    body: Record<string, string | number>,
  ) =>
    request<PayrollWorkbook>(`/payroll/periods/${periodId}/lines/${lineId}`, token, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  markPaid: (token: string, periodId: number, lineId: number) =>
    request<PayrollWorkbook>(`/payroll/periods/${periodId}/lines/${lineId}/mark-paid`, token, {
      method: "POST",
    }),

  markAllPaid: (token: string, periodId: number) =>
    request<PayrollWorkbook>(`/payroll/periods/${periodId}/mark-all-paid`, token, {
      method: "POST",
    }),

  finalize: (token: string, periodId: number) =>
    request<PayrollWorkbook>(`/payroll/periods/${periodId}/finalize`, token, {
      method: "POST",
    }),

  assistantChat: (token: string, question: string) =>
    request<{
      answer: string;
      tools_used: string[];
      exports: Array<{
        report_id: string;
        filename: string;
        format: string;
        download_url: string;
        row_count?: number;
        google_sheets_hint?: string;
      }>;
    }>("/assistant/chat", token, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  assistantHistory: (token: string) => request<AssistantMessage[]>("/assistant/history", token),
};
