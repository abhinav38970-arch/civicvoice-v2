"use client";

import { StaticPolicyPage } from "@/components/StaticPolicyPage";
import { chrome } from "@/lib/chrome";
import { useI18n } from "@/lib/i18n";

/** Matches CivicVoice v1 /privacy. */
export default function PrivacyPage() {
  const { lang } = useI18n();
  return (
    <StaticPolicyPage title={chrome(lang, "footerPrivacy")}>
      <p>
        We store your account email, name, language, optional profile interests,
        and saved neighborhood reports in a database on the server.
      </p>
      <p>
        You can export or delete your data from the profile API when signed in.
      </p>
    </StaticPolicyPage>
  );
}
