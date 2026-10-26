import type { FeedItem } from "@/lib/api";

/**
 * Keyword → topic slug used by the News sidebar.
 * Aligned with v1 data/topics.json (plus a few title words cities use).
 */
const TOPIC_KEYWORDS: Record<string, string[]> = {
  housing: [
    "housing",
    "rent",
    "rental",
    "cdbg",
    "affordable",
    "tenant",
    "landlord",
    "homeless",
    "homelessness",
    "apartment",
    "apartments",
    "zoning",
    "dwelling",
    "shelter",
  ],
  jobs: [
    "job",
    "jobs",
    "business",
    "businesses",
    "economic",
    "economy",
    "workforce",
    "employment",
    "employer",
    "fee schedule",
    "license",
    "commercial",
    "career",
    "vending",
    "commerce",
    "manufacturing",
  ],
  education: [
    "school",
    "schools",
    "education",
    "student",
    "students",
    "college",
    "classroom",
    "teacher",
    "fusd",
    "library",
    "university",
    "campus",
  ],
  health: [
    "health",
    "medical",
    "medi-cal",
    "hospital",
    "clinic",
    "covid",
    "wellness",
    "mental health",
  ],
  safety: [
    "police",
    "sheriff",
    "emergency",
    "preparedness",
    "safety",
    "fire",
    "flood",
    "cert",
    "opioid",
    "crime",
    "911",
    "public safety",
  ],
  transit: [
    "transit",
    "bart",
    "traffic",
    "street",
    "streets",
    "parking",
    "sidewalk",
    "road",
    "bus",
    "transportation",
    "resurfacing",
    "boulevard",
  ],
  elections: [
    "ballot",
    "ballots",
    "voter",
    "voters",
    "election",
    "elections",
    "proposition",
    "propositions",
    "nomination",
    "registrar",
    "charter",
    "measure",
    "vote",
    "voting",
    "poll",
  ],
  benefits: [
    "benefits",
    "benefit",
    "immigration",
    "immigrant",
    "assistance",
    "calfresh",
    "calworks",
    "medi-cal",
    "medicaid",
    "income",
    "ssi",
    "ssa",
    "snap",
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
  interests: string[] = [],
): FeedItem[] {
  if (!topic || topic === "all") return items;
  if (topic === "for-you") {
    // v1 "For you": items matching the user's chosen interests (all if none set).
    if (!interests.length) return items;
    return items.filter((item) =>
      inferTopics(item).some((t) => interests.includes(t)),
    );
  }
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
