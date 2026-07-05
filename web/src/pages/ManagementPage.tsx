import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, type Site, type Worker, type WorkerProfile } from "../api/client";
import { useAuth } from "../context/AuthContext";

const emptySite = {
  site_name: "",
  location: "",
  supervisor_name: "",
  project_start_date: "",
  expected_end_date: "",
  project_budget: "",
  status: "ACTIVE",
};

const emptyWorker = {
  full_name: "",
  phone_number: "",
  role: "",
  wage_type: "DAILY",
  daily_rate: "",
  weekly_rate: "",
  joining_date: "",
  image_url: "",
  status: "ACTIVE",
};

export function ManagementPage() {
  const { token, isAdmin } = useAuth();
  const [sites, setSites] = useState<Site[]>([]);
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [selectedWorkerId, setSelectedWorkerId] = useState<number | null>(null);
  const [profile, setProfile] = useState<WorkerProfile | null>(null);
  const [siteForm, setSiteForm] = useState(emptySite);
  const [workerForm, setWorkerForm] = useState(emptyWorker);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const filteredWorkers = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return workers;
    return workers.filter((worker) =>
      [worker.full_name, worker.role, worker.phone_number].some((value) => value?.toLowerCase().includes(needle)),
    );
  }, [workers, query]);

  async function load() {
    if (!token) return;
    const [siteRows, workerRows] = await Promise.all([api.listSites(token), api.listWorkers(token)]);
    setSites(siteRows);
    setWorkers(workerRows);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load management data"));
  }, [token]);

  useEffect(() => {
    if (!token || selectedWorkerId == null) {
      setProfile(null);
      return;
    }
    api.workerProfile(token, selectedWorkerId)
      .then(setProfile)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load worker profile"));
  }, [token, selectedWorkerId]);

  async function submitSite(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    setNotice("");
    try {
      await api.createSite(token, {
        ...siteForm,
        expected_end_date: siteForm.expected_end_date || null,
        project_budget: siteForm.project_budget || null,
      });
      setSiteForm(emptySite);
      setNotice("Site added. Telegram site lookups will show it immediately.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add site");
    }
  }

  async function submitWorker(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError("");
    setNotice("");
    try {
      await api.createWorker(token, {
        ...workerForm,
        phone_number: workerForm.phone_number || null,
        daily_rate: workerForm.daily_rate || null,
        weekly_rate: workerForm.weekly_rate || null,
        image_url: workerForm.image_url || null,
      });
      setWorkerForm(emptyWorker);
      setNotice("Worker added. Telegram worker lookups will show the worker immediately.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add worker");
    }
  }

  return (
    <div className="page management-page">
      <header className="page-header">
        <div>
          <h1>Site & Worker Management</h1>
          <p>Add master data here. Telegram can only read these lists and record field updates.</p>
        </div>
      </header>

      {error && <p className="error-banner">{error}</p>}
      {notice && <p className="success-banner">{notice}</p>}

      {isAdmin && (
        <section className="management-forms">
          <form className="panel form-grid" onSubmit={submitSite}>
            <h2>Add site</h2>
            <input required placeholder="Site name" value={siteForm.site_name} onChange={(e) => setSiteForm({ ...siteForm, site_name: e.target.value })} />
            <input required placeholder="Location" value={siteForm.location} onChange={(e) => setSiteForm({ ...siteForm, location: e.target.value })} />
            <input required placeholder="Supervisor name" value={siteForm.supervisor_name} onChange={(e) => setSiteForm({ ...siteForm, supervisor_name: e.target.value })} />
            <label>
              Start date
              <input required type="date" value={siteForm.project_start_date} onChange={(e) => setSiteForm({ ...siteForm, project_start_date: e.target.value })} />
            </label>
            <label>
              Expected end
              <input type="date" value={siteForm.expected_end_date} onChange={(e) => setSiteForm({ ...siteForm, expected_end_date: e.target.value })} />
            </label>
            <input type="number" min="0" step="0.01" placeholder="Project budget" value={siteForm.project_budget} onChange={(e) => setSiteForm({ ...siteForm, project_budget: e.target.value })} />
            <button type="submit">Add site</button>
          </form>

          <form className="panel form-grid" onSubmit={submitWorker}>
            <h2>Add worker</h2>
            <input required placeholder="Full name" value={workerForm.full_name} onChange={(e) => setWorkerForm({ ...workerForm, full_name: e.target.value })} />
            <input placeholder="Phone number" value={workerForm.phone_number} onChange={(e) => setWorkerForm({ ...workerForm, phone_number: e.target.value })} />
            <input required placeholder="Role / trade" value={workerForm.role} onChange={(e) => setWorkerForm({ ...workerForm, role: e.target.value })} />
            <select value={workerForm.wage_type} onChange={(e) => setWorkerForm({ ...workerForm, wage_type: e.target.value })}>
              <option value="DAILY">Daily</option>
              <option value="WEEKLY">Weekly</option>
              <option value="MONTHLY">Monthly</option>
              <option value="CONTRACT">Contract</option>
            </select>
            <input type="number" min="0" step="0.01" placeholder="Daily rate" value={workerForm.daily_rate} onChange={(e) => setWorkerForm({ ...workerForm, daily_rate: e.target.value })} />
            <input type="number" min="0" step="0.01" placeholder="Weekly rate" value={workerForm.weekly_rate} onChange={(e) => setWorkerForm({ ...workerForm, weekly_rate: e.target.value })} />
            <label>
              Joining date
              <input required type="date" value={workerForm.joining_date} onChange={(e) => setWorkerForm({ ...workerForm, joining_date: e.target.value })} />
            </label>
            <input placeholder="Image URL" value={workerForm.image_url} onChange={(e) => setWorkerForm({ ...workerForm, image_url: e.target.value })} />
            <button type="submit">Add worker</button>
          </form>
        </section>
      )}

      <section className="panel-grid">
        <article className="panel">
          <h2>Sites</h2>
          <div className="data-list">
            {sites.map((site) => (
              <div key={site.site_id} className="data-row">
                <strong>{site.site_name}</strong>
                <span>{site.location}</span>
                <small>{site.supervisor_name} · {site.status}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Workers</h2>
          <input className="search-input" placeholder="Search workers" value={query} onChange={(e) => setQuery(e.target.value)} />
          <div className="data-list">
            {filteredWorkers.map((worker) => (
              <button
                key={worker.employee_id}
                type="button"
                className={`data-row data-button ${selectedWorkerId === worker.employee_id ? "selected" : ""}`}
                onClick={() => setSelectedWorkerId(worker.employee_id)}
              >
                <strong>{worker.full_name}</strong>
                <span>{worker.role} · {worker.wage_type}</span>
                <small>{worker.phone_number || "No phone"} · {worker.status}</small>
              </button>
            ))}
          </div>
        </article>
      </section>

      {profile && (
        <section className="panel worker-profile">
          <div className="profile-head">
            <div className="worker-avatar">
              {profile.worker.image_url ? <img src={profile.worker.image_url} alt={profile.worker.full_name} /> : profile.worker.full_name.slice(0, 1)}
            </div>
            <div>
              <h2>{profile.worker.full_name}</h2>
              <p>{profile.worker.role} · {profile.worker.wage_type}</p>
              <small>Daily: ₹{profile.worker.daily_rate || "0"} · Weekly: ₹{profile.worker.weekly_rate || "0"}</small>
            </div>
          </div>

          <div className="profile-tables">
            <div>
              <h3>Attendance history</h3>
              <table>
                <thead>
                  <tr><th>Date</th><th>Site</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {profile.attendance.map((row) => (
                    <tr key={row.attendance_id}>
                      <td>{row.attendance_date}</td>
                      <td>{row.site_name}</td>
                      <td>{row.attendance_status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3>Payroll history</h3>
              <table>
                <thead>
                  <tr><th>Period</th><th>Gross</th><th>Paid</th><th>Due</th></tr>
                </thead>
                <tbody>
                  {profile.payroll.map((row) => (
                    <tr key={`${row.period_id}-${row.period_start}`}>
                      <td>{row.period_start} to {row.period_end}</td>
                      <td>₹{row.gross_wage}</td>
                      <td>₹{row.amount_paid}</td>
                      <td>₹{row.balance_due}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
