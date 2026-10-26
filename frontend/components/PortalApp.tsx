"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { CitationDrawer, type DrawerPayload } from "@/components/CitationDrawer";
import { PortalShell } from "@/components/PortalShell";
import { api, type AskResponse, type FeedItem, type User } from "@/lib/api";
import { chrome } from "@/lib/chrome";
import { formatFeedDate, nameFromEmail } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import {
  BALLOT_SIDEBAR,
  NEWS_SIDEBAR,
  SERVICE_PAGE_LINKS,
  SERVICES_SIDEBAR,
  TOPICS,
  type PortalNav,
} from "@/lib/portal";
import { filterBallotsByCategory, filterNewsByTopic } from "@/lib/topics";
import { speakText, speechSupported, startDictation } from "@/lib/voice";

function PortalAppInner({ tab }: { tab: PortalNav }) {
  const { lang } = useI18n();
  const params = useSearchParams();

  const [news, setNews] = useState<FeedItem[]>([]);
  const [homeFeed, setHomeFeed] = useState<FeedItem[]>([]);
  const [ballots, setBallots] = useState<FeedItem[]>([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [loadingHome, setLoadingHome] = useState(true);
  const [loadingBallots, setLoadingBallots] = useState(true);
  const [newsSub, setNewsSub] = useState("all");
  const [ballotSub, setBallotSub] = useState("measures");
  const [servicesSub, setServicesSub] = useState("streets");
  const [ballotDetail, setBallotDetail] = useState<FeedItem | null>(null);
  const [ballotDetailId, setBallotDetailId] = useState<string | null>(null);
  const [drawer, setDrawer] = useState<DrawerPayload | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerDocId, setDrawerDocId] = useState<string | null>(null);

  const [query, setQuery] = useState(params.get("q") || "");
  const [askBusy, setAskBusy] = useState(false);
  const [askStatus, setAskStatus] = useState("");
  const [askResult, setAskResult] = useState<AskResponse | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const micOk = useMemo(() => speechSupported(), []);
  const displayName = user
    ? nameFromEmail(user.email)
    : chrome(lang, "guest");

  useEffect(() => {
    let cancelled = false;
    api
      .me()
      .then((r) => {
        if (!cancelled) setUser(r.user);
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      })
      .finally(() => {
        if (!cancelled) setAuthReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const q = params.get("q");
    if (q && tab === "ask") setQuery(q);
  }, [params, tab]);

  useEffect(() => {
    let cancelled = false;
    // Drop previous-language rows immediately so chrome lang and body match.
    setNews([]);
    setBallots([]);
    setHomeFeed([]);
    setBallotDetail(null);
    setLoadingNews(true);
    setLoadingHome(true);
    setLoadingBallots(true);

    Promise.all([
      api.notices(30, lang, "Fremont"),
      api.ballots(30, lang, "Fremont"),
    ])
      .then(([n, b]) => {
        if (cancelled) return;
        setNews(n.items);
        setBallots(b.items);
        if (ballotDetailId) {
          const updated = b.items.find((x) => x.id === ballotDetailId);
          if (updated) setBallotDetail(updated);
        }
        const merged = [...n.items, ...b.items].sort((a, c) => {
          const ta = Date.parse(a.published_at || a.last_updated || "") || 0;
          const tb = Date.parse(c.published_at || c.last_updated || "") || 0;
          return tb - ta;
        });
        setHomeFeed(merged);
      })
      .catch(() => {
        if (cancelled) return;
        setNews([]);
        setBallots([]);
        setHomeFeed([]);
      })
      .finally(() => {
        if (cancelled) return;
        setLoadingNews(false);
        setLoadingHome(false);
        setLoadingBallots(false);
      });
    return () => {
      cancelled = true;
    };
  }, [lang, ballotDetailId]);

  useEffect(() => {
    if (!drawerOpen || !drawerDocId) return;
    let cancelled = false;
    (async () => {
      try {
        const doc = await api.document(drawerDocId, lang);
        if (cancelled) return;
        const chunk = doc.chunks[0];
        setDrawer({
          file: doc.title,
          page: chunk?.page ?? null,
          section: doc.source_name,
          text: chunk?.text || doc.title,
          originalText: chunk?.original_text || null,
        });
      } catch {
        /* keep */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [lang, drawerOpen, drawerDocId]);

  useEffect(() => {
    if (!askResult?.question) return;
    const q = askResult.question;
    let cancelled = false;
    (async () => {
      setAskBusy(true);
      try {
        const res = await api.ask(q, lang, "Fremont");
        if (!cancelled) setAskResult(res);
      } catch {
        /* keep */
      } finally {
        if (!cancelled) setAskBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  async function openDocDrawer(item: FeedItem) {
    setDrawerDocId(item.id);
    try {
      const doc = await api.document(item.id, lang);
      const chunk = doc.chunks[0];
      setDrawer({
        file: doc.title || item.title,
        page: chunk?.page ?? null,
        section: doc.source_name,
        text: chunk?.text || item.snippet || item.title,
        originalText: chunk?.original_text || null,
      });
    } catch {
      setDrawer({
        file: item.title,
        page: null,
        section: item.source_name,
        text: item.snippet || item.title,
        originalText: null,
      });
    }
    setDrawerOpen(true);
    document.body.classList.add("drawer-open");
  }

  function closeDrawer() {
    setDrawerDocId(null);
    setDrawerOpen(false);
    setDrawer(null);
    document.body.classList.remove("drawer-open");
  }

  async function openCitation(c: AskResponse["citations"][number]) {
    setDrawerDocId(c.document_id);
    try {
      const doc = await api.document(c.document_id, lang);
      const chunk =
        doc.chunks.find((x) => x.id === c.chunk_id) || doc.chunks[0];
      setDrawer({
        file: c.title,
        page: c.page,
        section: c.source_name,
        text: chunk?.text || c.text,
        originalText: chunk?.original_text || null,
      });
    } catch {
      setDrawer({
        file: c.title,
        page: c.page,
        section: c.source_name,
        text: c.text,
        originalText: null,
      });
    }
    setDrawerOpen(true);
    document.body.classList.add("drawer-open");
  }

  async function runAsk(q: string) {
    const question = q.trim();
    if (!question) {
      setAskStatus(chrome(lang, "typeQuestion"));
      return;
    }
    setAskBusy(true);
    setAskStatus(chrome(lang, "searching"));
    setAskResult(null);
    try {
      const res = await api.ask(question, lang, "Fremont");
      setAskResult(res);
      setAskStatus("");
    } catch (e) {
      setAskStatus(
        e instanceof Error ? e.message : chrome(lang, "noAnswerYet"),
      );
    } finally {
      setAskBusy(false);
    }
  }

  const filteredNews = filterNewsByTopic(news, newsSub);
  const newsTopicEmpty =
    !loadingNews && news.length > 0 && filteredNews.length === 0;
  const newsCatalogEmpty = !loadingNews && news.length === 0;

  const filteredBallots = filterBallotsByCategory(ballots, ballotSub);
  const ballotTopicEmpty =
    !loadingBallots && ballots.length > 0 && filteredBallots.length === 0;
  const ballotCatalogEmpty = !loadingBallots && ballots.length === 0;
  const ballotLeadKey =
    ballotSub === "statewide"
      ? ("ballot_lead_statewide" as const)
      : ballotSub === "local"
        ? ("ballot_lead_local" as const)
        : ballotSub === "basics"
          ? ("ballot_lead_basics" as const)
          : ("exampleSub" as const);

  return (
    <PortalShell active={tab} displayName={user ? displayName : undefined}>
      {tab === "home" && (
        <>
          <div className="home-head">
            <h1>
              {chrome(lang, "hello")}
              {authReady ? `, ${displayName}` : ""}
            </h1>
          </div>
          <div className="home-interests">
            <span>{chrome(lang, "basedOnInterests")}</span>{" "}
            <span id="interestText">
              {user
                ? [
                    user.city,
                    user.profession?.replace(/_/g, " "),
                    ...TOPICS.filter((t) =>
                      (user.interests || []).includes(t.id),
                    ).map((t) => t.label),
                  ]
                    .filter(Boolean)
                    .slice(0, 6)
                    .join(" · ") || chrome(lang, "addTopics")
                : chrome(lang, "city_fremont")}
            </span>{" "}
            <Link href="/onboarding">{chrome(lang, "editShort")}</Link>
          </div>
          <div className="quick-links">
            <Link href="/ballot">{chrome(lang, "homeQuickBallot")}</Link>
            <Link href="/ask">{chrome(lang, "homeQuickAsk")}</Link>
            <Link href="/news">{chrome(lang, "homeQuickMeetings")}</Link>
            <Link href="/services">{chrome(lang, "navServices")}</Link>
          </div>
          <section>
            <h2 style={{ fontSize: "1.1rem", margin: "16px 0 12px" }}>
              {chrome(lang, "homeFeed")}
            </h2>
            {loadingHome && <p className="muted">{chrome(lang, "loading")}</p>}
            <div className="feed-grid">
              {homeFeed.slice(0, 6).map((item) => {
                const when = formatFeedDate(
                  item.published_at || item.last_updated,
                );
                return (
                  <article key={item.id} className="feed-card">
                    <p className="feed-title">{item.title}</p>
                    <p className="feed-meta">
                      {[item.source_name, when].filter(Boolean).join(" · ")}
                    </p>
                    {item.snippet ? (
                      <p className="feed-meta" style={{ marginTop: 6 }}>
                        {item.snippet}
                      </p>
                    ) : null}
                    <button
                      type="button"
                      className="text-cta"
                      onClick={() => void openDocDrawer(item)}
                    >
                      {chrome(lang, "ctaReadSource")}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>
        </>
      )}

      {tab === "news" && (
        <div className="portal-layout">
          <aside className="portal-sidebar">
            <nav aria-label="News topics">
              {NEWS_SIDEBAR.map((s) => (
                <a
                  key={s.slug}
                  href="#"
                  aria-current={newsSub === s.slug ? "true" : undefined}
                  onClick={(e) => {
                    e.preventDefault();
                    setNewsSub(s.slug);
                  }}
                >
                  {chrome(lang, s.key)}
                </a>
              ))}
            </nav>
          </aside>
          <div className="portal-content">
            <h1>{chrome(lang, "newsTitle")}</h1>
            <p className="lead">{chrome(lang, "noticesSub")}</p>
            <div className="city-chips" role="group">
              <button type="button" className="city-chip active">
                {chrome(lang, "city_fremont")}
              </button>
            </div>
            {loadingNews && <p className="muted">{chrome(lang, "loading")}</p>}
            {newsCatalogEmpty && (
              <p className="muted">{chrome(lang, "newsEmpty")}</p>
            )}
            {newsTopicEmpty && (
              <p className="muted">{chrome(lang, "newsTopicEmpty")}</p>
            )}
            <div className="notices">
              {filteredNews.map((item) => {
                const when = formatFeedDate(
                  item.published_at || item.last_updated,
                );
                return (
                  <button
                    key={item.id}
                    type="button"
                    className="notice-item"
                    onClick={() => void openDocDrawer(item)}
                  >
                    <span>
                      <span className="notice-title">{item.title}</span>
                      <span className="notice-meta">{item.source_name}</span>
                    </span>
                    {when ? (
                      <span className="notice-date">{when}</span>
                    ) : (
                      <span className="status-chip is-current">
                        {chrome(lang, "statusCurrent")}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {tab === "ballot" && (
        <div className="portal-layout">
          <aside className="portal-sidebar">
            <nav aria-label="Ballot">
              {BALLOT_SIDEBAR.map((s) => (
                <a
                  key={s.slug}
                  href="#"
                  aria-current={ballotSub === s.slug ? "true" : undefined}
                  onClick={(e) => {
                    e.preventDefault();
                    setBallotSub(s.slug);
                    setBallotDetail(null);
                    setBallotDetailId(null);
                  }}
                >
                  {chrome(lang, s.key)}
                </a>
              ))}
            </nav>
          </aside>
          <div className="portal-content">
            <h1>{chrome(lang, "ballotTitle")}</h1>
            {!ballotDetail && (
              <>
                <p className="lead">{chrome(lang, ballotLeadKey)}</p>
                {ballotSub === "basics" && (
                  <p className="muted">
                    <a
                      href="https://voterguide.sos.ca.gov/"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {chrome(lang, "ballot_voter_guide")}
                      {" · "}
                      <span className="external-tag">
                        {chrome(lang, "externalGov")}
                      </span>
                    </a>
                  </p>
                )}
                {loadingBallots && (
                  <p className="muted">{chrome(lang, "loading")}</p>
                )}
                {ballotCatalogEmpty && (
                  <p className="muted">{chrome(lang, "ballotEmpty")}</p>
                )}
                {ballotTopicEmpty && (
                  <p className="muted">
                    {ballotSub === "local"
                      ? chrome(lang, "ballot_local_empty")
                      : chrome(lang, "ballotTopicEmpty")}
                  </p>
                )}
                <div className="topic-list">
                  {filteredBallots.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="topic-row"
                      onClick={() => {
                        setBallotDetailId(item.id);
                        setBallotDetail(item);
                      }}
                    >
                      <span className="topic-row-title">{item.title}</span>
                      {item.snippet && (
                        <span className="topic-row-desc">
                          {item.snippet.slice(0, 140)}
                          {item.snippet.length > 140 ? "…" : ""}
                        </span>
                      )}
                      <span className="topic-row-chev">›</span>
                    </button>
                  ))}
                </div>
              </>
            )}
            {ballotDetail && (
              <div className="result-card">
                <button
                  type="button"
                  className="link-btn back-btn"
                  onClick={() => {
                    setBallotDetailId(null);
                    setBallotDetail(null);
                  }}
                >
                  {chrome(lang, "backToList")}
                </button>
                <div className="result-head">
                  <div>
                    <h3>{ballotDetail.title}</h3>
                    <p className="topic-line">{ballotDetail.source_name}</p>
                  </div>
                  <button
                    type="button"
                    className="chip-btn"
                    onClick={() =>
                      speakText(
                        `${ballotDetail.title}. ${ballotDetail.snippet || ""}`,
                        lang,
                      )
                    }
                  >
                    🔊 {chrome(lang, "listen")}
                  </button>
                </div>
                {ballotDetail.snippet && <p>{ballotDetail.snippet}</p>}
                <div className="row" style={{ marginTop: 12 }}>
                  <button
                    type="button"
                    className="chip-btn"
                    onClick={() => void openDocDrawer(ballotDetail)}
                  >
                    {chrome(lang, "drawerTitle")}
                  </button>
                  {ballotDetail.url?.startsWith("http") && (
                    <a
                      className="chip-btn"
                      href={ballotDetail.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {chrome(lang, "officialPage")} ↗
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "services" && (
        <div className="portal-layout">
          <aside className="portal-sidebar">
            <nav aria-label="City services">
              {SERVICES_SIDEBAR.map((s) => (
                <a
                  key={s.slug}
                  href="#"
                  aria-current={servicesSub === s.slug ? "true" : undefined}
                  onClick={(e) => {
                    e.preventDefault();
                    setServicesSub(s.slug);
                  }}
                >
                  {chrome(lang, s.key)}
                </a>
              ))}
            </nav>
          </aside>
          <div className="portal-content">
            <h1>
              {chrome(
                lang,
                SERVICES_SIDEBAR.find((s) => s.slug === servicesSub)?.key ||
                  "navServices",
              )}
            </h1>
            <p className="lead">{chrome(lang, "servicesLead")}</p>
            <ul className="service-link-list">
              {(SERVICE_PAGE_LINKS[servicesSub] || []).map((link) => (
                <li key={link.url}>
                  <a href={link.url} target="_blank" rel="noopener noreferrer">
                    {link.title}
                  </a>{" "}
                  <span className="external-tag">
                    {chrome(lang, "externalGov")} · {link.agency}
                  </span>
                  {link.note ? (
                    <p className="muted" style={{ margin: "4px 0 0" }}>
                      {link.note}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {tab === "ask" && (
        <div className="portal-content" style={{ maxWidth: 780 }}>
          <h1>{chrome(lang, "askTitle")}</h1>
          <p className="lead">{chrome(lang, "askSub")}</p>
          <div className="ask-prompt">{chrome(lang, "askPrompt")}</div>
          <div className="ask-row">
            <div className="ask-field-wrap">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void runAsk(query);
                }}
                placeholder={chrome(lang, "askPlaceholder")}
              />
              {micOk && (
                <button
                  type="button"
                  className="icon-btn mic-inside"
                  onClick={() => startDictation(lang, setQuery)}
                >
                  🎙️
                </button>
              )}
            </div>
            <button
              type="button"
              id="askBtn"
              disabled={askBusy}
              onClick={() => void runAsk(query)}
            >
              {chrome(lang, "askButton")}
            </button>
          </div>
          <div className="example-chips">
            {(["exampleQ1", "exampleQ2", "exampleQ3"] as const).map((k) => (
              <button
                key={k}
                type="button"
                className="example-chip"
                onClick={() => {
                  const q = chrome(lang, k);
                  setQuery(q);
                  void runAsk(q);
                }}
              >
                {chrome(lang, k)}
              </button>
            ))}
          </div>
          {askStatus && <p className="status">{askStatus}</p>}
          {askResult && (
            <div className="result-card">
              <div className="result-head">
                <h3>{askResult.question}</h3>
                {askResult.summary && (
                  <button
                    type="button"
                    className="chip-btn"
                    onClick={() => speakText(askResult.summary || "", lang)}
                  >
                    🔊 {chrome(lang, "listen")}
                  </button>
                )}
              </div>
              {!askResult.summary_available && (
                <p className="honest-note">
                  {askResult.message || chrome(lang, "noAnswerYet")}
                </p>
              )}
              {askResult.summary && <p>{askResult.summary}</p>}
              <div style={{ marginTop: 12 }}>
                {askResult.citations.map((c) => (
                  <button
                    key={`${c.chunk_id}-${c.index}`}
                    type="button"
                    className="citation"
                    onClick={() => void openCitation(c)}
                  >
                    [{c.index}] {c.title}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <CitationDrawer
        open={drawerOpen}
        payload={drawer}
        onClose={closeDrawer}
      />
    </PortalShell>
  );
}

export function PortalApp({ tab }: { tab: PortalNav }) {
  return (
    <Suspense
      fallback={
        <div className="portal-shell">
          <p className="muted">Loading…</p>
        </div>
      }
    >
      <PortalAppInner tab={tab} />
    </Suspense>
  );
}
