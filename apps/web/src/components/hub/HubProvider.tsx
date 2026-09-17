"use client";
import {useAccount} from "../account/AccountProvider";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
  type ReactNode,
} from "react";
import {
  categories,
  discoveries,
  freshPlayer,
  parsePlayer,
  routes,
  type Category,
  type Discovery,
  type Language,
  type Mission,
  type PlayerState,
  type Route,
} from "./model";

function useHubState() {
  const [lang, setLang] = useState<Language>("pt");
  const [route, setRoute] = useState<Route>("home");
  const account=useAccount();
  const interestPrompted=useRef(false);
  const [guestPlayer, setPlayer] = useState<PlayerState>(freshPlayer);
  const player:PlayerState=account.user?{...guestPlayer,saved:account.user.saved,opened:account.user.opened,interests:account.user.interests.filter((c):c is Category=>categories.includes(c as Category)),claims:[]}:guestPlayer;
  const [ready, setReady] = useState(false);
  const [storage, setStorage] = useState(true);
  const [current, setCurrent] = useState<Discovery | null>(null);
  const [toast, setToast] = useState("");
  const [filter, setFilter] = useState<Category | "all">("all");
  const t = (pt: string, en: string) => (lang === "pt" ? pt : en);
  useEffect(() => {
    const sync = () => {
      const hash = window.location.hash.slice(1);
      setRoute(routes.includes(hash as Route) ? (hash as Route) : "home");
      setCurrent(null);
    };
    setLang(
      new URLSearchParams(window.location.search).get("lang") === "en"
        ? "en"
        : "pt",
    );
    const requestedCategory = new URLSearchParams(window.location.search).get("category");
    if(categories.includes(requestedCategory as Category))setFilter(requestedCategory as Category);
    sync();
    try {
      setPlayer(
        parsePlayer(
          JSON.parse(localStorage.getItem("anderzilla-hub-demo-v1") || "null"),
        ),
      );
    } catch {
      setStorage(false);
    }
    setReady(true);
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);
  useEffect(() => {
    if (ready) {
      try {
        localStorage.setItem("anderzilla-hub-demo-v1", JSON.stringify(guestPlayer));
      } catch {
        setStorage(false);
      }
    }
  }, [guestPlayer, ready]);
  useEffect(() => {
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
  }, [lang]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 3200);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    if (ready) {
      document.getElementById("hub-main")?.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    }
  }, [route, ready]);
  useEffect(()=>{if(account.user)setLang(account.user.language)},[account.user?.id,account.user?.language]);
  const changeLanguage = (value: Language) => {
    setLang(value);
    if(account.user)void account.savePreferences({language:value});
    const url = new URL(window.location.href);
    url.searchParams.set("lang", value);
    window.history.replaceState(null, "", url);
  };
  const toggleSave = (id: string) => {
    if(account.user){void account.savePreferences({saved:player.saved.includes(id)?player.saved.filter(x=>x!==id):[...player.saved,id]});return}
    setPlayer((p) => ({
      ...p,
      saved: p.saved.includes(id)
        ? p.saved.filter((x) => x !== id)
        : [...p.saved, id],
    }));
    setToast(t("Mochila atualizada.", "Backpack updated."));
  };
  const open = (item: Discovery) => {
    setCurrent(item);
    if(account.user){if(!player.opened.includes(item.id))void account.savePreferences({opened:[...player.opened,item.id]});return}
    setPlayer((p) => ({
      ...p,
      opened: p.opened.includes(item.id) ? p.opened : [...p.opened, item.id],
    }));
  };
  const surprise = () => {
    let pool = discoveries.filter((x) => !player.opened.includes(x.id));
    if (!pool.length) pool = discoveries.filter((x) => x.id !== current?.id);
    open(pool[Math.floor(Math.random() * pool.length)]);
  };
  const toggleInterest = (category: Category) => {
    if(account.user){void account.savePreferences({interests:player.interests.includes(category)?player.interests.filter(c=>c!==category):[...player.interests,category]});return}
    const next=player.interests.includes(category)?player.interests.filter(c=>c!==category):[...player.interests,category];
    setPlayer(p=>({...p,interests:next}));
    if(next.length>=3&&player.interests.length<3&&!interestPrompted.current){interestPrompted.current=true;account.open('reward')}
  };
  const claim = (id: Mission) => {
    const eligible=id==='quiz'?player.quizDone:player.interests.length>=3;
    if(!eligible)return;
    if(!account.user)account.open('reward');
    else setToast(t('Este progresso é local. KP oficial exige uma missão validada pelo servidor.','This progress is local. Official KP require a server-validated mission.'));
  };
  const completeQuiz = () => {
    setPlayer(p=>({...p,quizDone:true}));
    if(!account.user)account.open('reward');
    else setToast(t('Desafio local concluído. Nenhum KP oficial foi creditado.','Local challenge completed. No official KP were credited.'));
  };
  const reset = () => {
    setPlayer(freshPlayer());
    setToast(t("Dados locais limpos.", "Local data cleared."));
  };
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
  const date = (x: Discovery) =>
    new Intl.DateTimeFormat(lang === "pt" ? "pt-BR" : "en-US", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      timeZone: "UTC",
    }).format(new Date(x.published + "T12:00:00Z"));
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
    filter,
    setFilter,
    t,
    changeLanguage,
    toggleSave,
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
export function HubProvider({ children }: { children: ReactNode }) {
  const state = useHubState();
  return <Context.Provider value={state}>{children}</Context.Provider>;
}
export function useHub() {
  const context = useContext(Context);
  if (!context) throw new Error("HubProvider is required");
  return context;
}
