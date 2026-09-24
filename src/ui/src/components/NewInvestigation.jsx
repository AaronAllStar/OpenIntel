import React, { useState } from "react";
import { 
  Play, 
  Sliders, 
  ChevronDown, 
  ChevronUp, 
  AlertTriangle,
  Compass,
  Radar
} from "lucide-react";
import SearchCockpit from "./SearchCockpit";
import FacetSelector from "./FacetSelector";

export default function NewInvestigation({ onSubmit, onCancel }) {
  const [activeMode, setActiveMode] = useState("person");
  const [targetKind, setTargetKind] = useState("person_name");
  const [targetValue, setTargetValue] = useState("");
  const [suggestedName, setSuggestedName] = useState("");
  const [investigationName, setInvestigationName] = useState("");
  const [investigationType, setInvestigationType] = useState("quick");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Advanced engine & facet settings
  const [selectedEngines, setSelectedEngines] = useState([]);
  const [timeoutMs, setTimeoutMs] = useState(30000);
  const [maxResults, setMaxResults] = useState(500);
  const [storeRaw, setStoreRaw] = useState(false);
  const [allowPrivate, setAllowPrivate] = useState(false);

  const handleTargetChange = ({ kind, value, suggestedName: sName }) => {
    setTargetKind(kind);
    setTargetValue(value);
    setSuggestedName(sName || "");
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!targetValue.trim()) {
      setError("Por favor define un valor o parámetro válido para iniciar la investigación.");
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        name: investigationName.trim() || suggestedName || `Investigación: ${targetValue.trim()}`,
        target_kind: targetKind,
        target_value: targetValue.trim(),
        investigation_type: investigationType,
        settings: {
          timeout_ms: timeoutMs,
          max_results: maxResults,
          store_raw: storeRaw,
          allow_private_targets: allowPrivate,
          selected_engines: selectedEngines.length > 0 ? selectedEngines : undefined,
        },
      };

      await onSubmit(payload);
    } catch (err) {
      setError(err.message || "Error al iniciar la investigación");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-6 animate-fadeIn text-left">
      <div className="glass-panel p-6 sm:p-8 relative border border-slate-700/60 shadow-2xl">
        {/* Glow corner indicator */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Radar className="w-5 h-5 text-cyan-400 animate-pulse" />
              <h2 className="text-2xl font-bold text-white tracking-wide">
                Centro de Inteligencia & Exploración
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Selecciona el vector de búsqueda y configura los motores automatizados de OpenIntel.
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-[11px] text-cyan-300 font-mono">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            27 Motores Activos
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-3">
            <AlertTriangle size={16} className="text-rose-400 shrink-0 mt-0.5" />
            <div>
              <strong>Error de Validación:</strong> {error}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 1. Multi-modal Search Cockpit */}
          <div>
            <label className="block text-xs font-bold text-slate-200 uppercase tracking-wider mb-2.5 flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-[11px]">
                1
              </span>
              Modo y Parámetros del Objetivo
            </label>
            <SearchCockpit
              activeMode={activeMode}
              setActiveMode={setActiveMode}
              onTargetChange={handleTargetChange}
            />
          </div>

          {/* Optional Title Customization */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              Nombre de la Operación / Caso (Opcional)
            </label>
            <input
              type="text"
              placeholder={suggestedName || "ej. Operación Fénix - Auditoría Corporativa"}
              value={investigationName}
              onChange={(e) => setInvestigationName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-white text-xs placeholder-slate-500 focus:border-cyan-400 focus:outline-none"
            />
          </div>

          {/* 2. Investigation Depth */}
          <div>
            <label className="block text-xs font-bold text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-[11px]">
                2
              </span>
              Profundidad de Reconocimiento
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                id="investigation-type-quick"
                onClick={() => setInvestigationType("quick")}
                className={`p-3.5 rounded-xl border text-left text-xs transition-all ${
                  investigationType === "quick"
                    ? "bg-cyan-500/15 border-cyan-400 text-cyan-200 shadow-sm shadow-cyan-500/20"
                    : "bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                <div className="font-bold text-white mb-0.5 flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-cyan-400" />
                  Análisis Rápido (Recomendado)
                </div>
                <div className="text-[11px] text-slate-400 leading-snug">
                  Consultas concurrentes en motores prioritarios (menos de 20s).
                </div>
              </button>

              <button
                type="button"
                id="investigation-type-full"
                onClick={() => setInvestigationType("full")}
                className={`p-3.5 rounded-xl border text-left text-xs transition-all ${
                  investigationType === "full"
                    ? "bg-cyan-500/15 border-cyan-400 text-cyan-200 shadow-sm shadow-cyan-500/20"
                    : "bg-slate-900/40 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                <div className="font-bold text-white mb-0.5 flex items-center gap-1.5">
                  <Radar className="w-3.5 h-3.5 text-cyan-400" />
                  Reconocimiento Exhaustivo
                </div>
                <div className="text-[11px] text-slate-400 leading-snug">
                  Correlación completa de subdominios, fugas, repos y metadatos.
                </div>
              </button>
            </div>
          </div>

          {/* 3. Selección Modular de Motores y Facetas ("Poder seleccionar lo que necesito") */}
          <div className="border-t border-slate-800/80 pt-4">
            <button
              type="button"
              id="toggle-advanced-settings-btn"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full py-2.5 px-3 rounded-lg bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-cyan-300 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Sliders size={14} className="text-cyan-400" />
                <span>Personalizar Motores y Facetas ({selectedEngines.length === 0 ? "Automático / Todos" : `${selectedEngines.length} seleccionados`})</span>
              </div>
              {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {showAdvanced && (
              <div className="mt-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4 animate-fadeIn">
                <FacetSelector
                  selectedEngines={selectedEngines}
                  onSelectionChange={setSelectedEngines}
                />

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-800">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Límite de tiempo: {timeoutMs / 1000}s
                    </label>
                    <input
                      type="range"
                      min="10000"
                      max="60000"
                      step="5000"
                      value={timeoutMs}
                      onChange={(e) => setTimeoutMs(Number(e.target.value))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Resultados máximos: {maxResults}
                    </label>
                    <input
                      type="range"
                      min="100"
                      max="1000"
                      step="100"
                      value={maxResults}
                      onChange={(e) => setMaxResults(Number(e.target.value))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2 pt-2 border-t border-slate-800/80">
                  <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={storeRaw}
                      onChange={(e) => setStoreRaw(e.target.checked)}
                      className="rounded border-slate-700 text-cyan-500 focus:ring-cyan-500"
                    />
                    <span>Almacenar respuestas en bruto de los motores</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowPrivate}
                      onChange={(e) => setAllowPrivate(e.target.checked)}
                      className="rounded border-slate-700 text-cyan-500 focus:ring-cyan-500"
                    />
                    <span>Permitir IPs privadas (desactiva protección SSRF para redes de laboratorio)</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onCancel}
              className="btn-secondary text-xs"
              disabled={submitting}
            >
              Cancelar
            </button>
            <button
              type="submit"
              id="start-investigation-submit-btn"
              disabled={submitting}
              className="btn-primary text-xs px-6 py-2.5 font-bold"
            >
              <Play size={15} />
              {submitting ? "Desplegando Motores..." : "Iniciar Investigación"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
