import React, { createContext, useContext, useState, useEffect } from "react";

export const translations = {
  en: {
    // Header & Brand
    brandName: "OPENINTEL",
    versionBadge: "v0.1.0",
    brandTagline: "Unified OSINT Intelligence Engine",
    navDashboard: "Dashboard",
    navNewInvestigation: "New Investigation",
    refreshTooltip: "Refresh investigations",
    localhostBadge: "Localhost 127.0.0.1",
    footerText: "OpenIntel Personal OSINT Platform · Built for authorized investigative operations",

    // Ethical Modal
    ethicalTitle: "OpenIntel — Operational & Ethical Protocol",
    ethicalSubtitle: "Personal Self-Hosted OSINT Architecture",
    ethicalIntro: "Before proceeding, you must acknowledge the operational guidelines:",
    ethicalLawful: "Lawful Purpose",
    ethicalLawfulDesc: "OpenIntel is designed strictly for authorized reconnaissance, security assessments, and legitimate research.",
    ethicalCompliance: "Compliance",
    ethicalComplianceDesc: "You are responsible for complying with all applicable regulations (CFAA, GDPR, local privacy laws) and third-party terms of service.",
    ethicalNoBypass: "No Unauthorized Bypass",
    ethicalNoBypassDesc: "OpenIntel queries public sources only. It will not bypass rate limits, captchas, or login protections.",
    ethicalIsolation: "Local Isolation",
    ethicalIsolationDesc: "By default, this instance binds strictly to localhost (127.0.0.1) for evidence privacy.",
    ethicalAcceptBtn: "I Understand & Acknowledge Terms",

    // Dashboard
    dashboardHeroBadge: "OSINT Operations Center · 27 Integrated Engines",
    dashboardHeroTitle: "Unified Intelligence Platform",
    dashboardHeroDesc: "Investigate individuals, international phone numbers, national IDs (70+ countries), X/Twitter, Instagram, WhatsApp, corporate emails, and infrastructure networks with real-time graph correlation.",
    dashboardPersonTag: "First & Last Names",
    dashboardPhoneTag: "International Phone (E.164)",
    dashboardIdTag: "National IDs (70+ Countries)",
    dashboardDigitalTag: "Usernames, Emails, Domains",
    dashboardOpenCockpit: "New Investigation Cockpit",
    dashboardActiveEngines: "27 Active Engines",
    dashboardSubtext: "Sherlock · Twikit · WhatsApp · Amass · ID Validation",
    dashboardStatsActive: "Active Investigations",
    dashboardStatsEntities: "Discovered Entities",
    dashboardStatsEvidence: "Corroborated Evidence",
    dashboardSearchPlaceholder: "Search by target, name, or keyword...",
    dashboardFilterAll: "All Kinds",
    dashboardRecentTitle: "Recent Investigations",
    dashboardEmptyTitle: "No investigations yet",
    dashboardEmptyDesc: "Launch your first OSINT investigation to discover entities, correlate connections, and construct a property graph.",
    dashboardStatusCompleted: "Completed",
    dashboardStatusWorking: "In Progress",
    dashboardStatusFailed: "Failed",
    dashboardStatusCancelled: "Cancelled",
    dashboardViewResults: "View Results",

    // New Investigation
    newTitle: "New Investigation Cockpit",
    newSubtitle: "Select search space, target, and customized engine facets",
    newStep1: "1. Select Operational Target",
    newStep2: "2. Investigation Parameters",
    newInvestNameLabel: "Investigation Name (Optional)",
    newInvestNamePlaceholder: "e.g., Domain Recon — Acme Security",
    newInvestTypeLabel: "Investigation Profile",
    newTypeQuick: "Quick (Fast scan, priority engines)",
    newTypeDeep: "Deep (Complete recursive correlation)",
    newTypePassive: "Passive (Non-intrusive public registries)",
    newAdvancedSettings: "Advanced Engine & Facet Settings",
    newTimeoutLabel: "Adapter Timeout (ms)",
    newMaxResultsLabel: "Max Results per Engine",
    newStoreRawLabel: "Store raw HTTP/stdout observation blobs (opt-in)",
    newAllowPrivateLabel: "Allow private/internal network ranges (SSRF bypass caution)",
    newCancelBtn: "Cancel",
    newStartBtn: "Launch Investigation",
    newSubmittingBtn: "Initializing Engines...",
    newErrorEmpty: "Please provide a valid target value or parameter to start the investigation.",

    // Search Cockpit Modes
    modePerson: "Person (Name & Surname)",
    modePhone: "Phone with Country Code",
    modeLocation: "Country / City",
    modeId: "National ID & Tax Number",
    modeDigital: "Username / Email / Network",

    // Mode 1: Person
    personFirstLabel: "First Name",
    personFirstPlaceholder: "e.g., Jane",
    personLastLabel: "Last Name(s)",
    personLastPlaceholder: "e.g., Doe",
    personDomainLabel: "Company Domain (Optional)",
    personDomainPlaceholder: "e.g., company.com",
    personHint: "Generates corporate email permutations (first.last@domain) and probes professional networks.",

    // Mode 2: Phone
    phoneCountryLabel: "Country & Dial Code",
    phoneInputLabel: "Phone Number",
    phoneInputPlaceholder: "e.g., 612345678",
    phoneHint: "Normalized to ITU E.164 (+1, +34, +52). Automatically probes WhatsApp, carrier info, and telecom registries.",

    // Mode 3: Location
    locCountryLabel: "Country",
    locCityLabel: "City or Municipal Region",
    locCityPlaceholder: "e.g., Austin, Madrid, Bogota",
    locHint: "Maps geographic context, local entities, and regional infrastructure footprints.",

    // Mode 4: ID
    idCountryLabel: "Issuing Country / Jurisdiction",
    idNumberLabel: "National ID / Tax Identifier",
    idNumberPlaceholder: "e.g., 12345678Z or 111.444.777-35",
    idHint: "Verified by Rust algorithms in <2µs: Luhn, Weighted Modulo 11, Verhoeff, and Modulo 23.",

    // Mode 5: Digital
    digitalKindUsername: "Social Username / Handle",
    digitalKindEmail: "Email Address",
    digitalKindDomain: "Domain (FQDN)",
    digitalKindUrl: "Web URL",
    digitalKindIp: "IP Address",
    digitalKindRepo: "Git Repository",
    digitalValuePlaceholder: "e.g., john_doe, user@org.com, or target.com",

    // Facet Selector
    presetsTitle: "Quick Investigation Presets:",
    presetAll: "All Engines (Recommended)",
    presetSocial: "Social Only",
    presetPhone: "Phone & WhatsApp",
    presetCorporate: "Corporate Recon",
    presetNetwork: "Infrastructure & Leaks",
    presetId: "ID Validation Only",
    enginesSelectedCount: "engines selected",
    selectAll: "Select All",
    deselectAll: "Deselect All",

    // Engine Categories
    catSocial: "Social Media & Public Profiles",
    catTelecom: "Phone & Messaging",
    catCorporate: "Corporate Identity & Business Emails",
    catNetwork: "Infrastructure, Domains & Code",
    catRegistry: "National Registries & Identifiers",

    // Live Progress
    progressTitle: "Reconnaissance in Progress",
    progressStepValidate: "Target Validated & Normalized",
    progressStepDispatch: "Engine Discovery Initiated",
    progressStepProfiles: "Profile & Identity Resolution",
    progressStepCorrelate: "Relationship & Link Correlation",
    progressStepComplete: "Investigation Ready for Review",
    progressLiveLogs: "Real-Time Engine Stream",
    progressHideLogs: "Hide Live Stream",
    progressShowLogs: "Show Live Stream",
    progressCancelBtn: "Cancel Scan",
    progressViewResultsBtn: "View Investigation Graph",

    // Investigation Detail
    detailBackBtn: "Back to Dashboard",
    detailExportMd: "Export Markdown",
    detailExportJson: "Export JSON",
    detailTargetLabel: "Target",
    detailCreatedLabel: "Created",
    detailTypeLabel: "Profile",
    detailTabGraph: "Interactive Graph",
    detailTabEntities: "Discovered Entities",
    detailTabEvidence: "Evidence & Provenance",
    detailTabAudit: "Audit Trail",
    detailTabRaw: "Engine Logs",
    detailEvidenceSource: "Source & Tool",
    detailEvidenceObservation: "Observation",
    detailEvidenceClass: "Legal Classification",
    detailEvidenceConfidence: "Confidence",
    detailNoEntities: "No entities discovered for this target.",
    detailNoEvidence: "No evidence records recorded yet.",
  },

  es: {
    // Header & Brand
    brandName: "OPENINTEL",
    versionBadge: "v0.1.0",
    brandTagline: "Motor Unificado de Inteligencia OSINT",
    navDashboard: "Panel Principal",
    navNewInvestigation: "Nueva Investigación",
    refreshTooltip: "Actualizar investigaciones",
    localhostBadge: "Localhost 127.0.0.1",
    footerText: "Plataforma Personal OSINT OpenIntel · Desarrollada para operaciones de investigación autorizadas",

    // Ethical Modal
    ethicalTitle: "OpenIntel — Protocolo Operativo y Ético",
    ethicalSubtitle: "Arquitectura Personal de OSINT Autohospedada",
    ethicalIntro: "Antes de continuar, debes reconocer los lineamientos operativos:",
    ethicalLawful: "Propósito Legítimo",
    ethicalLawfulDesc: "OpenIntel está diseñado estrictamente para reconocimiento autorizado, auditorías de seguridad e investigación legítima.",
    ethicalCompliance: "Cumplimiento Legal",
    ethicalComplianceDesc: "Eres responsable de cumplir con las normativas aplicables (RGPD, CFAA, leyes locales de privacidad) y los términos de servicio de terceros.",
    ethicalNoBypass: "Sin Evasión No Autorizada",
    ethicalNoBypassDesc: "OpenIntel consulta únicamente fuentes públicas. No evade límites de peticiones, captchas ni barreras de autenticación.",
    ethicalIsolation: "Aislamiento Local",
    ethicalIsolationDesc: "Por defecto, esta instancia se vincula estrictamente a localhost (127.0.0.1) para resguardar la privacidad de las evidencias.",
    ethicalAcceptBtn: "Entiendo y Acepto los Términos",

    // Dashboard
    dashboardHeroBadge: "Centro de Operaciones OSINT · 27 Motores Integrados",
    dashboardHeroTitle: "Plataforma Unificada de Inteligencia",
    dashboardHeroDesc: "Investiga personas, números de teléfono con prefijo internacional, documentos de identidad (70+ países), perfiles de X, Instagram, WhatsApp, correos corporativos y redes de infraestructura con correlación de grafos en tiempo real.",
    dashboardPersonTag: "Nombres & Apellidos",
    dashboardPhoneTag: "Teléfono Internacional (E.164)",
    dashboardIdTag: "Documentos de Identidad (70+ Países)",
    dashboardDigitalTag: "Usuarios, Correos, Dominios",
    dashboardOpenCockpit: "Nuevo Cockpit de Investigación",
    dashboardActiveEngines: "27 Motores Activos",
    dashboardSubtext: "Sherlock · Twikit · WhatsApp · Amass · Validación de Documentos",
    dashboardStatsActive: "Investigaciones Activas",
    dashboardStatsEntities: "Entidades Descubiertas",
    dashboardStatsEvidence: "Evidencias Corroboradas",
    dashboardSearchPlaceholder: "Buscar por objetivo, nombre o palabra clave...",
    dashboardFilterAll: "Todos los Tipos",
    dashboardRecentTitle: "Investigaciones Recientes",
    dashboardEmptyTitle: "No hay investigaciones todavía",
    dashboardEmptyDesc: "Inicia tu primera investigación OSINT para descubrir entidades, correlacionar conexiones y construir un grafo de propiedades.",
    dashboardStatusCompleted: "Completada",
    dashboardStatusWorking: "En Progreso",
    dashboardStatusFailed: "Fallida",
    dashboardStatusCancelled: "Cancelada",
    dashboardViewResults: "Ver Resultados",

    // New Investigation
    newTitle: "Cockpit de Nueva Investigación",
    newSubtitle: "Selecciona el espacio de búsqueda, el objetivo y las facetas de motores personalizadas",
    newStep1: "1. Seleccionar Objetivo Operativo",
    newStep2: "2. Parámetros de la Investigación",
    newInvestNameLabel: "Nombre de la Investigación (Opcional)",
    newInvestNamePlaceholder: "ej., Reconocimiento de Dominio — Seguridad Acme",
    newInvestTypeLabel: "Perfil de Investigación",
    newTypeQuick: "Rápido (Escaneo veloz, motores prioritarios)",
    newTypeDeep: "Profundo (Correlación recursiva completa)",
    newTypePassive: "Pasivo (Registros públicos no intrusivos)",
    newAdvancedSettings: "Ajustes Avanzados de Motores y Facetas",
    newTimeoutLabel: "Tiempo Límite por Adaptador (ms)",
    newMaxResultsLabel: "Resultados Máximos por Motor",
    newStoreRawLabel: "Guardar respuestas raw HTTP/stdout (opcional)",
    newAllowPrivateLabel: "Permitir rangos de red privada/interna (precaución SSRF)",
    newCancelBtn: "Cancelar",
    newStartBtn: "Lanzar Investigación",
    newSubmittingBtn: "Inicializando Motores...",
    newErrorEmpty: "Por favor define un valor o parámetro válido para iniciar la investigación.",

    // Search Cockpit Modes
    modePerson: "Persona (Nombre y Apellido)",
    modePhone: "Teléfono con País",
    modeLocation: "País / Ciudad",
    modeId: "Documento de Identidad y Fiscal",
    modeDigital: "Usuario / Correo / Red",

    // Mode 1: Person
    personFirstLabel: "Nombre",
    personFirstPlaceholder: "ej., Carlos",
    personLastLabel: "Apellido(s)",
    personLastPlaceholder: "ej., Gómez",
    personDomainLabel: "Dominio de la Empresa (Opcional)",
    personDomainPlaceholder: "ej., empresa.com",
    personHint: "Genera permutaciones de correo corporativo (nombre.apellido@empresa) y consulta redes profesionales.",

    // Mode 2: Phone
    phoneCountryLabel: "País y Prefijo Telefónico",
    phoneInputLabel: "Número Telefónico",
    phoneInputPlaceholder: "ej., 612345678",
    phoneHint: "Normalizado a ITU E.164 (+1, +34, +52). Consulta automáticamente WhatsApp, operador y registros de telecomunicaciones.",

    // Mode 3: Location
    locCountryLabel: "País",
    locCityLabel: "Ciudad o Región Municipal",
    locCityPlaceholder: "ej., Madrid, Bogotá, Ciudad de México",
    locHint: "Mapea contexto geográfico, entidades locales y huellas de infraestructura regional.",

    // Mode 4: ID
    idCountryLabel: "País / Jurisdicción Emisora",
    idNumberLabel: "Documento de Identidad / Número Fiscal",
    idNumberPlaceholder: "ej., 12345678Z o 111.444.777-35",
    idHint: "Verificado por algoritmos en Rust en <2µs: Luhn, Módulo 11 Ponderado, Verhoeff y Módulo 23.",

    // Mode 5: Digital
    digitalKindUsername: "Nombre de Usuario en Redes",
    digitalKindEmail: "Dirección de Correo",
    digitalKindDomain: "Dominio (FQDN)",
    digitalKindUrl: "Dirección URL",
    digitalKindIp: "Dirección IP",
    digitalKindRepo: "Repositorio Git",
    digitalValuePlaceholder: "ej., usuario123, contacto@empresa.com o objetivo.com",

    // Facet Selector
    presetsTitle: "Presets Rápidos de Investigación:",
    presetAll: "Todos los Motores (Recomendado)",
    presetSocial: "Solo Redes Sociales",
    presetPhone: "Teléfono y WhatsApp",
    presetCorporate: "Reconocimiento Corporativo",
    presetNetwork: "Infraestructura y Fugas",
    presetId: "Solo Validación de Documentos",
    enginesSelectedCount: "motores seleccionados",
    selectAll: "Seleccionar Todos",
    deselectAll: "Deseleccionar Todos",

    // Engine Categories
    catSocial: "Redes Sociales y Perfiles Públicos",
    catTelecom: "Teléfono y Mensajería",
    catCorporate: "Identidad Corporativa y Correos Empresariales",
    catNetwork: "Infraestructura, Dominios y Código",
    catRegistry: "Registros Nacionales e Identificadores",

    // Live Progress
    progressTitle: "Reconocimiento en Progreso",
    progressStepValidate: "Objetivo Validado y Normalizado",
    progressStepDispatch: "Descubrimiento de Motores Iniciado",
    progressStepProfiles: "Resolución de Perfiles e Identidades",
    progressStepCorrelate: "Correlación de Relaciones y Vínculos",
    progressStepComplete: "Investigación Lista para Revisión",
    progressLiveLogs: "Flujo en Tiempo Real de Motores",
    progressHideLogs: "Ocultar Flujo en Vivo",
    progressShowLogs: "Mostrar Flujo en Vivo",
    progressCancelBtn: "Cancelar Escaneo",
    progressViewResultsBtn: "Ver Grafo de la Investigación",

    // Investigation Detail
    detailBackBtn: "Volver al Panel",
    detailExportMd: "Exportar Markdown",
    detailExportJson: "Exportar JSON",
    detailTargetLabel: "Objetivo",
    detailCreatedLabel: "Creado",
    detailTypeLabel: "Perfil",
    detailTabGraph: "Grafo Interactivo",
    detailTabEntities: "Entidades Descubiertas",
    detailTabEvidence: "Evidencia y Procedencia",
    detailTabAudit: "Registro de Auditoría",
    detailTabRaw: "Logs de Motores",
    detailEvidenceSource: "Fuente y Herramienta",
    detailEvidenceObservation: "Observación",
    detailEvidenceClass: "Clasificación Legal",
    detailEvidenceConfidence: "Confianza",
    detailNoEntities: "No se descubrieron entidades para este objetivo.",
    detailNoEvidence: "No hay registros de evidencia todavía.",
  },
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    return localStorage.getItem("openintel_lang") || "en";
  });

  const setLang = (newLang) => {
    setLangState(newLang);
    localStorage.setItem("openintel_lang", newLang);
  };

  const t = (key) => {
    return translations[lang]?.[key] || translations.en?.[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
