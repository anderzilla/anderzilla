"use client";
import { useRouter } from "next/navigation";
import {
  useAccount,
  AccountError,
  purgeLegacyVisitorStorage,
  savePostLoginIntent,
} from "../account/AccountProvider";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  categories,
  discoveries,
  freshPlayer,
  radarCardLabel,
  routes,
  type Category,
  type Discovery,
  type Language,
  type Mission,
  type PlayerState,
  type Route,
} from "./model";

function localeFromPath(pathname: string): Language | null {
  const first = pathname.split("/").filter(Boolean)[0];
  return first === "pt" || first === "en" ? first : null;
}

const LEGACY_HASH_REDIRECTS: Record<string, string> = {
  profile: "conta/perfil/",
  saved: "conta/mochila/",
  points: "conta/kp/",
  missions: "conta/missoes/",
  quiz: "conta/missoes/",
};

function useHubState(initialLang: Language) {
  const router = useRouter();
  const [lang, setLang] = useState<Language>(initialLang);
  const [route, setRoute] = useState<Route>("home");
  const account = useAccount();

  // Only authenticated members have saved/opened/interests. Visitors have zero personal state.
  const emptyGuest = freshPlayer();
  const player: PlayerState = account.user
    ? {
        ...emptyGuest,
        saved: account.user.saved,
        opened: account.user.opened,
        interests: account.user.interests.filter((c): c is Category =>
          categories.includes(c as Category),
        ),
        claims: [],
        quizDone: false,
      }
    : emptyGuest;

  const [ready, setReady] = useState(false);
  const [storage] = useState(true);
  const [current, setCurrent] = useState<Discovery | null>(null);
  const [toast, setToast] = useState("");
  const [undoItem, setUndoItem] = useState<{ id: string; expiresAt: number } | null>(null);
  const [filter, setFilter] = useState<Category | "all">("all");
  const [langPrompt, setLangPrompt] = useState<Language | null>(null);
  const t = useCallback((pt: string, en: string) => (lang === "pt" ? pt : en), [lang]);

  useEffect(() => {
    purgeLegacyVisitorStorage();
    const fromPath = localeFromPath(window.location.pathname);
    const activeLang =
      fromPath ??
      (new URLSearchParams(window.location.search).get("lang") === "en"
        ? "en"
        : "pt");
    setLang(activeLang);

    const sync = () => {
      const hash = window.location.hash.slice(1);
      if (hash && LEGACY_HASH_REDIRECTS[hash]) {
        window.location.replace(`/${activeLang}/${LEGACY_HASH_REDIRECTS[hash]}`);
        return;
      }
      setRoute(routes.includes(hash as Route) ? (hash as Route) : "home");
      setCurrent(null);
    };
    const requestedCategory = new URLSearchParams(window.location.search).get("category");
    if (categories.includes(requestedCategory as Category)) {
      setFilter(requestedCategory as Category);
    }
    sync();
    setReady(true);
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
  }, [lang]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    if (!undoItem) return;
    const remaining = Math.max(500, undoItem.expiresAt - Date.now());
    const timer = setTimeout(() => setUndoItem(null), remaining);
    return () => clearTimeout(timer);
  }, [undoItem]);

  useEffect(() => {
    if (ready) {
      document.getElementById("hub-main")?.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    }
  }, [route, ready]);

  useEffect(() => {
    if (account.user && !localeFromPath(window.location.pathname)) {
      setLang(account.user.language);
    }
  }, [account.user?.id, account.user?.language]);

  const navigateWithLanguage = useCallback((value: Language) => {
    setLang(value);
    const url = new URL(window.location.href);
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts[0] === "pt" || parts[0] === "en") {
      parts[0] = value;
      url.pathname = `/${parts.join("/")}/`;
      url.searchParams.delete("lang");
      router.push(url.pathname + url.search + url.hash);
      return;
    }
    url.searchParams.set("lang", value);
    window.history.replaceState(null, "", url);
  }, [router]);

  const changeLanguage = useCallback(
    async (value: Language, forceWithoutSave = false) => {
      if (account.user && !forceWithoutSave) {
        try {
          await account.patchProfile({ language: value });
          setLangPrompt(null);
          navigateWithLanguage(value);
        } catch {
          setLangPrompt(value);
          setToast(
            t(
              "Ainda não conseguimos confirmar essa mudança. Vamos conferir?",
              "We couldn’t confirm this change yet. Let’s check.",
            ),
          );
        }
        return;
      }
      setLangPrompt(null);
      navigateWithLanguage(value);
    },
    [account, navigateWithLanguage, t],
  );

  const requireMemberOrPrompt = useCallback(
    (intentPath?: string, saveDiscoveryId?: string): boolean => {
      if (!account.signedIn) {
        savePostLoginIntent({
          type: saveDiscoveryId ? "save_article" : "route",
          path: intentPath || window.location.pathname,
          discoveryId: saveDiscoveryId,
        });
        account.open("login");
        setToast(
          t(
            "Entre para montar sua mochila e continuar sua jornada.",
            "Sign in to build your backpack and continue exploring.",
          ),
        );
        return false;
      }
      if (account.onboardingRequired || !account.user) {
        savePostLoginIntent({
          type: saveDiscoveryId ? "save_article" : "route",
          path: intentPath || window.location.pathname,
          discoveryId: saveDiscoveryId,
        });
        account.open("onboarding");
        setToast(
          t(
            "Falta um passo para liberar seu espaço. Vamos concluir seu cadastro?",
            "One step left to unlock your space. Let’s finish your account.",
          ),
        );
        return false;
      }
      return true;
    },
    [account, t],
  );

  const toggleSave = useCallback(
    async (id: string) => {
      if (!requireMemberOrPrompt(window.location.pathname, id)) return;
      const isSaved = player.saved.includes(id);
      try {
        if (isSaved) {
          await account.request(`/api/member/backpack/${encodeURIComponent(id)}`, "DELETE", {});
          await account.refresh();
          account.notifySync("collections_updated");
          setUndoItem({ id, expiresAt: Date.now() + 8000 });
          setToast(t("Descoberta removida da mochila.", "Discovery removed from your backpack."));
        } else {
          await account.request(`/api/member/backpack/${encodeURIComponent(id)}`, "PUT", {});
          await account.refresh();
          account.notifySync("collections_updated");
          setUndoItem(null);
          setToast(t("Foi para a mochila. Bora para a próxima?", "Saved to your backpack. Ready for the next discovery?"));
        }
      } catch (e) {
        if (e instanceof AccountError && e.code === "content_unavailable") {
          setToast(t("Esta descoberta não está disponível agora.", "This discovery isn’t available right now."));
        } else {
          setToast(t("Ainda não conseguimos confirmar essa mudança. Vamos conferir?", "We couldn’t confirm this change yet. Let’s check."));
        }
      }
    },
    [account, player.saved, requireMemberOrPrompt, t],
  );

  const undoRemoveBookmark = useCallback(async () => {
    if (!undoItem || !account.user) return;
    const id = undoItem.id;
    setUndoItem(null);
    try {
      await account.request(`/api/member/backpack/${encodeURIComponent(id)}`, "PUT", {});
      await account.refresh();
      account.notifySync("collections_updated");
      setToast(t("Foi para a mochila. Bora para a próxima?", "Saved to your backpack. Ready for the next discovery?"));
    } catch {
      setToast(t("Ainda não conseguimos confirmar essa mudança. Vamos conferir?", "We couldn’t confirm this change yet. Let’s check."));
    }
  }, [undoItem, account, t]);

  const recordOpen = useCallback(
    async (discoveryId: string) => {
      if (!account.user) return;
      const gen = account.user.explorationGeneration || 1;
      const eventId = `open-${discoveryId}-${gen}-${Math.floor(Date.now() / 10000)}`;
      try {
        await account.request("/api/member/exploration/events", "POST", {
          discoveryId,
          eventType: "open",
          eventId,
          historyGeneration: gen,
        });
        await account.refresh();
        account.notifySync("collections_updated");
      } catch {}
    },
    [account],
  );

  const open = useCallback(
    (item: Discovery) => {
      setCurrent(item);
      if (account.user) {
        void recordOpen(item.id);
      }
    },
    [account.user, recordOpen],
  );

  const surprise = useCallback(() => {
    let pool = discoveries.filter((x) => !x.isDemo && !player.opened.includes(x.id));
    if (!pool.length) pool = discoveries.filter((x) => !x.isDemo && x.id !== current?.id);
    if (pool.length) open(pool[Math.floor(Math.random() * pool.length)]);
  }, [player.opened, current?.id, open]);

  const toggleInterest = useCallback(
    async (category: Category) => {
      if (!requireMemberOrPrompt(`/${lang}/conta/interesses/`)) return;
      const next = player.interests.includes(category)
        ? player.interests.filter((c) => c !== category)
        : [...player.interests, category];
      try {
        await account.request("/api/member/interests", "PUT", {
          categoryIds: next,
          expectedVersion: account.user?.interestsVersion || 1,
        });
        await account.refresh();
        account.notifySync("collections_updated");
        setToast(t("Seu Radar ganhou novos rumos.", "Your radar has a fresh direction."));
      } catch (e) {
        if (e instanceof AccountError && e.code === "interests_conflict") {
          await account.refresh().catch(() => {});
          setToast(
            t(
              "Seus interesses mudaram em outro acesso. Confira a seleção antes de salvar.",
              "Your interests changed in another session. Review your selection before saving.",
            ),
          );
        } else {
          setToast(
            t(
              "Ainda não conseguimos confirmar essa mudança. Vamos conferir?",
              "We couldn’t confirm this change yet. Let’s check.",
            ),
          );
        }
      }
    },
    [account, lang, player.interests, requireMemberOrPrompt, t],
  );

  const claim = useCallback(
    (_id: Mission) => {
      if (!requireMemberOrPrompt(`/${lang}/conta/missoes/`)) return;
      router.push(`/${lang}/conta/missoes/`);
    },
    [lang, requireMemberOrPrompt],
  );

  const completeQuiz = useCallback(() => {
    if (!requireMemberOrPrompt(`/${lang}/conta/missoes/`)) return;
    router.push(`/${lang}/conta/missoes/`);
  }, [lang, requireMemberOrPrompt]);

  const reset = useCallback(async () => {
    if (!requireMemberOrPrompt(`/${lang}/conta/exploracao/`)) return;
    try {
      await account.request("/api/member/exploration/clear", "POST", {
        confirm: true,
        expectedGeneration: account.user?.explorationGeneration || 1,
      });
      await account.refresh();
      account.notifySync("collections_updated");
      setToast(
        t(
          "Mapa renovado. Seu histórico de exploração foi limpo.",
          "A fresh map. Your exploration history is cleared.",
        ),
      );
    } catch {
      setToast(
        t(
          "Ainda não conseguimos confirmar essa mudança. Vamos conferir?",
          "We couldn’t confirm this change yet. Let’s check.",
        ),
      );
    }
  }, [account, lang, requireMemberOrPrompt, t]);

  const labels: Record<Category | "all", string> = {
    all: t("Tudo junto", "Everything"),
    games: "Games",
    consoles: "Consoles",
    celulares: t("Celulares", "Phones"),
    ia: t("Inteligência artificial", "Artificial intelligence"),
    gadgets: "Gadgets",
    curiosidades: t("Curiosidades", "Curiosities"),
  };
  const title = (x: Discovery) => (lang === "pt" ? x.titlePT : x.titleEN);
  const summary = (x: Discovery) => (lang === "pt" ? x.summaryPT : x.summaryEN);
  const fact = (x: Discovery) => (lang === "pt" ? x.fact : x.factEN);
  const date = (x: Discovery) => radarCardLabel(x, lang);
  const seen = new Set(
    discoveries
      .filter((x) => player.opened.includes(x.id))
      .map((x) => x.category),
  );
  const balance = account.balance;

  return {
    lang,
    route,
    player,
    ready,
    storage,
    current,
    setCurrent,
    toast,
    setToast,
    undoItem,
    undoRemoveBookmark,
    langPrompt,
    setLangPrompt,
    filter,
    setFilter,
    t,
    changeLanguage,
    requireMemberOrPrompt,
    toggleSave,
    recordOpen,
    open,
    surprise,
    toggleInterest,
    claim,
    completeQuiz,
    reset,
    labels,
    title,
    summary,
    fact,
    date,
    seen,
    balance,
    categories,
  };
}

const Context = createContext<ReturnType<typeof useHubState> | null>(null);

export function HubProvider({
  children,
  initialLang = "pt",
}: {
  children: ReactNode;
  initialLang?: Language;
}) {
  const state = useHubState(initialLang);
  return <Context.Provider value={state}>{children}</Context.Provider>;
}

export function useHub() {
  const context = useContext(Context);
  if (!context) throw new Error("HubProvider is required");
  return context;
}
