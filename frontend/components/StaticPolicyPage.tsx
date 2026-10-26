"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { PublicFooter } from "@/components/PublicFooter";
import { chrome } from "@/lib/chrome";
import { useI18n } from "@/lib/i18n";
import { LANG_META, type LangCode } from "@/lib/langs";

/** Public policy pages — same structure as CivicVoice v1 page_static.html. */
export function StaticPolicyPage({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const { lang, setLang } = useI18n();

  return (
    <div className="public-shell">
      <header className="public-top">
        <Link className="public-brand" href="/">
          Civic<span>Voice</span>
        </Link>
        <form className="lang-mini" onSubmit={(e) => e.preventDefault()}>
          <label className="sr-only" htmlFor="policy-lang">
            {chrome(lang, "changeLanguage")}
          </label>
          <select
            id="policy-lang"
            value={lang}
            onChange={(e) => setLang(e.target.value as LangCode)}
          >
            {LANG_META.map((l) => (
              <option key={l.code} value={l.code}>
                {l.native}
              </option>
            ))}
          </select>
        </form>
      </header>
      <main id="main-content" className="public-main">
        <article className="page-content">
          <h1>{title}</h1>
          {children}
        </article>
      </main>
      <PublicFooter />
    </div>
  );
}
