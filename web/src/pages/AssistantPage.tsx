import { FormEvent, useEffect, useState } from "react";
import { API_BASE, api, type ReportExport } from "../api/client";
import { useAuth } from "../context/AuthContext";

type ChatMessage = {
  id?: number;
  role: "user" | "assistant";
  text: string;
  exports?: ReportExport[];
  toolsUsed?: string[];
  createdAt?: string;
};

const SUGGESTIONS = [
  "Give me a daily operations summary for today.",
  "Which site is closest to exceeding its budget?",
  "Export attendance for the last 7 days as a spreadsheet.",
  "Compare inventory levels across all sites.",
  "Summarize the latest payroll period outstanding balance.",
];

export function AssistantPage() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api.assistantHistory(token)
      .then((history) => {
        setMessages(
          history.map((item) => ({
            id: item.message_id,
            role: item.role,
            text: item.text,
            exports: item.exports,
            toolsUsed: item.tools_used ?? undefined,
            createdAt: item.created_at,
          })),
        );
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load assistant history"));
  }, [token]);

  async function ask(prompt: string) {
    if (!token || !prompt.trim()) return;
    setBusy(true);
    setError("");
    setMessages((prev) => [...prev, { role: "user", text: prompt }]);
    setQuestion("");

    try {
      const result = await api.assistantChat(token, prompt);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: result.answer,
          exports: result.exports,
          toolsUsed: result.tools_used,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assistant request failed");
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    ask(question);
  }

  return (
    <div className="page assistant-page">
      <header className="page-header">
        <div>
          <h1>Management Intelligence</h1>
          <p>Ask questions in plain English. Export reports as XLSX (opens in Google Sheets) or CSV.</p>
        </div>
      </header>

      {error && <p className="error-banner">{error}</p>}

      <section className="panel assistant-suggestions">
        <h2>Try asking</h2>
        <div className="chip-row">
          {SUGGESTIONS.map((item) => (
            <button key={item} type="button" className="chip-btn" disabled={busy} onClick={() => ask(item)}>
              {item}
            </button>
          ))}
        </div>
      </section>

      <section className="panel assistant-chat">
        {messages.length === 0 ? (
          <p className="muted">No messages yet. Ask about sites, attendance, inventory, budget, or payroll.</p>
        ) : (
          <div className="chat-thread">
            {messages.map((msg, index) => (
              <article key={msg.id ?? `${msg.role}-${index}`} className={`chat-bubble chat-${msg.role}`}>
                <span className="chat-role">{msg.role === "user" ? "You" : "Assistant"}</span>
                {msg.createdAt && <small className="muted">{new Date(msg.createdAt).toLocaleString()}</small>}
                <p>{msg.text}</p>
                {msg.toolsUsed && msg.toolsUsed.length > 0 && (
                  <small className="muted">Tools used: {msg.toolsUsed.join(", ")}</small>
                )}
                {msg.exports && msg.exports.length > 0 && (
                  <div className="export-links">
                    {msg.exports.map((exp) => (
                      <a
                        key={exp.report_id}
                        className="export-link"
                        href={`${API_BASE}${exp.download_url}`}
                        download={exp.filename}
                        onClick={(e) => {
                          e.preventDefault();
                          if (!token) return;
                          fetch(`${API_BASE}${exp.download_url}`, {
                            headers: { Authorization: `Bearer ${token}` },
                          })
                            .then((r) => r.blob())
                            .then((blob) => {
                              const url = URL.createObjectURL(blob);
                              const a = document.createElement("a");
                              a.href = url;
                              a.download = exp.filename;
                              a.click();
                              URL.revokeObjectURL(url);
                            });
                        }}
                      >
                        Download {exp.filename}
                      </a>
                    ))}
                    <small className="muted">{msg.exports[0]?.google_sheets_hint}</small>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}

        <form className="assistant-form" onSubmit={onSubmit}>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Example: Export a weekly attendance spreadsheet and summarize which site had the most absences."
            rows={3}
            disabled={busy}
          />
          <button type="submit" disabled={busy || !question.trim()}>
            {busy ? "Thinking…" : "Ask assistant"}
          </button>
        </form>
      </section>
    </div>
  );
}
