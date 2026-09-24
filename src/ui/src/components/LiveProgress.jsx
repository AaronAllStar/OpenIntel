import React, { useState } from "react";
import { 
  CheckCircle2, 
  CircleDashed, 
  Circle, 
  Terminal, 
  ChevronDown, 
  ChevronUp,
  Activity,
  ArrowRight
} from "lucide-react";

const STAGES = [
  { id: "validate", label: "Target Validated & Normalized", minPct: 5 },
  { id: "dispatch", label: "Engine Discovery Initiated", minPct: 20 },
  { id: "profiles", label: "Profile & Identity Resolution", minPct: 50 },
  { id: "correlate", label: "Relationship & Link Correlation", minPct: 80 },
  { id: "complete", label: "Investigation Ready for Review", minPct: 100 },
];

export default function LiveProgress({
  progressPct = 10,
  currentStep = "Starting engines...",
  logs = [],
  status = "working",
  onViewResults,
}) {
  const [showLogs, setShowLogs] = useState(false);

  return (
    <div className="max-w-2xl mx-auto py-8 animate-fadeIn text-left">
      <div className="glass-panel p-8 relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2.5">
            <span className="pulse-indicator" />
            <h2 className="text-xl font-bold text-white">Reconnaissance in Progress</h2>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-sky-500/15 text-sky-400 font-mono font-semibold border border-sky-500/30">
            {Math.round(progressPct)}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 rounded-full bg-slate-950/80 border border-white/5 overflow-hidden mb-8">
          <div
            className="h-full bg-gradient-to-r from-sky-400 to-indigo-500 transition-all duration-300 ease-out"
            style={{ width: `${Math.max(5, Math.min(100, progressPct))}%` }}
          />
        </div>

        {/* UX Stepper Checklist */}
        <div className="space-y-4 mb-8">
          {STAGES.map((stage, idx) => {
            const isCompleted = progressPct >= stage.minPct || status === "review" || status === "final";
            const isCurrent = !isCompleted && (idx === 0 || progressPct >= STAGES[idx - 1].minPct);

            return (
              <div
                key={stage.id}
                className={`flex items-center gap-3.5 p-3 rounded-xl transition-all ${
                  isCurrent
                    ? "bg-sky-500/10 border border-sky-500/30 text-sky-300"
                    : isCompleted
                    ? "text-slate-300"
                    : "text-slate-600"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
                ) : isCurrent ? (
                  <CircleDashed size={18} className="text-sky-400 shrink-0 animate-spin" />
                ) : (
                  <Circle size={18} className="text-slate-700 shrink-0" />
                )}

                <div className="flex-1">
                  <div className="text-xs font-semibold">{stage.label}</div>
                  {isCurrent && (
                    <div className="text-[11px] text-sky-400 font-mono mt-0.5 animate-pulse">
                      {currentStep}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Completed Action */}
        {(status === "review" || status === "final") && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between animate-fadeIn">
            <div className="text-xs text-emerald-300 font-medium">
              All selected engines completed execution. Findings are normalized.
            </div>
            <button
              id="view-investigation-results-btn"
              onClick={onViewResults}
              className="btn-primary text-xs py-2 px-4"
            >
              Explore Findings
              <ArrowRight size={14} />
            </button>
          </div>
        )}

        {/* Collapsible Execution Logs */}
        <div className="border-t border-white/5 pt-4">
          <button
            type="button"
            onClick={() => setShowLogs(!showLogs)}
            className="flex items-center justify-between w-full text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-sky-400" />
              <span>Technical Execution Stream ({logs.length} events)</span>
            </div>
            {showLogs ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showLogs && (
            <div className="mt-3 p-4 rounded-xl bg-black/60 border border-white/5 font-mono text-[11px] text-slate-400 h-44 overflow-y-auto space-y-1 select-text">
              {logs.length === 0 ? (
                <div className="text-slate-600">Waiting for live events...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="text-slate-600">[{i + 1}]</span>
                    <span className="text-slate-300">{log}</span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
