"use client";
import { useEffect, useRef, useState } from "react";
import { useHub } from "./HubProvider";
import { discoveries, pointRules, type Mission } from "./model";
import { External, Icon, Passport } from "./Primitives";

export function PointsTeaser() {
  const { t, balance } = useHub();
  return (
    <section className="points-banner">
      <div>
        <p className="eyebrow">KARACA POINTS / {t("MODO DEMO", "DEMO MODE")}</p>
        <h2>
          {t(
            "Sua curiosidade ganha uma nova fase.",
            "Your curiosity levels up.",
          )}
        </h2>
        <p>
          {t(
            "Complete missões. Junte Karaca Points. Explore a futura Store Points.",
            "Complete missions. Collect Karaca Points. Explore the future Store Points.",
          )}
        </p>
      </div>
      <a className="button" href="#points">
        {balance} KP · {t("Ver missões", "View missions")} →
      </a>
    </section>
  );
}
function Wallet({ store = false }: { store?: boolean }) {
  const { t, balance } = useHub();
  return (
    <div className="points-wallet">
      <div>
        <span>{t("SALDO DEMONSTRATIVO", "DEMO BALANCE")}</span>
        <strong>
          {balance} <small>KP</small>
        </strong>
      </div>
      <a
        className={`button ${store ? "" : "pink"}`}
        href={store ? "#points" : "#store"}
      >
        {store ? t("Ganhar pontos", "Earn points") : "Store Points"} →
      </a>
    </div>
  );
}
export function PointsPage() {
  const { t, player, claim, ready } = useHub();
  const missions: {
    id: Mission;
    ready: boolean;
    title: string;
    copy: string;
    url: string;
  }[] = [
    {
      id: "quiz",
      ready: player.quizDone,
      title: t("Checkpoint da curiosidade", "Curiosity checkpoint"),
      copy: t(
        "Acerte as três perguntas do desafio. Uma recompensa por desafio, sem multiplicar ao repetir.",
        "Answer all three challenge questions correctly. One reward per challenge, no replay farming.",
      ),
      url: "#quiz",
    },
    {
      id: "interests",
      ready: player.interests.length >= 3,
      title: t("Monte seu radar", "Build your radar"),
      copy: t(
        "Escolha pelo menos três interesses. Missão única de boas-vindas.",
        "Choose at least three interests. A one-time welcome mission.",
      ),
      url: "#profile",
    },
  ];
  return (
    <div className="wrap subpage">
      <p className="eyebrow">KARACA! / PLAYER HUB</p>
      <h1>
        {t("Descobrir é só o começo.", "Discovery is just the beginning.")}
      </h1>
      <Wallet />
      <p className="notice">
        {t(
          "Prévia: pontos locais, sem valor e sem resgate real. O programa real terá conta, validação de missões e catálogo com estoque confirmado. Este saldo não será migrado.",
          "Preview: local points, no value and no real redemption. The real program will use accounts, mission verification and confirmed inventory. This balance will not migrate.",
        )}
      </p>
      <h2>{t("Suas missões", "Your missions")}</h2>
      <div className="mission-grid">
        {missions.map((m) => (
          <article className="mission-card" key={m.id}>
            <p className="eyebrow">
              +{pointRules[m.id]} KP · {t("DEMONSTRAÇÃO", "DEMO")}
            </p>
            <h3>{m.title}</h3>
            <p>{m.copy}</p>
            {player.claims.includes(m.id) ? (
              <span className="mission-done">
                ✓ {t("Recompensa recebida", "Reward claimed")}
              </span>
            ) : m.ready ? (
              <button
                className="button"
                disabled={!ready}
                onClick={() => claim(m.id)}
              >
                {t("Receber pontos demo", "Claim demo points")}
              </button>
            ) : (
              <a className="button secondary" href={m.url}>
                {t("Começar missão", "Start mission")} →
              </a>
            )}
          </article>
        ))}
      </div>
      <h2>{t("Extrato de Karaca Points", "Karaca Points activity")}</h2>
      <ul className="points-ledger">
        {player.claims.length ? (
          player.claims.map((id) => (
            <li key={id}>
              <span>{missions.find((m) => m.id === id)?.title}</span>
              <strong>+{pointRules[id]} KP</strong>
            </li>
          ))
        ) : (
          <li>
            {t(
              "Sua primeira missão começa agora.",
              "Your first mission starts now.",
            )}
          </li>
        )}
      </ul>
      <p>
        {t(
          "Na Store Points, só pontos conquistados no site. Sem comprar pontos, sem dinheiro no checkout.",
          "Store Points uses only points earned on the site. No points purchases and no cash checkout.",
        )}
      </p>
    </div>
  );
}
export function StorePage() {
  const { t } = useHub();
  return (
    <div className="wrap subpage">
      <p className="eyebrow">KARACA! / STORE POINTS</p>
      <h1>{t("Bons loots. Só com pontos.", "Great loot. Points only.")}</h1>
      <p className="lede">
        {t(
          "O destino dos seus Karaca Points: assinaturas, produtos digitais e gadgets fornecidos pelo AnderZilla. Catálogo em preparação.",
          "The destination for your Karaca Points: subscriptions, digital products and gadgets supplied by AnderZilla. Catalog in preparation.",
        )}
      </p>
      <Wallet store />
      <div className="mission-grid reward-concepts">
        {[
          [t("Assinaturas", "Subscriptions"), "◇"],
          [t("Produtos digitais", "Digital products"), "⌘"],
          ["Gadgets", "✦"],
        ].map(([name, glyph]) => (
          <article key={name} className="mission-card">
            <span className="reward-glyph" aria-hidden="true">
              {glyph}
            </span>
            <p className="eyebrow">
              {t("CATEGORIA PLANEJADA", "PLANNED CATEGORY")}
            </p>
            <h2>{name}</h2>
            <p>
              {t(
                "Produtos, custo em KP e disponibilidade serão anunciados após confirmação do estoque.",
                "Products, KP cost and availability will be announced after inventory confirmation.",
              )}
            </p>
            <button className="button secondary" disabled>
              {t("Em preparação", "In preparation")}
            </button>
          </article>
        ))}
      </div>
      <section className="redemption-steps">
        <h2>
          {t("Do checkpoint ao resgate", "From checkpoint to redemption")}
        </h2>
        <ol>
          <li>
            {t(
              "Ganhe pontos em missões verificadas.",
              "Earn points through verified missions.",
            )}
          </li>
          <li>
            {t(
              "Escolha um item disponível e confira região, entrega e custo em KP.",
              "Choose an available item and check region, delivery and KP cost.",
            )}
          </li>
          <li>
            {t(
              "Confirme o resgate. Os pontos e o estoque ficam reservados durante a análise.",
              "Confirm redemption. Points and stock are reserved during review.",
            )}
          </li>
          <li>
            {t(
              "Acompanhe a entrega na sua conta. Se o pedido for cancelado, a reserva é devolvida.",
              "Track delivery in your account. If cancelled, the reservation is released.",
            )}
          </li>
        </ol>
        <p className="notice">
          {t(
            "Nenhum produto disponível para resgate ainda. Pontos desta prévia são demonstrativos. Não há promessa de prêmio, conversão em dinheiro ou assinatura recorrente.",
            "No products are redeemable yet. Preview points are demonstrations. No prize, cash conversion or recurring subscription is promised.",
          )}
        </p>
      </section>
    </div>
  );
}
export function ProfilePage() {
  const { t, categories, labels, player, toggleInterest, reset } = useHub();
  return (
    <div className="wrap subpage">
      <p className="eyebrow">{t("SEU RADAR", "YOUR RADAR")}</p>
      <h1>{t("Escolha seu universo.", "Choose your universe.")}</h1>
      <p className="lede">
        {t(
          "Seus assuntos favoritos aparecem primeiro. Você ainda pode explorar todos os temas.",
          "Your favorite topics appear first. You can still explore every topic.",
        )}
      </p>
      <div
        className="interest-list"
        role="group"
        aria-label={t("Interesses", "Interests")}
      >
        {categories.map((cat) => (
          <button
            key={cat}
            className="interest"
            aria-pressed={player.interests.includes(cat)}
            onClick={() => toggleInterest(cat)}
          >
            <Icon name={cat} /> {labels[cat]}
          </button>
        ))}
      </div>
      <div style={{ maxWidth: 430 }}>
        <Passport />
      </div>
      <div className="notice">
        {t(
          "Preferências, mochila e progresso ficam somente neste navegador. Sem login, sincronização entre dispositivos ou coleta no servidor.",
          "Preferences, backpack and progress stay only in this browser. No login, cross-device sync or server-side collection.",
        )}
      </div>
      <a className="button" href="#home">
        {t("Voltar ao meu radar", "Back to my radar")}
      </a>
      <button className="quiet" onClick={reset}>
        {t("Limpar meus dados locais", "Clear my local data")}
      </button>
    </div>
  );
}
const questions = [
  {
    cat: "gadgets",
    pt: "Na tradução com AirPods descrita pela Apple, quem faz parte essencial da mágica?",
    en: "In the AirPods translation described by Apple, what is essential to the magic?",
    ptOptions: [
      "Só o fone, sem outro dispositivo.",
      "Apple Intelligence no iPhone compatível.",
      "Qualquer rádio Bluetooth.",
    ],
    enOptions: [
      "Just the earbuds, no other device.",
      "Apple Intelligence on a compatible iPhone.",
      "Any Bluetooth radio.",
    ],
    correct: 1,
  },
  {
    cat: "curiosidades",
    pt: "As auroras de Netuno anunciadas em 2025 foram registradas por qual instrumento?",
    en: "Which instrument captured the Neptune auroras announced in 2025?",
    ptOptions: [
      "Uma câmera de celular em órbita.",
      "O telescópio espacial Hubble.",
      "O espectrógrafo de infravermelho próximo do Webb.",
    ],
    enOptions: [
      "A phone camera in orbit.",
      "The Hubble Space Telescope.",
      "Webb’s near-infrared spectrograph.",
    ],
    correct: 2,
  },
  {
    cat: "celulares",
    pt: "Qual conexão com acessórios a Apple adicionou ao iPhone 17e?",
    en: "Which accessory connection did Apple add to iPhone 17e?",
    ptOptions: [
      "MagSafe.",
      "Entrada para cartuchos.",
      "Porta de fita cassete.",
    ],
    enOptions: ["MagSafe.", "A cartridge slot.", "A cassette tape port."],
    correct: 0,
  },
];
export function QuizPage() {
  const { t, lang, fact, completeQuiz } = useHub();
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState<number | null>(null);
  const [result, setResult] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const questionChanged = useRef(false);
  useEffect(() => {
    if (questionChanged.current) headingRef.current?.focus();
    questionChanged.current = true;
  }, [index, result]);
  const q = questions[index];
  const source = discoveries.find((x) => x.category === q.cat)!;
  if (result)
    return (
      <div className="wrap subpage quiz-page">
        <div className="badge-large">
          <Icon name="trophy" />
        </div>
        <h1 ref={headingRef} tabIndex={-1}>
          {t("Selo: curiosidade em dia.", "Badge: curiosity powered up.")}
        </h1>
        <p className="lede">
          {t(
            "Karaca! Você completou as três perguntas. A primeira conclusão libera 100 KP demonstrativos. Repetir não multiplica a recompensa.",
            "Karaca! You completed all three questions. Your first completion unlocks 100 demo KP. Replays do not multiply the reward.",
          )}
        </p>
        <button
          className="button"
          onClick={() => {
            setIndex(0);
            setAnswer(null);
            setResult(false);
          }}
        >
          {t("Jogar de novo", "Play again")}
        </button>{" "}
        <a className="button secondary" href="#points">
          Karaca Points →
        </a>
      </div>
    );
  return (
    <div className="wrap subpage quiz-page">
      <p className="eyebrow">
        <Icon name="trophy" />
        {t("DESAFIO DA VEZ", "YOUR NEXT CHALLENGE")}
      </p>
      <h1>
        {t(
          "Um checkpoint para a curiosidade.",
          "A checkpoint for your curiosity.",
        )}
      </h1>
      <p className="lede">
        {t(
          "O desafio usa as fontes do radar. Pode tentar de novo: cada resposta vem com uma explicação.",
          "This challenge uses sources from the radar. Try again anytime: every answer comes with an explanation.",
        )}
      </p>
      <section className="quiz-box">
        <p className="quiz-progress">
          {t("PERGUNTA", "QUESTION")} {index + 1} / 3
        </p>
        <h2 ref={headingRef} tabIndex={-1}>
          {q[lang]}
        </h2>
        <div className="answers">
          {(lang === "pt" ? q.ptOptions : q.enOptions).map((label, i) => (
            <button
              key={label}
              className={`answer ${answer === i ? (i === q.correct ? "correct" : "wrong") : ""}`}
              disabled={answer !== null}
              onClick={() => setAnswer(i)}
            >
              {String.fromCharCode(65 + i)}. {label}
            </button>
          ))}
        </div>
        {answer !== null && (
          <>
            <div className="feedback" role="status">
              <strong>
                {answer === q.correct
                  ? t("Boa! Esse é o detalhe.", "Nice! That is the detail.")
                  : t(
                      "Quase. Veja o que a fonte explica:",
                      "Almost. Here is what the source explains:",
                    )}
              </strong>
              <p>{fact(source)}</p>
              <External href={source.url}>{source.sourceName} ↗</External>
            </div>
            <button
              className="button"
              onClick={() => {
                if (answer === q.correct) {
                  if (index === 2) {
                    completeQuiz();
                    setResult(true);
                  } else setIndex(index + 1);
                }
                setAnswer(null);
              }}
            >
              {answer !== q.correct
                ? t("Tentar novamente", "Try again")
                : index === 2
                  ? t("Ver meu selo", "See my badge")
                  : t("Próxima pergunta", "Next question")}
              <Icon name="arrow" />
            </button>
          </>
        )}
      </section>
    </div>
  );
}
