type Props = {
  label: string;
  value: string | number;
  hint?: string;
};

export function KpiCard({ label, value, hint }: Props) {
  return (
    <article className="kpi-card">
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value">{value}</strong>
      {hint && <small className="kpi-hint">{hint}</small>}
    </article>
  );
}
