# CivicVoice — How My App Works
Hi, I'm Abhinav, a sophomore at Washington High in Fremont. I built CivicVoice so people who don't read English well can still understand their local government — city news, council updates, and ballots — in their own language.

This page explains how the app is built, and where it actually runs. The most important part first: it does not run on my laptop. Anyone can open the public website from any phone or computer, even when my Mac is off.

# Contents
Where the app runs
# Do I need Vercel for the frontend?
The parts of the app
# The database
Workflow 1 — Sign up, log in, and see your feed
Workflow 2 — Ask a question
Workflow 3 — Change the language
Workflow 4 — Report a problem in your city
Workflow 5 — How new data gets in, and how old data gets cleaned up


Deployment — how it all goes live
Security — the basics I check
Build order — what I will build first
Folder structure
Where the app runs
My code lives on GitHub. When I push code, the hosts below deploy it. After that, my laptop is not part of the app anymore.

Frontend. Runs in the user's browser. When someone opens the website, their phone or computer downloads the frontend files from a public host. After that, the frontend code runs on their device, in their browser.

Backend. Runs on a server in the cloud. This is a small computer in a data center, running my Python code all day. It is not my Mac. When the frontend needs data, it sends a request to this backend over the internet, and the backend sends an answer back.

Database. Runs on a database host in the cloud. This is where users, documents, and search data live. My backend talks to it with a password. Users never talk to it directly.

Ingest worker. Runs on a schedule in the cloud. Once a day, it checks official government websites for new updates and saves them to the database.

AI summarizer. Runs on the AI provider's servers. My backend sends it a question and some real document pieces, and it sends back a summary with citations.

How to test it. Turn off my local server completely, open the public website on a phone, and check that the feed, ballots, language switch, and Ask still work. If they do, the app is running in the cloud.

Do I need Vercel for the frontend?
No. Vercel is one option, not a requirement.

The requirement is a public website: anyone can open the link, without a login, without my Mac running, and without a password page. Any public host that does that works:

Vercel — easiest if the frontend is Next.js
Cloudflare Pages — free, fast, good for a static frontend
Netlify — similar to Vercel for a static frontend
Render or Fly.io — if I serve the frontend from the same server as the backend, then one public link covers everything
What does not count as public
A link that only works on localhost
A link that needs a Vercel login
A frontend that calls http://localhost:5001 for data
In that last case the page loads, but Ask breaks for everyone except me, because their browser tries to call my laptop.

For this app, I will use a public frontend host, a public backend host, and a hosted database. The exact host names can change. The public part cannot.

The parts of the app

User opens the public website on a phone or computer
        |
        v
Frontend — public host, runs in the user's browser
  - home feed, ballots, news, Ask, report, profile
  - language picker for 12 languages
  - it only talks to the backend through APIs, never to the database directly
        |
        v
Backend — public server in the cloud
  - checks who is logged in, limits how fast someone can ask questions
  - ranks the feed, searches documents, answers questions, handles reports
        |
        +---> Database — hosted Postgres with pgvector
        |       users, sources, documents, document pieces + search vectors,
        |       translations, reports, saved items, feedback
        |
        +---> Redis — cache and queue
        |       rate limits, login lockouts, cached answers,
        |       jobs for ingest and translation
        |
        +---> AI Provider — key kept in environment variables only
        |       writes summaries with citations, in the language asked for
        |       no key = show the real documents, never make up a summary
        |
        +---> File Storage — for original PDFs and source files
                the database only stores the link and a hash, not the file itself
The database
I use one Postgres database, with an extension called pgvector. Pgvector lets the database search by meaning, not just by exact words. That is how a question in Hindi can find the right English document.

Users
id, email, password_hash (Argon2), preferred_language, city, interests[], profession, created_at

Passwords are hashed, never stored as plain text. Login sessions use secure cookies.

Sources
id, name, url, host, type, last_fetched_at, content_hash, status

This is how the website shows "last updated." If a source has not been checked lately, users can see that.

Documents
id, source_id, title, url, published_at, type (news | council | voter_guide | ballot), city, language

Type and city are what make feed filtering and ballot pages fast.

Chunks
id, document_id, text, page, text_hash, embedding vector(1024), is_active, last_seen_run

A search vector is just a list of numbers that represents what the piece means. Similar meanings have similar numbers.

The embedding model is e5 (intfloat/multilingual-e5-base), with query: / passage: labels.

I also store which ingest run last saw each piece, so I can clean up old pieces safely.

Index: HNSW index on embedding for similarity search, plus a full-text index on text.

Translations
chunk_id, language, translated_text, provider, verified, created_at

Translations are saved here, so I don't have to translate the same piece again and again. If there is no checked translation, I show the English original and say so clearly.

Reports
id, user_id, category, description, location, status (draft | ready), external_link, created_at

A report in my app is never marked as submitted by the app itself, because Fremont does not have a system for apps to submit reports automatically.

Saved items and feedback
saved_items — id, user_id, document_id, created_at
feedback — id, user_id, query, chunk_ids, helpful, created_at
Feedback is used to see if search is working, not to train on user data without consent.

Why one database instead of a separate search database?
Because I can ask one question like "find pieces about housing, in Fremont, in Hindi" and get an answer in one query. A second database would mean keeping two copies in sync, and I don't need that yet.

Workflow 1 — Sign up, log in, and see your feed
A user opens the website and picks a language.
They sign up with email, password, city, interests, profession, and language.
The backend hashes the password, saves the user, and gives them a secure login cookie.
If someone types the wrong password 10 times, they are locked out for 10 minutes. This lockout is stored in Redis, so it still works if the backend restarts.
On the home page, the backend finds documents for that user's city, ranks them by interests and how recent they are, and sends them to the frontend.
The frontend shows the feed in the user's language.
Workflow 2 — Ask a question
This is the main feature. Here is what happens step by step when a user asks a question:

The user types a question, in any of the 12 languages.
The frontend sends it to the backend: POST /api/ask, with the question and language.
The backend checks that the question is not empty, the language is supported, and the user is not asking too fast.
It checks Redis to see if this exact question in this exact language was already answered. If yes, it returns that answer right away.
If not, it turns the question into a search vector, using the same model as the documents, with a query: label in front of it.
It searches the database two ways and combines the results:
By meaning, using pgvector, top 50 pieces
By exact keywords, using Postgres full-text search, top 50 pieces
It reranks those pieces with a small reranker model, and keeps the best 8.
It sends those 8 pieces to the AI, with instructions to write a summary in the user's language, and to cite the exact file and page for every claim.
Before showing the answer, it checks two things:
Every claim really comes from one of the 8 pieces
The answer does not try to persuade anyone how to vote on a ballot
If either check fails, it does not show the answer
It saves the answer in Redis, so the next person asking the same thing gets it faster.
The frontend shows the summary, plus a list of citations. Tapping a citation shows the original piece, with the English text below a translation if there is one.
If there is no AI key
The app does not make up a summary. It shows the real document pieces and says a summary is not available. That is better than a fake answer.

I also keep some pre-checked example questions and answers in the database. Those work without an AI call, so the app still works for demos and for first-time users.

Workflow 3 — Change the language
The user picks a language from the dropdown.
The frontend changes all the buttons and menus right away, from language files already on the user's device. No internet call needed for that part.
For news and documents, the frontend asks the backend again, with the new language.
The backend looks in the translations table:
If a checked translation exists, it sends that.
If not, it sends the English original and says "translation not yet available."
It can also queue a translation job in the background, and save the result for next time.
The frontend never pretends an untranslated piece is translated.
The whole dashboard switches, but I don't claim every single word is translated. Links to outside city pages and pieces without a translation stay in English, with a note.

Workflow 4 — Report a problem in your city
The user fills out a form: what kind of problem, a description, and a location. A photo is optional.
The backend saves it as a draft, writes a clean, copy-ready version of the report in the user's language, and finds the correct city request page for that kind of problem.
The frontend shows the report, a Copy button, and a button to open the city's request page.
It also says clearly: "CivicVoice does not submit this for you. Paste it on the city's page."
The user pastes it and submits it on the city's own website.
I do it this way because there is no automatic system for Fremont to accept reports from apps. Pretending my app submits it directly would be dishonest.

Workflow 5 — How new data gets in, and how old data gets cleaned up
New data does not come in when I push code. It comes in from a separate worker that runs once a day in the cloud, plus I can run it by hand for a demo.

The worker starts a run and gives it an ID.
For each official source, it only visits websites on my approved list, with approved web addresses.
It downloads the page or PDF, removes duplicates by checking a hash, and splits the text into small pieces.
It turns each piece into a search vector and saves it, or updates it if the text changed.
It marks every piece it saw in this run with the run ID, and updates the source's "last checked" time.
For cleanup, it does it in two safe steps, never just deleting everything at once:
First, it marks pieces it did not see in this run as inactive.
After 7 days, and after a good run, it deletes those inactive pieces for real.
It logs what it added, updated, and marked inactive, and any errors.
The website's "last updated" label reads from the sources table, so users can see how fresh the data is.

One safety rule
If downloading a source fails that day, the worker does not delete that source's pieces. A failed download should never wipe out good data.

Deployment — how it all goes live
Push code to GitHub. The main branch is the live version. Other branches are for trying new features.

Pushing to main starts a deploy:

Frontend goes to a public host, built and sent to servers around the world
Backend goes to a container host, built and started as a server in the cloud
Database changes are applied from migration files in db/migrations/, never edited by hand in production
Worker is the same backend code, run as a scheduled job
Secrets are set in the host dashboards, never in the code:

DATABASE_URL — the database connection, using the pooler port 6543 and SSL
CIVICVOICE_LLM_API_KEY, CIVICVOICE_LLM_BASE_URL, CIVICVOICE_LLM_MODEL
SESSION_SECRET — a random secret, different for local testing and for live
For local testing on my Mac, I run the same code with Postgres in Docker, and a local database address instead of the live one.

Hosting summary
Part	Where it runs	Notes
Frontend files
Vercel, Cloudflare Pages, or Netlify
Built from GitHub on push, works when my Mac is off
Database
Supabase or Neon, Postgres with pgvector
Free tiers are enough to start, paid tiers add no pausing and automatic backups
Backend
Fly.io or Render, as a container
Needs Python and the search model
Secrets
Host dashboards only
Never commit .env or API keys
Security — the basics I check
Passwords hashed, login cookies secure, extra tokens on forms that change data
Rate limits in Redis, so they still work after a restart
Every API input is checked, and every database query uses safe parameters, not pasted-in text
Ballot summaries are checked for persuasive language, and Ask answers are checked for real citations
Backups: I export the database by hand on the free tier, and use automatic daily backups on a paid tier
I log report creation and admin actions, but never passwords
Build order — what I will build first
Database tables and migrations
Backend API: login, feed, search, Ask with citations and checks
Frontend: pages, language files, language switch, citation view
Ingest worker and the "last updated" label
Reranker and translation cache
Folder structure

civicvoice/
  frontend/            # Next.js app, language files, pages, components
  backend/             # FastAPI app: api/, auth.py, retriever.py, summarizer.py, guards.py
  ingest/              # scheduled worker: fetch.py, parse.py, chunk.py, embed.py, cleanup.py
  db/
    migrations/        # database changes, in order, one file per change
    schema.sql         # full database layout, made from the migrations
  docs/
    architecture-workflow.md   # this file
  .gitignore
  README.md
