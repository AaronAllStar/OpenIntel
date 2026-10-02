import React from "react";
import { ShieldAlert, CheckCircle } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function EthicalNoticeModal({ onAccept }) {
  const { t } = useLanguage();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="glass-panel max-w-xl w-full p-8 border border-sky-500/30 shadow-2xl relative text-left">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <ShieldAlert size={28} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-wide">
              {t("ethicalTitle")}
            </h2>
            <p className="text-xs text-slate-400">{t("ethicalSubtitle")}</p>
          </div>
        </div>

        <div className="space-y-3 text-sm text-slate-300 my-6 bg-slate-900/50 p-4 rounded-xl border border-white/5">
          <p>{t("ethicalIntro")}</p>
          <ul className="list-disc pl-5 space-y-2 text-xs text-slate-400">
            <li>
              <strong className="text-slate-200">{t("ethicalLawful")}:</strong> {t("ethicalLawfulDesc")}
            </li>
            <li>
              <strong className="text-slate-200">{t("ethicalCompliance")}:</strong> {t("ethicalComplianceDesc")}
            </li>
            <li>
              <strong className="text-slate-200">{t("ethicalNoBypass")}:</strong> {t("ethicalNoBypassDesc")}
            </li>
            <li>
              <strong className="text-slate-200">{t("ethicalIsolation")}:</strong> {t("ethicalIsolationDesc")}
            </li>
          </ul>
        </div>

        <div className="flex justify-end gap-3">
          <button
            id="accept-ethical-terms-btn"
            onClick={onAccept}
            className="btn-primary w-full py-3 text-sm"
          >
            <CheckCircle size={18} />
            {t("ethicalAcceptBtn")}
          </button>
        </div>
      </div>
    </div>
  );
}
