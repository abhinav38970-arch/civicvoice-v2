"use client";

import { chrome } from "@/lib/chrome";
import { useI18n } from "@/lib/i18n";

export function PublicFooter() {
  const { lang } = useI18n();
  return (
    <footer className="public-footer">
      <a href="#">{chrome(lang, "footerPrivacy")}</a>
      <a href="#">{chrome(lang, "footerSecurity")}</a>
      <a
        href="https://registertovote.ca.gov/"
        target="_blank"
        rel="noopener noreferrer"
      >
        {chrome(lang, "ctaRegister")}
      </a>
      <span className="external-tag">{chrome(lang, "externalGov")}</span>
      <span> · {chrome(lang, "notGovSite")}</span>
    </footer>
  );
}
