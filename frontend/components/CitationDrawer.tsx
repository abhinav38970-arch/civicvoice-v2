"use client";

import { chrome } from "@/lib/chrome";
import { useI18n } from "@/lib/i18n";

export type DrawerPayload = {
  file: string;
  page: string | number | null;
  section?: string;
  text: string;
  originalText?: string | null;
};

export function CitationDrawer({
  open,
  payload,
  onClose,
}: {
  open: boolean;
  payload: DrawerPayload | null;
  onClose: () => void;
}) {
  const { lang } = useI18n();
  if (!open || !payload) return null;

  const showOrig =
    lang !== "en" &&
    payload.originalText &&
    payload.originalText.trim() &&
    payload.originalText !== payload.text;

  return (
    <>
      <div className="scrim" onClick={onClose} aria-hidden />
      <aside className="drawer" role="dialog" aria-label={chrome(lang, "drawerTitle")}>
        <div className="drawer-head">
          <h2>{chrome(lang, "drawerTitle")}</h2>
          <button type="button" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <p className="drawer-why">{chrome(lang, "drawerWhy")}</p>
        <dl className="drawer-meta">
          <div>
            <dt>{chrome(lang, "drawerFile")}</dt>
            <dd className="mono">{payload.file || "—"}</dd>
          </div>
          <div>
            <dt>{chrome(lang, "drawerPage")}</dt>
            <dd>{payload.page ?? "—"}</dd>
          </div>
          <div>
            <dt>{chrome(lang, "drawerSection")}</dt>
            <dd>{payload.section || "—"}</dd>
          </div>
        </dl>
        <p className="drawer-text-label">{chrome(lang, "drawerSourceText")}</p>
        <p className="drawer-text">{payload.text}</p>
        {!showOrig && lang !== "en" && !payload.originalText && (
          <p className="trans-note">{chrome(lang, "drawerNoTranslation")}</p>
        )}
        {showOrig && (
          <>
            <p className="drawer-text-label">{chrome(lang, "drawerOriginalText")}</p>
            <p className="drawer-text">{payload.originalText}</p>
          </>
        )}
      </aside>
    </>
  );
}
