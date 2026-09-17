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
import { CommerceHome } from "../commerce/CommerceHome";
import { flag } from "../commerce/data";
import {AccountProvider,useAccount} from "../account/AccountProvider";
import {AccountAccess,AccountDialog,AccountSyncStatus,UserAvatar} from "../account/AccountUI";

function Header() {
  const { t, lang, changeLanguage, route, player } = useHub();
  const account = useAccount();
  const links: [Route, string][] = [
    ["home", t("Explorar", "Explore")],
  ];
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
          <a href={`/?lang=${lang}&category=ia#home`}>{t("IA", "AI")}</a>
          <a href={`/?lang=${lang}&category=games#home`}>Games</a>
          <a href={`/?lang=${lang}&category=gadgets#home`}>Gadgets</a>
          <a href={`/${lang}/stackpick/`}>StackPick</a>
          <a href={`/${lang}/produtos/`}>{t("Produtos", "Products")}</a>
          <a href={`/${lang}/patrocine/`}>{t("Patrocine", "Sponsor")}</a>
        </nav>
        <div className="actions">
          <AccountAccess/>
          <a
            href="#saved"
            aria-label={`${t("Minha mochila", "My backpack")}: ${player.saved.length}`}
          >
            <Icon name="save" />{" "}
            <span className="count">{player.saved.length}</span>
          </a>
          <a className="profile-link" href="#profile">
            {account.user ? (
              <UserAvatar
                name={account.user.displayName}
                email={account.user.email}
                src={account.user.avatarUrl}
                size={26}
              />
            ) : (
              <Ghost size={26} />
            )}
            <span>{t("Seu radar", "Your radar")}</span>
          </a>
        </div>
      </header>
    </>
  );
}
function Footer() {
  const { t, lang } = useHub();
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
      <a href={`/${lang}/patrocine/`}>{t("Patrocine", "Sponsor")}</a>
      {flag("showPointsStore","global")&&<a href="#store">Store Points</a>}
      <a href={`/${lang}/stackpick/`}>StackPick</a>
      <a href={`/${lang}/produtos/`}>{t("Produtos", "Products")}</a>
      <a href={`/${lang}/transparencia/`}>{t("Transparência", "Transparency")}</a>
      <a href={`/${lang}/forgekit/`}>ForgeKit</a>
      <a href="/privacy">{t("Privacidade", "Privacy")}</a>
      <a href="/terms">{t("Termos", "Terms")}</a>
      <small>
        {t(
          "Curadoria editorial com fontes, créditos e data de apuração. Visitantes guardam progresso neste navegador; contas sincronizam preferências quando disponíveis. KP oficial depende de validação do servidor.",
          "Editorial curation with sources, credits and verification dates. Guests keep progress in this browser; accounts sync preferences when available. Official KP require server validation.",
        )}
      </small>
    </footer>
  );
}
function Home() {
  const { t, filter, setFilter, labels, player, surprise,title,summary } = useHub();
  const [query,setQuery]=useState('');
  const [pageSize,setPageSize]=useState(12);
  const matching = [...discoveries]
    .sort(
      (a, b) =>
        Number(player.interests.includes(b.category)) -
          Number(player.interests.includes(a.category)) ||
        b.published.localeCompare(a.published) || (b.eventDate||b.published).localeCompare(a.eventDate||a.published),
    )
    .filter((x) => (filter === "all" || x.category === filter)&&`${title(x)} ${summary(x)} ${x.tags||''}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  const categoryOrder=[...categories].sort((a,b)=>Number(player.interests.includes(b))-Number(player.interests.includes(a)));
  const groups=categoryOrder.map(category=>matching.filter(item=>item.category===category));
  const feed=filter==='all'&&!query.trim()?Array.from({length:Math.max(0,...groups.map(group=>group.length))},(_,index)=>groups.flatMap(group=>group[index]?[group[index]]:[])).flat():matching;
  function loadMore(){const next=feed[pageSize];setPageSize(size=>size+12);requestAnimationFrame(()=>{if(next)document.getElementById(`discovery-${next.id}`)?.querySelector<HTMLAnchorElement>('h3 a')?.focus()})}
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
        {feed.filter(item=>!item.isDemo).slice(0,4).map(item=><span key={item.id}>{title(item)}</span>)}
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
              onClick={() => {setFilter(cat);setPageSize(12)}}
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
            <label className="radar-search">{t('Buscar no radar','Search the radar')}<input type="search" value={query} onChange={e=>{setQuery(e.target.value);setPageSize(12)}} placeholder={t('Games, IA, gadgets…','Games, AI, gadgets…')}/></label>
            <p className="source">{feed.length} {t('descobertas neste radar','discoveries on this radar')}</p>
            <div className="feed" aria-live="polite">
              {!feed.length&&<p className="empty">{t('Nenhuma descoberta para esta busca.','No discoveries match your search.')}</p>}
              {feed.slice(0,pageSize).map((item) => (
                <DiscoveryCard key={item.id} item={item} />
              ))}
            </div>
            {feed.length>pageSize&&<button className="button secondary" onClick={loadMore}>{t('Carregar mais descobertas','Load more discoveries')} ({feed.length-pageSize})</button>}
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
  const account=useAccount();
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
          account.user?"Sua coleção pessoal, sincronizada com a conta e pronta para revisitar.":"Sua coleção pessoal, guardada neste navegador e pronta para revisitar.",
          account.user?"Your personal collection, synced with your account and ready to revisit.":"Your personal collection, stored in this browser and ready to revisit.",
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
    store: flag("showPointsStore", "global") ? StorePage : PointsPage,
  };
  const Page = pages[route];
  return (
    <div className="hub">
      <a className="skip" href="#hub-main">
        {t("Pular para o conteúdo", "Skip to content")}
      </a>
      <Header />
      <AccountSyncStatus/>
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
export default function Hub() {
  return (
    <AccountProvider><HubProvider>
      <HubContent />
    </HubProvider></AccountProvider>
  );
}
