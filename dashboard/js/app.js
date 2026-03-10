// ── Config ────────────────────────────────────────────────────────────────────
// Set AYAZDY_API_URL and AYAZDY_API_KEY in localStorage via the Settings panel,
// or hardcode defaults below for local dev.
const DEFAULT_API_URL = (window.location && window.location.origin) || "http://127.0.0.1:8000";
const DEFAULT_API_KEY = "your_super_secret_key";

function bootstrapDashboardConfig() {
  try {
    const params = new URLSearchParams(window.location.search || "");
    const qpUrl = params.get("api_url");
    const qpKey = params.get("api_key");

    if (qpUrl && !localStorage.getItem("ayazdy_api_url")) {
      localStorage.setItem("ayazdy_api_url", qpUrl);
    }
    if (qpKey && !localStorage.getItem("ayazdy_api_key")) {
      localStorage.setItem("ayazdy_api_key", qpKey);
    }
  } catch {
    // Keep dashboard functional even if URL parsing/localStorage fails.
  }
}

bootstrapDashboardConfig();

function cfg() {
  return {
    base: localStorage.getItem("ayazdy_api_url") || DEFAULT_API_URL,
    key:  localStorage.getItem("ayazdy_api_key") || DEFAULT_API_KEY,
  };
}

function api(path, opts = {}) {
  const { base, key } = cfg();
  return axios({
    url: base + path,
    headers: { "X-Api-Key": key, "Content-Type": "application/json" },
    ...opts,
  }).then(r => r.data);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const { useState, useEffect, useRef, useCallback } = React;

function riskColor(score) {
  if (!score && score !== 0) return "bg-gray-600";
  if (score <= 3) return "bg-green-600";
  if (score <= 6) return "bg-yellow-500";
  return "bg-red-600";
}

function Badge({ label, color = "bg-slate-600" }) {
  return (
    <span className={`${color} text-white text-xs font-semibold px-2 py-0.5 rounded-full`}>
      {label}
    </span>
  );
}

function Card({ title, children, action }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 shadow-lg flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-slate-200 font-semibold text-sm uppercase tracking-wide">{title}</h2>
        {action}
      </div>
      {children}
    </div>
  );
}

function Spinner() {
  return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-400 mx-auto" />;
}

function RefreshBtn({ onClick }) {
  return (
    <button onClick={onClick}
      className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-700 px-2 py-0.5 rounded">
      ↻ Refresh
    </button>
  );
}

// ── Health Panel ──────────────────────────────────────────────────────────────
function HealthPanel({ autoRefresh }) {
  const [data, setData] = useState(null);
  const [err, setErr]   = useState(null);

  const load = useCallback(() => {
    Promise.all([
      api("/monitor/health"),
      api("/monitor/telegram-config").catch(() => null),
    ])
      .then(([health, tg]) => setData({ ...health, telegram: tg }))
      .catch(e => setErr(e.message));
  }, []);

  useEffect(() => {
    load();
    if (!autoRefresh) return;
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load, autoRefresh]);

  return (
    <Card title="🩺 Health" action={<RefreshBtn onClick={load} />}>
      {err && <p className="text-red-400 text-xs">{err}</p>}
      {!data && !err && <Spinner />}
      {data && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <Row k="Status"  v={<Badge label={data.status} color={data.status === "ok" ? "bg-green-700" : "bg-red-700"} />} />
          <Row k="Ollama"  v={<Badge label={data.ollama_running ? "running" : "down"} color={data.ollama_running ? "bg-green-700" : "bg-red-700"} />} />
          <Row k="Approvals" v={data.pending_approvals ?? "—"} />
          <Row k="Telegram Bot" v={<Badge label={data.telegram_started ? "started" : "stopped"} color={data.telegram_started ? "bg-green-700" : "bg-yellow-700"} />} />
          <Row k="Telegram Config" v={data.telegram ? <Badge label={data.telegram.configured ? "ready" : "invalid"} color={data.telegram.configured ? "bg-green-700" : "bg-red-700"} /> : "—"} />
          {data.telegram && !data.telegram.configured && (
            <>
              <span className="text-slate-400 col-span-2">{(data.telegram.hints || []).join(" ")}</span>
            </>
          )}
        </div>
      )}
    </Card>
  );
}

// ── Stats Panel ───────────────────────────────────────────────────────────────
function StatsPanel({ autoRefresh }) {
  const [data, setData] = useState(null);

  const load = useCallback(() => {
    api("/monitor/stats").then(setData).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    if (!autoRefresh) return;
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load, autoRefresh]);

  const failRate = data ? ((data.total_failures / Math.max(data.total_executions, 1)) * 100).toFixed(1) : null;

  return (
    <Card title="📊 Stats" action={<RefreshBtn onClick={load} />}>
      {!data && <Spinner />}
      {data && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <Row k="Executions"  v={data.total_executions} />
          <Row k="Failures"    v={<span className={data.total_failures > 0 ? "text-red-400" : "text-green-400"}>{data.total_failures}</span>} />
          <Row k="Fail Rate"   v={<span className={parseFloat(failRate) > 20 ? "text-red-400" : "text-green-400"}>{failRate}%</span>} />
          <Row k="Avg Duration" v={data.average_execution_time ? `${data.average_execution_time.toFixed(2)}s` : "—"} />
          <Row k="Top Project" v={data.most_used_project || "—"} />
          <Row k="Top Task"    v={data.most_used_task || "—"} />
        </div>
      )}
    </Card>
  );
}

function Row({ k, v }) {
  return (
    <>
      <span className="text-slate-400">{k}</span>
      <span className="text-slate-200 font-medium truncate">{v}</span>
    </>
  );
}

// ── Project Selector ──────────────────────────────────────────────────────────
function ProjectSelector() {
  const [projects, setProjects] = useState([]);
  const [current,  setCurrent]  = useState(null);
  const [msg,      setMsg]      = useState(null);
  const [query,    setQuery]    = useState("");
  const [promptText, setPromptText] = useState("");
  const [promptOut, setPromptOut] = useState("");
  const [cmdText, setCmdText] = useState("");
  const [cmdOut, setCmdOut] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api("/projects").then(d => setProjects(d.projects || [])).catch(() => {});
    api("/project/current").then(d => setCurrent(d.project)).catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const select = (name) => {
    api("/queue/status")
      .then((status) => {
        const queueFiles = (status.queue || []).filter((f) => /\.(txt|md)$/i.test(f));
        const laterFiles = (status.later || []).filter((f) => /\.(txt|md)$/i.test(f));
        const needsConfirm = queueFiles.length > 0 || laterFiles.length > 0;

        if (needsConfirm) {
          const message = [
            "Pending agent-task text files found.",
            queueFiles.length ? `queue/: ${queueFiles.join(", ")}` : "queue/: none",
            laterFiles.length ? `later/: ${laterFiles.join(", ")}` : "later/: none",
            "",
            "Do you want to continue selecting this project and run only inside this selected project?",
          ].join("\n");
          const ok = window.confirm(message);
          if (!ok) {
            setMsg("Selection cancelled by user.");
            return Promise.resolve(null);
          }
        }

        return api("/project/select", {
          method: "post",
          data: { project: name, confirm_agent_tasks: true },
        });
      })
      .then((resp) => {
        if (!resp) return;
        setCurrent(name);
        setMsg(`Selected: ${name} (agent runs only in selected project context)`);
      })
      .catch(e => setMsg(`Error: ${e.message}`));
  };

  const runAnalysis = () => {
    if (!current) {
      setMsg("Select a project first.");
      return;
    }
    if (!promptText.trim()) {
      setMsg("Enter a prompt to analyze.");
      return;
    }

    setBusy(true);
    setPromptOut("");
    api("/chat", {
      method: "post",
      data: { prompt: promptText, project: current, execute_commands: false },
    })
      .then((d) => setPromptOut(d.reply || "(no reply)"))
      .catch((e) => setPromptOut(`Error: ${e.message}`))
      .finally(() => setBusy(false));
  };

  const runCommand = () => {
    if (!current) {
      setMsg("Select a project first.");
      return;
    }
    if (!cmdText.trim()) {
      setMsg("Enter a command to execute.");
      return;
    }

    setBusy(true);
    setCmdOut("");
    api("/project/run-custom", {
      method: "post",
      data: {
        project: current,
        command: cmdText,
        auto_approve: true,
        dry_run: false,
      },
    })
      .then((d) => setCmdOut(d.output || `(exit=${d.exit_code})`))
      .catch((e) => setCmdOut(`Error: ${e.message}`))
      .finally(() => setBusy(false));
  };

  const filteredProjects = projects.filter((p) =>
    p.toLowerCase().includes(query.trim().toLowerCase())
  );

  return (
    <Card title="📁 Projects" action={<RefreshBtn onClick={load} />}>
      {msg && <p className="text-xs text-indigo-300">{msg}</p>}
      {current && <p className="text-xs text-slate-400">Current: <span className="text-indigo-300 font-semibold">{current}</span></p>}
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search project..."
        className="bg-slate-700 text-slate-200 text-xs px-2 py-1.5 rounded border border-slate-600 focus:outline-none focus:border-indigo-500"
      />
      <div className="flex flex-col gap-1 max-h-40 overflow-y-auto">
        {filteredProjects.map(p => (
          <button key={p} onClick={() => select(p)}
            className={`text-left text-sm px-3 py-1.5 rounded-lg transition
              ${p === current ? "bg-indigo-700 text-white" : "bg-slate-700 hover:bg-slate-600 text-slate-200"}`}>
            {p}
          </button>
        ))}
        {filteredProjects.length === 0 && <p className="text-slate-500 text-xs">No matching projects.</p>}
      </div>

      <div className="mt-2 border-t border-slate-700 pt-3 flex flex-col gap-2">
        <p className="text-xs text-slate-400">After selecting a project:</p>

        <label className="text-xs text-slate-400">Analyze Prompt</label>
        <textarea
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          rows={3}
          placeholder="Ask analysis prompt for selected project..."
          className="bg-slate-700 text-slate-200 text-xs px-2 py-1.5 rounded border border-slate-600 focus:outline-none focus:border-indigo-500"
        />
        <button
          onClick={runAnalysis}
          disabled={busy}
          className="text-xs bg-indigo-700 hover:bg-indigo-600 disabled:opacity-50 text-white px-3 py-1 rounded"
        >
          {busy ? "Running..." : "Analyze Prompt"}
        </button>
        {promptOut && <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 max-h-28 overflow-y-auto whitespace-pre-wrap">{promptOut}</pre>}

        <label className="text-xs text-slate-400">Execute Command</label>
        <input
          value={cmdText}
          onChange={(e) => setCmdText(e.target.value)}
          placeholder="Example: python --version"
          className="bg-slate-700 text-slate-200 text-xs px-2 py-1.5 rounded border border-slate-600 focus:outline-none focus:border-indigo-500"
        />
        <button
          onClick={runCommand}
          disabled={busy}
          className="text-xs bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white px-3 py-1 rounded"
        >
          {busy ? "Running..." : "Execute Command"}
        </button>
        {cmdOut && <pre className="text-xs text-slate-300 bg-slate-900 rounded p-2 max-h-28 overflow-y-auto whitespace-pre-wrap">{cmdOut}</pre>}
      </div>
    </Card>
  );
}

// ── Execution History ─────────────────────────────────────────────────────────
function ExecutionHistory({ autoRefresh }) {
  const [rows, setRows] = useState([]);

  const load = useCallback(() => {
    api("/monitor/history?limit=20").then(d => setRows(d.history || [])).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    if (!autoRefresh) return;
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load, autoRefresh]);

  return (
    <Card title="🕒 Execution History" action={<RefreshBtn onClick={load} />}>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead className="text-slate-400 border-b border-slate-700">
            <tr>
              <th className="pb-1 pr-3">Project</th>
              <th className="pb-1 pr-3">Task</th>
              <th className="pb-1 pr-3">Status</th>
              <th className="pb-1 pr-3">Risk</th>
              <th className="pb-1 pr-3">Duration</th>
              <th className="pb-1">Time</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="py-1 pr-3 text-slate-300 truncate max-w-[80px]">{r.project}</td>
                <td className="py-1 pr-3 text-slate-300 truncate max-w-[120px]">{r.task}</td>
                <td className="py-1 pr-3">
                  <Badge label={r.status} color={r.status === "success" ? "bg-green-700" : "bg-red-700"} />
                </td>
                <td className="py-1 pr-3">
                  {r.risk_score != null
                    ? <Badge label={`R${r.risk_score}`} color={riskColor(r.risk_score)} />
                    : "—"}
                </td>
                <td className="py-1 pr-3 text-slate-400">{r.duration ? `${r.duration.toFixed(1)}s` : "—"}</td>
                <td className="py-1 text-slate-500">{r.timestamp ? r.timestamp.slice(0, 19).replace("T", " ") : "—"}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={6} className="py-4 text-center text-slate-500">No history yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ── Approval Queue ────────────────────────────────────────────────────────────
function ApprovalQueue({ autoRefresh }) {
  const [items, setItems] = useState([]);
  const [msg,   setMsg]   = useState(null);

  const load = useCallback(() => {
    api("/monitor/approvals").then(d => setItems(d.pending || [])).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    if (!autoRefresh) return;
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load, autoRefresh]);

  const act = (token, action) => {
    api(`/monitor/${action}/${token}`, { method: "post" })
      .then(() => { setMsg(`${action} sent`); load(); })
      .catch(e => setMsg(`Error: ${e.message}`));
  };

  return (
    <Card title="✅ Approval Queue" action={<RefreshBtn onClick={load} />}>
      {msg && <p className="text-xs text-indigo-300">{msg}</p>}
      <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
        {items.filter(it => it.status === "pending").map(it => (
          <div key={it.token} className="bg-slate-700 rounded-lg p-3 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-indigo-300 font-mono truncate">{it.token.slice(0, 16)}…</span>
              <Badge label="pending" color="bg-yellow-700" />
            </div>
            <p className="text-xs text-slate-300 truncate">{it.plan?.task || it.task || "—"}</p>
            <p className="text-xs text-slate-400">Project: {it.project || "—"}</p>
            <div className="flex gap-2">
              <button onClick={() => act(it.token, "approve")}
                className="flex-1 text-xs bg-green-700 hover:bg-green-600 text-white px-2 py-1 rounded">
                ✔ Approve
              </button>
              <button onClick={() => act(it.token, "reject")}
                className="flex-1 text-xs bg-red-700 hover:bg-red-600 text-white px-2 py-1 rounded">
                ✘ Reject
              </button>
            </div>
          </div>
        ))}
        {items.filter(it => it.status === "pending").length === 0 && (
          <p className="text-slate-500 text-xs text-center py-2">No pending approvals.</p>
        )}
      </div>
    </Card>
  );
}

// ── Audit Logs ────────────────────────────────────────────────────────────────
function AuditLogs({ autoRefresh }) {
  const [logs, setLogs] = useState([]);

  const load = useCallback(() => {
    api("/monitor/logs?limit=30").then(d => setLogs(d.entries || [])).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    if (!autoRefresh) return;
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load, autoRefresh]);

  return (
    <Card title="📋 Audit Logs" action={<RefreshBtn onClick={load} />}>
      <div className="flex flex-col gap-1 max-h-64 overflow-y-auto live-log">
        {logs.slice().reverse().map((entry, i) => {
          const e = typeof entry === "string" ? (() => { try { return JSON.parse(entry); } catch { return { raw: entry }; } })() : entry;
          return (
            <div key={i} className="flex gap-2 text-xs border-b border-slate-700/40 pb-1">
              <span className="text-slate-500 shrink-0">{(e.timestamp || "").slice(11, 19)}</span>
              <span className={`shrink-0 font-semibold ${e.status === "success" ? "text-green-400" : e.status === "failed" ? "text-red-400" : "text-yellow-400"}`}>
                {e.status || "info"}
              </span>
              <span className="text-slate-300 truncate">{e.task || e.raw || JSON.stringify(e)}</span>
            </div>
          );
        })}
        {logs.length === 0 && <p className="text-slate-500 text-xs text-center py-2">No audit entries.</p>}
      </div>
    </Card>
  );
}

// ── Live Log Stream (SSE) ─────────────────────────────────────────────────────
function LiveStream() {
  const [entries, setEntries] = useState([]);
  const [running, setRunning] = useState(false);
  const esRef = useRef(null);
  const bottomRef = useRef(null);

  const start = () => {
    if (esRef.current) return;
    const { base, key } = cfg();
    const url = `${base}/monitor/stream/logs?api_key=${encodeURIComponent(key)}`;
    const es = new EventSource(url);
    es.onmessage = e => {
      try {
        const d = JSON.parse(e.data);
        setEntries(prev => [...prev.slice(-199), d]);
      } catch {
        setEntries(prev => [...prev.slice(-199), { raw: e.data }]);
      }
    };
    es.onerror = () => { es.close(); esRef.current = null; setRunning(false); };
    esRef.current = es;
    setRunning(true);
  };

  const stop = () => {
    if (esRef.current) { esRef.current.close(); esRef.current = null; }
    setRunning(false);
  };

  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  useEffect(() => () => stop(), []);

  return (
    <Card title="📡 Live Log Stream (SSE)"
      action={
        <button onClick={running ? stop : start}
          className={`text-xs px-2 py-0.5 rounded border ${running ? "border-red-600 text-red-400 hover:text-red-300" : "border-green-700 text-green-400 hover:text-green-300"}`}>
          {running ? "⏹ Stop" : "▶ Start"}
        </button>
      }>
      <div className="live-log bg-slate-900 rounded-lg p-3 h-56 overflow-y-auto flex flex-col gap-0.5">
        {entries.map((e, i) => (
          <div key={i} className="text-xs text-slate-300">
            <span className="text-slate-500">{(e.timestamp || "").slice(11, 19)} </span>
            <span className={e.status === "success" ? "text-green-400" : e.status === "failed" ? "text-red-400" : "text-indigo-300"}>
              [{e.status || e.event || "log"}]
            </span>
            {" "}{e.task || e.raw || JSON.stringify(e)}
          </div>
        ))}
        {entries.length === 0 && <span className="text-slate-600 text-xs">Press ▶ Start to stream live events…</span>}
        <div ref={bottomRef} />
      </div>
    </Card>
  );
}

// ── Self-Check Panel ──────────────────────────────────────────────────────────
function SelfCheck() {
  const [data, setData] = useState(null);

  const run = () => {
    setData(null);
    api("/monitor/self-check").then(setData).catch(e => setData({ error: e.message }));
  };

  return (
    <Card title="🔍 Self-Check"
      action={<button onClick={run} className="text-xs border border-indigo-700 text-indigo-400 hover:text-indigo-300 px-2 py-0.5 rounded">Run</button>}>
      {!data && <p className="text-slate-500 text-xs text-center">Click Run to execute self-check.</p>}
      {data && data.error && <p className="text-red-400 text-xs">{data.error}</p>}
      {data && !data.error && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          {Object.entries(data).map(([k, v]) => (
            <React.Fragment key={k}>
              <span className="text-slate-400 capitalize">{k.replace(/_/g, " ")}</span>
              <span>
                {typeof v === "boolean"
                  ? <Badge label={v ? "✔ ok" : "✘ fail"} color={v ? "bg-green-700" : "bg-red-700"} />
                  : <span className="text-slate-200 text-xs">{String(v)}</span>}
              </span>
            </React.Fragment>
          ))}
        </div>
      )}
    </Card>
  );
}

// ── Retry Suggestions ─────────────────────────────────────────────────────────
function RetryPanel() {
  const [project, setProject] = useState("");
  const [data,    setData]    = useState(null);

  const check = () => {
    if (!project.trim()) return;
    api(`/monitor/history?project=${encodeURIComponent(project)}&limit=5`)
      .then(d => setData(d))
      .catch(e => setData({ error: e.message }));
  };

  return (
    <Card title="🔁 Retry Suggestions">
      <div className="flex gap-2">
        <input value={project} onChange={e => setProject(e.target.value)}
          placeholder="Project name…"
          className="flex-1 bg-slate-700 text-slate-200 text-xs px-2 py-1 rounded border border-slate-600 focus:outline-none focus:border-indigo-500" />
        <button onClick={check} className="text-xs bg-indigo-700 hover:bg-indigo-600 text-white px-3 py-1 rounded">
          Check
        </button>
      </div>
      {data && data.error && <p className="text-red-400 text-xs">{data.error}</p>}
      {data && !data.error && (
        <div className="flex flex-col gap-1 text-xs">
          {(data.history || []).filter(r => r.status !== "success").map((r, i) => (
            <div key={i} className="bg-slate-700/60 rounded p-2 flex justify-between">
              <span className="text-slate-300 truncate">{r.task}</span>
              <Badge label="retry?" color="bg-orange-700" />
            </div>
          ))}
          {(data.history || []).filter(r => r.status !== "success").length === 0 && (
            <p className="text-green-400">No failed tasks to retry.</p>
          )}
        </div>
      )}
    </Card>
  );
}

// ── Settings ──────────────────────────────────────────────────────────────────
function Settings({ onClose }) {
  const [url, setUrl] = useState(localStorage.getItem("ayazdy_api_url") || DEFAULT_API_URL);
  const [key, setKey] = useState(localStorage.getItem("ayazdy_api_key") || DEFAULT_API_KEY);

  const save = () => {
    localStorage.setItem("ayazdy_api_url", url);
    localStorage.setItem("ayazdy_api_key", key);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 border border-slate-600 rounded-xl p-6 w-96 shadow-2xl flex flex-col gap-4">
        <h2 className="text-slate-200 font-semibold">⚙️ Settings</h2>
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          API Base URL
          <input value={url} onChange={e => setUrl(e.target.value)}
            className="bg-slate-700 text-slate-200 px-2 py-1.5 rounded border border-slate-600 focus:outline-none focus:border-indigo-500" />
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          API Key (X-Api-Key)
          <input type="password" value={key} onChange={e => setKey(e.target.value)}
            className="bg-slate-700 text-slate-200 px-2 py-1.5 rounded border border-slate-600 focus:outline-none focus:border-indigo-500" />
        </label>
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="text-xs text-slate-400 hover:text-slate-200 px-3 py-1">Cancel</button>
          <button onClick={save} className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1 rounded">Save</button>
        </div>
      </div>
    </div>
  );
}

// ── App Shell ─────────────────────────────────────────────────────────────────
function App() {
  const [autoRefresh,    setAutoRefresh]    = useState(true);
  const [showSettings,   setShowSettings]   = useState(false);
  const [activeTab,      setActiveTab]      = useState("overview");

  const tabs = [
    { id: "overview",  label: "Overview" },
    { id: "history",   label: "History" },
    { id: "approvals", label: "Approvals" },
    { id: "logs",      label: "Logs" },
    { id: "stream",    label: "Live Stream" },
    { id: "tools",     label: "Tools" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🤖</span>
          <div>
            <h1 className="text-slate-100 font-bold text-base leading-none">Agent Ayazdy</h1>
            <p className="text-slate-500 text-xs">Control Center</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
            <span>Auto-refresh</span>
            <div onClick={() => setAutoRefresh(v => !v)}
              className={`w-9 h-5 rounded-full relative transition-colors ${autoRefresh ? "bg-indigo-600" : "bg-slate-600"}`}>
              <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-all ${autoRefresh ? "left-4" : "left-0.5"}`} />
            </div>
          </label>
          <button onClick={() => setShowSettings(true)}
            className="text-xs text-slate-400 hover:text-slate-200 border border-slate-600 px-3 py-1 rounded">
            ⚙️ Settings
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav className="bg-slate-900 border-b border-slate-700 px-6 flex gap-1">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 text-xs font-medium transition-colors border-b-2
              ${activeTab === t.id
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-300"}`}>
            {t.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="flex-1 p-6">
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <HealthPanel autoRefresh={autoRefresh} />
            <StatsPanel  autoRefresh={autoRefresh} />
            <ProjectSelector />
          </div>
        )}
        {activeTab === "history" && (
          <div className="flex flex-col gap-4">
            <ExecutionHistory autoRefresh={autoRefresh} />
          </div>
        )}
        {activeTab === "approvals" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ApprovalQueue autoRefresh={autoRefresh} />
          </div>
        )}
        {activeTab === "logs" && (
          <div className="flex flex-col gap-4">
            <AuditLogs autoRefresh={autoRefresh} />
          </div>
        )}
        {activeTab === "stream" && (
          <div className="flex flex-col gap-4">
            <LiveStream />
          </div>
        )}
        {activeTab === "tools" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SelfCheck />
            <RetryPanel />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-700 px-6 py-2 text-center text-xs text-slate-600">
        Agent Ayazdy Control Center · {new Date().getFullYear()}
      </footer>

      {showSettings && <Settings onClose={() => setShowSettings(false)} />}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
