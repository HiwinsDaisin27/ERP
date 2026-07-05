import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type Alert, type ChartSeries, type DashboardOverview, type InventoryRow, type SiteCard } from "../api/client";
import { KpiCard } from "../components/KpiCard";
import { useAuth } from "../context/AuthContext";

function toAttendanceRows(chart: ChartSeries) {
  return chart.labels.map((label, index) => {
    const row: Record<string, string | number> = { site: label };
    chart.series.forEach((s) => {
      row[s.name] = s.data[index] ?? 0;
    });
    return row;
  });
}

function toBudgetRows(chart: ChartSeries) {
  return chart.labels.map((label, index) => ({
    site: label,
    Allocated: chart.series[0]?.data[index] ?? 0,
    Spent: chart.series[1]?.data[index] ?? 0,
  }));
}

function toTrendRows(chart: ChartSeries) {
  return chart.labels.map((label, index) => ({
    date: label.slice(5),
    quantity: chart.series[0]?.data[index] ?? 0,
  }));
}

export function DashboardPage() {
  const { token } = useAuth();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [sites, setSites] = useState<SiteCard[]>([]);
  const [attendance, setAttendance] = useState<ChartSeries | null>(null);
  const [budget, setBudget] = useState<ChartSeries | null>(null);
  const [consumption, setConsumption] = useState<ChartSeries | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [inventory, setInventory] = useState<InventoryRow[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    const authToken = token;
    let cancelled = false;

    async function loadDashboard() {
      const [ov, siteCards, att, bud, cons, alertList, inventoryRows] = await Promise.all([
        api.overview(authToken),
        api.sites(authToken),
        api.attendance(authToken),
        api.budget(authToken),
        api.materialConsumption(authToken),
        api.alerts(authToken),
        api.inventory(authToken),
      ]);
      if (!cancelled) {
        setOverview(ov);
        setSites(siteCards);
        setAttendance(att);
        setBudget(bud);
        setConsumption(cons);
        setAlerts(alertList);
        setInventory(inventoryRows);
        setLastUpdated(new Date());
      }
    }

    loadDashboard().catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"));
    const interval = window.setInterval(() => {
      loadDashboard().catch((err) => setError(err instanceof Error ? err.message : "Failed to refresh dashboard"));
    }, 30000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [token]);

  if (error) return <p className="error-banner">{error}</p>;
  if (!overview) return <p className="loading">Loading dashboard…</p>;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Operations Dashboard</h1>
          <p>Site-centric visibility across workforce, inventory, and spend.</p>
        </div>
        {lastUpdated && <small className="muted">Live refresh: {lastUpdated.toLocaleTimeString()}</small>}
      </header>

      <section className="kpi-grid">
        <KpiCard label="Active sites" value={overview.active_sites} />
        <KpiCard label="Workers today" value={overview.workers_today} />
        <KpiCard label="Attendance today" value={overview.attendance_records_today} />
        <KpiCard label="Material moves today" value={overview.material_transactions_today} />
        <KpiCard label="Expenses today" value={`₹${overview.expenses_today}`} />
        <KpiCard label="Open payroll periods" value={overview.open_payroll_periods} />
      </section>

      <section className="panel-grid">
        <article className="panel">
          <h2>Site overview</h2>
          <div className="site-cards">
            {sites.map((site) => (
              <div key={site.site_id} className="site-card">
                <div className="site-card-head">
                  <strong>{site.site_name}</strong>
                  <span className={`pill pill-${site.status.toLowerCase()}`}>{site.status}</span>
                </div>
                <div className="site-metrics">
                  <span>{site.workers_today} workers today</span>
                  <span>{site.progress_updates_count} progress updates</span>
                </div>
                {site.budget_allocated && (
                  <div className="budget-bar">
                    <div
                      className="budget-fill"
                      style={{ width: `${Math.min(site.budget_used_percent ?? 0, 100)}%` }}
                    />
                  </div>
                )}
                <small>
                  Budget: ₹{site.budget_spent}
                  {site.budget_allocated ? ` / ₹${site.budget_allocated}` : ""}
                  {site.budget_used_percent != null ? ` (${site.budget_used_percent.toFixed(0)}%)` : ""}
                </small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Alerts</h2>
          {alerts.length === 0 ? (
            <p className="muted">No active alerts.</p>
          ) : (
            <ul className="alert-list">
              {alerts.map((alert, index) => (
                <li key={`${alert.alert_type}-${index}`} className={`alert alert-${alert.severity}`}>
                  {alert.message}
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <section className="panel">
        <h2>Inventory status</h2>
        {inventory.length === 0 ? (
          <p className="muted">No material stock records yet.</p>
        ) : (
          <div className="inventory-grid">
            {inventory.map((row) => (
              <div key={`${row.site_id}-${row.material_id}`} className={`inventory-item inventory-${row.status.toLowerCase()}`}>
                <strong>{row.material_name}</strong>
                <span>{row.site_name}</span>
                <small>{row.stock_level} {row.unit} · {row.status}</small>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel-grid charts">
        <article className="panel">
          <h2>Attendance by site (7 days)</h2>
          {attendance && (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={toAttendanceRows(attendance)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="site" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                {attendance.series.map((s, i) => (
                  <Bar key={s.name} dataKey={s.name} fill={["#f59e0b", "#38bdf8", "#f87171"][i % 3]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          )}
        </article>

        <article className="panel">
          <h2>Budget utilization</h2>
          {budget && (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={toBudgetRows(budget)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="site" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Bar dataKey="Allocated" fill="#64748b" />
                <Bar dataKey="Spent" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </article>

        <article className="panel panel-wide">
          <h2>Material consumption trend (30 days)</h2>
          {consumption && (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={toTrendRows(consumption)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Line type="monotone" dataKey="quantity" stroke="#38bdf8" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </article>
      </section>
    </div>
  );
}
