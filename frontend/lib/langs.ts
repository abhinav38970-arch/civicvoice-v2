export const LANG_CODES = [
  "en",
  "es",
  "hi",
  "pa",
  "zh",
  "fa",
  "vi",
  "tl",
  "ko",
  "ar",
  "pt",
  "ur",
] as const;

export type LangCode = (typeof LANG_CODES)[number];

export type LangMeta = {
  code: LangCode;
  native: string;
  name: string;
  verified: boolean;
};

/** Same language set / labels as Congressional CivicVoice. */
export const LANG_META: LangMeta[] = [
  { code: "en", native: "English", name: "English", verified: true },
  { code: "es", native: "Español", name: "Spanish", verified: true },
  { code: "hi", native: "हिन्दी", name: "Hindi", verified: true },
  { code: "pa", native: "ਪੰਜਾਬੀ", name: "Punjabi", verified: true },
  { code: "zh", native: "中文", name: "Chinese", verified: true },
  { code: "fa", native: "فارسی", name: "Farsi", verified: true },
  { code: "vi", native: "Tiếng Việt", name: "Vietnamese", verified: true },
  { code: "tl", native: "Tagalog", name: "Tagalog", verified: true },
  { code: "ko", native: "한국어", name: "Korean", verified: true },
  { code: "ar", native: "العربية", name: "Arabic", verified: true },
  { code: "pt", native: "Português", name: "Portuguese", verified: true },
  { code: "ur", native: "اردو", name: "Urdu", verified: true },
];

export const SPEECH_LOCALES: Record<string, string> = {
  en: "en-US",
  es: "es-US",
  hi: "hi-IN",
  pa: "pa-IN",
  zh: "zh-CN",
  fa: "fa-IR",
  vi: "vi-VN",
  tl: "fil-PH",
  ko: "ko-KR",
  ar: "ar-SA",
  pt: "pt-BR",
  ur: "ur-PK",
};

export function isRtl(lang: string): boolean {
  return lang === "ar" || lang === "fa" || lang === "ur";
}

export function isLangCode(value: string): value is LangCode {
  return (LANG_CODES as readonly string[]).includes(value);
}
