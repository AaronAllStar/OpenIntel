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

export default function Dashboard({
  investigations = [],
  loading = false,
  onNewInvestigation,
  onSelectInvestigation,
}) {
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

  return (
    <div className="space-y-8 animate-fadeIn text-left">
      {/* Top Hero Banner with Radar Widget */}
      <div className="glass-panel p-6 md:p-8 relative overflow-hidden border border-slate-700/60 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-semibold mb-3">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              Centro de Operaciones OSINT · 27 Motores Integrados
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
              Plataforma Unificada de Inteligencia
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              Explora personas, números de teléfono con prefijo internacional, documentos de identidad (70+ países), 
              perfiles de X, Instagram, WhatsApp, correos corporativos y redes de infraestructura con correlación de evidencia en tiempo real.
            </p>

            <div className="flex flex-wrap gap-2 mt-4">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <User size={12} className="text-cyan-400" /> Nombres & Apellidos
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <Phone size={12} className="text-emerald-400" /> Teléfono & WhatsApp
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <Fingerprint size={12} className="text-rose-400" /> Documentos de Identidad
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-700/80 text-[11px] text-slate-300">
                <Globe size={12} className="text-indigo-400" /> X, IG & Negocios
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
              <span className="text-[10px] text-cyan-400/80 font-mono tracking-wider">RADAR ACTIVO</span>
            </div>

            <button
              id="dashboard-new-investigation-btn"
              onClick={onNewInvestigation}
              className="btn-primary py-3.5 px-6 text-sm font-bold shadow-lg"
            >
              <PlusCircle size={18} />
              Nueva Investigación
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Investigaciones</span>
            <FolderGit2 size={18} className="text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{investigations.length}</div>
          <div className="text-xs text-slate-400 mt-1">Operaciones registradas</div>
        </div>

        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">En Ejecución</span>
            <Activity size={18} className="text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">{activeCount}</div>
          <div className="text-xs text-slate-400 mt-1">Motores sondeando en vivo</div>
        </div>

        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Entidades Halladas</span>
            <ShieldCheck size={18} className="text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{totalEntities}</div>
          <div className="text-xs text-slate-400 mt-1">Personas, perfiles, emails, números</div>
        </div>

        <div className="glass-panel p-5 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Evidencias Verificadas</span>
            <Database size={18} className="text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{totalEvidence}</div>
          <div className="text-xs text-slate-400 mt-1">Observaciones con clasificación</div>
        </div>
      </div>

      {/* Investigations Table & Interactive Filters */}
      <div className="glass-panel p-6 border border-slate-800/80 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Historial de Investigaciones & Casos
            </h2>
            <p className="text-xs text-slate-400">
              Selecciona cualquier caso para inspeccionar su grafo de relaciones y matriz de evidencia.
            </p>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Filtrar por nombre u objetivo..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:border-cyan-400 focus:outline-none"
            />
          </div>
        </div>

        {/* Target Kind Chips Filter */}
        <div className="flex flex-wrap gap-2">
          {[
            { id: "all", label: "Todos" },
            { id: "person_name", label: "Personas" },
            { id: "phone", label: "Teléfonos" },
            { id: "national_id", label: "IDs / Documentos" },
            { id: "username", label: "Usuarios / X / IG" },
            { id: "email", label: "Emails" },
            { id: "domain", label: "Dominios" },
          ].map((k) => (
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
            Cargando historial de investigaciones...
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs space-y-3">
            <p>No se encontraron investigaciones para los criterios seleccionados.</p>
            <button
              onClick={onNewInvestigation}
              className="btn-primary text-xs px-4 py-2"
            >
              Iniciar una Investigación Ahora
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-3 font-semibold">Caso / Objetivo</th>
                  <th className="pb-3 font-semibold">Tipo</th>
                  <th className="pb-3 font-semibold">Estado</th>
                  <th className="pb-3 font-semibold text-center">Entidades</th>
                  <th className="pb-3 font-semibold text-center">Evidencias</th>
                  <th className="pb-3 font-semibold">Fecha</th>
                  <th className="pb-3 font-semibold text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filtered.map((inv) => (
                  <tr
                    key={inv.id}
                    onClick={() => onSelectInvestigation(inv.id)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 pr-4">
                      <div className="font-bold text-white text-xs">{inv.name}</div>
                      <div className="text-[11px] font-mono text-cyan-400/90 truncate max-w-xs">
                        {inv.target?.value}
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] uppercase">
                        {inv.target?.kind || "general"}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                          inv.status === "final" || inv.status === "review"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            : inv.status === "running" || inv.status === "working"
                            ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 animate-pulse"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            inv.status === "final" || inv.status === "review"
                              ? "bg-emerald-400"
                              : inv.status === "running" || inv.status === "working"
                              ? "bg-cyan-400"
                              : "bg-slate-400"
                          }`}
                        />
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-slate-200">
                      {inv.entities_count || 0}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-slate-200">
                      {inv.evidence_count || 0}
                    </td>
                    <td className="py-3 pr-4 text-slate-400 text-[11px] font-mono">
                      {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : "-"}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectInvestigation(inv.id);
                        }}
                        className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold text-xs"
                      >
                        <span>Abrir</span>
                        <ArrowRight size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
