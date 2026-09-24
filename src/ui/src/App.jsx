import React, { useState, useEffect, useRef } from "react";
import { 
  Radar, 
  ShieldCheck, 
  PlusCircle, 
  Layers, 
  Activity, 
  RefreshCw,
  ExternalLink
} from "lucide-react";
import Dashboard from "./components/Dashboard";
import NewInvestigation from "./components/NewInvestigation";
import LiveProgress from "./components/LiveProgress";
import InvestigationDetail from "./components/InvestigationDetail";
import EthicalNoticeModal from "./components/EthicalNoticeModal";

const API_BASE =
  typeof window !== "undefined" && window.location.origin.includes(":5173")
    ? "http://127.0.0.1:8000/api/v1"
    : "/api/v1";

export default function App() {
  const [currentView, setCurrentView] = useState("dashboard"); // dashboard, new, progress, detail
  const [investigations, setInvestigations] = useState([]);
  const [activeInvestigationId, setActiveInvestigationId] = useState(null);
  const [activeInvestigationDetail, setActiveInvestigationDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showEthicalModal, setShowEthicalModal] = useState(false);

  // Live SSE stream states
  const [progressPct, setProgressPct] = useState(5);
  const [currentStep, setCurrentStep] = useState("Initializing investigation...");
  const [liveLogs, setLiveLogs] = useState([]);
  const [liveStatus, setLiveStatus] = useState("working");
  const eventSourceRef = useRef(null);

  // Check first-run ethical terms acknowledgement
  useEffect(() => {
    const acknowledged = localStorage.getItem("openintel_terms_acknowledged");
    if (!acknowledged) {
      setShowEthicalModal(true);
    }
  }, []);

  const handleAcceptTerms = () => {
    localStorage.setItem("openintel_terms_acknowledged", "true");
    setShowEthicalModal(false);
  };

  // Fetch list of investigations
  const fetchInvestigations = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/investigations`);
      if (res.ok) {
        const data = await res.json();
        setInvestigations(data);
      }
    } catch (err) {
      console.error("Failed to fetch investigations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvestigations();
  }, []);

  // Fetch single investigation detail
  const fetchInvestigationDetail = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/investigations/${id}`);
      if (res.ok) {
        const data = await res.json();
        setActiveInvestigationDetail(data);
        return data;
      }
    } catch (err) {
      console.error("Failed to fetch detail:", err);
    }
    return null;
  };

  // Setup Server-Sent Events (SSE) for real-time progress
  const startSseStream = (id) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setProgressPct(10);
    setCurrentStep("Connecting to real-time engine stream...");
    setLiveLogs([]);
    setLiveStatus("working");

    const es = new EventSource(`${API_BASE}/investigations/${id}/events`);
    eventSourceRef.current = es;

    es.addEventListener("progress", (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.pct !== undefined && payload.pct !== null) {
          setProgressPct(payload.pct);
        }
        if (payload.step) {
          setCurrentStep(payload.step);
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    });

    es.addEventListener("log", (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.message) {
          setLiveLogs((prev) => [payload.message, ...prev]);
        }
      } catch (err) {}
    });

    es.addEventListener("entity", (e) => {
      try {
        const payload = JSON.parse(e.data);
        const val = payload.entity?.value || "entity";
        setLiveLogs((prev) => [`[+] Discovered ${payload.entity?.kind}: ${val}`, ...prev]);
      } catch (err) {}
    });

    es.addEventListener("completed", () => {
      setProgressPct(100);
      setCurrentStep("Reconnaissance complete.");
      setLiveStatus("review");
      es.close();
      fetchInvestigationDetail(id);
      fetchInvestigations();
    });

    es.addEventListener("error", (e) => {
      console.warn("SSE error or connection closed", e);
      es.close();
    });
  };

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Form submission handler
  const handleCreateInvestigation = async (payload) => {
    const res = await fetch(`${API_BASE}/investigations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Server rejected investigation request");
    }

    const created = await res.json();
    setActiveInvestigationId(created.id);
    startSseStream(created.id);
    setCurrentView("progress");
    fetchInvestigations();
  };

  // Select an investigation to view details
  const handleSelectInvestigation = async (id) => {
    setActiveInvestigationId(id);
    const detail = await fetchInvestigationDetail(id);
    if (detail && (detail.status === "working" || detail.status === "running")) {
      startSseStream(id);
      setCurrentView("progress");
    } else {
      setCurrentView("detail");
    }
  };

  // Cancel investigation
  const handleCancelInvestigation = async (id) => {
    try {
      await fetch(`${API_BASE}/investigations/${id}/cancel`, { method: "POST" });
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      fetchInvestigationDetail(id);
      fetchInvestigations();
    } catch (err) {
      console.error("Cancel failed", err);
    }
  };

  // Export report
  const handleExport = async (id, format = "markdown") => {
    try {
      const res = await fetch(`${API_BASE}/investigations/${id}/export?format=${format}`);
      if (res.ok) {
        const text = await res.text();
        const blob = new Blob([text], {
          type: format === "markdown" ? "text/markdown" : "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `openintel-report-${id.slice(0, 8)}.${format === "markdown" ? "md" : "json"}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error("Export failed", err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col text-slate-100">
      {/* Top Application Header */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-white/5 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo & Brand */}
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => setCurrentView("dashboard")}
          >
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 text-slate-950 shadow-md shadow-cyan-500/20">
              <Radar size={22} className="stroke-[2.5]" />
            </div>
            <div>
              <div className="text-base font-extrabold tracking-wider text-white flex items-center gap-2">
                OPEN<span className="text-sky-400">INTEL</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-500/10 text-sky-400 font-mono border border-sky-500/20">
                  v0.1.0
                </span>
              </div>
              <p className="text-[10px] text-slate-500 font-mono tracking-tight">
                Unified OSINT Intelligence Engine
              </p>
            </div>
          </div>

          {/* Center Navigation */}
          <nav className="flex items-center gap-1.5">
            <button
              id="nav-dashboard-btn"
              onClick={() => setCurrentView("dashboard")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                currentView === "dashboard"
                  ? "bg-white/10 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers size={14} />
              <span>Dashboard</span>
            </button>

            <button
              id="nav-new-investigation-btn"
              onClick={() => setCurrentView("new")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                currentView === "new"
                  ? "bg-white/10 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <PlusCircle size={14} />
              <span>New Investigation</span>
            </button>
          </nav>

          {/* Right Status Badge */}
          <div className="flex items-center gap-3">
            <button
              onClick={fetchInvestigations}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              title="Refresh investigations"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            </button>

            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-white/5 text-[11px] font-mono text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400" />
              <span>Localhost 127.0.0.1</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {currentView === "dashboard" && (
          <Dashboard
            investigations={investigations}
            loading={loading}
            onNewInvestigation={() => setCurrentView("new")}
            onSelectInvestigation={handleSelectInvestigation}
          />
        )}

        {currentView === "new" && (
          <NewInvestigation
            onSubmit={handleCreateInvestigation}
            onCancel={() => setCurrentView("dashboard")}
          />
        )}

        {currentView === "progress" && (
          <LiveProgress
            progressPct={progressPct}
            currentStep={currentStep}
            logs={liveLogs}
            status={liveStatus}
            onViewResults={() => setCurrentView("detail")}
          />
        )}

        {currentView === "detail" && (
          <InvestigationDetail
            investigation={activeInvestigationDetail}
            onBack={() => {
              setCurrentView("dashboard");
              fetchInvestigations();
            }}
            onCancel={handleCancelInvestigation}
            onExport={handleExport}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 px-6 text-center text-xs text-slate-600 font-mono">
        OpenIntel Personal OSINT Platform · Built for authorized investigative operations
      </footer>

      {/* Ethical Protocol Modal */}
      {showEthicalModal && <EthicalNoticeModal onAccept={handleAcceptTerms} />}
    </div>
  );
}
