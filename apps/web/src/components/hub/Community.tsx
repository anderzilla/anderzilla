"use client";
import { useEffect, useRef, useState } from "react";
import { useHub } from "./HubProvider";
import {
  hubSettings,
  LIVE_STATUS_POLL_MS,
  LIVE_STATUS_URL,
  parseLiveStatus,
  platforms,
  socials,
  YOUTUBE_CHANNEL_URL,
  YOUTUBE_LIVE_URL,
  type Broadcast,
  type LiveStatus,
  type Platform,
} from "./model";
import { BrandAvatar } from "../BrandAssets";
import { External, Ghost, Icon } from "./Primitives";
import { DemoBadge } from "./Editorial";

type RemoteLive =
  | { state: "pending" }
  | { state: "ready"; status: LiveStatus }
  | { state: "error" };

function useLiveStatus(): RemoteLive {
  const [remote, setRemote] = useState<RemoteLive>({ state: "pending" });
  useEffect(() => {
    let cancelled = false;
    let current = 0;
    async function pull() {
      const id = ++current;
      try {
        const response = await fetch(LIVE_STATUS_URL, { cache: "no-store" });
        if (!response.ok) throw new Error(String(response.status));
        const status = parseLiveStatus(await response.json());
        if (!status) throw new Error("invalid status");
        if (!cancelled && id === current) setRemote({ state: "ready", status });
      } catch {
        if (!cancelled && id === current) setRemote({ state: "error" });
      }
    }
    void pull();
    const timer = window.setInterval(() => void pull(), LIVE_STATUS_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);
  return remote;
}
function activeBroadcast(now: number): Broadcast | null {
  const broadcast = hubSettings.broadcast;
  if (
    !broadcast ||
    Date.parse(broadcast.checkedAt) > now ||
    Date.parse(broadcast.expiresAt) <= now
  )
    return null;
  return broadcast;
}

export function LiveRoom({ inRoom = false }: { inRoom?: boolean }) {
  const { t, lang, ready } = useHub();
  const remote = useLiveStatus();
  const [now, setNow] = useState(0);
  useEffect(() => {
    if (!ready) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [ready]);
  const fallback =
    remote.state === "ready" ? null : activeBroadcast(now);
  const live = remote.state === "ready" && remote.status.live
    ? {
        title: remote.status.title,
        url: remote.status.url || YOUTUBE_LIVE_URL,
      }
    : fallback
      ? {
          title: fallback.title,
          url:
            fallback.platform === "youtube"
              ? YOUTUBE_LIVE_URL
              : platforms[fallback.platform].url,
        }
      : null;
  const next = hubSettings.events
    .filter((e) => !e.isDemo && Date.parse(e.startsAt) > now)
    .sort((a, b) => Date.parse(a.startsAt) - Date.parse(b.startsAt))[0];
  return (
    <section className={`live-room${live ? " is-live" : ""}`}>
      <div className="live-summary">
        <BrandAvatar size={54} />
        <div className="live-heading">
          <p className="eyebrow">
            <span className={`status-dot ${live ? "on" : ""}`} />
            {live
              ? t("ANDERSON AO VIVO AGORA", "ANDERSON IS LIVE NOW")
              : t("PONTO DE ENCONTRO", "MEETING POINT")}
          </p>
          <h2>
            {live
              ? live.title || t("AnderZilla", "AnderZilla")
              : t("A sala de live do Anderson", "Anderson’s stream room")}
          </h2>
          <p className={live ? "live-current-link" : undefined}>
            {live ? (
              <External href={live.url}>{live.url}</External>
            ) : (
              <>
                {t(
                  "Status não confirmado. Escolha um canal para conferir.",
                  "Status unconfirmed. Pick a channel to check.",
                )}{" "}
                <External href={YOUTUBE_CHANNEL_URL}>
                  youtube.com/@anderzilla-tv
                </External>
              </>
            )}
          </p>
        </div>
        {live ? (
          <External className="button" href={live.url}>
            {t("Assistir à live agora", "Watch the live now")}{" "}
            <Icon name="arrow" />
          </External>
        ) : (
          !inRoom && (
            <a className="button pink" href="#live">
              {t("Entrar na sala", "Enter the room")} <Icon name="arrow" />
            </a>
          )
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
      <p className="eyebrow">
        {t("ANDERSON / SALA DE LIVE", "ANDERSON / LIVE ROOM")}
      </p>
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
            <BrandAvatar size={85} />
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
export function AdPlacement() { return null; }
export function AffiliateArea() { const {lang,t}=useHub();return <p><a href={`/${lang}/parceiros/`}>{t('Ver afiliados por mercado','View affiliates by market')} →</a></p>; }
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
export function SponsorPage() {const {lang,t}=useHub();return <div className="wrap subpage"><h1>{t('Patrocine','Sponsor')}</h1><p className="lede">{t('Conheça os formatos disponíveis e nossa política de independência editorial.','Explore available formats and our editorial independence policy.')}</p><a className="button" href={`/${lang}/patrocine/`}>{t('Abrir área de patrocínios','Open sponsorship area')} →</a></div>;}
