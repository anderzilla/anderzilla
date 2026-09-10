"use client";
import { useState, type CSSProperties } from "react";
import { HubProvider, useHub } from "./HubProvider";
import {
  categories,
  colors,
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
  AdPlacement,
  AffiliateArea,
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

function Header() {
  const { t, lang, changeLanguage, route, player } = useHub();
  const links: [Route, string][] = [
    ["home", "Radar"],
    ["saved", t("Minha mochila", "My backpack")],
    ["quiz", t("Desafio", "Challenge")],
    ["live", "Live"],
    ["agenda", "Agenda"],
    ["points", "Karaca Points"],
  ];
  return (
    <>
      <div className="preview">
        <span>
          {t("PRÉVIA · HUB EM CONSTRUÇÃO", "PREVIEW · HUB UNDER CONSTRUCTION")}
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
        <a className="brand" href="#home">
          <Ghost size={45} />
          <div className="wordmark">
            ANDER<span>ZILLA</span>
            <small>
              {t("GAMES. TECH. BOAS DESCOBERTAS.", "GAMES. TECH. GREAT FINDS.")}
            </small>
          </div>
        </a>
        <nav aria-label={t("Principal", "Main")}>
          {links.map(([r, label]) => (
            <a
              href={`#${r}`}
              key={r}
              aria-current={route === r ? "page" : undefined}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="actions">
          <a
            href="#saved"
            aria-label={`${t("Minha mochila", "My backpack")}: ${player.saved.length}`}
          >
            <Icon name="save" />{" "}
            <span className="count">{player.saved.length}</span>
          </a>
          <a className="profile-link" href="#profile">
            <Ghost size={26} />
            <span>{t("Seu radar", "Your radar")}</span>
          </a>
        </div>
      </header>
    </>
  );
}
function Footer() {
  const { t } = useHub();
  return (
    <footer>
      <a className="wordmark" href="#home">
        ANDER<span>ZILLA</span>
      </a>
      <p>
        {t(
          "Um esconderijo para quem gosta de games e de fuçar no futuro.",
          "A hideout for people who love games and tinkering with the future.",
        )}
      </p>
      <a href="#channels">{t("Canais", "Channels")}</a>
      <a href="#sponsor">{t("Parcerias", "Partnerships")}</a>
      <a href="#store">Store Points</a>
      <a href="/stackpick">StackPick</a>
      <External href="https://anderzilla.gumroad.com/l/edkel">
        ForgeKit / {t("produto próprio", "own product")} ↗
      </External>
      <a href="/privacy">{t("Privacidade", "Privacy")}</a>
      <a href="/terms">{t("Termos", "Terms")}</a>
      <small>
        {t(
          "Prévia com curadoria datada e artes conceituais. Não é feed automático. Mochila, interesses e progresso ficam no navegador; pontos demonstrativos sem valor financeiro.",
          "Preview with dated curation and concept artwork. Not an automatic news feed. Backpack, interests and progress stay in your browser; demo points have no monetary value.",
        )}
      </small>
    </footer>
  );
}
function Home() {
  const { t, filter, setFilter, labels, player, surprise,title,summary } = useHub();
  const [query,setQuery]=useState('');
  const feed = [...discoveries]
    .sort(
      (a, b) =>
        Number(player.interests.includes(b.category)) -
          Number(player.interests.includes(a.category)) ||
        b.published.localeCompare(a.published),
    )
    .filter((x) => (filter === "all" || x.category === filter)&&`${title(x)} ${summary(x)} ${x.tags||''}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  function scrollFeed() {
    document
      .getElementById("feed-start")
      ?.scrollIntoView({
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
        {discoveries.filter(item=>!item.isDemo).slice(0,4).map(item=><span key={item.id}>{title(item)}</span>)}
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
          <section className="hero">
            <img
              src="/hub/discovery-room.png"
              width={1536}
              height={1024}
              alt=""
            />
            <p className="eyebrow">
              <span className="tag">GHOST&apos;S HIDEOUT</span>
              {t("ABRA UMA NOVA FASE", "ENTER A NEW LEVEL")}
            </p>
            <h2>
              {t("Seu próximo", "Your next")}
              <br />
              <em>“Karaca!”</em>
              <br />
              {t("está aqui.", "starts here.")}
            </h2>
            <p>
              {t(
                "Uma corrida nova, um gadget improvável ou uma IA que resolve aquele perrengue. Escolha sua próxima descoberta.",
                "A new race, an unexpected gadget or AI that solves a little everyday problem. Pick your next discovery.",
              )}
            </p>
            <div className="hero-buttons">
              <button className="button" onClick={scrollFeed}>
                {t("Entrar no radar", "Explore the radar")}
                <Icon name="arrow" />
              </button>
              <button className="button secondary" onClick={surprise}>
                <Icon name="shuffle" />
                {t("Abrir uma surpresa", "Open a surprise")}
              </button>
            </div>
            <span className="art-note">
              {t(
                "Arte conceitual · não representa produto real",
                "Concept art · not an actual product",
              )}
            </span>
          </section>
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
              onClick={() => setFilter(cat)}
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
                  "Curadoria + exemplos identificados como DEMO",
                  "Curation + examples labeled DEMO",
                )}
              </small>
            </div>
            <label className="radar-search">{t('Buscar no radar','Search the radar')}<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder={t('Games, IA, gadgets…','Games, AI, gadgets…')}/></label>
            <div className="feed" aria-live="polite">
              {!feed.length&&<p className="empty">{t('Nenhuma descoberta para esta busca.','No discoveries match your search.')}</p>}
              {feed.map((item) => (
                <DiscoveryCard key={item.id} item={item} />
              ))}
            </div>
          </section>
          <aside className="sidebar">
            <section className="quiz-teaser">
              <Icon name={player.quizDone ? "trophy" : "ia"} />
              <p className="eyebrow">
                {t("DESAFIO DA VEZ", "YOUR NEXT CHALLENGE")}
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
                  "Três perguntas. Umas descobertas inesperadas. Acerte, entenda e desbloqueie seu selo.",
                  "Three questions. A few unexpected discoveries. Learn the details and unlock your badge.",
                )}
              </p>
              <a className="button" href="#quiz">
                {t("Aceitar desafio", "Accept challenge")}
                <Icon name="arrow" />
              </a>
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
                  "Sua mochila junta o que vale revisitar. Abra, salve, compare e volte quando quiser.",
                  "Your backpack keeps what is worth revisiting. Open, save, compare and come back anytime.",
                )}
              </p>
              <a href="#saved">
                {t("Abrir minha mochila →", "Open my backpack →")}
              </a>
            </section>
          </aside>
        </div>
        <PointsTeaser />
        <AdPlacement />
        <AffiliateArea />
        <CMSSections />
        <section className="return-band">
          <Ghost size={68} />
          <div>
            <h2>
              {t("Um radar com a sua cara.", "A radar that feels like you.")}
            </h2>
            <p>
              {t(
                "Escolha seus temas. Eles aparecem primeiro na próxima visita.",
                "Choose your topics. They appear first on your next visit.",
              )}
            </p>
          </div>
          <a className="button secondary" href="#profile">
            {t("Personalizar meu radar", "Personalize my radar")}
            <Icon name="arrow" />
          </a>
        </section>
      </div>
    </>
  );
}
function SavedPage() {
  const { t, player } = useHub();
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
          "Sua coleção pessoal, guardada neste navegador e pronta para revisitar.",
          "Your personal collection, stored in this browser and ready to revisit.",
        )}
      </p>
      <div className="feed saved-feed">
        {items.length ? (
          items.map((item) => <DiscoveryCard item={item} key={item.id} />)
        ) : (
          <div className="empty">
            <Icon name="save" />
            <h2>
              {t(
                "Sua mochila espera o primeiro loot.",
                "Your backpack awaits its first find.",
              )}
            </h2>
            <p>
              {t(
                "Toque no marcador de uma descoberta para guardar aqui. Sem conta e sem pressa.",
                "Tap the bookmark on a discovery to save it here. No account and no rush.",
              )}
            </p>
            <a className="button" href="#home">
              {t("Voltar ao radar", "Back to radar")}
            </a>
          </div>
        )}
      </div>
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
    store: StorePage,
  };
  const Page = pages[route];
  return (
    <div className="hub">
      <a className="skip" href="#hub-main">
        {t("Pular para o conteúdo", "Skip to content")}
      </a>
      <Header />
      <main id="hub-main" tabIndex={-1}>
        <Page />
      </main>
      <Footer />
      <DetailDialog />
      <div id="toast" role="status" className={toast ? "show" : ""}>
        {toast}
      </div>
    </div>
  );
}
export default function Hub() {
  return (
    <HubProvider>
      <HubContent />
    </HubProvider>
  );
}
