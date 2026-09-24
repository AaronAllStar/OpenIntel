import React, { useState } from "react";
import { 
  ArrowLeft, 
  Share2, 
  Download, 
  ExternalLink, 
  ShieldCheck, 
  Network, 
  Database, 
  Layers, 
  ListFilter,
  FileText,
  Clock,
  Search,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import GraphView from "./GraphView";

export default function InvestigationDetail({
  investigation,
  onBack,
  onCancel,
  onExport,
}) {
  const [activeTab, setActiveTab] = useState("overview"); // overview, entities, graph, evidence
  const [entityFilter, setEntityFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  if (!investigation) {
    return <div className="p-8 text-center text-slate-400">Investigation details unavailable.</div>;
  }

  const entities = investigation.entities || [];
  const evidence = investigation.evidence || [];
  const relationships = investigation.relationships || [];

  // Filtered entities
  const filteredEntities = entities.filter((e) => {
    const matchesKind = entityFilter === "all" || e.kind === entityFilter;
    const matchesSearch = !searchQuery || e.value.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesKind && matchesSearch;
  });

  const entityKinds = ["all", ...new Set(entities.map((e) => e.kind))];

  return (
    <div className="space-y-6 animate-fadeIn text-left">
      {/* Top Navigation Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 glass-panel p-6">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-900 border border-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 font-mono font-semibold uppercase">
                {investigation.target_kind}
              </span>
              <h1 className="text-xl font-bold text-white font-mono">
                {investigation.target_value}
              </h1>
              <span
                className={`badge ${
                  investigation.status === "review" || investigation.status === "final"
                    ? "badge-supported"
                    : investigation.status === "working" || investigation.status === "running"
                    ? "badge-observed"
                    : "badge-potential"
                }`}
              >
                {investigation.status}
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-1 flex items-center gap-3">
              <span>{investigation.name}</span>
              <span>·</span>
              <span className="flex items-center gap-1 font-mono text-[11px]">
                <Clock size={12} />
                {investigation.created_at ? new Date(investigation.created_at).toLocaleString() : "N/A"}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {investigation.status === "working" && (
            <button
              onClick={() => onCancel(investigation.id)}
              className="btn-secondary text-xs text-rose-400 hover:text-rose-300"
            >
              Cancel Scan
            </button>
          )}
          <button
            id="export-markdown-report-btn"
            onClick={() => onExport(investigation.id, "markdown")}
            className="btn-secondary text-xs"
          >
            <Download size={14} />
            Export Markdown
          </button>
          <button
            id="export-json-report-btn"
            onClick={() => onExport(investigation.id, "json")}
            className="btn-secondary text-xs"
          >
            <FileText size={14} />
            Export JSON
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-white/5 pb-2">
        {[
          { id: "overview", label: "Overview", icon: Layers, count: null },
          { id: "entities", label: "Entities", icon: ShieldCheck, count: entities.length },
          { id: "graph", label: "Relationship Graph", icon: Network, count: relationships.length },
          { id: "evidence", label: "Evidence Provenance", icon: Database, count: evidence.length },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                active
                  ? "bg-sky-500/15 text-sky-400 border border-sky-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                Discovered Entities
              </div>
              <div className="text-2xl font-bold text-white">{entities.length}</div>
              <div className="text-xs text-slate-500 mt-1">Across multiple categories</div>
            </div>

            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                Linked Relationships
              </div>
              <div className="text-2xl font-bold text-sky-400">{relationships.length}</div>
              <div className="text-xs text-slate-500 mt-1">Direct and supported links</div>
            </div>

            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                Evidence Provenance Records
              </div>
              <div className="text-2xl font-bold text-emerald-400">{evidence.length}</div>
              <div className="text-xs text-slate-500 mt-1">Timestamped observations</div>
            </div>
          </div>

          {/* Key Relationships Highlight */}
          <div className="glass-panel p-6">
            <h2 className="text-sm font-bold text-white mb-4">Top Confirmed Associations</h2>
            {relationships.length === 0 ? (
              <div className="text-xs text-slate-500 py-4">No associations computed yet.</div>
            ) : (
              <div className="space-y-3">
                {relationships.slice(0, 5).map((rel) => (
                  <div
                    key={rel.id}
                    className="p-3.5 rounded-xl bg-slate-900/50 border border-white/5 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200">
                        {rel.reasoning || `${rel.predicate} relation established`}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                        Predicate: <span className="text-sky-400">{rel.predicate}</span>
                      </div>
                    </div>
                    <span className="badge badge-supported text-[10px]">{rel.confidence}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Entities */}
      {activeTab === "entities" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {entityKinds.map((k) => (
                <button
                  key={k}
                  onClick={() => setEntityFilter(k)}
                  className={`text-xs px-3 py-1.5 rounded-xl font-medium capitalize transition-all ${
                    entityFilter === k
                      ? "bg-sky-500 text-slate-950 font-semibold"
                      : "bg-slate-900/70 text-slate-400 hover:text-slate-200 border border-white/5"
                  }`}
                >
                  {k}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-white/10 w-full sm:w-64">
              <Search size={14} className="text-slate-400" />
              <input
                type="text"
                placeholder="Search entities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full font-mono"
              />
            </div>
          </div>

          {/* Entity Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredEntities.map((ent) => (
              <div
                key={ent.id}
                className="glass-panel glass-panel-hover p-4 text-left flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                      {ent.kind}
                    </span>
                    <span className="badge badge-observed text-[10px]">{ent.confidence}</span>
                  </div>

                  <div className="font-semibold text-white text-xs break-all font-mono mb-2">
                    {ent.value.startsWith("http") ? (
                      <a
                        href={ent.value}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sky-400 hover:underline flex items-center gap-1"
                      >
                        {ent.value}
                        <ExternalLink size={12} className="shrink-0" />
                      </a>
                    ) : (
                      ent.value
                    )}
                  </div>
                </div>

                {ent.attributes && Object.keys(ent.attributes).length > 0 && (
                  <div className="mt-3 pt-2 border-t border-white/5 text-[10px] text-slate-400 space-y-0.5 font-mono">
                    {Object.entries(ent.attributes).slice(0, 3).map(([k, v]) => (
                      <div key={k} className="truncate">
                        <span className="text-slate-500">{k}:</span> {String(v)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Relationship Graph */}
      {activeTab === "graph" && (
        <GraphView entities={entities} relationships={relationships} />
      )}

      {/* Tab 4: Evidence Provenance */}
      {activeTab === "evidence" && (
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-white">Full Evidence Provenance Trail</h2>
            <span className="text-xs text-slate-400 font-mono">{evidence.length} records</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-white/5 text-slate-400 uppercase font-semibold">
                  <th className="py-2.5 px-3">Tool</th>
                  <th className="py-2.5 px-3">Source</th>
                  <th className="py-2.5 px-3">Classification</th>
                  <th className="py-2.5 px-3">Raw Observation</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-slate-300">
                {evidence.map((ev) => (
                  <tr
                    key={ev.id}
                    className="hover:bg-white/[0.02] cursor-pointer"
                    onClick={() => setSelectedEvidence(ev)}
                  >
                    <td className="py-2.5 px-3 font-semibold text-sky-400">{ev.tool}</td>
                    <td className="py-2.5 px-3 text-slate-400">{ev.source}</td>
                    <td className="py-2.5 px-3">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                        ev.info_classification === "PUBLIC_REGISTRY"
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          : ev.info_classification === "PLATFORM_SIGNAL"
                          ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
                          : ev.info_classification === "INFERENCE"
                          ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                          : "bg-sky-500/15 text-sky-400 border border-sky-500/30"
                      }`}>
                        {ev.info_classification || "PUBLIC_OBSERVATION"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 max-w-xs truncate text-slate-300">
                      {ev.raw_observation}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="badge badge-observed text-[9px]">{ev.confidence}</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Evidence Provenance Modal */}
      {selectedEvidence && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel max-w-lg w-full p-6 text-left border-sky-500/30">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white">Evidence Provenance</h3>
                <p className="text-xs text-slate-400">Captured by {selectedEvidence.tool}</p>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="text-slate-500 hover:text-slate-300"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500 block mb-0.5">Source:</span>
                <span className="text-white font-mono bg-slate-900 px-2 py-1 rounded">
                  {selectedEvidence.source}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block mb-0.5">Raw Observation:</span>
                <div className="bg-slate-950 p-3 rounded-lg border border-white/5 font-mono text-[11px] text-slate-300 whitespace-pre-wrap">
                  {selectedEvidence.raw_observation}
                </div>
              </div>

              <div>
                <span className="text-slate-500 block mb-0.5">Classification:</span>
                <span className="font-mono text-sky-400 font-semibold">
                  {selectedEvidence.info_classification || "PUBLIC_OBSERVATION"}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block mb-0.5">Confidence:</span>
                <span className="badge badge-supported">{selectedEvidence.confidence}</span>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button onClick={() => setSelectedEvidence(null)} className="btn-secondary text-xs">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
