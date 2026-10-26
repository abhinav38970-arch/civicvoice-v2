"""Approved official hosts/paths for ingest. Only these may be fetched."""

ALLOWED_SOURCES = [
    {
        "name": "California Secretary of State — Voter Information Guides",
        "url": "https://www.sos.ca.gov/elections/voting-resources/voter-information-guides",
        "host": "www.sos.ca.gov",
        "type": "state",
        "doc_type": "voter_guide",
        "city": "Fremont",
        "title": "California Voter Information Guides",
    },
    {
        "name": "California Secretary of State — Elections",
        "url": "https://www.sos.ca.gov/elections",
        "host": "www.sos.ca.gov",
        "type": "state",
        "doc_type": "voter_guide",
        "city": "Fremont",
        "title": "California Elections and Voter Information",
    },
    {
        "name": "Alameda County Registrar of Voters",
        "url": "https://www.acvote.org/",
        "host": "www.acvote.org",
        "type": "county",
        "doc_type": "news",
        "city": "Fremont",
        "title": "Alameda County Registrar of Voters",
    },
    {
        "name": "Alameda County — Vote by Mail & ballot status",
        "url": "https://www.sos.ca.gov/elections/voter-registration/vote-mail",
        "host": "www.sos.ca.gov",
        "type": "state",
        "doc_type": "news",
        "city": "Fremont",
        "title": "California Vote by Mail information",
    },
    {
        "name": "California Official Voter Guide",
        "url": "https://voterguide.sos.ca.gov/",
        "host": "voterguide.sos.ca.gov",
        "type": "state",
        "doc_type": "voter_guide",
        "city": "Fremont",
        "title": "California Official Voter Information Guide",
    },
]

ALLOWED_HOSTS = {s["host"] for s in ALLOWED_SOURCES}
