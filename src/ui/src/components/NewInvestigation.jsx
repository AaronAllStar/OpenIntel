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
import { useLanguage } from "../context/LanguageContext";

export default function NewInvestigation({ onSubmit, onCancel }) {
  const { t, lang } = useLanguage();
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
      setError(t("newErrorEmpty"));
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      const defaultPrefix = lang === "es" ? "Investigación" : "Investigation";
      const payload = {
        name: investigationName.trim() || suggestedName || `${defaultPrefix}: ${targetValue.trim()}`,
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
      setError(err.message || "Failed to start investigation");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-4 text-left animate-fadeIn">
      {/* Header Banner */}
      <div className="flex items-center justify-between pb-6 mb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-2">
            <Compass className="text-cyan-400" size={24} />
            {t("newTitle")}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {t("newSubtitle")}
          </p>
        </div>

        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 transition-colors"
        >
          {t("newCancelBtn")}
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Step 1: Select Target & Mode */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white uppercase tracking-wider">
            <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 flex items-center justify-center text-xs font-mono">
              1
            </span>
            {t("newStep1")}
          </div>

          <SearchCockpit
            onTargetChange={handleTargetChange}
            activeMode={activeMode}
            setActiveMode={setActiveMode}
          />
        </div>

        {/* Step 2: Investigation Name & Type */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white uppercase tracking-wider">
            <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 flex items-center justify-center text-xs font-mono">
              2
            </span>
            {t("newStep2")}
          </div>

          <div className="glass-panel p-5 border border-slate-800 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  {t("newInvestNameLabel")}
                </label>
                <input
                  type="text"
                  placeholder={suggestedName || t("newInvestNamePlaceholder")}
                  value={investigationName}
                  onChange={(e) => setInvestigationName(e.target.value)}
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  {t("newInvestTypeLabel")}
                </label>
                <select
                  value={investigationType}
                  onChange={(e) => setInvestigationType(e.target.value)}
                  className="input-field bg-slate-900"
                >
                  <option value="quick">{t("newTypeQuick")}</option>
                  <option value="deep">{t("newTypeDeep")}</option>
                  <option value="passive">{t("newTypePassive")}</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Step 3: Granular Engine & Facet Selection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-white uppercase tracking-wider">
              <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 flex items-center justify-center text-xs font-mono">
                3
              </span>
              {t("presetsTitle")}
            </div>

            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium"
            >
              <Sliders size={14} />
              <span>{t("newAdvancedSettings")}</span>
              {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>

          <div className="glass-panel p-5 border border-slate-800">
            <FacetSelector
              selectedEngines={selectedEngines}
              onSelectionChange={setSelectedEngines}
            />
          </div>
        </div>

        {/* Advanced Settings Collapsible Drawer */}
        {showAdvanced && (
          <div className="glass-panel p-5 border border-slate-800 space-y-4 animate-fadeIn">
            <div className="text-xs font-bold text-slate-300 uppercase tracking-wider border-b border-slate-800 pb-2">
              {t("newAdvancedSettings")}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  {t("newTimeoutLabel")}
                </label>
                <input
                  type="number"
                  min="5000"
                  max="120000"
                  step="5000"
                  value={timeoutMs}
                  onChange={(e) => setTimeoutMs(Number(e.target.value))}
                  className="input-field font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  {t("newMaxResultsLabel")}
                </label>
                <input
                  type="number"
                  min="50"
                  max="2000"
                  step="50"
                  value={maxResults}
                  onChange={(e) => setMaxResults(Number(e.target.value))}
                  className="input-field font-mono"
                />
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-850">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                <input
                  type="checkbox"
                  checked={storeRaw}
                  onChange={(e) => setStoreRaw(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                />
                <span>{t("newStoreRawLabel")}</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-xs text-rose-300">
                <input
                  type="checkbox"
                  checked={allowPrivate}
                  onChange={(e) => setAllowPrivate(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-700 text-rose-500 focus:ring-0"
                />
                <span>{t("newAllowPrivateLabel")}</span>
              </label>
            </div>
          </div>
        )}

        {/* Validation / Execution Errors */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
            <AlertTriangle size={18} className="shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="px-5 py-2.5 rounded-xl border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-850 transition-colors"
          >
            {t("newCancelBtn")}
          </button>

          <button
            type="submit"
            id="start-investigation-submit-btn"
            disabled={submitting}
            className="btn-primary py-2.5 px-6 text-xs font-bold flex items-center gap-2"
          >
            {submitting ? (
              <>
                <Radar size={16} className="animate-spin" />
                <span>{t("newSubmittingBtn")}</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>{t("newStartBtn")}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
