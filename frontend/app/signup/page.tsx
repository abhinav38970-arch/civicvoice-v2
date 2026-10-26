"use client";

import { AuthLanding } from "@/components/AuthLanding";

/** Create-account tab of the Congressional auth portal. */
export default function SignupPage() {
  return <AuthLanding initialTab="register" />;
}
