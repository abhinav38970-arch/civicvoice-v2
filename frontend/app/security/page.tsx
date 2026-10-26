"use client";

import { StaticPolicyPage } from "@/components/StaticPolicyPage";
import { chrome } from "@/lib/chrome";
import { useI18n } from "@/lib/i18n";

/** Matches CivicVoice v1 /security. */
export default function SecurityPage() {
  const { lang } = useI18n();
  return (
    <StaticPolicyPage title={chrome(lang, "footerSecurity")}>
      <p>
        CivicVoice uses hashed passwords, signed session cookies, rate limiting,
        security headers, and parameterized SQL. See SECURITY notes in the
        repository for details.
      </p>
    </StaticPolicyPage>
  );
}
