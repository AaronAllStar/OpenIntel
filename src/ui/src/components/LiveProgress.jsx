import React, { useState } from "react";
import { 
  CheckCircle2, 
  CircleDashed, 
  Circle, 
  Terminal, 
  ChevronDown, 
  ChevronUp, 
  ArrowRight
} from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function LiveProgress({
  progressPct = 10,
  currentStep = "Starting engines...",
  logs = [],
  status = "working",
  onViewResults,
}) {
  const { t, lang } = useLanguage();
  const [showLogs, setShowLogs] = useState(false);

  const stages = [
    { id: "validate", label: t("progressStepValidate"), minPct: 5 },
    { id: "dispatch", label: t("progressStepDispatch"), minPct: 20 },
    { id: "profiles", label: t("progressStepProfiles"), minPct: 50 },
    { id: "correlate", label: t("progressStepCorrelate"), minPct: 80 },
    { id: "complete", label: t("progressStepComplete"), minPct: 100 },
  ];

  return (
    <div className="max-w-2xl mx-auto py-8 animate-fadeIn text-left">
      <div className="glass-panel p-8 relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2.5">
            <span className="pulse-indicator" />
            <h2 className="text-xl font-bold text-white">{t("progressTitle")}</h2>
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
          {stages.map((stage, idx) => {
            const isCompleted = progressPct >= stage.minPct || status === "review" || status === "final";
            const isCurrent = !isCompleted && (idx === 0 || progressPct >= stages[idx - 1].minPct);

            return (
              <div
                key={stage.id}
                className={`flex items-center gap-3.5 transition-opacity ${
                  isCompleted ? "opacity-100" : isCurrent ? "opacity-100" : "opacity-40"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
                ) : isCurrent ? (
                  <CircleDashed size={18} className="text-sky-400 animate-spin shrink-0" />
                ) : (
                  <Circle size={18} className="text-slate-600 shrink-0" />
                )}
                <span
                  className={`text-sm ${
                    isCurrent
                      ? "text-sky-400 font-medium font-mono"
                      : isCompleted
                      ? "text-slate-200 line-through text-slate-400"
                      : "text-slate-500"
                  }`}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Current Dynamic Telemetry Step */}
        <div className="bg-slate-950/80 rounded-xl p-4 border border-white/5 mb-6">
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider mb-1">
            {lang === "es" ? "Paso Operativo Actual" : "Current Operational Step"}
          </div>
          <div className="text-sm font-mono text-cyan-300 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span>{currentStep}</span>
          </div>
        </div>

        {/* Collapsible SSE Raw Terminal Logs */}
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => setShowLogs(!showLogs)}
            className="flex items-center justify-between w-full p-2.5 rounded-lg bg-slate-900/50 border border-white/5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-colors"
          >
            <div className="flex items-center gap-2 font-mono">
              <Terminal size={14} className="text-slate-400" />
              <span>{t("progressLiveLogs")} ({logs.length})</span>
            </div>
            {showLogs ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {showLogs && (
            <div className="bg-slate-950 rounded-xl p-3 border border-white/5 font-mono text-[11px] text-slate-400 max-h-48 overflow-y-auto space-y-1">
              {logs.length === 0 ? (
                <div className="text-slate-600 italic">
                  {lang === "es" ? "Esperando eventos del motor..." : "Waiting for engine events..."}
                </div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="leading-tight text-slate-300">
                    <span className="text-slate-600 mr-2">›</span>
                    {log}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Ready Action Button */}
        {(progressPct >= 100 || status === "review" || status === "final") && (
          <div className="mt-8 pt-6 border-t border-white/10 flex justify-end">
            <button
              onClick={onViewResults}
              className="btn-primary py-3 px-6 text-sm flex items-center gap-2"
            >
              <span>{t("progressViewResultsBtn")}</span>
              <ArrowRight size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
