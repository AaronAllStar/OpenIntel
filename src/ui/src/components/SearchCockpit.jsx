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
import { useLanguage } from "../context/LanguageContext";

export default function SearchCockpit({ onTargetChange, activeMode, setActiveMode }) {
  const { t, lang } = useLanguage();

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
        suggestedName: (lang === "es" ? `Persona: ${fullName}` : `Person: ${fullName}`) + (dom ? ` (${dom})` : ""),
      });
    }
  };

  const updatePhone = (country, num) => {
    setSelectedCountry(country);
    setRawPhoneNumber(num);
    const cleanNum = num.replace(/[\s\-\(\)]/g, "");
    if (cleanNum) {
      const e164 = `${country.dial}${cleanNum}`;
      onTargetChange({
        kind: "phone",
        value: e164,
        suggestedName: `${country.flag} ${e164} (${country.name})`,
      });
    }
  };

  const updateLocation = (countryName, cityName) => {
    setLocationCountry(countryName);
    setCity(cityName);
    const locString = cityName.trim() ? `${cityName.trim()}, ${countryName}` : countryName;
    if (locString.trim()) {
      onTargetChange({
        kind: "location",
        value: locString,
        suggestedName: (lang === "es" ? `Ubicación: ${locString}` : `Location: ${locString}`),
      });
    }
  };

  const updateNationalId = (country, idVal) => {
    setIdCountry(country);
    setIdNumber(idVal);
    const trimmed = idVal.trim();
    if (trimmed) {
      onTargetChange({
        kind: "national_id",
        value: trimmed,
        suggestedName: `${country.flag} ${country.code}:${trimmed} (${country.idName})`,
      });
    }
  };

  const updateDigital = (kind, val) => {
    setDigitalKind(kind);
    setDigitalValue(val);
    const trimmed = val.trim();
    if (trimmed) {
      onTargetChange({
        kind,
        value: trimmed,
        suggestedName: `${kind.toUpperCase()}: ${trimmed}`,
      });
    }
  };

  const searchModes = [
    { id: "person", label: t("modePerson"), icon: User, kind: "person_name" },
    { id: "phone", label: t("modePhone"), icon: Phone, kind: "phone" },
    { id: "location", label: t("modeLocation"), icon: MapPin, kind: "location" },
    { id: "id", label: t("modeId"), icon: Fingerprint, kind: "national_id" },
    { id: "digital", label: t("modeDigital"), icon: Globe, kind: "username" },
  ];

  return (
    <div className="space-y-6 text-left">
      {/* Search Mode Navigation Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        {searchModes.map((m) => {
          const Icon = m.icon;
          const isActive = activeMode === m.id;
          return (
            <button
              key={m.id}
              type="button"
              id={`search-mode-${m.id}-btn`}
              onClick={() => {
                setActiveMode(m.id);
                if (m.id === "person") updatePerson(firstName, lastName, personDomain);
                if (m.id === "phone") updatePhone(selectedCountry, rawPhoneNumber);
                if (m.id === "location") updateLocation(locationCountry, city);
                if (m.id === "id") updateNationalId(idCountry, idNumber);
                if (m.id === "digital") updateDigital(digitalKind, digitalValue);
              }}
              className={`flex items-center gap-2 p-3 rounded-xl border text-xs font-semibold transition-all text-left ${
                isActive
                  ? "bg-cyan-500/15 border-cyan-500/50 text-cyan-300 shadow-md shadow-cyan-500/10"
                  : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <Icon size={16} className={isActive ? "text-cyan-400" : "text-slate-400"} />
              <span className="truncate">{m.label}</span>
            </button>
          );
        })}
      </div>

      {/* Mode 1: Person Name & Corporate Domain */}
      {activeMode === "person" && (
        <div className="glass-panel p-5 border border-slate-800 space-y-4 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("personFirstLabel")} <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                placeholder={t("personFirstPlaceholder")}
                value={firstName}
                onChange={(e) => updatePerson(e.target.value, lastName, personDomain)}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("personLastLabel")} <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                placeholder={t("personLastPlaceholder")}
                value={lastName}
                onChange={(e) => updatePerson(firstName, e.target.value, personDomain)}
                className="input-field"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              {t("personDomainLabel")}
            </label>
            <div className="relative">
              <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder={t("personDomainPlaceholder")}
                value={personDomain}
                onChange={(e) => updatePerson(firstName, lastName, e.target.value)}
                className="input-field pl-9"
              />
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5">
              💡 {t("personHint")}
            </p>
          </div>
        </div>
      )}

      {/* Mode 2: Phone with Country Code */}
      {activeMode === "phone" && (
        <div className="glass-panel p-5 border border-slate-800 space-y-4 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-1">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("phoneCountryLabel")}
              </label>
              <div className="relative">
                <select
                  value={selectedCountry.code}
                  onChange={(e) => {
                    const c = COUNTRIES.find((x) => x.code === e.target.value) || COUNTRIES[0];
                    updatePhone(c, rawPhoneNumber);
                  }}
                  className="input-field pr-8 appearance-none bg-slate-900 cursor-pointer"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.flag} {c.name} ({c.dial})
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("phoneInputLabel")} <span className="text-rose-400">*</span>
              </label>
              <div className="flex rounded-xl bg-slate-950/80 border border-slate-700/80 overflow-hidden focus-within:border-cyan-400">
                <span className="flex items-center px-3.5 bg-slate-900 text-xs font-mono font-bold text-cyan-400 border-r border-slate-800">
                  {selectedCountry.dial}
                </span>
                <input
                  type="text"
                  required
                  placeholder={t("phoneInputPlaceholder")}
                  value={rawPhoneNumber}
                  onChange={(e) => updatePhone(selectedCountry, e.target.value)}
                  className="w-full bg-transparent px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none font-mono"
                />
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-400">
            💡 {t("phoneHint")}
          </p>
        </div>
      )}

      {/* Mode 3: Location */}
      {activeMode === "location" && (
        <div className="glass-panel p-5 border border-slate-800 space-y-4 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("locCountryLabel")}
              </label>
              <div className="relative">
                <select
                  value={locationCountry}
                  onChange={(e) => updateLocation(e.target.value, city)}
                  className="input-field pr-8 appearance-none bg-slate-900 cursor-pointer"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.name}>
                      {c.flag} {c.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("locCityLabel")}
              </label>
              <input
                type="text"
                placeholder={t("locCityPlaceholder")}
                value={city}
                onChange={(e) => updateLocation(locationCountry, e.target.value)}
                className="input-field"
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-400">
            💡 {t("locHint")}
          </p>
        </div>
      )}

      {/* Mode 4: National ID & Tax Number */}
      {activeMode === "id" && (
        <div className="glass-panel p-5 border border-slate-800 space-y-4 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-1">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("idCountryLabel")}
              </label>
              <div className="relative">
                <select
                  value={idCountry.code}
                  onChange={(e) => {
                    const c = COUNTRIES.find((x) => x.code === e.target.value) || COUNTRIES[0];
                    updateNationalId(c, idNumber);
                  }}
                  className="input-field pr-8 appearance-none bg-slate-900 cursor-pointer"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.flag} {c.name} ({c.idName})
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {t("idNumberLabel")} <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                placeholder={idCountry.idExample || t("idNumberPlaceholder")}
                value={idNumber}
                onChange={(e) => updateNationalId(idCountry, e.target.value)}
                className="input-field font-mono uppercase"
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-400">
            ⚡ {t("idHint")}
          </p>
        </div>
      )}

      {/* Mode 5: Digital Asset / Username / Email / Domain */}
      {activeMode === "digital" && (
        <div className="glass-panel p-5 border border-slate-800 space-y-4 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-1">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {lang === "es" ? "Tipo de Activo Digital" : "Digital Asset Type"}
              </label>
              <div className="relative">
                <select
                  value={digitalKind}
                  onChange={(e) => updateDigital(e.target.value, digitalValue)}
                  className="input-field pr-8 appearance-none bg-slate-900 cursor-pointer"
                >
                  <option value="username">{t("digitalKindUsername")}</option>
                  <option value="email">{t("digitalKindEmail")}</option>
                  <option value="domain">{t("digitalKindDomain")}</option>
                  <option value="url">{t("digitalKindUrl")}</option>
                  <option value="ip">{t("digitalKindIp")}</option>
                  <option value="repository">{t("digitalKindRepo")}</option>
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {lang === "es" ? "Valor del Objetivo" : "Target Value"} <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                placeholder={t("digitalValuePlaceholder")}
                value={digitalValue}
                onChange={(e) => updateDigital(digitalKind, e.target.value)}
                className="input-field font-mono"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
