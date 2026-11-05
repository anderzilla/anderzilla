"use client";
import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";
import { useHub } from "./HubProvider";
import { useAccount, savePostLoginIntent } from "../account/AccountProvider";
import { BrandAvatar } from "../BrandAssets";
import { articleUrl, colors, radarCardDate, type Discovery } from "./model";
import { DemoBadge, findMedia, SafeMarkdown } from "./Editorial";

const paths: Record<string, string> = {
  all: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  games:
    "M7 7h10c3 0 5 5 5 9s-3 5-6 1H8c-3 4-6 3-6-1s2-9 5-9z M6 10v5 M3.5 12.5h5 M16 11h.1 M19 14h.1",
  celulares:
    "M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z M10 5h4 M11 19h2",
  ia: "M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3z M19 2v4 M17 4h4",
  gadgets:
    "M3 14v-3a9 9 0 0 1 18 0v3 M3 12h4v9H5a2 2 0 0 1-2-2z M21 12h-4v9h2a2 2 0 0 0 2-2z",
  curiosidades:
    "M19 12a7 7 0 1 1-14 0 7 7 0 0 1 14 0z M6 8C-4 15 1 25 17 15S29 0 18 7",
  save: "M6 3h12v19l-6-4-6 4z",
  shuffle:
    "M3 6h3c4 0 8 12 12 12h3 M18 15l3 3-3 3 M3 18h3c1 0 3-2 4-4 M14 10c2-3 3-4 4-4h3 M18 3l3 3-3 3",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  "chevron-left": "M15 6 9 12l6 6",
  "chevron-right": "M9 6l6 6-6 6",
  pause: "M8 5v14 M16 5v14",
  play: "M8 5l11 7-11 7z",
  trophy:
    "M7 3h10v6a5 5 0 0 1-10 0z M7 5H3v3a4 4 0 0 0 4 4 M17 5h4v3a4 4 0 0 0 4 4 M12 14v6 M7 21h10",
};

export function Icon({ name }: { name: string }) {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name === "consoles" ? "games" : name] || paths.ia} />
    </svg>
  );
}

// Compatibility name for existing community UI; the artwork is the approved brand symbol.
export function Ghost({ size = 62 }: { size?: number }) {
  return <BrandAvatar size={size} />;
}

export function External({
  href,
  children,
  className,
  affiliate = false,
}: {
  href: string;
  children: ReactNode;
  className?: string;
  affiliate?: boolean;
}) {
  return (
    <a
      href={href}
      className={className}
      target="_blank"
      rel={affiliate ? "sponsored noopener noreferrer" : "noopener noreferrer"}
    >
      {children}
    </a>
  );
}

export function Art({ item, extra = "" }: { item: Discovery; extra?: string }) {
  const { lang } = useHub();
  const media = findMedia(item.coverMediaId);
  const shapes: Partial<Record<Discovery["category"], string>> = {
    celulares: "phone",
    ia: "orb",
    curiosidades: "planet",
  };
  const shape = shapes[item.category];
  if (media)
    return (
      <div className={`art cms-cover ${extra}`}>
        <img
          src={media.url}
          alt={(lang === "pt" ? media.altPT : media.altEN) || ""}
          loading="lazy"
          width={media.width}
          height={media.height}
        />
      </div>
    );
  return (
    <div className={`art ${item.category} ${extra}`} aria-hidden="true">
      {shape ? <div className={shape} /> : <Icon name={item.category} />}
    </div>
  );
}

export function SaveButton({
  item,
  label = false,
}: {
  item: Discovery;
  label?: boolean;
}) {
  const { player, t, toggleSave } = useHub();
  const account = useAccount();
  const saved = Boolean(account.user && player.saved.includes(item.id));
  const text = saved
    ? t("Tirar da mochila", "Remove from backpack")
    : t("Guardar na mochila", "Save to backpack");
  return (
    <button
      className={label ? "button secondary" : "save"}
      aria-label={text}
      aria-pressed={saved}
      onClick={() => void toggleSave(item.id)}
    >
      <Icon name="save" />
      {label && <span>{text}</span>}
    </button>
  );
}

export function DiscoveryCard({ item }: { item: Discovery }) {
  const { t, title, summary, date, labels, open, lang } = useHub();
  return (
    <article
      id={`discovery-${item.id}`}
      className="card"
      style={{ "--cat": colors[item.category] } as CSSProperties}
    >
      <Art item={item} />
      <div className="card-copy">
        {item.isDemo && <DemoBadge english={lang === "en"} />}
        <div className="card-category">
          <span>{labels[item.category]}</span>
          {item.editorialType && item.editorialType !== "news" && (
            <span className="archive">
              {
                ({
                  explainer: t("ENTENDA", "EXPLAINER"),
                  analysis: t("ANÁLISE", "ANALYSIS"),
                  comparison: t("COMPARATIVO", "COMPARISON"),
                  rumor: t("RUMOR", "RUMOR"),
                } as Record<string, string>)[item.editorialType]
              }
            </span>
          )}
          {item.published < "2026-01-01" && (
            <span className="archive">{t("ARQUIVO", "ARCHIVE")}</span>
          )}
        </div>
        <h3>
          <a href={articleUrl(item, lang)}>{title(item)}</a>
        </h3>
        <p>{summary(item)}</p>
        <button className="quiet" onClick={() => open(item)}>
          {t("Espiada rápida", "Quick look")} ↗
        </button>
        <div className="card-bottom">
          <small>
            {item.sourceName}
            <br />
            <time dateTime={radarCardDate(item).day}>{date(item)}</time>
          </small>
          <SaveButton item={item} />
        </div>
      </div>
    </article>
  );
}

export function Passport() {
  const { seen, t, categories, labels, lang } = useHub();
  const account = useAccount();
  if (!account.user) {
    return (
      <aside className="passport">
        <div className="passport-top">
          <Ghost />
          <div>
            <p className="eyebrow">{t("ÁREA DO JOGADOR", "PLAYER AREA")}</p>
            <h2>{t("Curiosidade desbloqueada.", "Curiosity unlocked.")}</h2>
          </div>
        </div>
        <p>
          {t(
            "Entre na sua conta para montar sua mochila, escolher interesses do Seu Radar, registrar sua exploração e participar das missões oficiais.",
            "Sign in to build your backpack, choose topics for Your Radar, track your exploration and join official missions.",
          )}
        </p>
        <div className="stamps" aria-hidden="true">
          {categories.map((cat) => (
            <span key={cat} className="stamp" title={labels[cat]}>
              <Icon name={cat} />
            </span>
          ))}
        </div>
        <button
          type="button"
          className="button secondary"
          onClick={() => {
            savePostLoginIntent({ type: "route", path: `/${lang}/conta/` });
            account.open(account.onboardingRequired ? "onboarding" : "login");
          }}
        >
          {t("Entrar para explorar meu espaço", "Sign in to open my space")}
        </button>
        <small>
          {t(
            "Notícias públicas continuam abertas. Mochila, Radar personalizado e KP são exclusivos da sua conta verificada.",
            "Public stories remain open. Your backpack, personalized Radar and KP belong exclusively to your verified account.",
          )}
        </small>
      </aside>
    );
  }
  return (
    <aside className="passport">
      <div className="passport-top">
        <Ghost />
        <div>
          <p className="eyebrow">{t("SUA EXPLORAÇÃO", "YOUR EXPLORATION")}</p>
          <h2>{t("Curiosidade desbloqueada.", "Curiosity unlocked.")}</h2>
        </div>
      </div>
      <p>
        {t(
          "Abra descobertas de temas diferentes e acompanhe os territórios visitados na sua conta.",
          "Open discoveries across different topics and track the territories visited in your account.",
        )}
      </p>
      <div className="progress-label">
        <span>{t("Territórios explorados", "Territories explored")}</span>
        <b>{seen.size}/6</b>
      </div>
      <div
        className="progress"
        role="progressbar"
        aria-label={t("Territórios", "Territories")}
        aria-valuemin={0}
        aria-valuemax={6}
        aria-valuenow={seen.size}
      >
        <div
          style={{ "--progress": `${(seen.size / 6) * 100}%` } as CSSProperties}
        />
      </div>
      <div className="stamps">
        {categories.map((cat) => (
          <span
            key={cat}
            className={`stamp ${seen.has(cat) ? "done" : ""}`}
            title={labels[cat]}
          >
            <Icon name={cat} />
          </span>
        ))}
      </div>
      <a className="button secondary" href={`/${lang}/conta/interesses/`}>
        {t("Escolher meus interesses", "Choose my interests")}
      </a>
      <small>
        {t(
          "Sincronizado com sua conta AnderZilla.",
          "Synced with your AnderZilla account.",
        )}
      </small>
    </aside>
  );
}

export function DetailDialog() {
  const {
    current,
    setCurrent,
    t,
    title,
    summary,
    fact,
    date,
    labels,
    surprise,
    lang,
  } = useHub();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (current) ref.current?.showModal();
    else ref.current?.close();
    document.body.style.overflow = current ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [current]);
  return (
    <dialog
      ref={ref}
      aria-labelledby="dialog-title"
      onClose={() => setCurrent(null)}
    >
      <button
        id="close"
        onClick={() => setCurrent(null)}
        aria-label={t("Fechar", "Close")}
      >
        ×
      </button>
      {current && (
        <>
          <Art item={current} extra="dialog-art" />
          <div className="dialog-copy">
            <p className="eyebrow">{labels[current.category]}</p>
            <h2 id="dialog-title">{title(current)}</h2>
            {current.isDemo && <DemoBadge english={lang === "en"} />}
            <p className="source">
              {current.sourceName} ·{" "}
              <time dateTime={radarCardDate(current).day}>{date(current)}</time>
            </p>
            <p>{summary(current)}</p>
            <div className="fact">
              <strong>
                {t("O detalhe que vale o clique", "The detail worth the click")}
              </strong>
              <SafeMarkdown body={fact(current)} />
            </div>
            <div className="dialog-buttons">
              <a className="button secondary" href={articleUrl(current, lang)}>
                {t("Ler artigo completo", "Read full article")}
              </a>
              <External className="button" href={current.url}>
                {t("Ver fonte original", "Read original source")} ↗
              </External>
              <SaveButton item={current} label />
              <button className="quiet" onClick={surprise}>
                {t("Outra descoberta →", "Another discovery →")}
              </button>
            </div>
            <p className="note">
              {current.verifiedAt
                ? t(
                    "Apuração documental, com fontes e datas no artigo.",
                    "Documentary reporting; sources and dates are listed in the article.",
                  )
                : t(
                    "Resumo de curadoria, não teste próprio nem link de afiliado. A data se refere à publicação original.",
                    "Curated summary, not a hands-on review or affiliate link. Date refers to original publication.",
                  )}
            </p>
          </div>
        </>
      )}
    </dialog>
  );
}
