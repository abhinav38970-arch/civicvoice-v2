// Prefer same-origin /backend proxy (see next.config.ts) so cookies work locally.
const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "/backend";

export type User = {
  id: string;
  email: string;
  preferred_language: string;
  city: string;
  interests: string[];
  profession: string | null;
  created_at: string | null;
};

export type FeedItem = {
  id: string;
  title: string;
  title_original?: string | null;
  url: string;
  published_at: string | null;
  type: string;
  city: string;
  language: string;
  source_name: string;
  source_name_original?: string | null;
  last_updated: string | null;
  score?: number;
  requested_language?: string;
  snippet?: string | null;
  snippet_original?: string | null;
  translation_available?: boolean;
  snippet_translated?: boolean;
};

export type Citation = {
  index: number;
  chunk_id: string;
  document_id: string;
  title: string;
  url: string;
  page: number | null;
  text: string;
  doc_type: string;
  source_name: string;
};

export type DocumentDetail = {
  id: string;
  title: string;
  url: string;
  published_at: string | null;
  type: string;
  city: string;
  language: string;
  requested_language?: string;
  source_name: string;
  last_updated: string | null;
  chunks: {
    id: string;
    text: string;
    original_text?: string | null;
    page: number | null;
    translation_available?: boolean;
  }[];
};

export type AskResponse = {
  question: string;
  language: string;
  city: string;
  summary: string | null;
  summary_available: boolean;
  source: string;
  reject_reason: string | null;
  message: string | null;
  citations: Citation[];
  cached: boolean;
};

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `Request failed (${res.status})`;
    throw new Error(detail);
  }

  return data as T;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  me: () => request<{ user: User }>("/api/auth/me"),

  signup: (body: {
    email: string;
    password: string;
    city: string;
    preferred_language: string;
    interests: string[];
    profession?: string;
  }) =>
    request<{ user: User }>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  login: (body: { email: string; password: string }) =>
    request<{ user: User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  logout: () =>
    request<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),

  updateProfile: (body: {
    interests?: string[];
    profession?: string;
    city?: string;
    preferred_language?: string;
  }) =>
    request<{ ok: boolean; user: User }>("/api/auth/profile", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  feed: (limit = 20, language?: string) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (language) q.set("language", language);
    return request<{ city: string; language: string; items: FeedItem[] }>(
      `/api/feed?${q}`,
    );
  },

  notices: (limit = 20, language = "en", city = "Fremont") => {
    const q = new URLSearchParams({
      limit: String(limit),
      language,
      city,
    });
    return request<{ city: string; language: string; section: string; items: FeedItem[] }>(
      `/api/notices?${q}`,
    );
  },

  ballots: (limit = 20, language = "en", city = "Fremont") => {
    const q = new URLSearchParams({
      limit: String(limit),
      language,
      city,
    });
    return request<{ city: string; language: string; section: string; items: FeedItem[] }>(
      `/api/ballots?${q}`,
    );
  },

  ask: (question: string, language: string, city = "Fremont") =>
    request<AskResponse>("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question, language, city }),
    }),

  document: (id: string, language = "en") =>
    request<DocumentDetail>(
      `/api/documents/${id}?language=${encodeURIComponent(language)}`,
    ),
};
