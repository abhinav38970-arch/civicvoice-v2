"use client";

import { AuthLanding } from "@/components/AuthLanding";

/** Home = Congressional landing (language + login / create account). */
export default function HomePage() {
  return <AuthLanding initialTab="login" />;
}
