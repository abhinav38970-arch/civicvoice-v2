"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { PublicFooter } from "@/components/PublicFooter";
import { api } from "@/lib/api";
import { chrome } from "@/lib/chrome";
import { useI18n } from "@/lib/i18n";
import { LANG_META, type LangCode } from "@/lib/langs";
import { PROFESSIONS, TOPICS } from "@/lib/portal";

/**
 * Login GUI from github.com/abhinav38970-arch/CivicVoice templates/index.html
 * — welcome-split + auth-card (Sign in / Sign up).
 */
function AuthLandingInner({
  initialTab = "login",
}: {
  initialTab?: "login" | "register";
}) {
  const router = useRouter();
  const params = useSearchParams();
  const { lang, setLang } = useI18n();
  const tabFromUrl = params.get("tab");

  const [authTab, setAuthTab] = useState<"login" | "register">(
    tabFromUrl === "register" || initialTab === "register" ? "register" : "login",
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [regLang, setRegLang] = useState<LangCode>(lang);
  const [profession, setProfession] = useState("");
  const [topics, setTopics] = useState<string[]>([]);
  const [consent, setConsent] = useState(false);
  const [loginErr, setLoginErr] = useState<string | null>(null);
  const [regErr, setRegErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (tabFromUrl === "register") setAuthTab("register");
    if (tabFromUrl === "login") setAuthTab("login");
  }, [tabFromUrl]);

  useEffect(() => {
    setRegLang(lang);
  }, [lang]);

  function goDashboard() {
    window.localStorage.setItem("civicvoice_lang_gate_done", "1");
    router.push("/home");
  }

  async function onLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoginErr(null);
    setBusy(true);
    try {
      await api.login({ email: email.trim(), password });
      goDashboard();
    } catch {
      setLoginErr("Could not sign in. Check your email and password.");
    } finally {
      setBusy(false);
    }
  }

  async function onRegister(e: React.FormEvent) {
    e.preventDefault();
    setRegErr(null);
    if (!consent) {
      setRegErr("Please accept the privacy policy to continue.");
      return;
    }
    if (password.length < 8) {
      setRegErr("Password needs at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      setLang(regLang);
      await api.signup({
        email: email.trim(),
        password,
        city: "Fremont",
        preferred_language: regLang,
        interests: topics,
        profession: profession || name.trim() || undefined,
      });
      goDashboard();
    } catch (ex) {
      const msg = ex instanceof Error ? ex.message : "";
      if (/exist|taken|already/i.test(msg)) {
        setRegErr("That email already has an account — try signing in.");
      } else {
        setRegErr(msg || "Couldn't create the account — check the fields and try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  function toggleTopic(id: string) {
    setTopics((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  return (
    <div className="public-shell">
      <a className="skip-link" href="#main-content">
        {chrome(lang, "skipLink")}
      </a>
      <header className="public-top">
        <Link className="public-brand" href="/">
          Civic<span>Voice</span>
        </Link>
        <form className="lang-mini" onSubmit={(e) => e.preventDefault()}>
          <label className="sr-only" htmlFor="util-lang">
            {chrome(lang, "changeLanguage")}
          </label>
          <select
            id="util-lang"
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
        <div className="welcome-split" id="auth">
          <div className="welcome-about">
            <h1>CivicVoice</h1>
            <p className="welcome-tagline">
              {chrome(lang, "welcomeDefinition")}
            </p>
            <ul className="welcome-bullets">
              <li>{chrome(lang, "welcomeBulletBallot")}</li>
              <li>{chrome(lang, "welcomeBulletNews")}</li>
              <li>{chrome(lang, "welcomeBulletReport")}</li>
            </ul>
            <p className="welcome-stat">
              64.2% of {chrome(lang, "city_fremont")} residents speak a language
              other than English at home (U.S. Census).
            </p>
            <figure className="welcome-accent">
              <Image
                src="/img/capitol-login.jpg"
                alt="California State Capitol building"
                width={640}
                height={360}
                priority
                style={{ width: "100%", height: "auto" }}
              />
              <figcaption>{chrome(lang, "welcomePhotoCredit")}</figcaption>
            </figure>
            <p className="muted" style={{ marginTop: 16 }}>
              <button
                type="button"
                className="auth-tab"
                style={{ borderBottom: "none", padding: 0, cursor: "pointer" }}
                onClick={goDashboard}
              >
                {chrome(lang, "continueGuest")} →
              </button>
            </p>
          </div>

          <div className="auth-card">
            <div className="auth-tabs">
              <button
                type="button"
                className={`auth-tab${authTab === "login" ? " active" : ""}`}
                onClick={() => setAuthTab("login")}
              >
                {chrome(lang, "loginTab")}
              </button>
              <button
                type="button"
                className={`auth-tab${authTab === "register" ? " active" : ""}`}
                onClick={() => setAuthTab("register")}
              >
                {chrome(lang, "registerTab")}
              </button>
            </div>

            {authTab === "login" ? (
              <form className="auth-form" onSubmit={onLogin}>
                <label className="field">
                  <span>{chrome(lang, "emailL")}</span>
                  <input
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>
                <label className="field">
                  <span>{chrome(lang, "passwordL")}</span>
                  <input
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </label>
                {loginErr && (
                  <p className="form-err" role="alert">
                    {loginErr}
                  </p>
                )}
                <button type="submit" className="primary-btn" disabled={busy}>
                  {chrome(lang, "loginTab")}
                </button>
              </form>
            ) : (
              <form className="auth-form" onSubmit={onRegister}>
                <label className="field">
                  <span>{chrome(lang, "nameL")}</span>
                  <input
                    type="text"
                    required
                    autoComplete="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </label>
                <label className="field">
                  <span>{chrome(lang, "emailL")}</span>
                  <input
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>
                <label className="field">
                  <span>{chrome(lang, "passwordHint")}</span>
                  <input
                    type="password"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </label>
                <label className="field">
                  <span>{chrome(lang, "chooseLanguage")}</span>
                  <select
                    value={regLang}
                    onChange={(e) => setRegLang(e.target.value as LangCode)}
                  >
                    {LANG_META.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.native}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>{chrome(lang, "professionLabel")}</span>
                  <select
                    value={profession}
                    onChange={(e) => setProfession(e.target.value)}
                  >
                    <option value="">{chrome(lang, "profSelect")}</option>
                    {PROFESSIONS.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </label>
                <span className="field-label">
                  {chrome(lang, "topicsPreferred")}
                </span>
                <div className="topic-checks">
                  {TOPICS.map((t) => (
                    <label key={t.id}>
                      <input
                        type="checkbox"
                        checked={topics.includes(t.id)}
                        onChange={() => toggleTopic(t.id)}
                      />{" "}
                      <span>{t.label}</span>
                    </label>
                  ))}
                </div>
                <label className="consent">
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                    required
                  />
                  <span>
                    {chrome(lang, "consentLead")}{" "}
                    <a href="#">{chrome(lang, "footerPrivacy")}</a>{" "}
                    {chrome(lang, "andWord")}{" "}
                    <a href="#">{chrome(lang, "footerSecurity")}</a>{" "}
                    {chrome(lang, "policiesWord")}
                  </span>
                </label>
                {regErr && (
                  <p className="form-err" role="alert">
                    {regErr}
                  </p>
                )}
                <button type="submit" className="primary-btn" disabled={busy}>
                  {chrome(lang, "registerTab")}
                </button>
              </form>
            )}
            <p className="muted" style={{ marginTop: 14 }}>
              {chrome(lang, "authNoteText")}
            </p>
          </div>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}

export function AuthLanding({
  initialTab = "login",
}: {
  initialTab?: "login" | "register";
}) {
  return (
    <Suspense
      fallback={
        <div className="public-shell">
          <p className="muted">Loading…</p>
        </div>
      }
    >
      <AuthLandingInner initialTab={initialTab} />
    </Suspense>
  );
}
