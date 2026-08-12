"use client";

import { Languages } from "lucide-react";
import { useI18n } from "@/lib/i18n";

/**
 * Small English/Bangla switch. Shows the language you'd switch TO,
 * so a Bangla-only reader sees "বাংলা" to tap.
 */
export function LanguageToggle({ className = "" }: { className?: string }) {
  const { lang, toggle } = useI18n();

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Switch language"
      className={`inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors ${className}`}
    >
      <Languages className="h-4 w-4" />
      <span>{lang === "en" ? "বাংলা" : "English"}</span>
    </button>
  );
}
