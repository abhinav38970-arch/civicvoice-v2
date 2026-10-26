"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PortalShell } from "@/components/PortalShell";
import { api, type DocumentDetail } from "@/lib/api";
import { chrome } from "@/lib/chrome";
import { useI18n } from "@/lib/i18n";

export default function DocumentPage() {
  const params = useParams();
  const id = String(params.id || "");
  const { lang } = useI18n();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.document(id, lang);
        if (!cancelled) setDoc(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Error");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, lang]);

  const hasExternal =
    Boolean(doc?.url) &&
    !doc!.url.includes("/sample/") &&
    (doc!.url.startsWith("http://") || doc!.url.startsWith("https://"));

  return (
    <PortalShell active="news">
      <p>
        <Link href="/news" className="link-btn">
          ← {chrome(lang, "navNews")}
        </Link>
      </p>
      {loading && <p className="muted">{chrome(lang, "loading")}</p>}
      {error && <p className="form-err">{error}</p>}
      {doc && (
        <div className="result-card">
          <h1 style={{ fontSize: "1.35rem", marginTop: 0 }}>{doc.title}</h1>
          <p className="muted">{doc.source_name}</p>
          {hasExternal && (
            <a
              className="chip-btn"
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {chrome(lang, "officialPage")} ↗
            </a>
          )}
          <div style={{ marginTop: 16 }}>
            {doc.chunks.map((c) => (
              <div key={c.id} className="source-item">
                {c.page != null && (
                  <p className="muted">
                    {chrome(lang, "drawerPage")} {c.page}
                  </p>
                )}
                <p className="source-text">{c.text}</p>
                {c.original_text && lang !== "en" && (
                  <p className="en-sub">({c.original_text.slice(0, 280)})</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </PortalShell>
  );
}
