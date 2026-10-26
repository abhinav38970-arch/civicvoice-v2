import type { FeedItem } from "@/lib/api";

/** Keyword → topic slug used by the News sidebar. */
const TOPIC_KEYWORDS: Record<string, string[]> = {
  housing: [
    "housing",
    "rent",
    "rental",
    "apartment",
    "homeless",
    "shelter",
    "zoning",
    "affordable",
  ],
  jobs: [
    "job",
    "jobs",
    "business",
    "economy",
    "employment",
    "workforce",
    "commerce",
    "employer",
  ],
  education: [
    "school",
    "education",
    "student",
    "library",
    "college",
    "university",
    "campus",
  ],
  health: [
    "health",
    "hospital",
    "clinic",
    "medical",
    "covid",
    "wellness",
    "mental health",
  ],
  safety: [
    "safety",
    "police",
    "fire",
    "crime",
    "emergency",
    "911",
    "public safety",
  ],
  transit: [
    "transit",
    "street",
    "road",
    "parking",
    "transportation",
    "resurfacing",
    "bus",
    "bart",
    "sidewalk",
    "traffic",
    "boulevard",
  ],
  elections: [
    "election",
    "ballot",
    "voter",
    "vote",
    "voting",
    "measure",
    "proposition",
    "registrar",
    "poll",
  ],
  benefits: [
    "benefit",
    "benefits",
    "immigration",
    "calfresh",
    "medi-cal",
    "medicaid",
    "snap",
    "assistance",
    "welfare",
  ],
};

/** English haystack so topic filters keep working after titles are localized. */
function filterHaystack(item: FeedItem): string {
  return [
    item.title_original || item.title,
    item.source_name_original || item.source_name,
    item.snippet_original || item.snippet || "",
    item.url,
    item.type,
  ]
    .join(" ")
    .toLowerCase();
}

export function inferTopics(item: FeedItem): string[] {
  const hay = filterHaystack(item);
  const hits: string[] = [];
  for (const [topic, words] of Object.entries(TOPIC_KEYWORDS)) {
    if (words.some((w) => hay.includes(w))) hits.push(topic);
  }
  // Ballot / voter-guide docs always count as elections.
  if (
    (item.type === "ballot" || item.type === "voter_guide") &&
    !hits.includes("elections")
  ) {
    hits.push("elections");
  }
  return hits;
}

export function filterNewsByTopic(
  items: FeedItem[],
  topic: string,
): FeedItem[] {
  if (!topic || topic === "all") return items;
  return items.filter((item) => inferTopics(item).includes(topic));
}

/** Ballot sidebar: measures | statewide | local | basics */
export function filterBallotsByCategory(
  items: FeedItem[],
  category: string,
): FeedItem[] {
  if (!category || category === "measures") return items;

  return items.filter((item) => {
    const hay = filterHaystack(item);
    const titleEn = (item.title_original || item.title).toLowerCase();

    const isStatewide =
      hay.includes("sos.ca.gov") ||
      hay.includes("voterguide.sos") ||
      hay.includes("statewide") ||
      hay.includes("proposition") ||
      hay.includes("california secretary") ||
      hay.includes("california official voter") ||
      hay.includes("california elections") ||
      hay.includes("california voter information");

    const isLocal =
      hay.includes("fremont") ||
      hay.includes("alameda") ||
      hay.includes("newark") ||
      hay.includes("union city") ||
      hay.includes("acgov") ||
      hay.includes("acvote") ||
      /\bmeasure\s+[a-z]\b/i.test(titleEn) ||
      (item.type === "ballot" && !isStatewide);

    const isBasics =
      item.type === "voter_guide" ||
      hay.includes("voter guide") ||
      hay.includes("voter information guide") ||
      hay.includes("how to vote") ||
      hay.includes("voterguide.sos");

    if (category === "statewide") return isStatewide;
    if (category === "local") return isLocal;
    if (category === "basics") {
      // Guides only — not individual local measures.
      if (item.type === "ballot" && /\bmeasure\s+[a-z]\b/i.test(titleEn)) {
        return false;
      }
      return isBasics;
    }
    return true;
  });
}
