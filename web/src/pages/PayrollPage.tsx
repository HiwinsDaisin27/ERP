import { FormEvent, useEffect, useState } from "react";
import { api, type PayrollPeriodListItem, type PayrollWorkbook } from "../api/client";
import { useAuth } from "../context/AuthContext";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function weekRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 6);
  return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) };
}

export function PayrollPage() {
  const { token, isAdmin } = useAuth();
  const [periods, setPeriods] = useState<PayrollPeriodListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [workbook, setWorkbook] = useState<PayrollWorkbook | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState(() => ({ ...weekRange(), period_type: "WEEK" }));

  async function loadPeriods() {
    if (!token) return;
    const list = await api.listPayrollPeriods(token);
    setPeriods(list);
    if (list.length && !selectedId) setSelectedId(list[0].period_id);
  }

  async function loadWorkbook(periodId: number) {
    if (!token) return;
    const wb = await api.getWorkbook(token, periodId);
    setWorkbook(wb);
  }

  useEffect(() => {
    loadPeriods().catch((err) => setError(err instanceof Error ? err.message : "Failed to load periods"));
  }, [token]);

  useEffect(() => {
    if (selectedId) {
      loadWorkbook(selectedId).catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load workbook"),
      );
    }
  }, [selectedId, token]);

  async function runAction(action: () => Promise<PayrollWorkbook>) {
    setBusy(true);
    setError("");
    try {
      const wb = await action();
      setWorkbook(wb);
      await loadPeriods();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function createPeriod(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin) return;
    setBusy(true);
    setError("");
    try {
      const wb = await api.createPayrollPeriod(token, {
        period_type: draft.period_type,
        period_start: draft.start,
        period_end: draft.end,
      });
      setWorkbook(wb);
      setSelectedId(wb.period_id);
      await loadPeriods();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveLine(lineId: number, field: string, value: string) {
    if (!token || !isAdmin || !selectedId || workbook?.status !== "DRAFT") return;
    await runAction(() => api.updateLine(token, selectedId, lineId, { [field]: value }));
  }

  const isDraft = workbook?.status === "DRAFT";

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Payroll Workbook</h1>
          <p>Editable worker ledger with attendance sync, payments, and period finalization.</p>
        </div>
        {isAdmin && workbook && isDraft && (
          <div className="action-row">
            <button
              type="button"
              disabled={busy}
              onClick={() => selectedId && runAction(() => api.recalculate(token!, selectedId))}
            >
              Recalculate
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => selectedId && runAction(() => api.markAllPaid(token!, selectedId))}
            >
              Mark all paid
            </button>
            <button
              type="button"
              className="primary-btn"
              disabled={busy}
              onClick={() => selectedId && runAction(() => api.finalize(token!, selectedId))}
            >
              Finalize period
            </button>
          </div>
        )}
      </header>

      {error && <p className="error-banner">{error}</p>}

      <section className="panel payroll-toolbar">
        <label>
          Period
          <select
            value={selectedId ?? ""}
            onChange={(e) => setSelectedId(Number(e.target.value))}
          >
            {periods.map((p) => (
              <option key={p.period_id} value={p.period_id}>
                #{p.period_id} {p.period_start} → {p.period_end} ({p.status})
              </option>
            ))}
          </select>
        </label>

        {isAdmin && (
          <form className="inline-form" onSubmit={createPeriod}>
            <select
              value={draft.period_type}
              onChange={(e) => setDraft({ ...draft, period_type: e.target.value })}
            >
              <option value="WEEK">Week</option>
              <option value="FORTNIGHT">Fortnight</option>
              <option value="MONTH">Month</option>
            </select>
            <input type="date" value={draft.start} onChange={(e) => setDraft({ ...draft, start: e.target.value })} />
            <input type="date" value={draft.end} onChange={(e) => setDraft({ ...draft, end: e.target.value })} />
            <button type="submit" disabled={busy}>
              New period
            </button>
          </form>
        )}
      </section>

      {workbook && (
        <>
          <section className="kpi-grid compact">
            <article className="kpi-card">
              <span className="kpi-label">Total gross</span>
              <strong className="kpi-value">₹{workbook.summary.total_gross}</strong>
            </article>
            <article className="kpi-card">
              <span className="kpi-label">Total paid</span>
              <strong className="kpi-value">₹{workbook.summary.total_paid}</strong>
            </article>
            <article className="kpi-card">
              <span className="kpi-label">Outstanding</span>
              <strong className="kpi-value">₹{workbook.summary.total_outstanding}</strong>
            </article>
            <article className="kpi-card">
              <span className="kpi-label">Workers</span>
              <strong className="kpi-value">{workbook.summary.worker_count}</strong>
            </article>
          </section>

          <section className="panel table-panel">
            <div className="table-scroll">
              <table className="workbook-table">
                <thead>
                  <tr>
                    <th>Worker</th>
                    <th>Present</th>
                    <th>Half</th>
                    <th>Absent</th>
                    <th>Rate/day</th>
                    <th>OT hrs</th>
                    <th>Advances</th>
                    <th>Deductions</th>
                    <th>Gross</th>
                    <th>Paid</th>
                    <th>Balance</th>
                    <th>Src</th>
                    {isAdmin && isDraft && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {workbook.lines.map((line) => (
                    <tr key={line.line_item_id}>
                      <td>{line.employee_name}</td>
                      <td>
                        {isAdmin && isDraft ? (
                          <input
                            className="cell-input"
                            defaultValue={line.days_present}
                            onBlur={(e) => saveLine(line.line_item_id, "days_present", e.target.value)}
                          />
                        ) : (
                          line.days_present
                        )}
                      </td>
                      <td>
                        {isAdmin && isDraft ? (
                          <input
                            className="cell-input"
                            defaultValue={line.half_days}
                            onBlur={(e) => saveLine(line.line_item_id, "half_days", e.target.value)}
                          />
                        ) : (
                          line.half_days
                        )}
                      </td>
                      <td>{line.days_absent}</td>
                      <td>
                        {isAdmin && isDraft ? (
                          <input
                            className="cell-input"
                            defaultValue={line.daily_rate_override ?? line.effective_daily_rate}
                            onBlur={(e) =>
                              saveLine(line.line_item_id, "daily_rate_override", e.target.value)
                            }
                          />
                        ) : (
                          line.effective_daily_rate
                        )}
                      </td>
                      <td>{line.overtime_hours}</td>
                      <td>
                        {isAdmin && isDraft ? (
                          <input
                            className="cell-input"
                            defaultValue={line.advances}
                            onBlur={(e) => saveLine(line.line_item_id, "advances", e.target.value)}
                          />
                        ) : (
                          line.advances
                        )}
                      </td>
                      <td>
                        {isAdmin && isDraft ? (
                          <input
                            className="cell-input"
                            defaultValue={line.deductions}
                            onBlur={(e) => saveLine(line.line_item_id, "deductions", e.target.value)}
                          />
                        ) : (
                          line.deductions
                        )}
                      </td>
                      <td>₹{line.gross_wage}</td>
                      <td>₹{line.amount_paid}</td>
                      <td className={Number(line.balance_due) > 0 ? "balance-due" : ""}>₹{line.balance_due}</td>
                      <td>
                        <span className="pill pill-small">{line.attendance_source}</span>
                      </td>
                      {isAdmin && isDraft && (
                        <td>
                          <button
                            type="button"
                            className="ghost-btn"
                            disabled={busy || Number(line.balance_due) <= 0}
                            onClick={() =>
                              selectedId &&
                              runAction(() => api.markPaid(token!, selectedId, line.line_item_id))
                            }
                          >
                            Mark paid
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="muted table-foot">
              Status: {workbook.status}
              {workbook.finalized_at ? ` · Finalized ${new Date(workbook.finalized_at).toLocaleString()}` : ""}
              · Created through {todayIso()}
            </p>
          </section>
        </>
      )}
    </div>
  );
}
