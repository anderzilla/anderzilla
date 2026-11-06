"use client";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useAccount, AccountError } from "./AccountProvider";
import { useHub } from "../hub/HubProvider";
import { AccountFeedback, MEMBER_MESSAGES } from "./AccountUI";

export type OfficialMissionItem = {
  id: string;
  version: number;
  awardKP: number;
  titlePT?: string;
  titleEN?: string;
  summaryPT?: string;
  summaryEN?: string;
  eligibility?: string;
  Completed?: boolean;
  completed?: boolean;
  receipt?: {
    receiptId?: string;
    awardedKP?: number;
    completedAt?: string;
  } | null;
  activeAttempt?: {
    attemptId: string;
    challengeId: string;
    status: string;
    expiresAt: string;
  } | null;
  pendingClaim?: {
    pendingId: string;
    pendingToken?: string;
    evidenceRef?: string;
    awardPreview: number;
    expiresAt: string;
    status: string;
  } | null;
};

type Challenge = {
  attemptId?: string;
  challengeId: string;
  missionId?: string;
  missionVersion?: number;
  kind: string;
  expiresAt: string;
  titlePT?: string;
  titleEN?: string;
  questions?: {
    id: string;
    promptPT: string;
    promptEN: string;
    options: { id: string; textPT: string; textEN: string }[];
  }[];
};

function expiry(value: string | number) {
  return typeof value === "number"
    ? new Date(value * 1000).toISOString()
    : value;
}

export function OfficialMissions({
  focusMissionId,
}: {
  focusMissionId?: string;
}) {
  const a = useAccount();
  const { t, lang, player, labels, categories } = useHub();
  const [missions, setMissions] = useState<OfficialMissionItem[]>([]);
  const [programStatus, setProgramStatus] = useState<string>("disabled");
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle",
  );
  const [selected, setSelected] = useState<OfficialMissionItem | null>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [interests, setInterests] = useState<string[]>([]);
  const [reload, setReload] = useState(0);
  const [lastClaimKey, setLastClaimKey] = useState<string | null>(null);
  const [uncertainClaim, setUncertainClaim] = useState(false);

  useEffect(() => {
    if (a.status !== "ready" || !a.user) {
      setMissions([]);
      setStatus("idle");
      return;
    }
    let active = true;
    setStatus("loading");
    void a
      .request("/api/points/missions")
      .then((data) => {
        if (!active) return;
        const items: OfficialMissionItem[] = Array.isArray(data.items)
          ? data.items
          : [];
        setMissions(items);
        setProgramStatus(
          typeof data.programStatus === "string"
            ? data.programStatus
            : a.capabilities.rewards
              ? "active"
              : "disabled",
        );
        setStatus("ready");
        if (focusMissionId) {
          const target = items.find((m) => m.id === focusMissionId);
          if (target) {
            setSelected(target);
            if (target.activeAttempt?.attemptId) {
              void a
                .request(
                  `/api/points/challenges/${encodeURIComponent(target.activeAttempt.attemptId)}`,
                )
                .then((ch) => {
                  if (active && ch && ch.challengeId) {
                    setChallenge({
                      ...ch,
                      expiresAt: expiry(ch.expiresAt),
                      titlePT: ch.titlePT || target.titlePT,
                      titleEN: ch.titleEN || target.titleEN,
                    });
                  }
                })
                .catch(() => undefined);
            }
          }
        }
      })
      .catch(() => {
        if (active) setStatus("error");
      });
    return () => {
      active = false;
    };
  }, [a.status, a.user, a.capabilities.rewards, a.request, reload, focusMissionId]);

  async function start(m: OfficialMissionItem) {
    await a.action(async () => {
      if (m.activeAttempt?.attemptId) {
        try {
          const resumed = await a.request(
            `/api/points/challenges/${encodeURIComponent(m.activeAttempt.attemptId)}`,
          );
          if (resumed && resumed.challengeId && resumed.status === "issued") {
            setSelected(m);
            setChallenge({
              ...resumed,
              expiresAt: expiry(resumed.expiresAt),
              titlePT: resumed.titlePT || m.titlePT,
              titleEN: resumed.titleEN || m.titleEN,
            });
            if (
              resumed.kind === "interests" &&
              interests.length === 0 &&
              player.interests.length > 0
            ) {
              setInterests(player.interests);
            }
            return;
          }
        } catch {
          // Proceed to issue a fresh challenge if resume fails
        }
      }
      const result = await a.request("/api/points/challenge", "POST", {
        missionId: m.id,
        missionVersion: m.version,
      });
      setSelected(m);
      setChallenge({
        ...result,
        expiresAt: expiry(result.expiresAt),
        titlePT: result.titlePT || m.titlePT,
        titleEN: result.titleEN || m.titleEN,
      });
      setAnswers({});
      setInterests(player.interests);
    });
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!challenge || !selected) return;
    await a.action(async () => {
      if (Date.parse(challenge.expiresAt) <= Date.now()) {
        throw new AccountError("mission_expired");
      }
      const result = await a.request("/api/points/evidence", "POST", {
        challengeId: challenge.challengeId,
        ...(challenge.kind === "interests" ? { interests } : { answers }),
      });
      if (
        typeof result.pendingToken !== "string" ||
        typeof result.awardPreview !== "number"
      ) {
        throw new AccountError("invalid_response");
      }
      a.rememberReward({
        pendingToken: result.pendingToken,
        evidenceRef: result.evidenceRef,
        missionId: selected.id,
        missionVersion: selected.version,
        awardPreview: result.awardPreview,
        expiresAt: expiry(result.expiresAt),
      });
      setChallenge(null);
      setReload((n) => n + 1);
    });
  }

  async function confirmClaim() {
    const activePending = a.pending || (a.pendingClaims[0]
      ? {
          pendingToken: a.pendingClaims[0].pendingId,
          missionId: a.pendingClaims[0].missionId,
          awardPreview: a.pendingClaims[0].awardKP,
          expiresAt: a.pendingClaims[0].expiresAt,
        }
      : null);
    if (!activePending) return;
    const key =
      lastClaimKey ||
      (typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random()}`);
    setLastClaimKey(key);
    try {
      const ok = await a.claimReward(activePending.pendingToken, key);
      if (ok) {
        setUncertainClaim(false);
        setLastClaimKey(null);
        setReload((n) => n + 1);
      } else {
        setUncertainClaim(true);
      }
    } catch {
      setUncertainClaim(true);
    }
  }

  async function checkClaimStatus() {
    if (!lastClaimKey) {
      await a.loadWallet();
      setReload((n) => n + 1);
      return;
    }
    await a.action(async () => {
      const statusRes = await a.request(
        "/api/points/operation-status?type=claim",
        "GET",
        undefined,
        lastClaimKey,
      );
      if (statusRes.status === "completed") {
        setUncertainClaim(false);
        setLastClaimKey(null);
        await a.loadWallet();
        setReload((n) => n + 1);
      }
    });
  }

  const idx = lang === "pt" ? 0 : 1;
  const msg = (key: string) =>
    MEMBER_MESSAGES[key]?.[idx] || MEMBER_MESSAGES.load_failed[idx];

  const displayedMissions = focusMissionId
    ? missions.filter((m) => m.id === focusMissionId)
    : missions;

  const activePending =
    a.pending ||
    (a.pendingClaims[0]
      ? {
          pendingToken: a.pendingClaims[0].pendingId,
          missionId: a.pendingClaims[0].missionId,
          awardPreview: a.pendingClaims[0].awardKP,
          expiresAt: a.pendingClaims[0].expiresAt,
        }
      : null);

  return (
    <section
      className="account-panel"
      aria-labelledby="official-missions-heading"
    >
      <h2 id="official-missions-heading">
        {t("Missões oficiais", "Official missions")}
      </h2>
      <p>
        {t(
          "Regras e recompensas são definidas e validadas pelo servidor.",
          "Rules and rewards are defined and validated by the server.",
        )}
      </p>

      {programStatus === "disabled" && (
        <p className="notice" role="status">
          {msg("kp_disabled")}
        </p>
      )}
      {programStatus === "new_activity_paused" && (
        <p className="notice" role="status">
          {msg("mission_paused")}
        </p>
      )}
      {programStatus === "maintenance" && (
        <p className="notice" role="status">
          {msg("warming")}
        </p>
      )}
      {programStatus === "closed" && (
        <p className="notice" role="status">
          {msg("kp_disabled")}
        </p>
      )}

      {activePending && (
        <div
          className="official-mission-card pending-claim-banner"
          role="region"
          aria-label={t("Recompensa pendente", "Pending reward")}
        >
          <p className="eyebrow">
            {t(
              "VALIDAÇÃO APROVADA · PENDENTE DE CONFIRMAÇÃO",
              "VALIDATION APPROVED · PENDING CONFIRMATION",
            )}
          </p>
          <h3>
            {activePending.awardPreview} KP · {activePending.missionId}
          </h3>
          <p className="official-mission-deadline">
            {t("Expira em", "Expires at")}{" "}
            {new Date(activePending.expiresAt).toLocaleString(
              lang === "pt" ? "pt-BR" : "en-US",
            )}
          </p>
          <div className="account-actions">
            <button
              className="button"
              disabled={a.busy}
              onClick={() => void confirmClaim()}
            >
              {t("Confirmar resgate de KP", "Confirm KP claim")}
            </button>
            {uncertainClaim && (
              <button
                className="button secondary"
                disabled={a.busy}
                onClick={() => void checkClaimStatus()}
              >
                {t("Conferir status", "Check status")}
              </button>
            )}
          </div>
        </div>
      )}

      {status === "loading" ? (
        <div className="account-loader" role="status" aria-busy="true">
          <span className="account-spinner" aria-hidden="true" />
          <p>{t("Carregando missões oficiais…", "Loading official missions…")}</p>
        </div>
      ) : status === "error" ? (
        <div className="notice">
          <p>{msg("load_failed")}</p>
          <button
            className="button secondary"
            onClick={() => setReload((n) => n + 1)}
          >
            {t("Tentar novamente", "Try again")}
          </button>
        </div>
      ) : !displayedMissions.length ? (
        <p className="notice">{msg("mission_empty")}</p>
      ) : !challenge ? (
        <div className="official-mission-grid">
          {displayedMissions.map((m) => {
            const isCompleted = Boolean(m.completed || m.Completed);
            const hasActiveAttempt = Boolean(
              m.activeAttempt && m.activeAttempt.status === "issued",
            );
            return (
              <article
                className="official-mission-card"
                key={`${m.id}-${m.version}`}
              >
                <p className="eyebrow">
                  {isCompleted
                    ? t("CONCLUÍDA", "COMPLETED")
                    : hasActiveAttempt
                      ? t("EM ANDAMENTO", "IN PROGRESS")
                      : t("DISPONÍVEL", "AVAILABLE")}
                </p>
                <h3>
                  {(lang === "pt" ? m.titlePT : m.titleEN) ||
                    t("Missão oficial", "Official mission")}
                </h3>
                {(m.summaryPT || m.summaryEN) && (
                  <p>{lang === "pt" ? m.summaryPT : m.summaryEN}</p>
                )}
                <p className="mission-award-pill">
                  <strong>{m.awardKP} KP</strong> ·{" "}
                  {t("sujeitos à validação", "subject to validation")}
                </p>
                {isCompleted ? (
                  <p className="mission-done">
                    ✓ {t("Missão concluída", "Mission completed")}
                    {m.receipt?.receiptId ? ` (${m.receipt.receiptId})` : ""}
                  </p>
                ) : (
                  <div className="account-actions">
                    <button
                      className="button"
                      disabled={
                        a.busy ||
                        m.eligibility === "program_paused" ||
                        m.eligibility === "reward_capacity"
                      }
                      onClick={() => void start(m)}
                    >
                      {hasActiveAttempt
                        ? t("Retomar tentativa", "Resume attempt")
                        : t("Iniciar missão", "Start mission")}
                    </button>
                    {!focusMissionId && (
                      <Link
                        className="button secondary"
                        href={`/${lang}/conta/missoes/detalhe/?id=${encodeURIComponent(m.id)}`}
                      >
                        {t("Detalhes", "Details")}
                      </Link>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      ) : (
        <form className="account-form" onSubmit={submit}>
          <h3>
            {(lang === "pt" ? challenge.titlePT : challenge.titleEN) ||
              t("Sua tentativa oficial", "Your official attempt")}
          </h3>
          <p className="official-mission-deadline">
            {t("Expira em", "Expires at")}{" "}
            {new Date(challenge.expiresAt).toLocaleString(
              lang === "pt" ? "pt-BR" : "en-US",
            )}
          </p>
          {challenge.kind === "interests" ? (
            <fieldset>
              <legend>
                {t(
                  "Escolha seus interesses (mínimo 3)",
                  "Choose your interests (at least 3)",
                )}
              </legend>
              {categories.map((c) => (
                <label className="account-check" key={c}>
                  <input
                    type="checkbox"
                    checked={interests.includes(c)}
                    onChange={() =>
                      setInterests((xs) =>
                        xs.includes(c)
                          ? xs.filter((x) => x !== c)
                          : [...xs, c],
                      )
                    }
                  />
                  {labels[c]}
                </label>
              ))}
            </fieldset>
          ) : (
            challenge.questions?.map((q) => (
              <fieldset key={q.id}>
                <legend>{lang === "pt" ? q.promptPT : q.promptEN}</legend>
                {q.options.map((o) => (
                  <label className="account-check" key={o.id}>
                    <input
                      type="radio"
                      required
                      name={q.id}
                      value={o.id}
                      checked={answers[q.id] === o.id}
                      onChange={() =>
                        setAnswers((xs) => ({ ...xs, [q.id]: o.id }))
                      }
                    />
                    {lang === "pt" ? o.textPT : o.textEN}
                  </label>
                ))}
              </fieldset>
            ))
          )}
          <div className="account-actions">
            <button className="button" disabled={a.busy}>
              {t("Enviar para validação", "Submit for validation")}
            </button>
            <button
              type="button"
              className="quiet"
              disabled={a.busy}
              onClick={() => {
                setChallenge(null);
                setSelected(null);
              }}
            >
              {t("Voltar às missões", "Back to missions")}
            </button>
          </div>
        </form>
      )}
      <AccountFeedback />
    </section>
  );
}
