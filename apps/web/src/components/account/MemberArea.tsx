"use client";
import Link from "next/link";
import { useCallback, useEffect, useState, type CSSProperties } from "react";
import {
  AccountError,
  consumePostLoginIntent,
  savePostLoginIntent,
  useAccount,
} from "./AccountProvider";
import {
  AccountDialog,
  AccountFeedback,
  AccountPanel,
  AccountSyncStatus,
  AccountWallet,
  MEMBER_MESSAGES,
} from "./AccountUI";
import dynamic from "next/dynamic";

const OfficialMissions = dynamic(() => import("./OfficialMissions").then(m => m.OfficialMissions), { ssr: false, loading: () => <div className="account-loader" aria-busy="true" /> });
import { HubProvider, useHub } from "../hub/HubProvider";
import { Header, Footer } from "../hub/Hub";
import { DetailDialog, Ghost, Icon } from "../hub/Primitives";
import {
  categories,
  colors,
  type Category,
  type Language,
} from "../hub/model";
import "../hub/hub.css";
import "./account.css";

export type MemberAreaView =
  | "dashboard"
  | "radar"
  | "backpack"
  | "interests"
  | "exploration"
  | "kp"
  | "wallet"
  | "missions"
  | "mission_detail"
  | "profile";

type CatalogProjection = {
  id?: string;
  discoveryId: string;
  available: boolean;
  savedAt?: string;
  openedAt?: string;
  openCount?: number;
  category?: Category;
  titlePT?: string;
  titleEN?: string;
  summaryPT?: string;
  summaryEN?: string;
  slugPT?: string;
  slugEN?: string;
  sourceName?: string;
  published?: string;
  updatedAt?: string;
  verifiedAt?: string;
};

type DashboardPayload = {
  greetingName: string;
  radar: {
    status: string;
    declaredInterests: Category[];
    totalMatching: number;
    items: CatalogProjection[];
  };
  wallet: {
    programStatus: string;
    available: number;
    reserved: number;
    lifetimeEarned: number;
    pendingCount: number;
  };
  backpack: {
    totalCount: number;
    items: CatalogProjection[];
  };
  nextMission: {
    programStatus: string;
    mission: {
      id: string;
      version: number;
      awardKP: number;
      titlePT?: string;
      titleEN?: string;
      summaryPT?: string;
      summaryEN?: string;
      activeAttempt?: { attemptId: string; expiresAt: string } | null;
      pendingClaim?: {
        pendingId: string;
        awardPreview: number;
        expiresAt: string;
      } | null;
    } | null;
  };
  exploration: {
    territoriesExplored: number;
    territoriesTotal: number;
    totalOpened: number;
    recentItems: CatalogProjection[];
  };
  interests: {
    items: Category[];
    version: number;
    updatedAt?: string | null;
  };
};

function memberMsg(key: string, lang: Language): string {
  const idx = lang === "pt" ? 0 : 1;
  return MEMBER_MESSAGES[key]?.[idx] || MEMBER_MESSAGES.load_failed[idx];
}

function itemHref(item: CatalogProjection, lang: Language): string {
  const slug =
    (lang === "pt" ? item.slugPT : item.slugEN) ||
    item.id ||
    item.discoveryId;
  return `/${lang}/radar/${encodeURIComponent(slug)}/`;
}

function itemTitle(item: CatalogProjection, lang: Language): string {
  return (
    (lang === "pt" ? item.titlePT : item.titleEN) ||
    item.titlePT ||
    item.titleEN ||
    item.discoveryId
  );
}

function itemSummary(item: CatalogProjection, lang: Language): string {
  return (
    (lang === "pt" ? item.summaryPT : item.summaryEN) ||
    item.summaryPT ||
    item.summaryEN ||
    ""
  );
}

function MemberSubnav({
  view,
  lang,
  t,
}: {
  view: MemberAreaView;
  lang: Language;
  t: (pt: string, en: string) => string;
}) {
  const navItems: { key: MemberAreaView; href: string; label: string }[] = [
    {
      key: "dashboard",
      href: `/${lang}/conta/`,
      label: t("Painel do jogador", "Player dashboard"),
    },
    {
      key: "radar",
      href: `/${lang}/conta/radar/`,
      label: t("Seu Radar", "Your Radar"),
    },
    {
      key: "backpack",
      href: `/${lang}/conta/mochila/`,
      label: t("Mochila", "Backpack"),
    },
    {
      key: "interests",
      href: `/${lang}/conta/interesses/`,
      label: t("Interesses", "Interests"),
    },
    {
      key: "exploration",
      href: `/${lang}/conta/exploracao/`,
      label: t("Exploração", "Exploration"),
    },
    {
      key: "kp",
      href: `/${lang}/conta/kp/`,
      label: "Karaca Points",
    },
    {
      key: "wallet",
      href: `/${lang}/conta/carteira/`,
      label: t("Carteira", "Wallet"),
    },
    {
      key: "missions",
      href: `/${lang}/conta/missoes/`,
      label: t("Missões", "Missions"),
    },
    {
      key: "profile",
      href: `/${lang}/conta/perfil/`,
      label: t("Perfil", "Profile"),
    },
  ];
  const activeKey = view === "mission_detail" ? "missions" : view;
  return (
    <nav
      className="member-subnav"
      aria-label={t("Navegação da conta", "Account navigation")}
    >
      {navItems.map((item) => (
        <Link
          key={item.key}
          href={item.href}
          className="member-subnav-link"
          aria-current={activeKey === item.key ? "page" : undefined}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}

function DashboardView() {
  const a = useAccount();
  const { t, lang, labels } = useHub();
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    if (!a.user) return;
    let active = true;
    setState("loading");
    void a
      .request("/api/member/dashboard")
      .then((res) => {
        if (!active) return;
        setData(res as DashboardPayload);
        setState("ready");
      })
      .catch(() => {
        if (active) setState("error");
      });
    return () => {
      active = false;
    };
  }, [a.user?.id, a.request, reload]);

  const msg = (key: string) => memberMsg(key, lang);
  const name =
    data?.greetingName ||
    a.user?.displayName ||
    t("Jogador", "Player");

  return (
    <section aria-labelledby="dashboard-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">
            {t("PAINEL DO JOGADOR", "PLAYER DASHBOARD")}
          </p>
          <h1 id="dashboard-heading">
            {t(`E aí, ${name}.`, `Hey, ${name}.`)}
          </h1>
        </div>
        <div className="member-quick-links">
          <Link href={`/${lang}/conta/perfil/`}>{t("Perfil", "Profile")}</Link>
          <span aria-hidden="true">·</span>
          <Link href={`/${lang}/conta/kp/`}>{t("Regras KP", "KP Rules")}</Link>
          <span aria-hidden="true">·</span>
          <Link href={`/${lang}/transparencia/`}>{t("Ajuda", "Help")}</Link>
        </div>
      </div>

      {state === "loading" && (
        <div className="member-dashboard-grid" role="status" aria-busy="true">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="member-block-card skeleton-card">
              <div className="skeleton-line short" />
              <div className="skeleton-line medium" />
              <div className="skeleton-line long" />
            </div>
          ))}
        </div>
      )}

      {state === "error" && (
        <div className="member-block-card">
          <p>{msg("load_failed")}</p>
          <button
            className="button secondary"
            onClick={() => setReload((n) => n + 1)}
          >
            {t("Tentar novamente", "Try again")}
          </button>
        </div>
      )}

      {state === "ready" && data && (
        <div className="member-dashboard-grid">
          {/* Block 1: Seu Radar */}
          <article className="member-block-card span-2">
            <div className="member-block-head">
              <div>
                <h2>{t("Seu Radar", "Your Radar")}</h2>
              </div>
              <Link className="button secondary" href={`/${lang}/conta/radar/`}>
                {t("Abrir Seu Radar", "Open Your Radar")} →
              </Link>
            </div>
            {data.radar.declaredInterests.length === 0 ? (
              <div className="member-empty-box">
                <p>{msg("interests_empty")}</p>
                <Link className="button" href={`/${lang}/conta/interesses/`}>
                  {t("Escolher interesses", "Choose interests")}
                </Link>
              </div>
            ) : data.radar.items.length === 0 ? (
              <div className="member-empty-box">
                <p>{msg("radar_empty")}</p>
                <Link className="button secondary" href={`/${lang}/radar/`}>
                  {t("Ver todo o Radar", "See all Radar")}
                </Link>
              </div>
            ) : (
              <ul className="member-mini-list">
                {data.radar.items.map((item) => (
                  <li key={item.discoveryId} className="member-mini-item">
                    <div>
                      <span className="member-tag">
                        {item.category ? labels[item.category] : "Radar"}
                      </span>
                      <h3>
                        <Link href={itemHref(item, lang)}>
                          {itemTitle(item, lang)}
                        </Link>
                      </h3>
                      <p>{itemSummary(item, lang)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </article>

          {/* Block 2: KP e Carteira */}
          <article className="member-block-card">
            <div className="member-block-head">
              <div>
                <h2>{t("KP e Carteira", "KP & Wallet")}</h2>
              </div>
              <Link className="button secondary" href={`/${lang}/conta/carteira/`}>
                {t("Carteira", "Wallet")}
              </Link>
            </div>
            {data.wallet.programStatus === "disabled" ? (
              <p className="notice">{msg("kp_disabled")}</p>
            ) : (
              <>
                <p className="account-balance">
                  {data.wallet.available} <small>KP</small>
                </p>
                <p>
                  {t("Disponível", "Available")}:{" "}
                  <strong>{data.wallet.available} KP</strong> ·{" "}
                  {t("Reservado", "Reserved")}:{" "}
                  <strong>{data.wallet.reserved} KP</strong>
                </p>
                <p>
                  {t("Total ganho na conta", "Lifetime earned")}:{" "}
                  <strong>{data.wallet.lifetimeEarned} KP</strong>
                </p>
              </>
            )}
          </article>

          {/* Block 3: Mochila */}
          <article className="member-block-card">
            <div className="member-block-head">
              <div>
                <h2>
                  {t("Mochila", "Backpack")} ({data.backpack.totalCount})
                </h2>
              </div>
              <Link className="button secondary" href={`/${lang}/conta/mochila/`}>
                {t("Ver todos", "See all")}
              </Link>
            </div>
            {data.backpack.items.length === 0 ? (
              <div className="member-empty-box">
                <p>{msg("backpack_empty")}</p>
                <Link className="button secondary" href={`/${lang}/radar/`}>
                  {t("Explorar Radar", "Explore Radar")}
                </Link>
              </div>
            ) : (
              <ul className="member-mini-list">
                {data.backpack.items.map((item) => (
                  <li key={item.discoveryId} className="member-mini-item">
                    {item.available ? (
                      <Link href={itemHref(item, lang)}>
                        {itemTitle(item, lang)}
                      </Link>
                    ) : (
                      <span className="unavailable-text">
                        {msg("content_unavailable")}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </article>

          {/* Block 4: Próxima missão */}
          <article className="member-block-card">
            <div className="member-block-head">
              <div>
                <h2>{t("Próxima missão", "Next mission")}</h2>
              </div>
              <Link className="button secondary" href={`/${lang}/conta/missoes/`}>
                {t("Missões", "Missions")}
              </Link>
            </div>
            {data.nextMission.programStatus === "disabled" ? (
              <p className="notice">{msg("kp_disabled")}</p>
            ) : !data.nextMission.mission ? (
              <p className="notice">{msg("mission_empty")}</p>
            ) : (
              <div>
                <h3>
                  {lang === "pt"
                    ? data.nextMission.mission.titlePT
                    : data.nextMission.mission.titleEN}
                </h3>
                <p>
                  {lang === "pt"
                    ? data.nextMission.mission.summaryPT
                    : data.nextMission.mission.summaryEN}
                </p>
                <p>
                  <strong>{data.nextMission.mission.awardKP} KP</strong>
                </p>
                <Link
                  className="button"
                  href={`/${lang}/conta/missoes/detalhe/?id=${encodeURIComponent(data.nextMission.mission.id)}`}
                >
                  {data.nextMission.mission.pendingClaim
                    ? t("Confirmar resgate de KP", "Confirm KP claim")
                    : data.nextMission.mission.activeAttempt
                      ? t("Retomar missão", "Resume mission")
                      : t("Iniciar missão", "Start mission")}
                </Link>
              </div>
            )}
          </article>

          {/* Block 5: Exploração */}
          <article className="member-block-card">
            <div className="member-block-head">
              <div>
                <h2>{t("Exploração", "Exploration")}</h2>
              </div>
              <Link
                className="button secondary"
                href={`/${lang}/conta/exploracao/`}
              >
                {t("Histórico", "History")}
              </Link>
            </div>
            <p className="member-stat-line">
              <strong>
                {data.exploration.territoriesExplored}/
                {data.exploration.territoriesTotal}
              </strong>{" "}
              {t("territórios explorados", "territories explored")} ·{" "}
              <strong>{data.exploration.totalOpened}</strong>{" "}
              {t("descobertas abertas", "discoveries opened")}
            </p>
            {data.exploration.recentItems.length === 0 ? (
              <p className="notice">{msg("exploration_empty")}</p>
            ) : (
              <ul className="member-mini-list">
                {data.exploration.recentItems.map((item) => (
                  <li key={item.discoveryId} className="member-mini-item">
                    {item.available ? (
                      <Link href={itemHref(item, lang)}>
                        {itemTitle(item, lang)}
                      </Link>
                    ) : (
                      <span className="unavailable-text">
                        {msg("content_unavailable")}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </article>

          {/* Block 6: Seus interesses */}
          <article className="member-block-card">
            <div className="member-block-head">
              <div>
                <h2>{t("Seus interesses", "Your interests")}</h2>
              </div>
              <Link
                className="button secondary"
                href={`/${lang}/conta/interesses/`}
              >
                {t("Editar", "Edit")}
              </Link>
            </div>
            {data.interests.items.length === 0 ? (
              <p className="notice">{msg("interests_empty")}</p>
            ) : (
              <div className="member-chip-row">
                {data.interests.items.map((cat) => (
                  <span key={cat} className="member-topic-badge">
                    <Icon name={cat} /> {labels[cat]}
                  </span>
                ))}
              </div>
            )}
          </article>
        </div>
      )}
    </section>
  );
}

function MemberRadarView() {
  const a = useAccount();
  const { t, lang, labels, toggleSave, player } = useHub();
  const [items, setItems] = useState<CatalogProjection[]>([]);
  const [declaredInterests, setDeclaredInterests] = useState<Category[]>([]);
  const [statusFlag, setStatusFlag] = useState<string>("ok");
  const [tempCategory, setTempCategory] = useState<Category | "all">("all");
  const [temporaryFilterOutsideInterests, setTemporaryFilterOutsideInterests] =
    useState(false);
  const [query, setQuery] = useState("");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const loadRadar = useCallback(
    async (cursor?: string | null, append = false) => {
      if (!a.user) return;
      if (!append) setLoading(true);
      setError(false);
      try {
        const params = new URLSearchParams();
        params.set("limit", "12");
        if (tempCategory !== "all") params.set("category", tempCategory);
        if (query.trim()) params.set("q", query.trim());
        if (cursor) params.set("cursor", cursor);
        const res = await a.request(`/api/member/radar?${params.toString()}`);
        const newItems = Array.isArray(res.items) ? res.items : [];
        setItems((prev) => (append ? [...prev, ...newItems] : newItems));
        setDeclaredInterests(
          Array.isArray(res.declaredInterests) ? res.declaredInterests : [],
        );
        setStatusFlag(typeof res.status === "string" ? res.status : "ok");
        setTemporaryFilterOutsideInterests(
          Boolean(res.temporaryFilterOutsideInterests),
        );
        setNextCursor(typeof res.nextCursor === "string" ? res.nextCursor : null);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    },
    [a.user?.id, a.request, tempCategory, query],
  );

  useEffect(() => {
    void loadRadar(null, false);
  }, [loadRadar]);

  const msg = (key: string) => memberMsg(key, lang);

  return (
    <section aria-labelledby="member-radar-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">{t("SEU RADAR PESSOAL", "YOUR PERSONAL RADAR")}</p>
          <h1 id="member-radar-heading">{t("Seu Radar", "Your Radar")}</h1>
          <p className="lede">
            {t(
              "Recorte das notas publicadas que combinam com seus interesses salvos, da mais recente para a mais antiga.",
              "A feed of published stories matching your saved interests, from newest to oldest.",
            )}
          </p>
        </div>
        <div className="member-quick-links">
          <Link className="button secondary" href={`/${lang}/conta/interesses/`}>
            {t("Editar interesses salvos", "Edit saved interests")}
          </Link>
          <Link className="button secondary" href={`/${lang}/radar/`}>
            {t("Radar completo", "Full Radar")}
          </Link>
        </div>
      </div>

      <div
        className="dock"
        role="group"
        aria-label={t("Filtro temporário de tema", "Temporary topic filter")}
      >
        {(["all", ...categories] as (Category | "all")[]).map((cat) => (
          <button
            key={cat}
            className="category"
            style={
              {
                "--cat": cat === "all" ? "#a8bdff" : colors[cat],
              } as CSSProperties
            }
            aria-pressed={tempCategory === cat}
            onClick={() => setTempCategory(cat)}
          >
            <Icon name={cat} />
            {cat === "all"
              ? t("Meus interesses", "My interests")
              : labels[cat]}
          </button>
        ))}
      </div>

      {temporaryFilterOutsideInterests && tempCategory !== "all" && (
        <p className="notice" role="status">
          {t(
            `Filtro temporário ativo (${labels[tempCategory]}). Seus interesses salvos não foram alterados.`,
            `Temporary filter active (${labels[tempCategory]}). Your saved interests were not changed.`,
          )}
        </p>
      )}

      <label className="radar-search">
        {t("Buscar no Seu Radar", "Search Your Radar")}
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("Games, IA, gadgets…", "Games, AI, gadgets…")}
        />
      </label>

      {loading ? (
        <div className="account-loader" role="status" aria-busy="true">
          <span className="account-spinner" aria-hidden="true" />
          <p>{t("Atualizando Seu Radar…", "Updating Your Radar…")}</p>
        </div>
      ) : error ? (
        <div className="member-block-card">
          <p>{msg("load_failed")}</p>
          <button
            className="button secondary"
            onClick={() => void loadRadar(null, false)}
          >
            {t("Tentar novamente", "Try again")}
          </button>
        </div>
      ) : statusFlag === "interests_empty" && tempCategory === "all" ? (
        <div className="member-block-card">
          <h2>{t("Personalize seu Radar", "Personalize your Radar")}</h2>
          <p>{msg("interests_empty")}</p>
          <div className="account-actions">
            <Link className="button" href={`/${lang}/conta/interesses/`}>
              {t("Escolher interesses", "Choose interests")}
            </Link>
            <Link className="button secondary" href={`/${lang}/radar/`}>
              {t("Explorar todas as notícias", "Explore all stories")}
            </Link>
          </div>
        </div>
      ) : items.length === 0 ? (
        <div className="member-block-card">
          <p>{msg("radar_empty")}</p>
          {declaredInterests.length > 0 && tempCategory !== "all" && (
            <button
              className="button secondary"
              onClick={() => setTempCategory("all")}
            >
              {t("Voltar aos meus interesses", "Back to my interests")}
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="member-card-list" aria-live="polite">
            {items.map((item) => {
              const saved = player.saved.includes(item.discoveryId);
              return (
                <article
                  key={item.discoveryId}
                  className="member-content-card"
                >
                  <div className="member-content-body">
                    <span className="member-tag">
                      {item.category ? labels[item.category] : "Radar"}
                    </span>
                    <h3>
                      <Link href={itemHref(item, lang)}>
                        {itemTitle(item, lang)}
                      </Link>
                    </h3>
                    <p>{itemSummary(item, lang)}</p>
                    <small>
                      {item.sourceName} · {item.published}
                    </small>
                  </div>
                  <div className="member-content-actions">
                    <button
                      type="button"
                      className="button secondary"
                      aria-pressed={saved}
                      onClick={() => void toggleSave(item.discoveryId)}
                    >
                      <Icon name={saved ? "check" : "save"} />
                      {saved
                        ? t("Na mochila", "In backpack")
                        : t("Guardar", "Save")}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
          {nextCursor && (
            <button
              className="button secondary"
              onClick={() => void loadRadar(nextCursor, true)}
            >
              {t("Carregar mais", "Load more")}
            </button>
          )}
        </>
      )}
    </section>
  );
}

function BackpackView() {
  const a = useAccount();
  const { t, lang, labels, undoRemoveBookmark } = useHub();
  const [items, setItems] = useState<CatalogProjection[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [categoryFilter, setCategoryFilter] = useState<Category | "all">("all");
  const [query, setQuery] = useState("");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [lastRemovedId, setLastRemovedId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [confirmBatchRemove, setConfirmBatchRemove] = useState(false);

  const loadBackpack = useCallback(
    async (cursor?: string | null, append = false) => {
      if (!a.user) return;
      if (!append) setLoading(true);
      setError(false);
      try {
        const params = new URLSearchParams();
        params.set("limit", "20");
        if (categoryFilter !== "all") params.set("category", categoryFilter);
        if (query.trim()) params.set("q", query.trim());
        if (cursor) params.set("cursor", cursor);
        const res = await a.request(
          `/api/member/backpack?${params.toString()}`,
        );
        const newItems = Array.isArray(res.items) ? res.items : [];
        setItems((prev) => (append ? [...prev, ...newItems] : newItems));
        setTotalCount(
          typeof res.totalCount === "number" ? res.totalCount : newItems.length,
        );
        setNextCursor(typeof res.nextCursor === "string" ? res.nextCursor : null);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    },
    [a.user?.id, a.request, categoryFilter, query],
  );

  useEffect(() => {
    void loadBackpack(null, false);
  }, [loadBackpack]);

  async function removeOne(discoveryId: string) {
    await a.action(async () => {
      await a.request(
        `/api/member/backpack/${encodeURIComponent(discoveryId)}`,
        "DELETE",
        {},
      );
      setItems((prev) => prev.filter((x) => x.discoveryId !== discoveryId));
      setTotalCount((n) => Math.max(0, n - 1));
      setSelectedIds((prev) => prev.filter((id) => id !== discoveryId));
      setLastRemovedId(discoveryId);
      await a.refresh();
      a.notifySync("collections_updated");
    });
  }

  async function handleUndo() {
    if (!lastRemovedId) return;
    const id = lastRemovedId;
    setLastRemovedId(null);
    void undoRemoveBookmark();
    await a.action(async () => {
      await a.request(
        `/api/member/backpack/${encodeURIComponent(id)}`,
        "PUT",
        {},
      );
      await loadBackpack(null, false);
      await a.refresh();
      a.notifySync("collections_updated");
    });
  }

  async function removeBatch() {
    if (selectedIds.length === 0) return;
    const idsToRemove = [...selectedIds];
    await a.action(async () => {
      for (const id of idsToRemove) {
        await a.request(
          `/api/member/backpack/${encodeURIComponent(id)}`,
          "DELETE",
          {},
        );
      }
      setSelectedIds([]);
      setConfirmBatchRemove(false);
      await loadBackpack(null, false);
      await a.refresh();
      a.notifySync("collections_updated");
    });
  }

  const msg = (key: string) => memberMsg(key, lang);

  return (
    <section aria-labelledby="backpack-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">{t("COLEÇÃO PESSOAL", "PERSONAL COLLECTION")}</p>
          <h1 id="backpack-heading">
            {t("Minha Mochila", "My Backpack")} ({totalCount})
          </h1>
          <p className="lede">
            {t(
              "Itens guardados na sua conta para ler, comparar e revisitar quando quiser.",
              "Items saved in your account to read, compare and revisit anytime.",
            )}
          </p>
        </div>
      </div>

      {lastRemovedId && (
        <div className="account-success" role="status">
          <span>{msg("bookmark_removed")} </span>
          <button className="button secondary" onClick={() => void handleUndo()}>
            {t("Desfazer", "Undo")}
          </button>
        </div>
      )}

      <div
        className="dock"
        role="group"
        aria-label={t("Filtrar mochila por categoria", "Filter backpack by category")}
      >
        {(["all", ...categories] as (Category | "all")[]).map((cat) => (
          <button
            key={cat}
            className="category"
            style={
              {
                "--cat": cat === "all" ? "#a8bdff" : colors[cat],
              } as CSSProperties
            }
            aria-pressed={categoryFilter === cat}
            onClick={() => setCategoryFilter(cat)}
          >
            <Icon name={cat} />
            {labels[cat]}
          </button>
        ))}
      </div>

      <label className="radar-search">
        {t("Buscar na mochila", "Search backpack")}
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("Filtrar itens salvos…", "Filter saved items…")}
        />
      </label>

      {selectedIds.length > 0 && (
        <div
          className="member-batch-bar"
          role="region"
          aria-label={t("Ações em lote", "Batch actions")}
        >
          <span>
            <strong>{selectedIds.length}</strong>{" "}
            {t("selecionado(s)", "selected")}
          </span>
          {!confirmBatchRemove ? (
            <button
              className="button secondary"
              onClick={() => setConfirmBatchRemove(true)}
            >
              {t("Remover selecionados", "Remove selected")}
            </button>
          ) : (
            <div className="account-actions">
              <span>
                {t(
                  `Confirmar remoção de ${selectedIds.length} item(ns)?`,
                  `Confirm removing ${selectedIds.length} item(s)?`,
                )}
              </span>
              <button
                className="button"
                disabled={a.busy}
                onClick={() => void removeBatch()}
              >
                {t("Confirmar remoção", "Confirm removal")}
              </button>
              <button
                className="quiet"
                onClick={() => setConfirmBatchRemove(false)}
              >
                {t("Cancelar", "Cancel")}
              </button>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="account-loader" role="status" aria-busy="true">
          <span className="account-spinner" aria-hidden="true" />
          <p>{t("Abrindo sua mochila…", "Opening your backpack…")}</p>
        </div>
      ) : error ? (
        <div className="member-block-card">
          <p>{msg("load_failed")}</p>
          <button
            className="button secondary"
            onClick={() => void loadBackpack(null, false)}
          >
            {t("Tentar novamente", "Try again")}
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="member-block-card">
          <p>{msg("backpack_empty")}</p>
          <Link className="button" href={`/${lang}/radar/`}>
            {t("Explorar o Radar", "Explore the Radar")}
          </Link>
        </div>
      ) : (
        <>
          <div className="member-card-list" aria-live="polite">
            {items.map((item) => {
              const checked = selectedIds.includes(item.discoveryId);
              return (
                <article
                  key={item.discoveryId}
                  className="member-content-card"
                >
                  <div className="member-content-select">
                    <input
                      type="checkbox"
                      aria-label={
                        item.available
                          ? `${t("Selecionar", "Select")} ${itemTitle(item, lang)}`
                          : `${t("Selecionar item indisponível", "Select unavailable item")} ${item.discoveryId}`
                      }
                      checked={checked}
                      onChange={() =>
                        setSelectedIds((prev) =>
                          prev.includes(item.discoveryId)
                            ? prev.filter((id) => id !== item.discoveryId)
                            : [...prev, item.discoveryId],
                        )
                      }
                    />
                  </div>
                  <div className="member-content-body">
                    {item.available ? (
                      <>
                        <span className="member-tag">
                          {item.category ? labels[item.category] : "Radar"}
                        </span>
                        <h3>
                          <Link href={itemHref(item, lang)}>
                            {itemTitle(item, lang)}
                          </Link>
                        </h3>
                        <p>{itemSummary(item, lang)}</p>
                        <small>
                          {item.sourceName} ·{" "}
                          {t("Salvo em", "Saved on")}{" "}
                          {item.savedAt
                            ? new Date(item.savedAt).toLocaleDateString(
                                lang === "pt" ? "pt-BR" : "en-US",
                              )
                            : ""}
                        </small>
                      </>
                    ) : (
                      <div className="unavailable-placeholder">
                        <p className="eyebrow">
                          {t("ITEM INDISPONÍVEL", "UNAVAILABLE ITEM")}
                        </p>
                        <p>{msg("content_unavailable")}</p>
                      </div>
                    )}
                  </div>
                  <div className="member-content-actions">
                    <button
                      type="button"
                      className="button secondary"
                      disabled={a.busy}
                      onClick={() => void removeOne(item.discoveryId)}
                    >
                      {t("Remover da mochila", "Remove from backpack")}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
          {nextCursor && (
            <button
              className="button secondary"
              onClick={() => void loadBackpack(nextCursor, true)}
            >
              {t("Carregar mais", "Load more")}
            </button>
          )}
        </>
      )}
    </section>
  );
}

function InterestsView() {
  const a = useAccount();
  const { t, lang, labels } = useHub();
  const [serverInterests, setServerInterests] = useState<Category[]>([]);
  const [draftInterests, setDraftInterests] = useState<Category[]>([]);
  const [version, setVersion] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [conflict, setConflict] = useState(false);
  const [savedBanner, setSavedBanner] = useState(false);

  const loadInterests = useCallback(async () => {
    if (!a.user) return;
    setLoading(true);
    setConflict(false);
    try {
      const res = await a.request("/api/member/interests");
      const rawList = Array.isArray(res.interests)
        ? res.interests
        : Array.isArray(res.categoryIds)
          ? res.categoryIds
          : [];
      const list = rawList as Category[];
      setServerInterests(list);
      setDraftInterests(list);
      setVersion(typeof res.version === "number" ? res.version : 1);
    } finally {
      setLoading(false);
    }
  }, [a.user?.id, a.request]);

  useEffect(() => {
    void loadInterests();
  }, [loadInterests]);

  const isDirty =
    draftInterests.length !== serverInterests.length ||
    draftInterests.some((c) => !serverInterests.includes(c));

  useEffect(() => {
    if (!isDirty) return;
    function onBeforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault();
      e.returnValue = "";
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [isDirty]);

  function toggleDraft(cat: Category) {
    setSavedBanner(false);
    setDraftInterests((prev) =>
      prev.includes(cat) ? prev.filter((x) => x !== cat) : [...prev, cat],
    );
  }

  async function save() {
    setSavedBanner(false);
    setConflict(false);
    try {
      const res = await a.request("/api/member/interests", "PUT", {
        interests: draftInterests,
        categoryIds: draftInterests,
        expectedVersion: version,
      });
      const updated = Array.isArray(res.interests)
        ? (res.interests as Category[])
        : draftInterests;
      setServerInterests(updated);
      setDraftInterests(updated);
      setVersion(typeof res.version === "number" ? res.version : version + 1);
      setSavedBanner(true);
      await a.refresh();
      a.notifySync("collections_updated");
    } catch (err) {
      if (
        err instanceof AccountError &&
        (err.code === "interests_conflict" || err.status === 409)
      ) {
        setConflict(true);
      }
    }
  }

  const msg = (key: string) => memberMsg(key, lang);

  return (
    <section aria-labelledby="interests-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">
            {t("PREFERÊNCIAS EDITORIAIS", "EDITORIAL PREFERENCES")}
          </p>
          <h1 id="interests-heading">
            {t("Seus interesses", "Your interests")}
          </h1>
          <p className="lede">
            {t(
              "Escolha os temas que compõem o Seu Radar. Você pode selecionar quantos quiser ou deixar todos desmarcados.",
              "Choose the topics that shape Your Radar. Select as many as you like or leave all unchecked.",
            )}
          </p>
        </div>
      </div>

      {savedBanner && (
        <p className="account-success" role="status">
          {msg("interests_saved")}
        </p>
      )}

      {conflict && (
        <div className="account-error" role="alert">
          <p>{msg("interests_conflict")}</p>
          <button
            type="button"
            className="button secondary"
            onClick={() => void loadInterests()}
          >
            {t("Revisar seleção", "Review selection")}
          </button>
        </div>
      )}

      {loading ? (
        <div className="account-loader" role="status" aria-busy="true">
          <span className="account-spinner" aria-hidden="true" />
          <p>{t("Carregando interesses…", "Loading interests…")}</p>
        </div>
      ) : (
        <div className="member-block-card">
          <div
            className="member-interests-grid"
            role="group"
            aria-label={t("Temas disponíveis", "Available topics")}
          >
            {categories.map((cat) => {
              const selected = draftInterests.includes(cat);
              return (
                <button
                  key={cat}
                  type="button"
                  className={`member-interest-tile ${selected ? "selected" : ""}`}
                  aria-pressed={selected}
                  onClick={() => toggleDraft(cat)}
                >
                  <span className="member-interest-icon">
                    <Icon name={cat} />
                  </span>
                  <span className="member-interest-name">{labels[cat]}</span>
                  <span className="member-interest-state">
                    {selected
                      ? `✓ ${t("Selecionado", "Selected")}`
                      : t("Não selecionado", "Not selected")}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="account-actions">
            <button
              type="button"
              className="button"
              disabled={a.busy || !isDirty}
              onClick={() => void save()}
            >
              {t("Salvar interesses", "Save interests")}
            </button>
            <button
              type="button"
              className="button secondary"
              disabled={a.busy || !isDirty}
              onClick={() => {
                setDraftInterests(serverInterests);
                setSavedBanner(false);
              }}
            >
              {t("Cancelar", "Cancel")}
            </button>
            <Link className="button secondary" href={`/${lang}/conta/radar/`}>
              {t("Ver Seu Radar →", "View Your Radar →")}
            </Link>
          </div>
        </div>
      )}
    </section>
  );
}

function ExplorationView() {
  const a = useAccount();
  const { t, lang, labels } = useHub();
  const [items, setItems] = useState<CatalogProjection[]>([]);
  const [territoriesExplored, setTerritoriesExplored] = useState(0);
  const [territoriesTotal, setTerritoriesTotal] = useState(6);
  const [totalOpened, setTotalOpened] = useState(0);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirmClear, setConfirmClear] = useState(false);

  const loadExploration = useCallback(
    async (cursor?: string | null, append = false) => {
      if (!a.user) return;
      if (!append) setLoading(true);
      try {
        const params = new URLSearchParams();
        params.set("limit", "20");
        if (cursor) params.set("cursor", cursor);
        const res = await a.request(
          `/api/member/exploration?${params.toString()}`,
        );
        const newItems = Array.isArray(res.items) ? res.items : [];
        setItems((prev) => (append ? [...prev, ...newItems] : newItems));
        setTerritoriesExplored(
          typeof res.territoriesExplored === "number"
            ? res.territoriesExplored
            : 0,
        );
        setTerritoriesTotal(
          typeof res.territoriesTotal === "number" ? res.territoriesTotal : 6,
        );
        setTotalOpened(
          typeof res.totalOpened === "number"
            ? res.totalOpened
            : newItems.length,
        );
        setNextCursor(typeof res.nextCursor === "string" ? res.nextCursor : null);
      } finally {
        setLoading(false);
      }
    },
    [a.user?.id, a.request],
  );

  useEffect(() => {
    void loadExploration(null, false);
  }, [loadExploration]);

  async function removeEntry(discoveryId: string) {
    await a.action(async () => {
      await a.request(
        `/api/member/exploration/${encodeURIComponent(discoveryId)}`,
        "DELETE",
        {},
      );
      await loadExploration(null, false);
      await a.refresh();
      a.notifySync("collections_updated");
    });
  }

  async function clearAll() {
    await a.action(async () => {
      await a.request("/api/member/exploration/clear", "POST", {
        confirm: true,
        expectedGeneration: a.user?.explorationGeneration || 1,
      });
      setConfirmClear(false);
      await loadExploration(null, false);
      await a.refresh();
      a.notifySync("collections_updated");
    });
  }

  const msg = (key: string) => memberMsg(key, lang);

  return (
    <section aria-labelledby="exploration-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">{t("MEMÓRIA DE LEITURA", "READING MEMORY")}</p>
          <h1 id="exploration-heading">
            {t("Exploração e Passaporte", "Exploration & Passport")}
          </h1>
          <p className="lede">
            {t(
              "Seu mapa de descobertas. Este histórico registra o que você abriu, sem conceder KP automaticamente.",
              "Your discovery map. This history records what you opened, without awarding KP automatically.",
            )}
          </p>
        </div>
        {items.length > 0 && !confirmClear && (
          <button
            type="button"
            className="button secondary"
            onClick={() => setConfirmClear(true)}
          >
            {t("Limpar histórico", "Clear history")}
          </button>
        )}
      </div>

      {confirmClear && (
        <div
          className="member-block-card"
          role="alertdialog"
          aria-labelledby="clear-history-title"
        >
          <h2 id="clear-history-title">
            {t("Confirmar limpeza do histórico", "Confirm clearing history")}
          </h2>
          <p>{msg("history_clear_confirm")}</p>
          <div className="account-actions">
            <button
              type="button"
              className="button"
              disabled={a.busy}
              onClick={() => void clearAll()}
            >
              {t("Sim, limpar histórico", "Yes, clear history")}
            </button>
            <button
              type="button"
              className="button secondary"
              onClick={() => setConfirmClear(false)}
            >
              {t("Cancelar", "Cancel")}
            </button>
          </div>
        </div>
      )}

      <div className="member-block-card">
        <h2>{t("Progresso por território", "Territory progress")}</h2>
        <p className="member-stat-line">
          <strong>
            {territoriesExplored} / {territoriesTotal}
          </strong>{" "}
          {t("territórios visitados", "territories visited")} ·{" "}
          <strong>{totalOpened}</strong>{" "}
          {t("descobertas abertas", "discoveries opened")}
        </p>
      </div>

      {loading ? (
        <div className="account-loader" role="status" aria-busy="true">
          <span className="account-spinner" aria-hidden="true" />
          <p>{t("Carregando histórico…", "Loading history…")}</p>
        </div>
      ) : items.length === 0 ? (
        <div className="member-block-card">
          <p>{msg("exploration_empty")}</p>
          <Link className="button" href={`/${lang}/radar/`}>
            {t("Explorar o Radar", "Explore the Radar")}
          </Link>
        </div>
      ) : (
        <>
          <div className="member-card-list" aria-live="polite">
            {items.map((item) => (
              <article key={item.discoveryId} className="member-content-card">
                <div className="member-content-body">
                  {item.available ? (
                    <>
                      <span className="member-tag">
                        {item.category ? labels[item.category] : "Radar"}
                      </span>
                      <h3>
                        <Link href={itemHref(item, lang)}>
                          {itemTitle(item, lang)}
                        </Link>
                      </h3>
                      <p>{itemSummary(item, lang)}</p>
                      <small>
                        {t("Lido em", "Read on")}{" "}
                        {item.openedAt
                          ? new Date(item.openedAt).toLocaleDateString(
                              lang === "pt" ? "pt-BR" : "en-US",
                            )
                          : ""}
                      </small>
                    </>
                  ) : (
                    <div className="unavailable-placeholder">
                      <p>{msg("content_unavailable")}</p>
                    </div>
                  )}
                </div>
                <div className="member-content-actions">
                  <button
                    type="button"
                    className="button secondary"
                    disabled={a.busy}
                    onClick={() => void removeEntry(item.discoveryId)}
                  >
                    {t("Remover do histórico", "Remove from history")}
                  </button>
                </div>
              </article>
            ))}
          </div>
          {nextCursor && (
            <button
              className="button secondary"
              onClick={() => void loadExploration(nextCursor, true)}
            >
              {t("Carregar mais", "Load more")}
            </button>
          )}
        </>
      )}
    </section>
  );
}

function KPProgramView() {
  const a = useAccount();
  const { t, lang } = useHub();
  const programStatus =
    a.capabilities.kpProgramState ||
    (a.capabilities.rewards ? "active" : "disabled");
  const msg = (key: string) => memberMsg(key, lang);

  return (
    <section aria-labelledby="kp-program-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">KARACA POINTS</p>
          <h1 id="kp-program-heading">
            {t("Programa Karaca Points", "Karaca Points Program")}
          </h1>
          <p className="lede">
            {t(
              "Pontos oficiais conquistados em missões verificadas pelo servidor na sua conta AnderZilla.",
              "Official points earned through server-validated missions in your AnderZilla account.",
            )}
          </p>
        </div>
        <div className="member-quick-links">
          <Link className="button" href={`/${lang}/conta/carteira/`}>
            {t("Abrir Carteira", "Open Wallet")}
          </Link>
          <Link className="button secondary" href={`/${lang}/conta/missoes/`}>
            {t("Missões oficiais", "Official missions")}
          </Link>
        </div>
      </div>

      <div className="member-block-card">
        <h2>{t("Status operacional do programa", "Program operational status")}</h2>
        <p className="member-stat-line">
          {programStatus === "active"
            ? t("Ativo para contas verificadas", "Active for verified accounts")
            : programStatus === "new_activity_paused"
              ? msg("mission_paused")
              : programStatus === "maintenance"
                ? msg("warming")
                : msg("kp_disabled")}
        </p>
      </div>

      <div className="member-block-card">
        <h2>{t("Regras essenciais", "Essential rules")}</h2>
        <ul className="member-rules-list">
          <li>
            {t(
              "Karaca Points (KP) não são dinheiro, valor mobiliário, depósito, criptoativo ou crédito financeiro.",
              "Karaca Points (KP) are not money, securities, deposits, cryptoassets or financial credit.",
            )}
          </li>
          <li>
            {t(
              "KP não podem ser comprados, vendidos, transferidos entre contas ou convertidos em dinheiro.",
              "KP cannot be bought, sold, transferred between accounts or converted into cash.",
            )}
          </li>
          <li>
            {t(
              "Somente contas autenticadas de maiores de 18 anos com e-mail verificado e cadastro completo participam de missões oficiais.",
              "Only authenticated 18+ accounts with verified email and completed registration participate in official missions.",
            )}
          </li>
          <li>
            {t(
              "Abrir notícias ou usar atividades demonstrativas locais nunca gera crédito de KP.",
              "Opening news stories or using local demo activities never credits KP.",
            )}
          </li>
        </ul>
      </div>
    </section>
  );
}

function WalletDetailView() {
  const a = useAccount();
  const { t, lang } = useHub();
  const [reasonFilter, setReasonFilter] = useState<string>("all");
  const [entries, setEntries] = useState<
    {
      id: string;
      reason: string;
      availableDelta: number;
      reservedDelta: number;
      createdAt: string;
      referenceId?: string;
    }[]
  >([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadLedger = useCallback(
    async (cursor?: string | null, append = false) => {
      if (!a.user) return;
      if (!append) setLoading(true);
      try {
        const params = new URLSearchParams();
        params.set("limit", "20");
        if (reasonFilter !== "all") params.set("reason", reasonFilter);
        if (cursor) params.set("cursor", cursor);
        const res = await a.request(
          `/api/points/ledger?${params.toString()}`,
        );
        const rawList = Array.isArray(res.entries)
          ? res.entries
          : Array.isArray(res.items)
            ? res.items
            : [];
        const list = rawList.map((r: any) => ({
          id: String(r.id || ""),
          reason: String(r.reason || r.description || "mission"),
          availableDelta:
            typeof r.availableDelta === "number"
              ? r.availableDelta
              : Number(r.available_delta ?? r.amount ?? 0),
          reservedDelta:
            typeof r.reservedDelta === "number"
              ? r.reservedDelta
              : Number(r.reserved_delta ?? r.reservedAmount ?? 0),
          createdAt:
            typeof r.created_at === "number"
              ? new Date(r.created_at * 1000).toISOString()
              : String(r.createdAt || r.created_at || new Date().toISOString()),
          referenceId: r.referenceId || r.reference_id || r.missionId,
        }));
        setEntries((prev) => (append ? [...prev, ...list] : list));
        setNextCursor(typeof res.nextCursor === "string" ? res.nextCursor : null);
      } finally {
        setLoading(false);
      }
    },
    [a.user?.id, a.request, reasonFilter],
  );

  useEffect(() => {
    void loadLedger(null, false);
  }, [loadLedger]);

  return (
    <section aria-labelledby="wallet-detail-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">{t("SALDO E EXTRATO", "BALANCE & LEDGER")}</p>
          <h1 id="wallet-detail-heading">
            {t("Carteira e Extrato KP", "KP Wallet & Ledger")}
          </h1>
        </div>
        <Link className="button secondary" href={`/${lang}/conta/missoes/`}>
          {t("Missões oficiais", "Official missions")} →
        </Link>
      </div>

      <AccountWallet />

      <div className="member-block-card">
        <div className="member-block-head">
          <h2>{t("Extrato auditável", "Auditable ledger")}</h2>
          <div
            className="member-chip-row"
            role="group"
            aria-label={t("Filtrar extrato", "Filter ledger")}
          >
            {[
              ["all", t("Todos", "All")],
              ["mission", t("Missões", "Missions")],
            ].map(([val, label]) => (
              <button
                key={val}
                type="button"
                className="button secondary"
                aria-pressed={reasonFilter === val}
                onClick={() => setReasonFilter(val)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        {loading ? (
          <p role="status">{t("Carregando extrato…", "Loading ledger…")}</p>
        ) : entries.length === 0 ? (
          <p className="notice">
            {t(
              "Nenhuma movimentação registrada ainda.",
              "No activity yet.",
            )}
          </p>
        ) : (
          <ul className="member-mini-list">
            {entries.map((entry) => (
              <li key={entry.id} className="member-mini-item">
                <div>
                  <strong>
                    {entry.availableDelta >= 0
                      ? `+${entry.availableDelta}`
                      : entry.availableDelta}{" "}
                    KP
                  </strong>{" "}
                  · {entry.reason === "mission" ? t("Missão concluída", "Mission completed") : t("Movimentação de KP", "KP activity")}
                  {entry.referenceId ? ` (${entry.referenceId})` : ""}
                  <br />
                  <small>
                    {new Date(entry.createdAt).toLocaleString(
                      lang === "pt" ? "pt-BR" : "en-US",
                    )}
                  </small>
                </div>
              </li>
            ))}
          </ul>
        )}
        {nextCursor && (
          <button
            className="button secondary"
            onClick={() => void loadLedger(nextCursor, true)}
          >
            {t("Carregar mais", "Load more")}
          </button>
        )}
      </div>
    </section>
  );
}

function ProfileView() {
  const { t } = useHub();
  return (
    <section aria-labelledby="profile-view-heading">
      <div className="member-dashboard-header">
        <div>
          <p className="eyebrow">{t("DADOS E PRIVACIDADE", "DATA & PRIVACY")}</p>
          <h1 id="profile-view-heading">
            {t("Perfil, Segurança e Privacidade", "Profile, Security & Privacy")}
          </h1>
          <p className="lede">
            {t(
              "Gerencie seu perfil, preferências de comunicação, exportação de dados e exclusão da conta.",
              "Manage your profile, communication preferences, data export and account deletion.",
            )}
          </p>
        </div>
      </div>
      <AccountPanel />
    </section>
  );
}

function MemberAreaContent({
  view,
  missionId,
}: {
  view: MemberAreaView;
  missionId?: string;
}) {
  const account = useAccount();
  const { t, lang, toast } = useHub();
  const [resolvedMissionId, setResolvedMissionId] = useState(missionId === "detalhe" ? undefined : missionId);
  useEffect(() => {
    if (missionId !== "detalhe") return;
    const value = new URLSearchParams(window.location.search).get("id");
    setResolvedMissionId(value && /^[A-Za-z0-9_.:-]{1,64}$/.test(value) ? value : undefined);
  }, [missionId]);

  useEffect(() => {
    if (!account.user) return;
    const intent = consumePostLoginIntent();
    if (
      intent &&
      intent.type === "route" &&
      intent.path &&
      typeof window !== "undefined" &&
      intent.path !== window.location.pathname
    ) {
      window.location.assign(intent.path);
    }
  }, [account.user]);

  const msg = (key: string) => memberMsg(key, lang);

  return (
    <div className="hub">
      <a className="skip" href="#member-main">
        {t("Pular para o conteúdo", "Skip to content")}
      </a>
      <Header />
      <AccountSyncStatus />
      <main id="member-main" className="wrap member-area-main" tabIndex={-1}>
        <MemberSubnav view={view} lang={lang} t={t} />

        {!account.user && (account.status === "loading" || account.profileStatus === "loading") ? (
          <div className="account-loader" role="status" aria-busy="true">
            <span className="account-spinner" aria-hidden="true" />
            <p>{t("Verificando sua sessão…", "Verifying your session…")}</p>
          </div>
        ) : !account.user && (account.profileStatus === "waking" || account.profileStatus === "error" || account.status === "unavailable") ? (
          <div className="member-block-card" role="status">
            <h2>{t("Conectando à sua conta", "Connecting to your account")}</h2>
            <p>{msg(account.profileStatus === "error" || account.status === "unavailable" ? "load_failed" : "warming")}</p>
            <button
              className="button secondary"
              onClick={() => void account.reconnect()}
            >
              {t("Tentar novamente", "Try again")}
            </button>
          </div>
        ) : !account.user ? (
          <div className="member-block-card member-gate-card">
            <Ghost size={56} />
            <h1>
              {account.onboardingRequired
                ? t("Falta concluir seu cadastro", "Complete your registration")
                : t("Área exclusiva para membros", "Members-only area")}
            </h1>
            <p>
              {account.onboardingRequired
                ? msg("complete_account")
                : account.signedIn
                  ? msg("session_expired")
                  : msg("member_required")}
            </p>
            <div className="account-actions">
              <button
                type="button"
                className="button"
                onClick={() => {
                  if (typeof window !== "undefined") {
                    savePostLoginIntent({
                      type: "route",
                      path: `${window.location.pathname}${window.location.search}`,
                    });
                  }
                  account.open(
                    account.onboardingRequired ? "onboarding" : "login",
                  );
                }}
              >
                {account.onboardingRequired
                  ? t("Completar cadastro", "Complete registration")
                  : t("Entrar na conta", "Sign in to account")}
              </button>
              <Link className="button secondary" href={`/${lang}/radar/`}>
                {t("Voltar ao Radar público", "Back to public Radar")}
              </Link>
            </div>
            <AccountFeedback />
          </div>
        ) : (
          <>
            {view === "dashboard" && <DashboardView />}
            {view === "radar" && <MemberRadarView />}
            {view === "backpack" && <BackpackView />}
            {view === "interests" && <InterestsView />}
            {view === "exploration" && <ExplorationView />}
            {view === "kp" && <KPProgramView />}
            {view === "wallet" && <WalletDetailView />}
            {view === "missions" && <OfficialMissions />}
            {view === "mission_detail" && (
              <OfficialMissions focusMissionId={resolvedMissionId} />
            )}
            {view === "profile" && <ProfileView />}
          </>
        )}
      </main>
      <Footer />
      <DetailDialog />
      <AccountDialog />
      <div id="toast" role="status" className={toast ? "show" : ""}>
        {toast}
      </div>
    </div>
  );
}

export function MemberArea({
  lang,
  view,
  missionId,
}: {
  lang: Language;
  view: MemberAreaView;
  missionId?: string;
}) {
  return (

      <HubProvider initialLang={lang}>
        <MemberAreaContent view={view} missionId={missionId} />
      </HubProvider>

  );
}
