import React, { useState } from "react";
import { 
  Search, 
  PlusCircle, 
  FolderGit2, 
  Activity, 
  ShieldCheck, 
  Database,
  ArrowRight,
  Clock,
  Radar,
  Sparkles,
  User,
  Phone,
  Fingerprint,
  Globe
} from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function Dashboard({
  investigations = [],
  loading = false,
  onNewInvestigation,
  onSelectInvestigation,
}) {
  const { t, lang } = useLanguage();
  const [searchTerm, setSearchTerm] = useState("");
  const [filterKind, setFilterKind] = useState("all");

  const activeCount = investigations.filter(
    (i) => i.status === "running" || i.status === "working"
  ).length;

  const totalEntities = investigations.reduce(
    (acc, curr) => acc + (curr.entities_count || 0), 0
  );

  const totalEvidence = investigations.reduce(
    (acc, curr) => acc + (curr.evidence_count || 0), 0
  );

  const filtered = investigations.filter((inv) => {
    const matchesSearch =
      inv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inv.target?.value?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesKind = filterKind === "all" || inv.target?.kind === filterKind;
    return matchesSearch && matchesKind;
  });

  const filterChips = lang === "es" ? [
    { id: "all", label: "Todos" },
    { id: "person_name", label: "Personas" },
    { id: "phone", label: "Teléfonos" },
    { id: "national_id", label: "Documentos / IDs" },
    { id: "username", label: "Usuarios / X / IG" },
    { id: "email", label: "Emails" },
    { id: "domain", label: "Dominios" },
  ] : [
    { id: "all", label: "All" },
    { id: "person_name", label: "Persons" },
    { id: "phone", label: "Phones" },
    { id: "national_id", label: "National IDs" },
    { id: "username", label: "Usernames / X / IG" },
    { id: "email", label: "Emails" },
    { id: "domain", label: "Domains" },
  ];

  const getStatusLabel = (status) => {
    switch (status) {
      case "completed":
        return t("dashboardStatusCompleted");
      case "working":
      case "running":
        return t("dashboardStatusWorking");
      case "failed":
        return t("dashboardStatusFailed");
      case "cancelled":
        return t("dashboardStatusCancelled");
      default:
        return status;
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn text-left">
      {/* Top Hero Banner with Radar Widget */}
      <div className="glass-panel p-6 md:p-8 relative overflow-hidden border border-slate-700/60 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-semibold mb-3">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              {t("dashboardHeroBadge")}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
              {t("dashboardHeroTitle")}
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              {t("dashboardHeroDesc")}
            </p>

            <div className="flex flex-wrap gap-2 mt-4">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <User size={12} className="text-cyan-400" /> {t("dashboardPersonTag")}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <Phone size={12} className="text-emerald-400" /> {t("dashboardPhoneTag")}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <Fingerprint size={12} className="text-rose-400" /> {t("dashboardIdTag")}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <Globe size={12} className="text-indigo-400" /> {t("dashboardDigitalTag")}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            {/* Visual Radar Indicator */}
            <div className="hidden lg:flex flex-col items-center gap-2 pr-4 border-r border-slate-800">
              <div className="radar-ring flex items-center justify-center">
                <div className="radar-sweep-beam" />
                <Radar className="w-8 h-8 text-cyan-400 opacity-90 z-10 animate-pulse" />
              </div>
              <span className="text-[10px] text-cyan-400/80 font-mono tracking-wider">
                {lang === "es" ? "RADAR ACTIVO" : "ACTIVE RADAR"}
              </span>
            </div>

            <button
              id="dashboard-new-investigation-btn"
              onClick={onNewInvestigation}
              className="btn-primary py-3.5 px-6 text-sm font-bold shadow-lg"
            >
              <PlusCircle size={18} />
              {t("navNewInvestigation")}
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">{t("dashboardRecentTitle")}</span>
            <FolderGit2 size={18} className="text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{investigations.length}</div>
          <div className="text-xs text-slate-400 mt-1">{lang === "es" ? "Operaciones registradas" : "Total recorded operations"}</div>
        </div>

        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">{t("dashboardStatsActive")}</span>
            <Activity size={18} className="text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">{activeCount}</div>
          <div className="text-xs text-slate-400 mt-1">{lang === "es" ? "Motores sondeando en vivo" : "Live engines running"}</div>
        </div>

        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">{t("dashboardStatsEntities")}</span>
            <ShieldCheck size={18} className="text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{totalEntities}</div>
          <div className="text-xs text-slate-400 mt-1">{lang === "es" ? "Personas, perfiles, emails, números" : "Profiles, emails, phones, IDs"}</div>
        </div>

        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">{t("dashboardStatsEvidence")}</span>
            <Database size={18} className="text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{totalEvidence}</div>
          <div className="text-xs text-slate-400 mt-1">{lang === "es" ? "Observaciones con clasificación" : "Corroborated observations"}</div>
        </div>
      </div>

      {/* Investigations Table & Interactive Filters */}
      <div className="glass-panel p-6 border border-slate-800/80 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              {t("dashboardRecentTitle")}
            </h2>
            <p className="text-xs text-slate-400">
              {lang === "es" ? "Selecciona cualquier caso para inspeccionar su grafo de relaciones y matriz de evidencia." : "Select any investigation to inspect its relationship graph and evidence provenance."}
            </p>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder={t("dashboardSearchPlaceholder")}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:border-cyan-400 focus:outline-none"
            />
          </div>
        </div>

        {/* Target Kind Chips Filter */}
        <div className="flex flex-wrap gap-2">
          {filterChips.map((k) => (
            <button
              key={k.id}
              onClick={() => setFilterKind(k.id)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                filterKind === k.id
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {k.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            {lang === "es" ? "Cargando historial de investigaciones..." : "Loading investigations..."}
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs space-y-3">
            <p>{t("dashboardEmptyDesc")}</p>
            <button
              onClick={onNewInvestigation}
              className="btn-primary text-xs px-4 py-2"
            >
              {t("navNewInvestigation")}
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-3 font-semibold">{lang === "es" ? "Caso / Objetivo" : "Target / Case"}</th>
                  <th className="pb-3 font-semibold">{lang === "es" ? "Tipo" : "Type"}</th>
                  <th className="pb-3 font-semibold">{lang === "es" ? "Estado" : "Status"}</th>
                  <th className="pb-3 font-semibold text-center">{lang === "es" ? "Entidades" : "Entities"}</th>
                  <th className="pb-3 font-semibold text-center">{lang === "es" ? "Evidencias" : "Evidence"}</th>
                  <th className="pb-3 font-semibold">{lang === "es" ? "Fecha" : "Date"}</th>
                  <th className="pb-3 font-semibold text-right">{lang === "es" ? "Acción" : "Action"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {filtered.map((inv) => {
                  const isCompleted = inv.status === "completed";
                  const isWorking = inv.status === "working" || inv.status === "running";
                  const isFailed = inv.status === "failed";

                  return (
                    <tr
                      key={inv.id}
                      onClick={() => onSelectInvestigation(inv.id)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                    >
                      <td className="py-3.5 pr-4">
                        <div className="font-semibold text-white group-hover:text-cyan-300 transition-colors">
                          {inv.name}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5 mt-0.5">
                          <span className="text-slate-500 uppercase">{inv.target?.kind || "target"}:</span>
                          <span>{inv.target?.value || "N/A"}</span>
                        </div>
                      </td>

                      <td className="py-3 text-slate-300 capitalize">
                        {inv.investigation_type || "quick"}
                      </td>

                      <td className="py-3">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            isCompleted
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : isWorking
                              ? "bg-sky-500/10 text-sky-400 border-sky-500/20 animate-pulse"
                              : isFailed
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              : "bg-slate-700/20 text-slate-400 border-slate-700/30"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isCompleted
                                ? "bg-emerald-400"
                                : isWorking
                                ? "bg-sky-400"
                                : isFailed
                                ? "bg-rose-400"
                                : "bg-slate-400"
                            }`}
                          />
                          {getStatusLabel(inv.status)}
                        </span>
                      </td>

                      <td className="py-3 text-center font-mono font-medium text-slate-300">
                        {inv.entities_count || 0}
                      </td>

                      <td className="py-3 text-center font-mono font-medium text-slate-300">
                        {inv.evidence_count || 0}
                      </td>

                      <td className="py-3 text-slate-400 text-[11px]">
                        <div className="flex items-center gap-1">
                          <Clock size={12} className="text-slate-500" />
                          <span>
                            {inv.created_at
                              ? new Date(inv.created_at).toLocaleDateString(lang === "es" ? "es-ES" : "en-US", {
                                  month: "short",
                                  day: "numeric",
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })
                              : "N/A"}
                          </span>
                        </div>
                      </td>

                      <td className="py-3 text-right">
                        <button
                          className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 group-hover:text-white group-hover:border-cyan-500/40 group-hover:bg-cyan-500/10 transition-all inline-flex items-center gap-1 text-[11px] font-semibold"
                        >
                          <span>{t("dashboardViewResults")}</span>
                          <ArrowRight size={12} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
