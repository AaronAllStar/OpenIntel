import React from "react";
import { CheckSquare, Square, Sparkles } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export function getEngineCategories(lang = "en") {
  const isEs = lang === "es";

  return [
    {
      id: "social",
      title: isEs ? "Redes Sociales y Perfiles Públicos" : "Social Media & Public Profiles",
      color: "cyan",
      engines: [
        { id: "twikit", name: "X (Twitter) - Twikit", desc: isEs ? "Búsqueda y extracción pública en X sin login" : "Public extraction on X/Twitter without API keys" },
        { id: "instaloader", name: "Instagram - Instaloader", desc: isEs ? "Metadatos, biografía y presencia en Instagram" : "Public profile metadata and bio extraction on Instagram" },
        { id: "sherlock", name: "Sherlock", desc: isEs ? "Búsqueda de nombre de usuario en 400+ plataformas" : "Username reconnaissance across 400+ platforms" },
        { id: "maigret", name: "Maigret", desc: isEs ? "Parsing profundo de perfiles, avatares y tags" : "Deep recursive profile, avatar, and tag parsing" },
        { id: "blackbird", name: "Blackbird", desc: isEs ? "Reconocimiento ultra-rápido en 500+ sitios web" : "High-speed username reconnaissance across 500+ sites" },
        { id: "socialscan", name: "Socialscan", desc: isEs ? "Sondas de señal de cuenta sin credenciales" : "Non-intrusive registration presence signals without credentials" },
      ],
    },
    {
      id: "telecom",
      title: isEs ? "Teléfono y Mensajería" : "Phone & Messaging",
      color: "emerald",
      engines: [
        { id: "whatsapp", name: "WhatsApp Intelligence", desc: isEs ? "Verificación de presencia wa.me, API directa y vCard" : "wa.me click-to-chat verification, direct presence, and vCard" },
        { id: "phoneinfoga", name: "PhoneInfoga & ITU", desc: isEs ? "Normalización ITU, operador y formato internacional" : "ITU E.164 normalization, carrier lookup, and telecom routing" },
        { id: "bellingcat_telegram", name: "Bellingcat Telegram", desc: isEs ? "Detección de presencia pública en Telegram" : "Public phone number registration presence in Telegram" },
        { id: "ignorant", name: "Ignorant", desc: isEs ? "Comprobación de cuenta asociada a teléfono" : "Phone-to-account association reconnaissance" },
        { id: "searchphone", name: "SearchPhone", desc: isEs ? "Enrutamiento global de telecomunicaciones" : "Global telecommunications routing and carrier footprint" },
      ],
    },
    {
      id: "corporate",
      title: isEs ? "Identidad Corporativa y Correos Empresariales" : "Corporate Identity & Business Emails",
      color: "amber",
      engines: [
        { id: "email_enrich", name: "Email Enrich (Business)", desc: isEs ? "Generación de permutaciones corporativas y validación DNS MX" : "Corporate email permutations and async DNS MX validation" },
        { id: "email_finder", name: "Email Finder", desc: isEs ? "Descubrimiento de esquemas de correo empresarial y buzones públicos" : "Corporate email scheme discovery and public mailboxes" },
        { id: "the_harvester", name: "theHarvester", desc: isEs ? "Recolección de correos, subdominios y transparencia de certificados" : "Email harvest, subdomains, and certificate transparency" },
        { id: "holehe", name: "Holehe", desc: isEs ? "Verificación de registro de correo en 120+ servicios" : "Email account registration probes across 120+ services" },
        { id: "ghunt", name: "GHunt", desc: isEs ? "Huella pública en servicios de Google (Maps, Drive, etc.)" : "Public footprint across Google services (Maps, Drive, reviews)" },
        { id: "h8mail", name: "H8mail", desc: isEs ? "Correlación de fugas y brechas públicas de correo" : "Public breach disclosures and credential leak correlation" },
        { id: "crosslinked", name: "CrossLinked", desc: isEs ? "Mapeo de personal y organizaciones en LinkedIn" : "Corporate personnel and organization structure mapping" },
      ],
    },
    {
      id: "network",
      title: isEs ? "Infraestructura, Dominios y Código" : "Infrastructure, Domains & Code",
      color: "indigo",
      engines: [
        { id: "amass", name: "OWASP Amass", desc: isEs ? "Mapeo de activos externos y enrutamiento DNS" : "External network asset mapping and DNS graph routing" },
        { id: "dnstwist", name: "DNSTwist", desc: isEs ? "Detección de typosquatting y permutaciones de dominio" : "Typosquatting detection and domain permutation permutations" },
        { id: "recon_ng", name: "Recon-ng", desc: isEs ? "Framework de reconocimiento web modular" : "Modular open source web reconnaissance framework" },
        { id: "photon", name: "Photon", desc: isEs ? "Rastreador web de alta velocidad para endpoints" : "Ultra-fast web crawler for endpoints, keys, and links" },
        { id: "spiderfoot", name: "SpiderFoot", desc: isEs ? "Correlación profunda de red e inteligencia OSINT" : "Deep infrastructure correlation and multi-source OSINT" },
        { id: "octosuite", name: "OctoSuite", desc: isEs ? "Inteligencia de repositorios GitHub y colaboradores" : "GitHub repository intelligence and contributor auditing" },
        { id: "trufflehog", name: "TruffleHog", desc: isEs ? "Auditoría de secretos y claves expuestas en commits/código" : "High-entropy secrets and credential audits in git commits" },
        { id: "metagoofil", name: "Metagoofil", desc: isEs ? "Extracción de metadatos y autores en documentos públicos" : "Metadata and author extraction in public PDFs and documents" },
      ],
    },
    {
      id: "registry",
      title: isEs ? "Registros Nacionales e Identificadores" : "National Registries & Identifiers",
      color: "rose",
      engines: [
        { id: "id_validation", name: "ID Validation (Rust Engine)", desc: isEs ? "Validación de algoritmos de control en <2µs (DNI, NIE, SSN, RFC, CPF en 70+ países)" : "Algorithmic checksum verification in <2µs (DNI, NIE, SSN, RFC, CPF across 70+ countries)" },
      ],
    },
  ];
}

export default function FacetSelector({ selectedEngines, onSelectionChange }) {
  const { t, lang } = useLanguage();
  const categories = getEngineCategories(lang);
  const allEngineIds = categories.flatMap((c) => c.engines.map((e) => e.id));

  const presets = [
    { id: "all", label: t("presetAll"), icon: Sparkles, engines: [] },
    { id: "social_only", label: t("presetSocial"), engines: ["twikit", "instaloader", "sherlock", "maigret", "blackbird", "socialscan"] },
    { id: "phone_whatsapp", label: t("presetPhone"), engines: ["whatsapp", "phoneinfoga", "bellingcat_telegram", "ignorant", "searchphone"] },
    { id: "corporate_recon", label: t("presetCorporate"), engines: ["email_enrich", "email_finder", "the_harvester", "crosslinked", "holehe"] },
    { id: "network_audit", label: t("presetNetwork"), engines: ["amass", "dnstwist", "photon", "trufflehog", "spiderfoot", "octosuite"] },
    { id: "id_check", label: t("presetId"), engines: ["id_validation"] },
  ];

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
    if (selectedEngines.length === 0) return true; // Empty array means automated all
    return selectedEngines.includes(id);
  };

  const toggleCategory = (categoryEngines) => {
    const ids = categoryEngines.map((e) => e.id);
    const allSelected = ids.every((id) => isEngineSelected(id));

    if (allSelected) {
      const current = selectedEngines.length === 0 ? allEngineIds : selectedEngines;
      onSelectionChange(current.filter((id) => !ids.includes(id)));
    } else {
      const current = selectedEngines.length === 0 ? [] : selectedEngines;
      const combined = Array.from(new Set([...current, ...ids]));
      onSelectionChange(combined);
    }
  };

  return (
    <div className="space-y-4 text-left">
      {/* Quick Selection Presets */}
      <div>
        <label className="block text-xs font-semibold text-slate-300 mb-2">
          {t("presetsTitle")}
        </label>
        <div className="flex flex-wrap gap-2">
          {presets.map((preset) => {
            const isPresetActive =
              preset.engines.length === 0
                ? selectedEngines.length === 0 || selectedEngines.length === allEngineIds.length
                : preset.engines.length === selectedEngines.length &&
                  preset.engines.every((id) => selectedEngines.includes(id));

            return (
              <button
                key={preset.id}
                type="button"
                id={`preset-${preset.id}-btn`}
                onClick={() => applyPreset(preset.engines)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isPresetActive
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm"
                    : "bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800"
                }`}
              >
                {preset.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Select All / Deselect All Controls */}
      <div className="flex items-center justify-between text-xs pt-1 pb-1">
        <span className="text-slate-400 font-mono">
          {selectedEngines.length === 0
            ? `${allEngineIds.length} / ${allEngineIds.length} ${t("enginesSelectedCount")}`
            : `${selectedEngines.length} / ${allEngineIds.length} ${t("enginesSelectedCount")}`}
        </span>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => onSelectionChange([])}
            className="text-cyan-400 hover:text-cyan-300 text-xs font-medium"
          >
            {t("selectAll")}
          </button>
          <button
            type="button"
            onClick={() => onSelectionChange(["none"])}
            className="text-slate-400 hover:text-slate-300 text-xs font-medium"
          >
            {t("deselectAll")}
          </button>
        </div>
      </div>

      {/* Categorized Engine Checkboxes */}
      <div className="space-y-4">
        {categories.map((cat) => {
          const catIds = cat.engines.map((e) => e.id);
          const allCatSelected = catIds.every((id) => isEngineSelected(id));

          return (
            <div
              key={cat.id}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-3"
            >
              <div className="flex items-center justify-between border-b border-slate-850 pb-2">
                <span className="text-xs font-bold text-white flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full bg-${cat.color}-400`} />
                  {cat.title}
                </span>
                <button
                  type="button"
                  onClick={() => toggleCategory(cat.engines)}
                  className="text-[11px] text-slate-400 hover:text-slate-200"
                >
                  {allCatSelected ? t("deselectAll") : t("selectAll")}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {cat.engines.map((engine) => {
                  const checked = isEngineSelected(engine.id);

                  return (
                    <div
                      key={engine.id}
                      onClick={() => toggleEngine(engine.id)}
                      className={`flex items-start gap-2.5 p-2.5 rounded-lg border cursor-pointer transition-all ${
                        checked
                          ? "bg-slate-900/80 border-cyan-500/30 text-white"
                          : "bg-slate-950/40 border-slate-850 text-slate-500 hover:border-slate-750"
                      }`}
                    >
                      <div className="mt-0.5 text-cyan-400">
                        {checked ? <CheckSquare size={16} /> : <Square size={16} className="text-slate-600" />}
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-semibold text-slate-200 leading-tight">
                          {engine.name}
                        </div>
                        <div className="text-[10px] text-slate-400 leading-normal mt-0.5">
                          {engine.desc}
                        </div>
                      </div>
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
