"use client";
import Link from "next/link";
import { useState, type CSSProperties } from "react";
import { BrandWordmark } from "../BrandAssets";
import { HubProvider, useHub } from "./HubProvider";
import {
  categories,
  colors,
  compareRadarNewestFirst,
  discoveries,
  socials,
  type Category,
  type Route,
} from "./model";
import {
  DetailDialog,
  DiscoveryCard,
  External,
  Ghost,
  Icon,
  Passport,
} from "./Primitives";
import {
  AgendaPage,
  ChannelsPage,
  LivePage,
  LiveRoom,
  SponsorPage,
} from "./Community";
import {
  PointsPage,
  PointsTeaser,
  ProfilePage,
  QuizPage,
  StorePage,
} from "./Rewards";
import "./hub.css";
import { CMSSections } from "./CMSSections";
import { HeroCarousel } from "./HeroCarousel";
import { CommerceHome } from "../commerce/CommerceHome";
import { flag } from "../commerce/data";
import { useAccount } from "../account/AccountProvider";
import {
  AccountAccess,
  AccountDialog,
  AccountSyncStatus,
} from "../account/AccountUI";

export function Header() {
  const { t, lang, changeLanguage, route } = useHub();
  const links: [Route, string][] = [["home", t("Explorar", "Explore")]];
  return (
    <>
      <div className="preview">
        <span>
          {t("GAMES · IA · TECNOLOGIA", "GAMES · AI · TECHNOLOGY")}
        </span>
        <div className="languages" aria-label="Language">
          <button
            aria-pressed={lang === "pt"}
            onClick={() => changeLanguage("pt")}
          >
            PT
          </button>
          <span>/</span>
          <button
            aria-pressed={lang === "en"}
            onClick={() => changeLanguage("en")}
          >
            EN
          </button>
        </div>
      </div>
      <header>
        <Link className="brand" href={`/${lang}/#home`}>
          <div>
            <BrandWordmark />
            <small>
              {t(
                "GAMES. TECH. BOAS DESCOBERTAS.",
                "GAMES. TECH. GREAT FINDS.",
              )}
            </small>
          </div>
        </Link>
        <nav aria-label={t("Principal", "Main")}>
          {links.map(([r, label]) => (
            <Link
              href={`/${lang}/#${r}`}
              key={r}
              aria-current={route === r ? "page" : undefined}
            >
              {label}
            </Link>
          ))}
          <Link href={`/${lang}/?category=ia#home`}>{t("IA", "AI")}</Link>
          <Link href={`/${lang}/?category=games#home`}>Games</Link>
          <Link href={`/${lang}/?category=gadgets#home`}>Gadgets</Link>
          <Link href={`/${lang}/stackpick/`}>StackPick</Link>
          <Link href={`/${lang}/produtos/`}>{t("Produtos", "Products")}</Link>
          <Link href={`/${lang}/patrocine/`}>{t("Patrocine", "Sponsor")}</Link>
        </nav>
        <div className="actions">
          <AccountAccess />
        </div>
      </header>
    </>
  );
}

export function Footer() {
  const { t, lang } = useHub();
  return (
    <footer>
      <Link className="brand-footer" href={`/${lang}/#home`}>
        <BrandWordmark />
      </Link>
      <p>
        {t(
          "Um esconderijo para quem gosta de games e de fuçar no futuro.",
          "A hideout for people who love games and tinkering with the future.",
        )}
      </p>
      <Link href={`/${lang}/#channels`}>{t("Canais", "Channels")}</Link>
      <Link href={`/${lang}/patrocine/`}>{t("Patrocine", "Sponsor")}</Link>
      {flag("showPointsStore", "global") && (
        <Link href={`/${lang}/#store`}>Store Points</Link>
      )}
      <Link href={`/${lang}/stackpick/`}>StackPick</Link>
      <Link href={`/${lang}/produtos/`}>{t("Produtos", "Products")}</Link>
      <Link href={`/${lang}/transparencia/`}>
        {t("Transparência", "Transparency")}
      </Link>
      <Link href={`/${lang}/forgekit/`}>ForgeKit</Link>
      <Link href="/privacy/">{t("Privacidade", "Privacy")}</Link>
      <Link href="/terms/">{t("Termos", "Terms")}</Link>
      <small>
        {t(
          "Curadoria editorial com fontes, créditos e data de apuração. Mochila, interesses, histórico e Karaca Points oficiais pertencem à conta autenticada e verificada.",
          "Editorial curation with sources, credits and verification dates. Your backpack, interests, history and official Karaca Points belong to your verified account.",
        )}
      </small>
    </footer>
  );
}

function Home() {
  const {
    t,
    lang,
    filter,
    setFilter,
    labels,
    player,
    surprise,
    title,
    summary,
  } = useHub();
  const [query, setQuery] = useState("");
  const [pageSize, setPageSize] = useState(12);
  const matching = discoveries
    .filter(
      (x) =>
        (filter === "all" || x.category === filter) &&
        `${title(x)} ${summary(x)} ${x.tags || ""}`
          .toLocaleLowerCase()
          .includes(query.trim().toLocaleLowerCase()),
    )
    .sort(compareRadarNewestFirst);
  const feed = matching;
  function loadMore() {
    const next = feed[pageSize];
    setPageSize((size) => size + 12);
    requestAnimationFrame(() => {
      if (next)
        document
          .getElementById(`discovery-${next.id}`)
          ?.querySelector<HTMLAnchorElement>("h3 a")
          ?.focus();
    });
  }
  function scrollFeed() {
    document.getElementById("feed-start")?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
    document.getElementById("feed-title")?.focus({ preventScroll: true });
  }
  return (
    <>
      <div className="ticker">
        <strong>{t("NO RADAR", "ON THE RADAR")}</strong>
        {feed
          .filter((item) => !item.isDemo)
          .slice(0, 4)
          .map((item) => (
            <span key={item.id}>{title(item)}</span>
          ))}
      </div>
      <div className="wrap">
        <div className="welcome">
          <div>
            <h1>
              {t(
                "E aí, player. Bora descobrir?",
                "Hey, player. Ready to explore?",
              )}
            </h1>
            <p>
              {t(
                "Games, IA e coisas que fazem a gente dizer: “Karaca!”",
                "Games, AI and things that make us say: “Karaca!”",
              )}
            </p>
          </div>
          <button
            className="surprise"
            onClick={surprise}
            aria-label={t("Me surpreenda", "Surprise me")}
          >
            <Icon name="shuffle" />
            {t("Me surpreenda", "Surprise me")}
          </button>
        </div>
        <div className="hero-layout">
          <HeroCarousel onExplore={scrollFeed} />
          <Passport />
        </div>
        <div className="dock" role="group" aria-label="Radar">
          {(["all", ...categories] as (Category | "all")[]).map((cat) => (
            <button
              key={cat}
              className="category"
              style={
                {
                  "--cat": cat === "all" ? "#a8bdff" : colors[cat],
                } as CSSProperties
              }
              aria-pressed={filter === cat}
              onClick={() => {
                setFilter(cat);
                setPageSize(12);
              }}
            >
              <Icon name={cat} />
              {labels[cat]}
            </button>
          ))}
        </div>
        <LiveRoom />
        <div className="content" id="feed-start">
          <section aria-labelledby="feed-title">
            <div className="heading">
              <h2 id="feed-title" tabIndex={-1}>
                {t("Drops no seu", "Drops on your")} <span>radar</span>
              </h2>
              <small>
                {t(
                  "Notícias, comparativos e explicadores com fontes",
                  "Sourced news, comparisons and explainers",
                )}
              </small>
            </div>
            <label className="radar-search">
              {t("Buscar no radar", "Search the radar")}
              <input
                type="search"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setPageSize(12);
                }}
                placeholder={t(
                  "Games, IA, gadgets…",
                  "Games, AI, gadgets…",
                )}
              />
            </label>
            <p className="source">
              {feed.length}{" "}
              {t("descobertas neste radar", "discoveries on this radar")}
            </p>
            <div className="feed" aria-live="polite">
              {!feed.length && (
                <p className="empty">
                  {t(
                    "Nenhuma descoberta para esta busca.",
                    "No discoveries match your search.",
                  )}
                </p>
              )}
              {feed.slice(0, pageSize).map((item) => (
                <DiscoveryCard key={item.id} item={item} />
              ))}
            </div>
            {feed.length > pageSize && (
              <button className="button secondary" onClick={loadMore}>
                {t("Carregar mais descobertas", "Load more discoveries")} (
                {feed.length - pageSize})
              </button>
            )}
          </section>
          <aside className="sidebar">
            <section className="quiz-teaser">
              <Icon name={player.quizDone ? "trophy" : "ia"} />
              <p className="eyebrow">
                {t("DESAFIO EDITORIAL", "EDITORIAL CHALLENGE")}
              </p>
              <h2>
                {player.quizDone
                  ? t("Curiosidade em dia.", "Curiosity powered up.")
                  : t(
                      "Você sabe mesmo como isso funciona?",
                      "Do you really know how this works?",
                    )}
              </h2>
              <p>
                {t(
                  "Missões oficiais com Karaca Points exigem conta verificada e validação no servidor.",
                  "Official missions with Karaca Points require a verified account and server validation.",
                )}
              </p>
              <Link className="button" href={`/${lang}/conta/missoes/`}>
                {t("Ver missões oficiais", "View official missions")}
                <Icon name="arrow" />
              </Link>
            </section>
            <section className="sidebar-panel">
              <h2>{t("O papo continua", "Keep the conversation going")}</h2>
              {socials.slice(0, 3).map(([name, url]) => (
                <External className="channel-link" key={name} href={url}>
                  <span>{name[0]}</span>
                  {name}
                  <b>↗</b>
                </External>
              ))}
              <p>
                {t(
                  "Canais do Ghost. Status de live e horários só quando confirmados.",
                  "Ghost’s channels. Live status and schedules require confirmation.",
                )}
              </p>
            </section>
            <section className="loot">
              <h2>
                {t(
                  "Quem guarda, descobre depois.",
                  "Good finds deserve a save.",
                )}
              </h2>
              <p>
                {t(
                  "Sua mochila junta o que vale revisitar na sua conta. Abra, salve, compare e volte quando quiser.",
                  "Your backpack keeps what is worth revisiting in your account. Open, save, compare and come back anytime.",
                )}
              </p>
              <Link href={`/${lang}/conta/mochila/`}>
                {t("Abrir minha mochila →", "Open my backpack →")}
              </Link>
            </section>
          </aside>
        </div>
        <PointsTeaser />
        <CommerceHome />
        <CMSSections />
        <section className="return-band">
          <Ghost size={68} />
          <div>
            <h2>
              {t("Um radar com a sua cara.", "A radar that feels like you.")}
            </h2>
            <p>
              {t(
                "Escolha seus temas na sua conta. Seu Radar lista as notas da mais nova para a mais antiga.",
                "Choose your topics in your account. Your Radar lists notes from newest to oldest.",
              )}
            </p>
          </div>
          <Link className="button secondary" href={`/${lang}/conta/interesses/`}>
            {t("Personalizar meu radar", "Personalize my radar")}
            <Icon name="arrow" />
          </Link>
        </section>
      </div>
    </>
  );
}

function SavedPage() {
  const account = useAccount();
  const { t, lang, player } = useHub();
  const items = discoveries.filter((x) => player.saved.includes(x.id));
  return (
    <div className="wrap subpage">
      <p className="eyebrow">
        <Icon name="save" />
        {t("MINHA MOCHILA", "MY BACKPACK")}
      </p>
      <h1>
        {t("Coisas boas merecem um save.", "Good discoveries deserve a save.")}
      </h1>
      <p className="lede">
        {t(
          "Sua coleção pessoal, sincronizada com a sua conta e pronta para revisitar.",
          "Your personal collection, synced with your account and ready to revisit.",
        )}
      </p>
      {!account.user ? (
        <div className="empty">
          <Icon name="save" />
          <h2>
            {t(
              "Entre na sua conta para usar a Mochila.",
              "Sign in to your account to use your Backpack.",
            )}
          </h2>
          <p>
            {t(
              "Itens salvos são sincronizados na sua conta verificada, sem depender de armazenamento local.",
              "Saved items are synced to your verified account, without relying on local browser storage.",
            )}
          </p>
          <Link className="button" href={`/${lang}/conta/mochila/`}>
            {t("Ir para Minha Mochila", "Go to My Backpack")}
          </Link>
        </div>
      ) : (
        <div className="feed saved-feed">
          {items.length ? (
            items.map((item) => <DiscoveryCard item={item} key={item.id} />)
          ) : (
            <div className="empty">
              <Icon name="save" />
              <h2>
                {t(
                  "Sua mochila está vazia.",
                  "Your backpack is empty.",
                )}
              </h2>
              <p>
                {t(
                  "Salve notícias e descobertas para ler com calma depois.",
                  "Save stories and discoveries to read later at your own pace.",
                )}
              </p>
              <Link className="button" href={`/${lang}/radar/`}>
                {t("Explorar o Radar", "Explore the Radar")}
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function HubContent() {
  const { route, t, toast } = useHub();
  const pages = {
    home: Home,
    saved: SavedPage,
    quiz: QuizPage,
    profile: ProfilePage,
    channels: ChannelsPage,
    sponsor: SponsorPage,
    live: LivePage,
    agenda: AgendaPage,
    points: PointsPage,
    store: flag("showPointsStore", "global") ? StorePage : PointsPage,
  };
  const Page = pages[route];
  return (
    <div className="hub">
      <a className="skip" href="#hub-main">
        {t("Pular para o conteúdo", "Skip to content")}
      </a>
      <Header />
      <AccountSyncStatus />
      <main id="hub-main" tabIndex={-1}>
        <Page />
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

export default function Hub({
  initialLang = "pt",
}: {
  initialLang?: "pt" | "en";
}) {
  return (

      <HubProvider initialLang={initialLang}>
        <HubContent />
      </HubProvider>

  );
}
