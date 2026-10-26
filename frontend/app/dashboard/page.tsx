"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import type { PortalNav } from "@/lib/portal";

const TABS: PortalNav[] = [
  "home",
  "news",
  "ballot",
  "services",
  "ask",
];

function DashboardRedirectInner() {
  const router = useRouter();
  const params = useSearchParams();
  useEffect(() => {
    const tab = (params.get("tab") as PortalNav) || "home";
    const dest = TABS.includes(tab) ? `/${tab}` : "/home";
    const q = params.get("q");
    router.replace(q ? `${dest}?q=${encodeURIComponent(q)}` : dest);
  }, [router, params]);
  return (
    <div className="portal-shell">
      <p className="muted">Loading…</p>
    </div>
  );
}

export default function DashboardRedirectPage() {
  return (
    <Suspense
      fallback={
        <div className="portal-shell">
          <p className="muted">Loading…</p>
        </div>
      }
    >
      <DashboardRedirectInner />
    </Suspense>
  );
}
