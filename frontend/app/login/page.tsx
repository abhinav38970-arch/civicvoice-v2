"use client";

import { AuthLanding } from "@/components/AuthLanding";

/** Same login UI as Congressional CivicVoice index.html auth portal. */
export default function LoginPage() {
  return <AuthLanding initialTab="login" />;
}
