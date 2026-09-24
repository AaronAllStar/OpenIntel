import React, { useState } from "react";
import { 
  User, 
  Phone, 
  MapPin, 
  Fingerprint, 
  Globe, 
  AtSign, 
  GitBranch, 
  Building2,
  ChevronDown
} from "lucide-react";
import { COUNTRIES } from "../data/countries";

export const SEARCH_MODES = [
  { id: "person", label: "Persona (Nombre y Apellido)", icon: User, kind: "person_name" },
  { id: "phone", label: "Teléfono con País", icon: Phone, kind: "phone" },
  { id: "location", label: "País / Ciudad", icon: MapPin, kind: "location" },
  { id: "id", label: "Documento de Identidad", icon: Fingerprint, kind: "national_id" },
  { id: "digital", label: "Usuario / Email / Red", icon: Globe, kind: "username" },
];

export default function SearchCockpit({ onTargetChange, activeMode, setActiveMode }) {
  // Mode 1: Person
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [personDomain, setPersonDomain] = useState("");

  // Mode 2: Phone
  const [selectedCountry, setSelectedCountry] = useState(COUNTRIES[0]);
  const [rawPhoneNumber, setRawPhoneNumber] = useState("");

  // Mode 3: Location
  const [locationCountry, setLocationCountry] = useState(COUNTRIES[1].name);
  const [city, setCity] = useState("");

  // Mode 4: ID
  const [idCountry, setIdCountry] = useState(COUNTRIES[1]);
  const [idNumber, setIdNumber] = useState("");

  // Mode 5: Digital
  const [digitalKind, setDigitalKind] = useState("username");
  const [digitalValue, setDigitalValue] = useState("");

  // Trigger parent state update whenever inputs change
  const updatePerson = (first, last, dom) => {
    setFirstName(first);
    setLastName(last);
    setPersonDomain(dom);
    const fullName = `${first.trim()} ${last.trim()}`.trim();
    if (fullName) {
      const fullTarget = dom.trim() ? `${fullName} @ ${dom.trim()}` : fullName;
      onTargetChange({
        kind: "person_name",
        value: fullTarget,
        suggestedName: `Persona: ${fullName}` + (dom ? ` (${dom})` : ""),
      });
    }
  };

  const updatePhone = (country, number) => {
    setSelectedCountry(country);
    setRawPhoneNumber(number);
    const cleanDigits = number.replace(/[^0-9]/g, "");
    if (cleanDigits) {
      const e164 = `${country.dial}${cleanDigits}`;
      onTargetChange({
        kind: "phone",
        value: e164,
        suggestedName: `Teléfono: ${e164} (${country.name})`,
      });
    }
  };

  const updateLocation = (countryName, cityName) => {
    setLocationCountry(countryName);
    setCity(cityName);
    const val = cityName.trim() ? `${cityName.trim()}, ${countryName}` : countryName;
    onTargetChange({
      kind: "location",
      value: val,
      suggestedName: `Localización: ${val}`,
    });
  };

  const updateId = (country, idVal) => {
    setIdCountry(country);
    setIdNumber(idVal);
    if (idVal.trim()) {
      onTargetChange({
        kind: "national_id",
        value: idVal.trim(),
        suggestedName: `${country.idName}: ${idVal.trim()} (${country.name})`,
      });
    }
  };

  const updateDigital = (kind, val) => {
    setDigitalKind(kind);
    setDigitalValue(val);
    if (val.trim()) {
      onTargetChange({
        kind: kind,
        value: val.trim(),
        suggestedName: `${kind.toUpperCase()}: ${val.trim()}`,
      });
    }
  };

  return (
    <div className="space-y-4">
      {/* Mode Navigation Tabs */}
      <div className="flex flex-wrap gap-2 p-1.5 rounded-xl bg-slate-900/80 border border-slate-800">
        {SEARCH_MODES.map((mode) => {
          const Icon = mode.icon;
          const isActive = activeMode === mode.id;
          return (
            <button
              key={mode.id}
              type="button"
              onClick={() => setActiveMode(mode.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-cyan-400" : "text-slate-500"}`} />
              <span>{mode.label}</span>
            </button>
          );
        })}
      </div>

      {/* Mode 1: Person (Nombre y Apellido) */}
      {activeMode === "person" && (
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3 animate-fadeIn">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Nombre</label>
              <input
                type="text"
                placeholder="ej. Elena, Carlos"
                value={firstName}
                onChange={(e) => updatePerson(e.target.value, lastName, personDomain)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-700/80 text-white text-sm focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Apellido(s)</label>
              <input
                type="text"
                placeholder="ej. Navarro, Gómez"
                value={lastName}
                onChange={(e) => updatePerson(firstName, e.target.value, personDomain)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-700/80 text-white text-sm focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Empresa u Organización (Opcional para derivación de correo corporativo)
            </label>
            <input
              type="text"
              placeholder="ej. acme.com o Banco Santander"
              value={personDomain}
              onChange={(e) => updatePerson(firstName, lastName, e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg bg-slate-950/70 border border-slate-800 text-slate-200 text-xs focus:border-cyan-400 focus:outline-none"
            />
          </div>
        </div>
      )}

      {/* Mode 2: Phone (Teléfono con selector de país) */}
      {activeMode === "phone" && (
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3 animate-fadeIn">
          <label className="block text-xs font-semibold text-slate-300">Número de Teléfono Internacional</label>
          <div className="flex gap-2">
            {/* Country Selector */}
            <div className="relative w-48 shrink-0">
              <select
                value={selectedCountry.code}
                onChange={(e) => {
                  const found = COUNTRIES.find((c) => c.code === e.target.value) || COUNTRIES[0];
                  updatePhone(found, rawPhoneNumber);
                }}
                className="w-full appearance-none px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs font-medium focus:border-cyan-400 focus:outline-none cursor-pointer pr-8"
              >
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code} className="bg-slate-900 text-white">
                    {c.flag} {c.name} ({c.dial})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Phone Input */}
            <div className="relative flex-1">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-cyan-400 text-xs font-mono font-bold">
                {selectedCountry.dial}
              </div>
              <input
                type="tel"
                placeholder="612 345 678 o 202 555 0143"
                value={rawPhoneNumber}
                onChange={(e) => updatePhone(selectedCountry, e.target.value)}
                className="w-full pl-12 pr-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-700/80 text-white text-sm focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400 font-mono"
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-400">
            Formato normalizado automáticamente a E.164 para WhatsApp, Telegram y PhoneInfoga.
          </p>
        </div>
      )}

      {/* Mode 3: Location (País / Ciudad) */}
      {activeMode === "location" && (
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3 animate-fadeIn">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">País</label>
              <select
                value={locationCountry}
                onChange={(e) => updateLocation(e.target.value, city)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs font-medium focus:border-cyan-400 focus:outline-none"
              >
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.name} className="bg-slate-900 text-white">
                    {c.flag} {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Ciudad / Región</label>
              <input
                type="text"
                placeholder="ej. Madrid, Barcelona, Bogotá, CDMX"
                value={city}
                onChange={(e) => updateLocation(locationCountry, e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-700/80 text-white text-sm focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400"
              />
            </div>
          </div>
        </div>
      )}

      {/* Mode 4: ID (Documento de Identidad por País) */}
      {activeMode === "id" && (
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3 animate-fadeIn">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">País Emisor</label>
              <select
                value={idCountry.code}
                onChange={(e) => {
                  const found = COUNTRIES.find((c) => c.code === e.target.value) || COUNTRIES[0];
                  updateId(found, idNumber);
                }}
                className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs font-medium focus:border-cyan-400 focus:outline-none"
              >
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code} className="bg-slate-900 text-white">
                    {c.flag} {c.name} ({c.idName})
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Número ({idCountry.idName})
              </label>
              <input
                type="text"
                placeholder={`ej. ${idCountry.idExample}`}
                value={idNumber}
                onChange={(e) => updateId(idCountry, e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-700/80 text-white text-sm focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400 font-mono"
              />
            </div>
          </div>
          <p className="text-[11px] text-cyan-400/90 font-mono">
            Algoritmo de comprobación: Verificación de dígito de control por registro oficial ({idCountry.name}).
          </p>
        </div>
      )}

      {/* Mode 5: Digital (Usuario / Email / Red / Repositorio) */}
      {activeMode === "digital" && (
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3 animate-fadeIn">
          <div className="flex flex-wrap gap-2 mb-2">
            {[
              { id: "username", label: "Usuario" },
              { id: "email", label: "Email" },
              { id: "domain", label: "Dominio" },
              { id: "repository", label: "Repositorio Git" },
              { id: "organization", label: "Organización" },
              { id: "ip", label: "Dirección IP" },
              { id: "url", label: "URL Web" },
            ].map((dk) => (
              <button
                key={dk.id}
                type="button"
                onClick={() => updateDigital(dk.id, digitalValue)}
                className={`px-2.5 py-1 rounded text-xs transition-colors ${
                  digitalKind === dk.id
                    ? "bg-cyan-500/30 text-cyan-300 border border-cyan-400/50"
                    : "bg-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                {dk.label}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Valor del Objetivo ({digitalKind})
            </label>
            <input
              type="text"
              placeholder={
                digitalKind === "username" ? "ej. shadow_broker, janesmith" :
                digitalKind === "email" ? "ej. contact@target.com" :
                digitalKind === "domain" ? "ej. company.com" :
                digitalKind === "repository" ? "ej. torvalds/linux o https://github.com/..." :
                "ej. objetivo a investigar"
              }
              value={digitalValue}
              onChange={(e) => updateDigital(digitalKind, e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-700/80 text-white text-sm focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400 font-mono"
            />
          </div>
        </div>
      )}
    </div>
  );
}
