"use client";

import { useCallback, useEffect, useState } from "react";

import { chrome } from "@/lib/chrome";
import { NEWS_CITIES } from "@/lib/portal";

const STORAGE_KEY = "civicvoice.city";
const VALID = new Set<string>(NEWS_CITIES.map((c) => c.id));

/** Selected city shared across Home / News / Ballot (persisted per browser). */
export function useSelectedCity(): [string, (city: string) => void] {
  const [city, setCityState] = useState("all");

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved && VALID.has(saved)) setCityState(saved);
    } catch {
      /* storage unavailable */
    }
  }, []);

  const setCity = useCallback((next: string) => {
    if (!VALID.has(next)) return;
    setCityState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
  }, []);

  return [city, setCity];
}

export function CityChips({
  lang,
  value,
  onChange,
}: {
  lang: string;
  value: string;
  onChange: (city: string) => void;
}) {
  return (
    <div className="city-chips" role="group" aria-label="Filter by city">
      {NEWS_CITIES.map((c) => (
        <button
          key={c.id}
          type="button"
          className={`city-chip${value === c.id ? " active" : ""}`}
          aria-pressed={value === c.id}
          onClick={() => onChange(c.id)}
        >
          {chrome(lang, c.key)}
        </button>
      ))}
    </div>
  );
}
