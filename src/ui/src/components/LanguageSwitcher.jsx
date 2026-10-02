import React from "react";
import { useLanguage } from "../context/LanguageContext";
import { Globe } from "lucide-react";

export default function LanguageSwitcher() {
  const { lang, setLang } = useLanguage();

  return (
    <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-700/60 rounded-xl p-1 shadow-inner">
      <button
        type="button"
        id="lang-btn-en"
        onClick={() => setLang("en")}
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
          lang === "en"
            ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20 font-bold"
            : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
        }`}
        title="English"
      >
        <span>🇺🇸</span>
        <span>EN</span>
      </button>

      <button
        type="button"
        id="lang-btn-es"
        onClick={() => setLang("es")}
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
          lang === "es"
            ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20 font-bold"
            : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
        }`}
        title="Español"
      >
        <span>🇪🇸</span>
        <span>ES</span>
      </button>
    </div>
  );
}
