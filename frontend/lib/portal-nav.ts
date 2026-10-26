import type { ChromeKey } from "@/lib/chrome";
import type { PortalNav } from "@/lib/portal";

export const PORTAL_NAV: {
  id: PortalNav;
  href: string;
  key: ChromeKey;
}[] = [
  { id: "home", href: "/home", key: "navHome" },
  { id: "news", href: "/news", key: "navNews" },
  { id: "ballot", href: "/ballot", key: "navBallot" },
  { id: "services", href: "/services", key: "navServices" },
  { id: "ask", href: "/ask", key: "navAsk" },
];

export function navFromPath(pathname: string): PortalNav {
  if (pathname.startsWith("/news")) return "news";
  if (pathname.startsWith("/ballot")) return "ballot";
  if (pathname.startsWith("/services")) return "services";
  if (pathname.startsWith("/ask")) return "ask";
  if (pathname.startsWith("/home")) return "home";
  if (pathname.startsWith("/dashboard")) {
    // legacy query tabs
    return "home";
  }
  return "home";
}
