"use client";

import { useEffect, useMemo, useRef, useState, useSyncExternalStore, type FocusEvent, type KeyboardEvent, type PointerEvent } from "react";
import { articleUrl, discoveries, radarCardDate, type Discovery } from "./model";
import { buildHeroSlides, heroUpdatedLabel, type HeroSlide } from "./hero-slides";
import { type ManualBanner } from "./hero-banners";
import { findMedia } from "./Editorial";
import { Icon } from "./Primitives";
import { useHub } from "./HubProvider";

const AUTOPLAY_MS = 6500;

function subscribeUtcDay(onChange: () => void) {
  const timer = window.setInterval(onChange, 60 * 60 * 1000);
  document.addEventListener("visibilitychange", onChange);
  return () => {
    window.clearInterval(timer);
    document.removeEventListener("visibilitychange", onChange);
  };
}

function useUtcDay() {
  return useSyncExternalStore(
    subscribeUtcDay,
    () => new Date().toISOString().slice(0, 10),
    () => "",
  );
}

function slideId(slide: HeroSlide) {
  return slide.kind === "news" ? `news-${slide.item.id}` : `manual-${slide.banner.id}`;
}

function BannerTitle({ banner }: { banner: ManualBanner }) {
  const { lang } = useHub();
  const lines = banner.title[lang].split("\n");
  return (
    <h2>
      {lines.map((line, index) => {
        const emphasis = banner.emphasis;
        const at = emphasis ? line.indexOf(emphasis) : -1;
        return (
          <span key={`${index}-${line}`}>
            {index > 0 && <br />}
            {at >= 0 && emphasis ? (
              <>
                {line.slice(0, at)}
                <em>{emphasis}</em>
                {line.slice(at + emphasis.length)}
              </>
            ) : (
              line
            )}
          </span>
        );
      })}
    </h2>
  );
}

function SlideArt({
  src,
  alt,
  width,
  height,
}: {
  src: string;
  alt: string;
  width?: number;
  height?: number;
}) {
  return (
    <img
      className="hero-slide-art"
      src={src}
      alt={alt}
      width={width}
      height={height}
      decoding="async"
      draggable={false}
    />
  );
}

function NewsSlide({ item, active }: { item: Discovery; active: boolean }) {
  const { t, lang, title, labels } = useHub();
  const media = findMedia(item.coverMediaId);
  const day = radarCardDate(item).day;
  const label = heroUpdatedLabel(item, lang);
  return (
    <>
      {media && (
        <SlideArt
          src={media.url}
          alt={(lang === "pt" ? media.altPT : media.altEN) || ""}
          width={media.width}
          height={media.height}
        />
      )}
      <div className="brand-hero-copy">
        <p className="eyebrow">
          <span className="tag">{labels[item.category]}</span>
          {t("NOTÍCIA", "STORY")}
        </p>
        <h2>{title(item)}</h2>
        {label && (
          <p className="hero-updated">
            <time dateTime={day}>{label}</time>
          </p>
        )}
        <div className="hero-buttons">
          <a className="button" href={articleUrl(item, lang)} tabIndex={active ? undefined : -1}>
            {t("Ler notícia completa", "Read the full story")}
            <Icon name="arrow" />
          </a>
        </div>
      </div>
    </>
  );
}

function ManualSlide({
  banner,
  active,
  onExplore,
}: {
  banner: ManualBanner;
  active: boolean;
  onExplore: () => void;
}) {
  const { t, lang, surprise } = useHub();
  const link = banner.link?.[lang];
  const external = !!link && /^https:\/\//i.test(link);
  return (
    <>
      <SlideArt
        src={banner.image}
        alt={banner.imageAlt[lang]}
        width={banner.width}
        height={banner.height}
      />
      <div className="brand-hero-copy">
        <p className="eyebrow">
          <span className="tag">{banner.kicker[lang]}</span>
          {banner.kickerNote?.[lang]}
        </p>
        <BannerTitle banner={banner} />
        <p>{banner.text[lang]}</p>
        <div className="hero-buttons">
          {link ? (
            <a
              className="button"
              href={link}
              tabIndex={active ? undefined : -1}
              {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
            >
              {banner.cta?.[lang] || t("Saiba mais", "Learn more")}
              <Icon name="arrow" />
            </a>
          ) : (
            banner.fallback && (
              <>
                <button className="button" type="button" onClick={onExplore} tabIndex={active ? undefined : -1}>
                  {t("Entrar no radar", "Explore the radar")}
                  <Icon name="arrow" />
                </button>
                <button className="button secondary" type="button" onClick={surprise} tabIndex={active ? undefined : -1}>
                  <Icon name="shuffle" />
                  {t("Abrir uma surpresa", "Open a surprise")}
                </button>
              </>
            )
          )}
        </div>
      </div>
    </>
  );
}

export function HeroCarousel({ onExplore }: { onExplore: () => void }) {
  const { t, lang, title } = useHub();
  const today = useUtcDay();
  const slides = useMemo(() => buildHeroSlides(discoveries, today), [today]);
  const signature = slides.map(slideId).join("|");
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [pageHidden, setPageHidden] = useState(false);
  const [motion, setMotion] = useState<"unknown" | "reduce" | "ok">("unknown");
  const [announcement, setAnnouncement] = useState("");
  const swipe = useRef<{ id: number; x: number; y: number } | null>(null);
  const root = useRef<HTMLElement>(null);
  const count = slides.length;
  const active = ((index % count) + count) % count;

  useEffect(() => {
    setIndex(0);
  }, [signature]);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setMotion(media.matches ? "reduce" : "ok");
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);

  useEffect(() => {
    const apply = () => setPageHidden(document.hidden);
    apply();
    document.addEventListener("visibilitychange", apply);
    return () => document.removeEventListener("visibilitychange", apply);
  }, []);

  const autoplay = motion === "ok" && count > 1 && !paused && !hovered && !focused && !pageHidden;

  useEffect(() => {
    if (!autoplay) return;
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % count);
    }, AUTOPLAY_MS);
    return () => window.clearInterval(timer);
  }, [autoplay, count, active]);

  function labelOf(slide: HeroSlide) {
    const text = slide.kind === "news" ? title(slide.item) : slide.banner.title[lang];
    return text.replace(/\n/g, " ");
  }

  function go(next: number, announce: boolean) {
    const wrapped = ((next % count) + count) % count;
    const focusedSlide = document.activeElement?.closest(".hero-slide");
    setIndex(wrapped);
    if (focusedSlide) {
      queueMicrotask(() => root.current?.querySelector<HTMLElement>(".hero-control")?.focus());
    }
    if (!announce) return;
    const position = t(`Slide ${wrapped + 1} de ${count}`, `Slide ${wrapped + 1} of ${count}`);
    setAnnouncement(`${position}: ${labelOf(slides[wrapped])}`);
  }

  function onKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (count < 2 || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === "ArrowRight") {
      event.preventDefault();
      go(active + 1, true);
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      go(active - 1, true);
    } else if (event.key === "Home") {
      event.preventDefault();
      go(0, true);
    } else if (event.key === "End") {
      event.preventDefault();
      go(count - 1, true);
    }
  }

  function onPointerDown(event: PointerEvent<HTMLElement>) {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    const target = event.target;
    if (target instanceof Element && target.closest("a, button")) return;
    swipe.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
  }

  function onPointerUp(event: PointerEvent<HTMLElement>) {
    const start = swipe.current;
    swipe.current = null;
    if (!start || start.id !== event.pointerId || count < 2) return;
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    if (Math.abs(dx) < 48 || Math.abs(dx) < Math.abs(dy) * 1.2) return;
    go(active + (dx < 0 ? 1 : -1), true);
  }

  return (
    <section
      ref={root}
      className="hero brand-hero hero-carousel"
      aria-roledescription={t("carrossel", "carousel")}
      aria-label={t("Destaques do radar", "Radar highlights")}
      tabIndex={count > 1 ? 0 : undefined}
      onKeyDown={onKeyDown}
      onFocus={() => setFocused(true)}
      onBlur={(event: FocusEvent<HTMLElement>) => {
        const next = event.relatedTarget;
        if (next instanceof Node && event.currentTarget.contains(next)) return;
        setFocused(false);
      }}
      onPointerEnter={(event) => {
        if (event.pointerType === "mouse") setHovered(true);
      }}
      onPointerLeave={(event) => {
        if (event.pointerType === "mouse") setHovered(false);
      }}
      onPointerDown={onPointerDown}
      onPointerUp={onPointerUp}
      onPointerCancel={() => {
        swipe.current = null;
      }}
    >
      {slides.map((slide, slideIndex) => {
        const shown = slideIndex === active;
        const position = t(`Slide ${slideIndex + 1} de ${count}`, `Slide ${slideIndex + 1} of ${count}`);
        return (
          <div
            key={slideId(slide)}
            className={`hero-slide${count > 1 ? " has-controls" : ""}`}
            id={`hero-slide-${slideId(slide)}`}
            role="group"
            aria-roledescription={t("slide", "slide")}
            aria-label={`${position}: ${labelOf(slide)}`}
            hidden={!shown}
          >
            {slide.kind === "news" ? (
              <NewsSlide item={slide.item} active={shown} />
            ) : (
              <ManualSlide banner={slide.banner} active={shown} onExplore={onExplore} />
            )}
          </div>
        );
      })}
      {count > 1 && (
        <div className="hero-controls">
          <button type="button" className="hero-control" onClick={() => go(active - 1, true)} aria-label={t("Slide anterior", "Previous slide")}>
            <Icon name="chevron-left" />
          </button>
          <div className="hero-dots" role="group" aria-label={t("Escolher slide", "Choose slide")}>
            {slides.map((slide, slideIndex) => (
              <button
                key={slideId(slide)}
                type="button"
                className="hero-dot"
                aria-current={slideIndex === active ? "true" : undefined}
                aria-label={`${t(`Slide ${slideIndex + 1} de ${count}`, `Slide ${slideIndex + 1} of ${count}`)}: ${labelOf(slide)}`}
                onClick={() => go(slideIndex, true)}
              />
            ))}
          </div>
          {motion === "ok" && (
            <button
              type="button"
              className="hero-control"
              aria-pressed={paused}
              onClick={() => setPaused((value) => !value)}
            >
              <Icon name={paused ? "play" : "pause"} />
              <span className="visually-hidden">
                {paused ? t("Retomar rotação automática", "Resume automatic rotation") : t("Pausar rotação automática", "Pause automatic rotation")}
              </span>
            </button>
          )}
          <button type="button" className="hero-control" onClick={() => go(active + 1, true)} aria-label={t("Próximo slide", "Next slide")}>
            <Icon name="chevron-right" />
          </button>
        </div>
      )}
      <p className="visually-hidden" aria-live="polite">
        {announcement}
      </p>
    </section>
  );
}
