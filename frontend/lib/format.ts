/** Short date for feed/notice rows, e.g. "Oct 26, 2026". */
export function formatFeedDate(
  iso: string | null | undefined,
  locale = "en",
): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  try {
    return d.toLocaleDateString(locale, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return d.toLocaleDateString();
  }
}

/** Display name from email local-part, e.g. "ada.lovelace@x.com" → "Ada". */
export function nameFromEmail(email: string): string {
  const local = email.split("@")[0] || email;
  const token = local.split(/[._+-]/)[0] || local;
  if (!token) return email;
  return token.charAt(0).toUpperCase() + token.slice(1);
}
