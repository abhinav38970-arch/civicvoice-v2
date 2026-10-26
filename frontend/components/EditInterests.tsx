"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { PortalShell } from "@/components/PortalShell";
import { api, type User } from "@/lib/api";
import { chrome } from "@/lib/chrome";
import { nameFromEmail } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PROFESSIONS, TOPICS } from "@/lib/portal";

const CITIES = [
  { id: "Fremont", key: "city_fremont" as const },
  { id: "Newark", key: "city_newark" as const },
  { id: "Union City", key: "city_union_city" as const },
];

export function EditInterests() {
  const { lang, setLang } = useI18n();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [topics, setTopics] = useState<string[]>([]);
  const [profession, setProfession] = useState("");
  const [city, setCity] = useState("Fremont");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .me()
      .then((r) => {
        if (cancelled) return;
        setUser(r.user);
        setTopics(r.user.interests || []);
        setProfession(r.user.profession || "");
        setCity(r.user.city || "Fremont");
        if (r.user.preferred_language) {
          setLang(r.user.preferred_language as typeof lang);
        }
      })
      .catch(() => {
        if (!cancelled) router.replace("/");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [router, setLang]);

  function toggleTopic(id: string) {
    setTopics((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id],
    );
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    if (!consent) {
      setErr(chrome(lang, "consentProfile"));
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await api.updateProfile({
        interests: topics,
        profession: profession || "",
        city,
        preferred_language: lang,
      });
      router.push("/home");
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Could not save — try again.");
    } finally {
      setBusy(false);
    }
  }

  const displayName = user ? nameFromEmail(user.email) : undefined;

  return (
    <PortalShell active="home" displayName={displayName}>
      <div className="onboarding-steps">
        <h1>{chrome(lang, "onboardTitle")}</h1>
        <p className="muted">{chrome(lang, "onboardLead")}</p>

        {loading ? (
          <p className="muted">{chrome(lang, "loading")}</p>
        ) : (
          <form onSubmit={(e) => void onSave(e)}>
            <fieldset>
              <legend>
                <strong>{chrome(lang, "topicsLegend")}</strong>
              </legend>
              <div className="chip-select" id="topicChips">
                {TOPICS.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    data-value={t.id}
                    className={topics.includes(t.id) ? "selected" : undefined}
                    onClick={() => toggleTopic(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend>
                <strong>{chrome(lang, "situationLegend")}</strong>
              </legend>
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
              <label className="field">
                <span>{chrome(lang, "cityOptional")}</span>
                <select
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                >
                  {CITIES.map((c) => (
                    <option key={c.id} value={c.id}>
                      {chrome(lang, c.key)}
                    </option>
                  ))}
                </select>
              </label>
            </fieldset>

            <fieldset>
              <legend>
                <strong>{chrome(lang, "privacyLegend")}</strong>
              </legend>
              <label className="consent">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  required
                />
                <span>{chrome(lang, "consentProfile")}</span>
              </label>
            </fieldset>

            {err && (
              <p className="form-err" role="alert">
                {err}
              </p>
            )}

            <button type="submit" className="primary-btn" disabled={busy}>
              {chrome(lang, "saveHome")}
            </button>
            <p>
              <Link href="/home">{chrome(lang, "backHome")}</Link>
            </p>
          </form>
        )}
      </div>
    </PortalShell>
  );
}
