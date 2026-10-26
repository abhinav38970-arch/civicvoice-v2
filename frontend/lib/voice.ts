import { SPEECH_LOCALES } from "@/lib/langs";

export function speakText(text: string, lang: string): void {
  if (typeof window === "undefined" || !window.speechSynthesis || !text.trim()) {
    return;
  }
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = SPEECH_LOCALES[lang] || "en-US";
  window.speechSynthesis.speak(u);
}

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((ev: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

export function speechSupported(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return !!(w.SpeechRecognition || w.webkitSpeechRecognition);
}

export function startDictation(
  lang: string,
  onText: (text: string) => void,
): (() => void) | null {
  if (!speechSupported()) return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition;
  if (!Ctor) return null;
  const rec = new Ctor();
  rec.lang = SPEECH_LOCALES[lang] || "en-US";
  rec.interimResults = false;
  rec.continuous = false;
  rec.onresult = (ev) => {
    const t = ev.results?.[0]?.[0]?.transcript;
    if (t) onText(t);
  };
  rec.onerror = () => {};
  rec.start();
  return () => {
    try {
      rec.stop();
    } catch {
      /* ignore */
    }
  };
}
