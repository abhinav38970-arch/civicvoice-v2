"""Approved official hosts/paths for ingest. Only these may be fetched."""

ALLOWED_SOURCES = [
    # —— State / county (ballot & elections) ——
    {
        "name": "California Secretary of State — Voter Information Guides",
        "url": "https://www.sos.ca.gov/elections/voting-resources/voter-information-guides",
        "host": "www.sos.ca.gov",
        "type": "state",
        "doc_type": "voter_guide",
        "city": "Alameda County",
        "title": "California Voter Information Guides",
    },
    {
        "name": "California Secretary of State — Elections",
        "url": "https://www.sos.ca.gov/elections",
        "host": "www.sos.ca.gov",
        "type": "state",
        "doc_type": "voter_guide",
        "city": "Alameda County",
        "title": "California Elections and Voter Information",
    },
    {
        "name": "Alameda County Registrar of Voters",
        "url": "https://www.acvote.org/",
        "host": "www.acvote.org",
        "type": "county",
        "doc_type": "news",
        "city": "Alameda County",
        "title": "Alameda County Registrar of Voters",
    },
    {
        "name": "Alameda County — Vote by Mail & ballot status",
        "url": "https://www.sos.ca.gov/elections/voter-registration/vote-mail",
        "host": "www.sos.ca.gov",
        "type": "state",
        "doc_type": "news",
        "city": "Alameda County",
        "title": "California Vote by Mail information",
    },
    {
        "name": "California Official Voter Guide",
        "url": "https://voterguide.sos.ca.gov/",
        "host": "voterguide.sos.ca.gov",
        "type": "state",
        "doc_type": "voter_guide",
        "city": "Alameda County",
        "title": "California Official Voter Information Guide",
    },
    # —— City news (official public pages) ——
    # Fremont news index (CivicPlus). Live fetches may return Akamai 403 from
    # datacenter IPs; keep on allowlist so scheduled/browser-capable runs can use it.
    {
        "name": "City of Fremont — News",
        "url": "https://www.fremont.gov/about/news-media/fremont-news",
        "host": "www.fremont.gov",
        "type": "city",
        "doc_type": "news",
        "city": "Fremont",
        "title": "City of Fremont News",
        # Listing page: ingest linked articles (not the index itself as a feed card).
        "discover_articles": True,
        "discover_limit": 20,
        "skip_listing_doc": True,
    },
    {
        "name": "City of Newark — News",
        "url": "https://www.newarkca.gov/residents/news",
        "host": "www.newarkca.gov",
        "type": "city",
        "doc_type": "news",
        "city": "Newark",
        "title": "City of Newark News",
        # Detail pages are bot-blocked; the listing carries the text.
        "listing_items": "div.content_area h3",
        "discover_limit": 15,
        "skip_listing_doc": True,
    },
    {
        "name": "City of Union City — City News",
        "url": "https://www.unioncityca.gov/185/City-News",
        "host": "www.unioncityca.gov",
        "type": "city",
        "doc_type": "news",
        "city": "Union City",
        "title": "City of Union City News",
        # Article detail pages 403 even in a browser; cards on the listing carry
        # headline, date, and summary.
        "listing_items": "h3.article-list-header",
        "discover_limit": 20,
        "skip_listing_doc": True,
    },
]

ALLOWED_HOSTS = {s["host"] for s in ALLOWED_SOURCES}
# Legacy / redirect aliases so follow_redirects + browser landings stay allowed.
ALLOWED_HOSTS |= {
    "www.newark.org",
    "newark.org",
    "www.unioncity.org",
    "unioncity.org",
    "fremont.gov",
    "www.fremont.gov",
}
