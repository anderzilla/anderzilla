"use client";
import { useEffect, useRef, useState } from "react";
import {
  AccountProvider,
  consumePostLoginIntent,
  savePostLoginIntent,
  useAccount,
} from "../account/AccountProvider";
import { AccountAccess, AccountDialog } from "../account/AccountUI";
import { HubProvider, useHub } from "./HubProvider";
import { Icon } from "./Primitives";

function ArticleMemberBarInner({
  discoveryId,
}: {
  discoveryId: string;
}) {
  const account = useAccount();
  const { t, lang, player, toggleSave, recordOpen, toast } = useHub();
  const recordedRef = useRef(false);
  const [intentApplied, setIntentApplied] = useState(false);

  useEffect(() => {
    if (account.status !== "ready" || !account.user) return;
    if (!recordedRef.current) {
      recordedRef.current = true;
      void recordOpen(discoveryId);
    }
    if (!intentApplied) {
      const intent = consumePostLoginIntent();
      if (
        intent &&
        intent.type === "save_article" &&
        intent.discoveryId === discoveryId
      ) {
        setIntentApplied(true);
        if (!player.saved.includes(discoveryId)) {
          void toggleSave(discoveryId);
        }
      }
    }
  }, [
    account.status,
    account.user,
    discoveryId,
    intentApplied,
    player.saved,
    recordOpen,
    toggleSave,
  ]);

  const isSaved = Boolean(account.user && player.saved.includes(discoveryId));

  function handleSaveClick() {
    if (!account.user) {
      const returnPath =
        typeof window !== "undefined"
          ? `${window.location.pathname}${window.location.search}`
          : `/${lang}/radar/`;
      savePostLoginIntent({
        type: "save_article",
        path: returnPath,
        discoveryId,
      });
      account.open("login");
      return;
    }
    void toggleSave(discoveryId);
  }

  return (
    <div className="article-member-bar">
      <div className="article-member-actions">
        <button
          type="button"
          className={`button ${isSaved ? "secondary" : ""}`}
          aria-pressed={account.user ? isSaved : undefined}
          onClick={handleSaveClick}
        >
          <Icon name={isSaved ? "check" : "save"} />
          {!account.user
            ? t("Entrar para guardar na mochila", "Sign in to save to backpack")
            : isSaved
              ? t("Salvo na mochila", "Saved in backpack")
              : t("Guardar na mochila", "Save to backpack")}
        </button>
        {account.user && (
          <a className="button secondary" href={`/${lang}/conta/mochila/`}>
            {t("Minha mochila", "My backpack")} →
          </a>
        )}
        <AccountAccess />
      </div>
      <AccountDialog />
      {toast && (
        <div id="toast" role="status" className="show">
          {toast}
        </div>
      )}
    </div>
  );
}

export function ArticleMemberBar({
  discoveryId,
  itemVersion: _itemVersion,
  lang,
}: {
  discoveryId: string;
  itemVersion?: string;
  lang: "pt" | "en";
}) {
  return (
    <AccountProvider>
      <HubProvider initialLang={lang}>
        <ArticleMemberBarInner discoveryId={discoveryId} />
      </HubProvider>
    </AccountProvider>
  );
}
