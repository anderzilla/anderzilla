"use client";
import { useEffect, useRef, useState } from "react";
import { useHub } from "./HubProvider";
import {
  discoveries,
  hubSettings,
  platforms,
  socials,
  type Platform,
} from "./model";
import { External, Ghost, Icon } from "./Primitives";
import { DemoBadge } from "./Editorial";

export function LiveRoom({ inRoom = false }: { inRoom?: boolean }) {
  const { t, lang, ready } = useHub();
  const [now, setNow] = useState(0);
  useEffect(() => {
    if (!ready) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [ready]);
  const b = hubSettings.broadcast;
  const live =
    b && Date.parse(b.checkedAt) <= now && Date.parse(b.expiresAt) > now
      ? b
      : null;
  const next = hubSettings.events
    .filter((e) => !e.isDemo && Date.parse(e.startsAt) > now)
    .sort((a, b) => Date.parse(a.startsAt) - Date.parse(b.startsAt))[0];
  return (
    <section className="live-room">
      <div className="live-summary">
        <Ghost size={54} />
        <div className="live-heading">
          <p className="eyebrow">
            <span className={`status-dot ${live ? "on" : ""}`} />
            {live
              ? t("AO VIVO AGORA", "LIVE NOW")
              : t("PONTO DE ENCONTRO", "MEETING POINT")}
          </p>
          <h2>
            {live
              ? live.title
              : t("A sala de live do Ghost", "Ghost’s stream room")}
          </h2>
          <p>
            {live
              ? platforms[live.platform].name
              : t(
                  "Status não confirmado. Escolha um canal para conferir.",
                  "Status unconfirmed. Pick a channel to check.",
                )}
          </p>
        </div>
        {!inRoom && (
          <a className="button pink" href="#live">
            {t("Entrar na sala", "Enter the room")} <Icon name="arrow" />
          </a>
        )}
      </div>
      <div className="schedule">
        <strong>{t("PRÓXIMA LIVE", "NEXT STREAM")}</strong>
        <span>
          {next
            ? `${lang === "pt" ? next.titlePT : next.titleEN} · ${platforms[next.platform].name} · ${new Intl.DateTimeFormat(lang === "pt" ? "pt-BR" : "en-US", { dateStyle: "medium", timeStyle: "short", timeZone: "America/Sao_Paulo" }).format(new Date(next.startsAt))} / Brasília`
            : t(
                "Agenda a confirmar. Os canais continuam a um clique.",
                "Schedule to be confirmed. The channels are one click away.",
              )}
        </span>
        <a href="#agenda">{t("Abrir agenda →", "View schedule →")}</a>
      </div>
    </section>
  );
}
export function LivePage() {
  const { t } = useHub();
  const [platform, setPlatform] = useState<Platform>("twitch");
  const [src, setSrc] = useState("");
  const [narrow, setNarrow] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const p = platforms[platform];
  const youtube = hubSettings.youtubeVideoId;
  const embeddable =
    platform === "twitch" ||
    (platform === "youtube" && !!youtube && /^[\w-]{11}$/.test(youtube));
  function load() {
    if (platform === "twitch") {
      if ((box.current?.clientWidth || 0) < 400) {
        setNarrow(true);
        return;
      }
      const url = new URL("https://player.twitch.tv/");
      url.searchParams.set("channel", "anderzillacwb");
      url.searchParams.set("parent", window.location.hostname);
      url.searchParams.set("autoplay", "false");
      setSrc(url.href);
    } else if (platform === "youtube" && youtube && /^[\w-]{11}$/.test(youtube))
      setSrc(`https://www.youtube-nocookie.com/embed/${youtube}?autoplay=0`);
  }
  return (
    <div className="wrap subpage">
      <p className="eyebrow">GHOST / LIVE ROOM</p>
      <h1>
        {t("Puxa uma cadeira. Bora de live.", "Pull up a chair. Let’s stream.")}
      </h1>
      <LiveRoom inRoom />
      <div
        className="live-tabs"
        role="group"
        aria-label={t("Plataforma", "Platform")}
      >
        {(Object.keys(platforms) as Platform[]).map((id) => (
          <button
            key={id}
            className="interest"
            aria-pressed={platform === id}
            onClick={() => {
              setPlatform(id);
              setSrc("");
              setNarrow(false);
            }}
          >
            {platforms[id].name}
          </button>
        ))}
      </div>
      <div ref={box} className={`stream-placeholder ${src ? "playing" : ""}`}>
        {src ? (
          <iframe
            src={src}
            title={`${p.name} — AnderZilla`}
            allow="fullscreen; encrypted-media; picture-in-picture"
            allowFullScreen
            referrerPolicy="strict-origin-when-cross-origin"
          />
        ) : narrow ? (
          <p>
            {t(
              "Nesta largura, assista direto na Twitch ou gire o aparelho para abrir uma janela maior.",
              "At this width, watch directly on Twitch or rotate your device for a larger window.",
            )}
          </p>
        ) : (
          <>
            <Ghost size={85} />
            <h2>{p.name} / AnderZilla</h2>
            <p>
              {t(
                "Assista aqui ou acompanhe pela plataforma.",
                "Watch here or follow on the platform.",
              )}
            </p>
            {embeddable ? (
              <button className="button" onClick={load}>
                {t("Abrir player no site", "Open player on site")} ▷
              </button>
            ) : (
              <p className="stream-note">
                {t(
                  "Player integrado ainda não configurado para este canal.",
                  "Embedded player is not configured for this channel yet.",
                )}
              </p>
            )}
          </>
        )}
      </div>
      <div className="stream-toolbar">
        <External className="button secondary" href={p.url}>
          {t("Abrir na", "Open on")} {p.name} ↗
        </External>
        <p>
          {t(
            "O player é da plataforma e carrega somente quando você abre. Se não reproduzir aqui, use o link direto.",
            "The platform player loads only when you open it. If playback is unavailable here, use the direct link.",
          )}
        </p>
      </div>
      <a className="button secondary" href="#agenda">
        {t("Ver agenda de lives e eventos", "View stream and event schedule")} →
      </a>
    </div>
  );
}
export function AgendaPage() {
  const { t, lang, ready } = useHub();
  const events = ready
    ? hubSettings.events
        .filter((e) => Date.parse(e.startsAt) > Date.now())
        .sort((a, b) => Date.parse(a.startsAt) - Date.parse(b.startsAt))
    : [];
  return (
    <div className="wrap subpage">
      <p className="eyebrow">GHOST / AGENDA</p>
      <h1>
        {t("Marca aí. A gente se encontra.", "Save the date. See you there.")}
      </h1>
      <p className="lede">
        {t(
          "Lives e eventos do AnderZilla, com tema, plataforma e horário de Brasília.",
          "AnderZilla streams and events, with topic, platform and Brasília time.",
        )}
      </p>
      <div className="agenda-list">
        {events.length ? (
          events.map((e) => (
            <article className="agenda-event" key={e.id}>
              <div className="event-date">
                <time dateTime={e.startsAt}>
                  {new Intl.DateTimeFormat(lang === "pt" ? "pt-BR" : "en-US", {
                    dateStyle: "medium",
                    timeStyle: "short",
                    timeZone: "America/Sao_Paulo",
                  }).format(new Date(e.startsAt))}
                </time>
              </div>
              <div>
                <p className="eyebrow">
                  {platforms[e.platform].name} / Brasília
                </p>
                <h2>{lang === "pt" ? e.titlePT : e.titleEN}</h2>{e.isDemo&&<DemoBadge english={lang==='en'}/>}
              </div>
              <External
                className="button secondary"
                href={e.url||platforms[e.platform].url}
              >
                {t("Abrir canal", "Open channel")} ↗
              </External>
            </article>
          ))
        ) : (
          <section className="agenda-empty">
            <div className="calendar-art" aria-hidden="true">
              <span>GHOST</span>
              <strong>＋</strong>
            </div>
            <h2>
              {t(
                "O próximo encontro ainda vai ganhar data.",
                "Our next meetup is still waiting for a date.",
              )}
            </h2>
            <p>
              {t(
                "Nenhum evento anunciado por enquanto. Quando houver uma live marcada, ela aparece aqui com todos os detalhes.",
                "No events announced yet. When a stream is scheduled, it will appear here with all the details.",
              )}
            </p>
            <a className="button pink" href="#channels">
              {t(
                "Enquanto isso, conheça os canais",
                "Meanwhile, explore the channels",
              )}{" "}
              ↗
            </a>
          </section>
        )}
      </div>
    </div>
  );
}
export function AdPlacement() {
  const { t } = useHub();
  return (
    <section
      className="ad-placement"
      aria-label={t(
        "Espaço publicitário demonstrativo",
        "Demonstration advertising placement",
      )}
    >
      <p className="eyebrow">
        {t(
          "PUBLICIDADE · ESPAÇO DEMONSTRATIVO",
          "ADVERTISEMENT · DEMONSTRATION PLACEMENT",
        )}
      </p>
      <div>
        <strong>
          {t(
            "Sua marca no radar de quem curte tecnologia.",
            "Your brand on the radar of tech lovers.",
          )}
        </strong>
        <span>
          {t(
            "Games, gadgets, IA. Com contexto, sem interromper a diversão.",
            "Games, gadgets, AI. With context, without interrupting the fun.",
          )}
        </span>
      </div>
      <a className="button secondary" href="#sponsor">
        {t("Conhecer os formatos", "Explore the formats")} ↗
      </a>
    </section>
  );
}
export function AffiliateArea() {
  const { t, lang, title, labels } = useHub();
  const active = hubSettings.affiliates.filter(
    (a) => a.status === "active" && a.url.startsWith("https://"),
  );
  return (
    <section className="affiliate-area">
      <div className="heading">
        <div>
          <p className="eyebrow">
            {t("CURADORIA & AFILIADOS", "CURATION & AFFILIATES")}
          </p>
          <h2>
            Loot & <span>upgrades</span>
          </h2>
        </div>
        <small>
          {t("Escolhas para o seu universo", "Choices for your universe")}
        </small>
      </div>
      <p className="affiliate-disclosure">
        {active.some(a=>!a.isDemo)
          ? t(
              "Os links identificados como afiliados podem gerar comissão para o AnderZilla.",
              "Links labeled affiliate may earn AnderZilla a commission.",
            )
          : t(
              "Área de afiliados em preparação. Por enquanto, os links abaixo são oficiais e não geram comissão para o AnderZilla.",
              "Affiliate area in preparation. For now, the links below are official and do not earn AnderZilla a commission.",
            )}
      </p>
      <div className="affiliate-grid">
        {active.length
          ? active.map((a) => (
              <article key={a.url} className="affiliate-card">
                <div>
                  <p className="eyebrow">
                    {a.isDemo?<DemoBadge english={lang==='en'}/>:t("LINK DE AFILIADO", "AFFILIATE LINK")}
                  </p>
                  <h3>{lang === "pt" ? a.titlePT : a.titleEN}</h3>
                  <>{a.isDemo?<p>{t("Sem oferta ou parceria ativa","No active offer or partnership")}</p>:<External href={a.url} affiliate>{t("Ver oferta", "View offer")} ↗</External>}</>
                </div>
              </article>
            ))
          : discoveries
              .filter((d) =>
                ["consoles", "celulares", "gadgets"].includes(d.category),
              )
              .map((d) => (
                <article key={d.id} className="affiliate-card">
                  <div className="affiliate-icon">
                    <Icon name={d.category} />
                  </div>
                  <div>
                    <p className="eyebrow">
                      {labels[d.category]} ·{" "}
                      {t("LINK OFICIAL", "OFFICIAL LINK")}
                    </p>
                    <h3>{title(d)}</h3>
                    <External href={d.url}>
                      {t("Conhecer na fonte", "Explore at the source")} ↗
                    </External>
                  </div>
                </article>
              ))}
      </div>
    </section>
  );
}
export function ChannelsPage() {
  const { t } = useHub();
  return (
    <div className="wrap subpage">
      <p className="eyebrow">@ANDERZILLA</p>
      <h1>
        {t("Aperta o play. Puxa uma cadeira.", "Press play. Pull up a chair.")}
      </h1>
      <p className="lede">
        {t(
          "Games, tech e conversa com o Ghost. Escolha onde acompanhar.",
          "Games, tech and conversations with Ghost. Choose where to follow.",
        )}
      </p>
      <div className="channel-grid">
        {socials.map(([name, url]) => (
          <section key={name} className="channel-card">
            <Ghost size={60} />
            <h2>{name}</h2>
            <p>
              {t(
                "Sem indicador de “ao vivo” ou agenda até haver confirmação real.",
                "No “live now” indicator or schedule without confirmation.",
              )}
            </p>
            <External className="button secondary" href={url}>
              {t("Ir para o canal", "Visit channel")} ↗
            </External>
          </section>
        ))}
      </div>
    </div>
  );
}
export function SponsorPage() {
  const { t } = useHub();
  return (
    <div className="wrap subpage">
      <p className="eyebrow">{t("PARCERIAS", "PARTNERSHIPS")}</p>
      <h1>
        {t(
          "Marcas também podem entrar na conversa.",
          "Brands can join the conversation too.",
        )}
      </h1>
      <p className="lede">
        {t(
          "Games, gadgets e IA dão boas histórias quando existe algo interessante para mostrar. Demonstrações entram na pauta com identificação comercial e opinião independente.",
          "Games, gadgets and AI make good stories when there is something interesting to show. Demonstrations join the editorial mix with commercial disclosure and independent opinion.",
        )}
      </p>
      <div className="notice">
        {t(
          "Conceito comercial: sem patrocinadores, preços ou formulário simulado. Contato e recebimento serão validados antes de operar.",
          "Commercial concept: no sponsors, prices or simulated form. Contact and receiving process will be validated before operation.",
        )}
      </div>
      <h2>ForgeKit</h2>
      <p className="lede">
        {t(
          "Para quem também quer construir: o produto próprio é uma opção contextual. Confira conteúdo, preço e condições na Gumroad.",
          "For people who also want to build: our own product is a contextual option. Check contents, price and terms on Gumroad.",
        )}
      </p>
      <External
        className="button secondary"
        href="https://anderzilla.gumroad.com/l/edkel"
      >
        ForgeKit / Gumroad ↗
      </External>
      <p>
        <a href="/forgekit">ForgeKit</a> · <a href="/stackpick">StackPick</a>
      </p>
    </div>
  );
}
