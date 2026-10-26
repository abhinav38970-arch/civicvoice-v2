"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { PublicFooter } from "@/components/PublicFooter";
import { api } from "@/lib/api";
import { chrome } from "@/lib/chrome";
import { nameFromEmail } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { LANG_META, type LangCode } from "@/lib/langs";
import type { PortalNav } from "@/lib/portal";
import { PORTAL_NAV, navFromPath } from "@/lib/portal-nav";

export function PortalShell({
  active,
  children,
  displayName,
}: {
  active?: PortalNav;
  children: ReactNode;
  /** Optional override; otherwise resolved from the signed-in session. */
  displayName?: string;
}) {
  const { lang, setLang } = useI18n();
  const router = useRouter();
  const pathname = usePathname() || "/home";
  const current = active ?? navFromPath(pathname);
  const [q, setQ] = useState("");
  const [sessionName, setSessionName] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .me()
      .then((r) => {
        if (cancelled) return;
        setSessionName(nameFromEmail(r.user.email));
      })
      .catch(() => {
        if (!cancelled) setSessionName(null);
      })
      .finally(() => {
        if (!cancelled) setAuthChecked(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const userName = displayName ?? sessionName;
  const signedIn = Boolean(userName);

  async function logout() {
    try {
      await api.logout();
    } catch {
      /* ignore */
    }
    router.push("/");
  }

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;
    router.push(`/ask?q=${encodeURIComponent(query)}`);
  }

  return (
    <div className="portal-shell">
      <a className="skip-link" href="#main-content">
        {chrome(lang, "skipLink")}
      </a>
      <header className="portal-bar">
        <div className="portal-bar-row">
          <Link className="portal-brand" href="/home">
            CivicVoice
          </Link>
          <form className="portal-search" role="search" onSubmit={onSearch}>
            <label className="sr-only" htmlFor="global-search">
              {chrome(lang, "searchPlaceholder")}
            </label>
            <span className="portal-search-field">
              <input
                id="global-search"
                name="q"
                type="search"
                placeholder={chrome(lang, "searchPlaceholder")}
                value={q}
                onChange={(e) => setQ(e.target.value)}
                autoComplete="off"
              />
            </span>
            <button type="submit" className="portal-search-go">
              {chrome(lang, "searchButton")}
            </button>
          </form>
          <div className="portal-tools">
            <label className="sr-only" htmlFor="portal-lang">
              {chrome(lang, "changeLanguage")}
            </label>
            <select
              id="portal-lang"
              name="lang"
              value={lang}
              onChange={(e) => {
                const next = e.target.value as LangCode;
                setLang(next);
                // Persist preferred language for signed-in users (partial update).
                void api
                  .updateProfile({ preferred_language: next })
                  .catch(() => {
                    /* guest or offline — local lang still applies */
                  });
              }}
            >
              {LANG_META.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.native}
                </option>
              ))}
            </select>
            {!authChecked ? null : !signedIn ? (
              <Link href="/" className="portal-signin">
                {chrome(lang, "loginTab")}
              </Link>
            ) : (
              <details className="profile-menu">
                <summary>
                  <span className="sr-only">{chrome(lang, "profileMenu")}</span>
                  <span className="portal-user-name">{userName}</span>
                </summary>
                <div className="profile-dropdown">
                  <div className="profile-city">
                    {chrome(lang, "city_fremont")}
                  </div>
                  <Link href="/onboarding">{chrome(lang, "editInterests")}</Link>
                  <button
                    type="button"
                    onClick={() => {
                      const blob = new Blob(
                        [JSON.stringify({ language: lang }, null, 2)],
                        { type: "application/json" },
                      );
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "civicvoice-export.json";
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    {chrome(lang, "exportData")}
                  </button>
                  <button type="button" onClick={() => void logout()}>
                    {chrome(lang, "signOut")}
                  </button>
                </div>
              </details>
            )}
          </div>
        </div>
        <nav className="portal-nav" aria-label="Primary">
          {PORTAL_NAV.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className={current === item.id ? "is-active" : undefined}
              aria-current={current === item.id ? "page" : undefined}
            >
              {chrome(lang, item.key)}
            </Link>
          ))}
        </nav>
      </header>
      <main id="main-content" className="portal-main">
        <div
          id="aria-live-status"
          className="live-region"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        />
        {children}
      </main>
      <PublicFooter />
    </div>
  );
}
