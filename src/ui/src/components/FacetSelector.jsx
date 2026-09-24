import React from "react";
import { CheckSquare, Square, Sparkles } from "lucide-react";

export const ENGINE_CATEGORIES = [
  {
    id: "social",
    title: "Redes Sociales y Perfiles",
    color: "cyan",
    engines: [
      { id: "twikit", name: "X (Twitter) - Twikit", desc: "Búsqueda y extracción pública en X sin login" },
      { id: "instaloader", name: "Instagram - Instaloader", desc: "Metadatos, biografía y presencia en Instagram" },
      { id: "sherlock", name: "Sherlock", desc: "Búsqueda de nombre de usuario en 400+ plataformas" },
      { id: "maigret", name: "Maigret", desc: "Parsing profundo de perfiles, avatares y tags" },
      { id: "blackbird", name: "Blackbird", desc: "Reconocimiento ultra-rápido en 500+ sitios web" },
      { id: "socialscan", name: "Socialscan", desc: "Sondas de señal de cuenta sin credenciales" },
    ],
  },
  {
    id: "telecom",
    title: "Teléfono y Mensajería",
    color: "emerald",
    engines: [
      { id: "whatsapp", name: "WhatsApp Intelligence", desc: "Verificación de presencia wa.me, API directa y vCard" },
      { id: "phoneinfoga", name: "PhoneInfoga & ITU", desc: "Normalización ITU, operador y formato internacional" },
      { id: "bellingcat_telegram", name: "Bellingcat Telegram", desc: "Detección de presencia pública en Telegram" },
      { id: "ignorant", name: "Ignorant", desc: "Comprobación de cuenta asociada a teléfono" },
      { id: "searchphone", name: "SearchPhone", desc: "Enrutamiento global de telecomunicaciones" },
    ],
  },
  {
    id: "corporate",
    title: "Identidad Corporativa y Correos de Empresa",
    color: "amber",
    engines: [
      { id: "email_enrich", name: "Email Enrich (Business)", desc: "Generación de permutaciones corporativas y validación DNS MX" },
      { id: "email_finder", name: "Email Finder", desc: "Descubrimiento de esquemas de correo empresarial y buzones públicos" },
      { id: "the_harvester", name: "theHarvester", desc: "Recolección de correos, subdominios y transparencia de certificados" },
      { id: "holehe", name: "Holehe", desc: "Verificación de registro de correo en 120+ servicios" },
      { id: "ghunt", name: "GHunt", desc: "Huella pública en servicios de Google (Maps, Drive, etc.)" },
      { id: "h8mail", name: "H8mail", desc: "Correlación de fugas y brechas públicas de correo" },
      { id: "crosslinked", name: "CrossLinked", desc: "Mapeo de personal y organizaciones en LinkedIn" },
    ],
  },
  {
    id: "network",
    title: "Infraestructura, Dominios y Código",
    color: "indigo",
    engines: [
      { id: "amass", name: "OWASP Amass", desc: "Mapeo de activos externos y enrutamiento DNS" },
      { id: "dnstwist", name: "DNSTwist", desc: "Detección de typosquatting y permutaciones de dominio" },
      { id: "recon_ng", name: "Recon-ng", desc: "Framework de reconocimiento web modular" },
      { id: "photon", name: "Photon", desc: "Rastreador web de alta velocidad para endpoints" },
      { id: "spiderfoot", name: "SpiderFoot", desc: "Correlación profunda de red e inteligencia OSINT" },
      { id: "octosuite", name: "OctoSuite", desc: "Inteligencia de repositorios GitHub y colaboradores" },
      { id: "trufflehog", name: "TruffleHog", desc: "Auditoría de secretos y claves expuestas en commits/código" },
      { id: "metagoofil", name: "Metagoofil", desc: "Extracción de metadatos y autores en documentos públicos" },
    ],
  },
  {
    id: "registry",
    title: "Registros Nacionales e Identificadores",
    color: "rose",
    engines: [
      { id: "id_validation", name: "ID Validation (stdnum/idnumbers)", desc: "Validación de algoritmo de control para DNI, NIE, SSN, RFC, CPF (70+ países)" },
    ],
  },
];

const PRESETS = [
  { id: "all", label: "Todos los Motores", icon: Sparkles, engines: [] },
  { id: "social_only", label: "Solo Redes Sociales", engines: ["twikit", "instaloader", "sherlock", "maigret", "blackbird", "socialscan"] },
  { id: "phone_whatsapp", label: "Teléfono y WhatsApp", engines: ["whatsapp", "phoneinfoga", "bellingcat_telegram", "ignorant", "searchphone"] },
  { id: "corporate_recon", label: "Reconocimiento Corporativo", engines: ["email_enrich", "email_finder", "the_harvester", "crosslinked", "holehe"] },
  { id: "network_audit", label: "Infraestructura y Fugas", engines: ["amass", "dnstwist", "photon", "trufflehog", "spiderfoot", "octosuite"] },
  { id: "id_check", label: "Validación de Documentos", engines: ["id_validation"] },
];

export default function FacetSelector({ selectedEngines, onSelectionChange }) {
  const allEngineIds = ENGINE_CATEGORIES.flatMap((c) => c.engines.map((e) => e.id));

  const applyPreset = (presetEngines) => {
    onSelectionChange(presetEngines);
  };

  const toggleEngine = (id) => {
    if (selectedEngines.includes(id)) {
      onSelectionChange(selectedEngines.filter((e) => e !== id));
    } else {
      onSelectionChange([...selectedEngines, id]);
    }
  };

  const isEngineSelected = (id) => {
    if (selectedEngines.length === 0) return true; // Empty array means automated all/recommended
    return selectedEngines.includes(id);
  };

  const toggleCategory = (categoryEngines) => {
    const ids = categoryEngines.map((e) => e.id);
    const allSelected = ids.every((id) => isEngineSelected(id));

    if (allSelected) {
      // Remove all in this category
      const current = selectedEngines.length === 0 ? allEngineIds : selectedEngines;
      onSelectionChange(current.filter((id) => !ids.includes(id)));
    } else {
      // Add all in this category
      const current = selectedEngines.length === 0 ? [] : selectedEngines;
      const combined = Array.from(new Set([...current, ...ids]));
      onSelectionChange(combined);
    }
  };

  return (
    <div className="space-y-4">
      {/* Quick Selection Presets */}
      <div>
        <label className="block text-xs font-semibold text-slate-300 mb-2">
          Presets Rápidos de Investigación:
        </label>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => {
            const isActive =
              p.engines.length === 0
                ? selectedEngines.length === 0
                : p.engines.every((id) => selectedEngines.includes(id)) &&
                  selectedEngines.length === p.engines.length;

            return (
              <button
                key={p.id}
                type="button"
                onClick={() => applyPreset(p.engines)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-cyan-500 text-slate-950 font-bold shadow-glow"
                    : "bg-slate-800/80 text-slate-300 hover:bg-slate-700/80 border border-slate-700/60"
                }`}
              >
                {p.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Engine Category Groups */}
      <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
        {ENGINE_CATEGORIES.map((cat) => {
          const catIds = cat.engines.map((e) => e.id);
          const allActive = catIds.every((id) => isEngineSelected(id));

          return (
            <div
              key={cat.id}
              className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/90 space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  {cat.title}
                </span>
                <button
                  type="button"
                  onClick={() => toggleCategory(cat.engines)}
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  {allActive ? "Desmarcar categoría" : "Seleccionar todo"}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {cat.engines.map((eng) => {
                  const checked = isEngineSelected(eng.id);
                  return (
                    <div
                      key={eng.id}
                      onClick={() => toggleEngine(eng.id)}
                      className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all ${
                        checked
                          ? "bg-cyan-950/30 border-cyan-500/40 text-slate-100"
                          : "bg-slate-950/40 border-slate-800/60 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {checked ? (
                          <CheckSquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                        ) : (
                          <Square className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                        )}
                        <span className="text-xs font-semibold text-white">{eng.name}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 pl-5 leading-relaxed line-clamp-2">
                        {eng.desc}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
