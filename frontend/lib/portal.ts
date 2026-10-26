export const TOPICS = [
  { id: "housing", label: "Housing" },
  { id: "jobs", label: "Jobs & business" },
  { id: "education", label: "Education" },
  { id: "health", label: "Health" },
  { id: "safety", label: "Public safety" },
  { id: "transit", label: "Transportation" },
  { id: "elections", label: "Elections & ballot" },
  { id: "benefits", label: "Benefits & immigration" },
];

export const PROFESSIONS = [
  { id: "renter", label: "Renter" },
  { id: "homeowner", label: "Homeowner" },
  { id: "small_business", label: "Small business" },
  { id: "student", label: "Student" },
  { id: "senior", label: "Senior" },
  { id: "healthcare", label: "Healthcare worker" },
  { id: "teacher", label: "Teacher" },
  { id: "tech_worker", label: "Tech worker" },
  { id: "gig_worker", label: "Gig / day labor" },
];

export const NEWS_SIDEBAR = [
  { slug: "all", key: "newsAll" as const },
  { slug: "housing", key: "topicHousing" as const },
  { slug: "jobs", key: "topicJobs" as const },
  { slug: "education", key: "topicEducation" as const },
  { slug: "health", key: "topicHealth" as const },
  { slug: "safety", key: "topicSafety" as const },
  { slug: "transit", key: "topicTransit" as const },
  { slug: "elections", key: "topicElections" as const },
  { slug: "benefits", key: "topicBenefits" as const },
];

export const BALLOT_SIDEBAR = [
  { slug: "measures", key: "ballotAll" as const },
  { slug: "statewide", key: "ballotStatewide" as const },
  { slug: "local", key: "ballotLocal" as const },
  { slug: "basics", key: "ballotBasics" as const },
];

export const SERVICES_SIDEBAR = [
  { slug: "streets", key: "svcStreets" as const, label: "Streets and sidewalks" },
  { slug: "housing", key: "svcHousing" as const, label: "Housing and rent" },
  { slug: "utilities", key: "svcUtilities" as const, label: "Utilities" },
  { slug: "permits", key: "svcPermits" as const, label: "Permits and business" },
  { slug: "parks", key: "svcParks" as const, label: "Parks and community" },
  { slug: "contact", key: "svcContact" as const, label: "Contact the city" },
];

/** Official service links per category — matched to CivicVoice v1. */
export const SERVICE_PAGE_LINKS: Record<
  string,
  { title: string; url: string; agency: string; note?: string }[]
> = {
  streets: [
    {
      title: "Report a pothole or road issue",
      url: "https://www.fremont.gov/our-city/departments/public-works",
      agency: "Fremont Public Works",
    },
    {
      title: "Newark public works",
      url: "https://www.newarkca.gov/departments/public-works",
      agency: "Newark",
    },
  ],
  housing: [
    {
      title: "Fremont rent review program",
      url: "https://www.fremont.gov/government/departments/housing/rent-review-program",
      agency: "Fremont Housing",
    },
    {
      title: "Alameda County housing resources",
      url: "https://www.acgov.org/cda/housing/",
      agency: "Alameda County",
    },
  ],
  utilities: [
    {
      title: "City of Fremont utilities",
      url: "https://www.fremont.gov/our-city/departments/public-works/utilities",
      agency: "Fremont",
    },
  ],
  permits: [
    {
      title: "Fremont permits and licenses",
      url: "https://www.fremont.gov/business/permits-licenses",
      agency: "Fremont",
    },
    {
      title: "Union City business licenses",
      url: "https://www.unioncity.org/161/Business-Licenses",
      agency: "Union City",
    },
  ],
  parks: [
    {
      title: "Fremont parks and recreation",
      url: "https://www.fremont.gov/our-city/departments/parks-recreation",
      agency: "Fremont",
    },
  ],
  contact: [
    {
      title: "Contact Fremont",
      url: "https://www.fremont.gov/our-city/contact-us",
      agency: "Fremont",
    },
    {
      title: "Contact Newark",
      url: "https://www.newarkca.gov/our-city/contact-us",
      agency: "Newark",
    },
    {
      title: "Contact Union City",
      url: "https://www.unioncity.org/27/Contact-Us",
      agency: "Union City",
    },
  ],
};

export type PortalNav =
  | "home"
  | "news"
  | "ballot"
  | "services"
  | "report"
  | "ask";
