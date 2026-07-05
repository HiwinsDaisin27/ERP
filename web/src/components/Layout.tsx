import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout() {
  const { user, logout, canViewPayroll } = useAuth();
  const canUseAssistant = user?.role === "ADMIN" || user?.role === "MANAGEMENT";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">TS</span>
          <div>
            <strong>TheSecond</strong>
            <small>Construction ERP</small>
          </div>
        </div>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/management">Sites & Workers</NavLink>
          {canUseAssistant && (
            <NavLink to="/assistant">Intelligence Assistant</NavLink>
          )}
          {canViewPayroll && (
            <NavLink to="/payroll">Payroll Workbook</NavLink>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="user-chip">
            <span>{user?.full_name}</span>
            <small>{user?.role}</small>
          </div>
          <button type="button" className="ghost-btn" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
