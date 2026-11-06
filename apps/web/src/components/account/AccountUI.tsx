"use client";
import Link from "next/link";
import dynamic from 'next/dynamic';
const loading = () => <div className="account-loader" aria-busy="true" />;
const SignIn = dynamic(() => import('@clerk/react').then(m => m.SignIn), {ssr: false, loading});
const SignUp = dynamic(() => import('@clerk/react').then(m => m.SignUp), {ssr: false, loading});
const UserProfile = dynamic(() => import('@clerk/react').then(m => m.UserProfile), {ssr: false, loading});
import {useEffect, useRef, useState, type FormEvent, type KeyboardEvent} from 'react';
import {useAccount, AccountError, consumePostLoginIntent} from './AccountProvider';
import {useHub} from '../hub/HubProvider';
import {BrandAvatar} from '../BrandAssets';
import {discoveries} from '../hub/model';
import './account.css';

export const MEMBER_MESSAGES: Record<string, [string, string]> = {
  member_required: [
    'Entre para montar sua mochila e continuar sua jornada.',
    'Sign in to build your backpack and continue exploring.',
  ],
  complete_account: [
    'Falta um passo para liberar seu espaço. Vamos concluir seu cadastro?',
    'One step left to unlock your space. Let’s finish your account.',
  ],
  session_expired: [
    'Sua sessão terminou. Entre de novo para continuar de onde parou.',
    'Your session ended. Sign in again to pick up where you left off.',
  ],
  account_unavailable: [
    'Seu acesso precisa de uma revisão. Fale com a gente para conferir o próximo passo.',
    'Your access needs a review. Contact us to check the next step.',
  ],
  warming: [
    'Preparando seu espaço. Já vamos continuar.',
    'Getting your space ready. We’ll continue shortly.',
  ],
  load_failed: [
    'Não conseguimos abrir este bloco agora. Vamos tentar de novo?',
    'We couldn’t load this section just now. Try again?',
  ],
  offline: [
    'Parece que a conexão deu uma pausa. Reconecte para continuar.',
    'Looks like your connection paused. Reconnect to continue.',
  ],
  save_failed: [
    'Ainda não conseguimos confirmar essa mudança. Vamos conferir?',
    'We couldn’t confirm this change yet. Let’s check.',
  ],
  saving: ['Guardando sua mudança…', 'Saving your change…'],
  saved: ['Pronto! Mudança salva.', 'All set! Change saved.'],
  backpack_empty: [
    'Sua mochila está pronta para a primeira descoberta.',
    'Your backpack is ready for its first discovery.',
  ],
  bookmark_added: [
    'Foi para a mochila. Bora para a próxima?',
    'Saved to your backpack. Ready for the next discovery?',
  ],
  bookmark_removed: [
    'Descoberta removida da mochila.',
    'Discovery removed from your backpack.',
  ],
  content_unavailable: [
    'Esta descoberta não está disponível agora.',
    'This discovery isn’t available right now.',
  ],
  interests_empty: ['Quais temas entram no seu Radar?', 'What belongs on your radar?'],
  interests_saved: ['Seu Radar ganhou novos rumos.', 'Your radar has a fresh direction.'],
  interests_conflict: [
    'Seus interesses mudaram em outro acesso. Confira a seleção antes de salvar.',
    'Your interests changed in another session. Review your selection before saving.',
  ],
  radar_empty: [
    'Nenhuma novidade nesses temas por enquanto. Bora abrir o mapa?',
    'No fresh stories in these topics yet. Ready to explore a little wider?',
  ],
  exploration_empty: [
    'Sua próxima descoberta começa aqui.',
    'Your next discovery starts here.',
  ],
  history_clear_confirm: [
    'Limpar sua exploração? Mochila, interesses e KP não mudam.',
    'Clear your exploration history? Your backpack, interests and KP won’t change.',
  ],
  history_cleared: [
    'Mapa renovado. Seu histórico de exploração foi limpo.',
    'A fresh map. Your exploration history is cleared.',
  ],
  kp_disabled: [
    'Karaca Points ainda não está liberado. Seu Radar já tem muita coisa para explorar.',
    'Karaca Points isn’t available yet. There’s plenty to explore on your radar.',
  ],
  wallet_failed: [
    'Não conseguimos consultar seus KP agora. Atualize para conferir o saldo.',
    'We couldn’t check your KP just now. Refresh to see your balance.',
  ],
  mission_empty: [
    'Nenhuma missão nova por aqui. Seu Radar continua aberto.',
    'No new missions right now. Your radar is ready to explore.',
  ],
  mission_paused: [
    'Esta missão está em pausa. Escolha outra para continuar.',
    'This mission is paused. Choose another to keep going.',
  ],
  mission_expired: [
    'O tempo desta tentativa terminou. Confira se já dá para tentar de novo.',
    'This attempt has timed out. Check whether another attempt is available.',
  ],
  mission_try_again: [
    'Ainda não foi dessa vez. Revise as pistas e confira quando pode tentar de novo.',
    'Not quite this time. Review the hints and check when you can try again.',
  ],
  mission_checking: ['Conferindo sua missão…', 'Checking your mission…'],
  award_pending: ['Missão validada. Falta confirmar seus KP.', 'Mission verified. Confirm your KP to finish.'],
  award_uncertain: [
    'A confirmação ainda não chegou. Vamos conferir antes de repetir.',
    'Confirmation hasn’t arrived yet. Let’s check before trying again.',
  ],
  award_already: [
    'Esta missão já rendeu seus KP. Confira no extrato.',
    'You’ve already earned this mission’s KP. Check your activity.',
  ],
  claim_expired: [
    'O prazo para confirmar estes KP terminou. Confira as opções desta missão.',
    'The time to confirm these KP has ended. Check this mission’s options.',
  ],
  rate_limited: [
    'Vamos dar uma pausa. Tente novamente mais tarde.',
    'Let’s take a pause. Please try again later.',
  ],
  reauth_required: [
    'Para proteger sua conta, confirme seu acesso antes de continuar.',
    'To protect your account, confirm your access before continuing.',
  ],
  delete_confirm: [
    'Excluir sua conta? Você perderá o acesso ao seu espaço. Confira abaixo o que será removido e o que precisa ser mantido.',
    'Delete your account? You’ll lose access to your space. Review what will be removed and what must be retained below.',
  ],
  deletion_pending: [
    'Seu acesso já foi encerrado. Falta concluir uma etapa da exclusão.',
    'Your access is closed. One deletion step still needs to finish.',
  ],
  logout_unconfirmed: [
    'Você saiu desta tela. Falta confirmar o encerramento desta sessão.',
    'You’ve left this screen. This session still needs sign-out confirmation.',
  ],
};

const notices: Record<string, [string, string]> = {
  profile_completed: ['Pronto! Mudança salva.', 'All set! Change saved.'],
  reward_pending: MEMBER_MESSAGES.award_pending,
  reward_claimed: ['Karaca! KP confirmados na carteira.', 'Karaca! KP confirmed in your wallet.'],
  preferences_saved: MEMBER_MESSAGES.saved,
  verification_sent: ['Confira seu e-mail e informe o código de verificação.', 'Check your email and enter the verification code.'],
  email_verified: ['E-mail verificado.', 'Email verified.'],
  signed_out: ['Você saiu desta sessão.', 'You signed out of this session.'],
  account_deleted: ['Conta excluída com sucesso.', 'Account deleted.'],
  export_ready: ['Seu arquivo de dados está pronto para download.', 'Your data file is ready to download.'],
};

const errors: Record<string, [string, string]> = {
  ...MEMBER_MESSAGES,
  onboarding_required: MEMBER_MESSAGES.complete_account,
  minor_registration_unavailable: [
    'O cadastro é permitido apenas para maiores de 18 anos.',
    'Registration is available only to adults aged 18 or older.',
  ],
  policy_changed: [
    'Os termos foram atualizados. Recarregue e leia a versão atual.',
    'The terms changed. Reload and read the current version.',
  ],
  registration_conflict: [
    'Não foi possível concluir com os dados informados. Use sua conta existente ou procure o suporte.',
    'Could not complete registration with these details. Use your existing account or contact support.',
  ],
  registration_unavailable: [
    'Não foi possível concluir o cadastro. Procure o suporte.',
    'Registration could not be completed. Contact support.',
  ],
  age_restricted: [
    'O cadastro é permitido apenas para maiores de 18 anos.',
    'Registration is available only to adults aged 18 or older.',
  ],
  invalid_cpf: ['Confira o CPF informado.', 'Check the CPF entered.'],
  cpf_in_use: [
    'Não foi possível usar este CPF. Acesse sua conta existente ou procure o suporte.',
    'This CPF could not be used. Sign in to your existing account or contact support.',
  ],
  invalid_birth_date: ['Confira a data de nascimento.', 'Check the date of birth.'],
  account_suspended: MEMBER_MESSAGES.account_unavailable,
  account_deleted: MEMBER_MESSAGES.account_unavailable,
  temporarily_unavailable: MEMBER_MESSAGES.warming,
  account_link_required: [
    'Já existe um registro anterior com este e-mail que precisa de migração assistida. Contate player.one@anderzilla.com.',
    'A prior record with this email requires assisted migration. Contact player.one@anderzilla.com.',
  ],
  reward_expired: MEMBER_MESSAGES.mission_expired,
  authentication_required: MEMBER_MESSAGES.session_expired,
  unavailable: [
    'Contas ainda não estão disponíveis neste ambiente.',
    'Accounts are not available in this environment yet.',
  ],
  network_error: MEMBER_MESSAGES.offline,
  invalid_credentials: ['Confira seus dados de acesso.', 'Check your sign-in details.'],
  email_not_verified: ['Verifique seu e-mail antes de continuar.', 'Verify your email before continuing.'],
  evidence_invalid: MEMBER_MESSAGES.mission_try_again,
  reward_capacity: [
    'Cobertura de KP encerrada para esta campanha; nenhum crédito pendente foi gerado.',
    'KP coverage for this campaign is full; no pending credit was created.',
  ],
  challenge_expired: MEMBER_MESSAGES.mission_expired,
  pending_expired: MEMBER_MESSAGES.claim_expired,
  pending_claimed: MEMBER_MESSAGES.award_already,
  mission_changed: [
    'Essa missão foi atualizada. Escolha-a de novo na lista.',
    'This mission was updated. Pick it again from the list.',
  ],
  mission_unavailable: [
    'Essa missão não está disponível agora. Escolha outra na lista.',
    'This mission is not available right now. Pick another from the list.',
  ],
  mission_ineligible: [
    'Você já utilizou o limite desta missão ou campanha.',
    'You have reached the limit for this mission or campaign.',
  ],
  rewards_unavailable: MEMBER_MESSAGES.kp_disabled,
  program_maintenance: [
    'Karaca Points está em manutenção rápida. Tente novamente em instantes.',
    'Karaca Points is under brief maintenance. Please try again shortly.',
  ],
  invalid_avatar: [
    'Não foi possível usar essa imagem. Tente JPEG, PNG ou WebP.',
    'Could not use that image. Try JPEG, PNG or WebP.',
  ],
  avatar_too_large: [
    'Imagem muito grande. Tente outra foto menor.',
    'Image too large. Try a smaller photo.',
  ],
};

export function AccountFeedback() {
  const a = useAccount();
  const {lang} = useHub();
  const message = a.error
    ? errors[a.error] || MEMBER_MESSAGES.save_failed
    : notices[a.notice];
  if (!message) return null;
  return (
    <div className={a.error ? 'account-error' : 'account-success'} role={a.error ? 'alert' : 'status'}>
      <p>{message[lang === 'pt' ? 0 : 1]}</p>
      {a.error === 'logout_unconfirmed' && (
        <button type="button" className="button secondary" onClick={() => void a.logout()}>
          {lang === 'pt' ? 'Tentar encerrar sessão' : 'Try signing out again'}
        </button>
      )}
    </div>
  );
}

export function AccountSyncStatus() {
  const a = useAccount();
  const {t, lang, undoItem, undoRemoveBookmark, langPrompt, setLangPrompt, changeLanguage} = useHub();

  return (
    <>
      {a.pendingIntentConfirmation && a.user && (
        <div className="wrap member-intent-banner" role="region" aria-label={t('Confirmar ação pendente', 'Confirm pending action')}>
          <div className="notice member-intent-box">
            <p>
              {(() => {
                const disc = discoveries.find((d) => d.id === a.pendingIntentConfirmation?.discoveryId);
                const title = disc ? (lang === 'pt' ? disc.titlePT : disc.titleEN) : a.pendingIntentConfirmation?.discoveryId;
                return t(
                  `Você entrou! Deseja guardar "${title}" na sua mochila agora?`,
                  `You are signed in! Would you like to save "${title}" to your backpack now?`,
                );
              })()}
            </p>
            <div className="account-actions">
              <button
                type="button"
                className="button"
                onClick={async () => {
                  const id = a.pendingIntentConfirmation?.discoveryId;
                  a.setPendingIntentConfirmation(null);
                  if (id) {
                    try {
                      await a.request(`/api/member/backpack/${encodeURIComponent(id)}`, 'PUT', {});
                      await a.refresh();
                      a.notifySync('collections_updated');
                      a.setNotice('preferences_saved');
                    } catch {}
                  }
                }}
              >
                {t('Guardar na mochila', 'Save to backpack')}
              </button>
              <button type="button" className="quiet" onClick={() => a.setPendingIntentConfirmation(null)}>
                {t('Agora não', 'Not now')}
              </button>
            </div>
          </div>
        </div>
      )}
      {undoItem && a.user && (
        <div className="wrap member-undo-banner" role="status" aria-live="polite">
          <div className="notice member-intent-box">
            <span>{t('Descoberta removida da mochila.', 'Discovery removed from your backpack.')}</span>
            <button type="button" className="button secondary" onClick={() => void undoRemoveBookmark()}>
              {t('Desfazer', 'Undo')}
            </button>
          </div>
        </div>
      )}
      {langPrompt && (
        <div className="wrap member-undo-banner" role="alert">
          <div className="account-error member-intent-box">
            <span>
              {t(
                'Não conseguimos salvar a preferência de idioma na conta agora. Deseja mudar o idioma desta página mesmo assim?',
                'Could not save the language preference to your account right now. Switch page language anyway?',
              )}
            </span>
            <div className="account-actions">
              <button type="button" className="button secondary" onClick={() => void changeLanguage(langPrompt, true)}>
                {t('Continuar sem salvar', 'Continue without saving')}
              </button>
              <button type="button" className="quiet" onClick={() => setLangPrompt(null)}>
                {t('Cancelar', 'Cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
      {a.error && !a.screen && (
        <div className="wrap">
          <AccountFeedback />
          <button className="quiet" onClick={() => a.setError('')}>
            {t('Fechar aviso', 'Dismiss notice')}
          </button>
        </div>
      )}
    </>
  );
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase();
}

function hueFrom(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = ((h * 31 + seed.charCodeAt(i)) >>> 0);
  return h % 360;
}

export function UserAvatar({
  name,
  email,
  src,
  size = 32,
}: {
  name?: string;
  email?: string;
  src?: string | null;
  size?: number;
}) {
  const [broken, setBroken] = useState(false);
  const label = name || email || '';
  if (src && !broken) {
    return (
      <img
        className="user-avatar"
        src={src}
        width={size}
        height={size}
        alt=""
        referrerPolicy="no-referrer"
        onError={() => setBroken(true)}
      />
    );
  }
  return (
    <span
      className="user-avatar user-avatar-generic"
      style={{
        width: size,
        height: size,
        fontSize: Math.round(size * 0.42),
        background: `hsl(${hueFrom(label || 'anderzilla')} 55% 32%)`,
      }}
      aria-hidden="true"
    >
      {initials(label)}
    </span>
  );
}

const AVATAR_PRESETS = Array.from({length: 8}, (_, i) => `/hub/avatars/preset-${i + 1}.svg`);

function resizeAvatar(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('read_failed'));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error('decode_failed'));
      img.onload = () => {
        const size = 160;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('canvas_unavailable'));
          return;
        }
        const side = Math.min(img.naturalWidth, img.naturalHeight);
        const sx = (img.naturalWidth - side) / 2;
        const sy = (img.naturalHeight - side) / 2;
        ctx.drawImage(img, sx, sy, side, side, 0, 0, size, size);
        resolve(canvas.toDataURL('image/jpeg', 0.82));
      };
      img.src = reader.result as string;
    };
    reader.readAsDataURL(file);
  });
}

export function AvatarPicker() {
  const a = useAccount();
  const {t, lang} = useHub();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const user = a.user;
  if (!user) return null;

  async function choose(url: string | null) {
    setErr('');
    setBusy(true);
    try {
      await a.patchProfile({avatarUrl: url});
      setOpen(false);
      a.setNotice('preferences_saved');
    } catch (e) {
      setErr(e instanceof AccountError ? e.code : 'request_failed');
    } finally {
      setBusy(false);
    }
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setErr('invalid_avatar');
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setErr('avatar_too_large');
      return;
    }
    setErr('');
    setBusy(true);
    try {
      const dataUri = await resizeAvatar(file);
      await a.patchProfile({avatarUrl: dataUri});
      setOpen(false);
      a.setNotice('preferences_saved');
    } catch (e) {
      setErr(e instanceof AccountError ? e.code : 'invalid_avatar');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="avatar-picker">
      <button type="button" className="button secondary" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        {t('Trocar avatar', 'Change avatar')}
      </button>
      {open && (
        <div className="avatar-picker-panel">
          <p className="account-hint">{t('Avatares oficiais AnderZilla', 'Official AnderZilla avatars')}</p>
          <div className="avatar-grid">
            {AVATAR_PRESETS.map((p, i) => (
              <button
                type="button"
                key={p}
                className="avatar-option"
                disabled={busy}
                onClick={() => void choose(p)}
                aria-label={`${t('Usar avatar', 'Use avatar')} ${i + 1}`}
                aria-pressed={user.avatarUrl === p}
              >
                <img src={p} width={48} height={48} alt="" />
              </button>
            ))}
          </div>
          <div className="account-actions">
            <button type="button" className="button secondary" disabled={busy} onClick={() => fileRef.current?.click()}>
              {t('Enviar foto (JPEG, PNG ou WebP)', 'Upload photo (JPEG, PNG or WebP)')}
            </button>
            {user.avatarUrl && (
              <button type="button" className="quiet" disabled={busy} onClick={() => void choose(null)}>
                {t('Remover foto', 'Remove photo')}
              </button>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => void onFile(e)} />
          {err && (
            <p className="account-error" role="alert">
              {(errors[err] || MEMBER_MESSAGES.save_failed)[lang === 'pt' ? 0 : 1]}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Header authentication controls:
 * - Visitor: only "Entrar" button (no personal counters, no Ghost avatar as user avatar).
 * - Verifying identity: neutral skeleton without stale data.
 * - Authenticated incomplete onboarding: "Concluir cadastro" CTA.
 * - Authenticated complete member:
 *   1. "Seu Radar" link (`/{lang}/conta/radar/`)
 *   2. KP chip (`{available} KP` with accessible aria-label -> `/{lang}/conta/carteira/`, or `KP —` when unknown/error, or neutral `Karaca Points` link when disabled; never 0 on error)
 *   3. Avatar + DisplayName disclosure button (`aria-expanded`) opening the 10-item navigation disclosure menu.
 */
export function AccountAccess() {
  const a = useAccount();
  const {t, lang} = useHub();
  const [menuOpen, setMenuOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    setMenuOpen(false);
  }, [a.user?.id, a.sessionEpoch]);

  useEffect(() => {
    if (!menuOpen) return;
    const onPointerDown = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [menuOpen]);

  function onMenuKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Escape' && menuOpen) {
      e.preventDefault();
      setMenuOpen(false);
      triggerRef.current?.focus();
    }
  }

  // Skeleton state while verifying an active session
  if (!a.user && a.signedIn && (a.profileStatus === 'loading' || a.profileStatus === 'waking')) {
    return (
      <div className="member-header-skeleton" role="status" aria-label={t('Verificando acesso…', 'Verifying access…')}>
        <span className="skeleton-pill" aria-hidden="true" />
      </div>
    );
  }

  // Signed in at Clerk but onboarding not finished yet
  if (a.signedIn && a.onboardingRequired && !a.user) {
    return (
      <div className="member-header-bar">
        <button type="button" className="button secondary member-complete-btn" onClick={() => a.open('onboarding')}>
          {t('Concluir cadastro', 'Finish account')}
        </button>
      </div>
    );
  }

  // Visitor (not signed in)
  if (!a.user) {
    return (
      <button type="button" className="account-access" onClick={() => a.open('login')}>
        {t('Entrar', 'Sign in')}
      </button>
    );
  }

  const kpActive = a.capabilities.rewards || a.capabilities.kpProgramState === 'active' || a.capabilities.kpProgramState === 'new_activity_paused';
  const formattedBalance =
    typeof a.balance === 'number'
      ? new Intl.NumberFormat(lang === 'pt' ? 'pt-BR' : 'en-US').format(a.balance)
      : null;

  return (
    <div className="member-header-bar" ref={wrapperRef} onKeyDown={onMenuKeyDown}>
      <Link className="member-radar-link" href={`/${lang}/conta/radar/`}>
        {t('Seu Radar', 'Your Radar')}
      </Link>

      {kpActive ? (
        <Link
          className="member-kp-chip"
          href={`/${lang}/conta/carteira/`}
          aria-label={
            formattedBalance !== null
              ? t(
                  `Carteira: ${formattedBalance} Karaca Points disponíveis`,
                  `Wallet: ${formattedBalance} available Karaca Points`,
                )
              : t(
                  'Carteira de Karaca Points: saldo em atualização',
                  'Karaca Points wallet: balance updating',
                )
          }
        >
          <span className="kp-badge-dot" aria-hidden="true" />
          <span>{formattedBalance !== null ? `${formattedBalance} KP` : 'KP —'}</span>
        </Link>
      ) : (
        <Link
          className="member-kp-chip is-neutral"
          href={`/${lang}/conta/kp/`}
          aria-label={t('Karaca Points: ver regras e estado do programa', 'Karaca Points: view program rules and status')}
        >
          <span>Karaca Points</span>
        </Link>
      )}

      <div className="member-disclosure">
        <button
          ref={triggerRef}
          type="button"
          className="member-disclosure-trigger"
          aria-expanded={menuOpen}
          aria-controls="member-navigation-disclosure"
          onClick={() => setMenuOpen((o) => !o)}
        >
          <UserAvatar name={a.user.displayName} email={a.user.email} src={a.user.avatarUrl} size={28} />
          <span className="member-trigger-name">{a.user.displayName}</span>
          <span className="member-trigger-caret" aria-hidden="true">
            ▾
          </span>
        </button>

        {menuOpen && (
          <nav
            id="member-navigation-disclosure"
            className="member-disclosure-panel"
            aria-label={t('Menu do jogador', 'Player menu')}
          >
            <ul className="member-disclosure-list">
              <li>
                <Link href={`/${lang}/conta/`} onClick={() => setMenuOpen(false)}>
                  {t('Painel do jogador', 'Player dashboard')}
                </Link>
              </li>
              <li>
                <Link href={`/${lang}/conta/radar/`} onClick={() => setMenuOpen(false)}>
                  {t('Seu Radar', 'Your Radar')}
                </Link>
              </li>
              <li>
                <Link href={`/${lang}/conta/mochila/`} onClick={() => setMenuOpen(false)}>
                  {t('Mochila', 'Backpack')}
                </Link>
              </li>
              <li>
                <Link href={`/${lang}/conta/interesses/`} onClick={() => setMenuOpen(false)}>
                  {t('Interesses', 'Interests')}
                </Link>
              </li>
              <li>
                <Link href={`/${lang}/conta/exploracao/`} onClick={() => setMenuOpen(false)}>
                  {t('Exploração', 'Exploration')}
                </Link>
              </li>
              <li className="member-disclosure-divider" role="separator" aria-hidden="true" />
              <li>
                <Link href={`/${lang}/conta/kp/`} onClick={() => setMenuOpen(false)}>
                  Karaca Points
                </Link>
              </li>
              <li>
                <Link href={`/${lang}/conta/carteira/`} onClick={() => setMenuOpen(false)}>
                  {t('Carteira', 'Wallet')}
                </Link>
              </li>
              <li>
                <Link href={`/${lang}/conta/missoes/`} onClick={() => setMenuOpen(false)}>
                  {t('Missões oficiais', 'Official missions')}
                </Link>
              </li>
              <li className="member-disclosure-divider" role="separator" aria-hidden="true" />
              <li>
                <Link href={`/${lang}/conta/perfil/`} onClick={() => setMenuOpen(false)}>
                  {t('Perfil', 'Profile')}
                </Link>
              </li>
              <li>
                <button
                  type="button"
                  className="member-disclosure-signout"
                  onClick={() => {
                    setMenuOpen(false);
                    void a.logout();
                  }}
                >
                  {t('Sair', 'Sign out')}
                </button>
              </li>
            </ul>
          </nav>
        )}
      </div>
    </div>
  );
}

function Availability() {
  const a = useAccount();
  const {t} = useHub();
  return (
    <div className="account-availability">
      {a.status === 'loading' ? (
        <p role="status">{t('Preparando seu espaço. Já vamos continuar.', 'Getting your space ready. We’ll continue shortly.')}</p>
      ) : (
        <>
          <p>
            {t(
              'O acesso da conta está em pausa neste momento. As notícias públicas continuam abertas para leitura.',
              'Account access is paused right now. Public stories remain open for reading.',
            )}
          </p>
          <button className="button secondary" onClick={() => void a.reconnect()}>
            {t('Tentar novamente', 'Try again')}
          </button>
        </>
      )}
    </div>
  );
}

const securityEnabled = process.env.NEXT_PUBLIC_CLERK_SECURITY_ENABLED === 'true';

function ManagedEntry() {
  const a = useAccount();
  const {t, lang} = useHub();
  const [adult, setAdult] = useState(false);

  if (a.authEnabled && a.authLoaded && a.signedIn && (a.profileStatus === 'blocked' || a.profileStatus === 'error')) {
    return (
      <div className="account-availability">
        <p role="alert">
          {a.deletionPending
            ? MEMBER_MESSAGES.deletion_pending[lang === 'pt' ? 0 : 1]
            : a.profileStatus === 'blocked'
              ? MEMBER_MESSAGES.account_unavailable[lang === 'pt' ? 0 : 1]
              : MEMBER_MESSAGES.load_failed[lang === 'pt' ? 0 : 1]}
        </p>
        <div className="account-actions">
          {a.deletionPending ? (
            <button className="button secondary" disabled={a.busy} onClick={() => void a.remove('')}>
              {t('Conferir exclusão', 'Check deletion')}
            </button>
          ) : a.profileStatus === 'blocked' ? (
            <a className="button secondary" href="mailto:player.one@anderzilla.com">
              {t('Falar com suporte', 'Contact support')}
            </a>
          ) : (
            <button className="button secondary" disabled={a.busy} onClick={() => void a.action(() => a.refresh())}>
              {t('Tentar novamente', 'Try again')}
            </button>
          )}
          <button className="quiet" disabled={a.busy} onClick={() => void a.logout()}>
            {t('Sair', 'Sign out')}
          </button>
        </div>
      </div>
    );
  }

  if (a.authEnabled && a.authLoaded && a.signedIn && a.profileStatus !== 'ready') {
    return (
      <div className="account-loader" role="status" aria-live="polite">
        <span className="account-spinner" aria-hidden="true" />
        <p>{MEMBER_MESSAGES.warming[lang === 'pt' ? 0 : 1]}</p>
      </div>
    );
  }

  if (a.authEnabled && (a.screen !== 'register' || a.entry !== 'returning')) {
    return !a.authLoaded ? (
      <p role="status">{MEMBER_MESSAGES.warming[lang === 'pt' ? 0 : 1]}</p>
    ) : a.signedIn ? (
      <OnboardingForm />
    ) : a.screen === 'register' ? (
      <div className="account-clerk">
        <SignUp
          routing="hash"
          signInUrl={`/${lang}/conta/?account=login`}
          forceRedirectUrl={`/${lang}/conta/?account=complete`}
          fallback={<p role="status">{t('Carregando cadastro…', 'Loading registration…')}</p>}
        />
      </div>
    ) : (
      <>
        <div className="account-clerk">
          <SignIn
            routing="hash"
            withSignUp={false}
            forceRedirectUrl={`/${lang}/conta/?account=complete`}
            fallback={<p role="status">{t('Carregando login…', 'Loading sign-in…')}</p>}
          />
        </div>
        <p className="account-hint">
          {t('Use a opção de recuperação no login se esqueceu sua senha.', 'Use the recovery option in sign-in if you forgot your password.')}
        </p>
        <button className="quiet" onClick={() => a.open('register')}>
          {t('Ainda não tenho conta', 'I do not have an account yet')}
        </button>
      </>
    );
  }

  return (
    <div className="account-entry">
      <p>{MEMBER_MESSAGES.member_required[lang === 'pt' ? 0 : 1]}</p>
      <p className="account-hint">
        {t(
          'E-mail confirmado, CPF e um espaço só seu. O cadastro está disponível para maiores de 18 anos.',
          'Verified email, CPF and your own space. Registration is available to adults aged 18 or older.',
        )}
      </p>
      {a.screen !== 'register' && (
        <button className="button" onClick={() => a.enableAuth('returning')}>
          {t('Já tenho conta — entrar', 'I have an account — sign in')}
        </button>
      )}
      <form
        className="account-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (adult) {
            a.open('register');
            a.enableAuth('adult');
          }
        }}
      >
        <label className="account-check">
          <input type="checkbox" required checked={adult} onChange={(e) => setAdult(e.target.checked)} />
          <span>{t('Confirmo que tenho 18 anos ou mais.', 'I confirm I am at least 18 years old.')}</span>
        </label>
        <button className="button secondary" disabled={!adult}>
          {t('Criar minha conta', 'Create my account')}
        </button>
      </form>
    </div>
  );
}

export function OnboardingForm() {
  const a = useAccount();
  const {t, lang} = useHub();
  const [cpf, setCpf] = useState('');
  const [name, setName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [terms, setTerms] = useState(false);
  const [marketing, setMarketing] = useState(false);

  if (a.user) {
    return (
      <>
        <p>{t('Seu espaço do jogador está pronto.', 'Your player space is ready.')}</p>
        <Link
          className="button"
          href={`/${lang}/conta/`}
          onClick={() => {
            a.open(null);
          }}
        >
          {t('Abrir meu painel', 'Open my dashboard')}
        </Link>
      </>
    );
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    const birth = new Date(birthDate + 'T12:00:00Z');
    const parts = Object.fromEntries(
      new Intl.DateTimeFormat('en-CA', {
        timeZone: 'America/Sao_Paulo',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      })
        .formatToParts(new Date())
        .map((p) => [p.type, p.value]),
    );
    const year = Number(parts.year);
    const month = Number(parts.month) - 1;
    const day = Number(parts.day);
    let age = year - birth.getUTCFullYear();
    if (month < birth.getUTCMonth() || (month === birth.getUTCMonth() && day < birth.getUTCDate())) age--;
    if (!Number.isFinite(age) || age < 0 || age > 120) {
      a.setError('invalid_birth_date');
      return;
    }
    if (age < 18) {
      a.setError('age_restricted');
      return;
    }
    await a.completeOnboarding({
      cpf,
      displayName: name,
      birthDate,
      termsAccepted: terms,
      termsVersion: a.capabilities.termsVersion,
      privacyVersion: a.capabilities.privacyVersion,
      marketingOptIn: age < 18 ? false : marketing,
      lang: lang === 'pt' ? 'pt-BR' : 'en',
    });
    setCpf('');
  }

  return (
    <>
      <p>{MEMBER_MESSAGES.complete_account[lang === 'pt' ? 0 : 1]}</p>
      <form className="account-form" onSubmit={submit}>
        <label>
          {t('Nome no radar', 'Display name')}
          <input
            required
            autoComplete="nickname"
            minLength={2}
            maxLength={60}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label>
          CPF
          <input
            required
            inputMode="numeric"
            autoComplete="off"
            maxLength={14}
            pattern="[0-9.\- ]{11,14}"
            value={cpf}
            onChange={(e) => setCpf(e.target.value)}
            aria-describedby="cpf-purpose"
          />
        </label>
        <small id="cpf-purpose">
          {t(
            'Usado para evitar cadastros duplicados e proteger sua conta. Nunca aparece publicamente.',
            'Used to prevent duplicate registrations and protect your account. Never shown publicly.',
          )}
        </small>
        <label>
          {t('Data de nascimento', 'Date of birth')}
          <input
            type="date"
            required
            autoComplete="bday"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            max={new Date().toISOString().slice(0, 10)}
          />
        </label>
        <label className="account-check">
          <input type="checkbox" required checked={terms} onChange={(e) => setTerms(e.target.checked)} />
          <span>
            {t('Li e aceito os', 'I accept the')}{' '}
            <Link href={`/${lang}/termos/`} target="_blank" rel="noopener noreferrer">
              {t('Termos de uso', 'Terms of use')}
            </Link>{' '}
            {t('e li a', 'and have read the')}{' '}
            <Link href={`/${lang}/privacidade/`} target="_blank" rel="noopener noreferrer">
              {t('Privacidade', 'Privacy notice')}
            </Link>
            .
          </span>
        </label>
        <label className="account-check">
          <input type="checkbox" checked={marketing} onChange={(e) => setMarketing(e.target.checked)} />
          <span>{t('Receber novidades por e-mail (opcional).', 'Receive email updates (optional).')}</span>
        </label>
        <button className="button" disabled={a.busy}>
          {a.busy ? t('Guardando sua mudança…', 'Saving your change…') : t('Concluir cadastro', 'Finish account')}
        </button>
      </form>
      <button className="quiet" disabled={a.busy} onClick={() => void a.logout()}>
        {t('Sair desta sessão', 'Sign out of this session')}
      </button>
    </>
  );
}

export function AccountDialog() {
  const a = useAccount();
  const {t} = useHub();
  const dialog = useRef<HTMLDialogElement>(null);
  const previous = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (a.screen && a.screen !== 'delete_confirm') {
      if (!dialog.current?.open) {
        previous.current = document.activeElement as HTMLElement;
        dialog.current?.showModal();
      }
      requestAnimationFrame(() => dialog.current?.querySelector<HTMLElement>('h2')?.focus());
    } else if (dialog.current?.open) {
      dialog.current.close();
      previous.current?.focus();
    }
  }, [a.screen, a.authEnabled]);

  const title =
    a.screen === 'security'
      ? t('Segurança e acesso', 'Security and access')
      : a.signedIn && !a.user
        ? t('Concluir cadastro', 'Finish your account')
        : a.screen === 'register'
          ? t('Criar conta AnderZilla', 'Create AnderZilla account')
          : t('Entrar no AnderZilla', 'Sign in to AnderZilla');

  return (
    <dialog
      ref={dialog}
      className="account-dialog"
      aria-labelledby="account-title"
      onCancel={() => a.open(null)}
      onClose={() => {
        if (a.screen && a.screen !== 'delete_confirm') a.open(null);
      }}
    >
      <button className="account-close" aria-label={t('Fechar', 'Close')} onClick={() => a.open(null)}>
        ×
      </button>
      <div className="account-ghost">
        <BrandAvatar size={54} />
      </div>
      <h2 id="account-title" tabIndex={-1}>
        {title}
      </h2>
      {a.status !== 'ready' ? (
        <Availability />
      ) : a.screen === 'security' && a.authEnabled && a.authLoaded && a.signedIn && securityEnabled ? (
        <div className="account-clerk account-security">
          <UserProfile routing="hash" />
        </div>
      ) : (
        <ManagedEntry />
      )}
      <AccountFeedback />
    </dialog>
  );
}

export function PendingReward() {
  const a = useAccount();
  const {t, lang} = useHub();
  if (!a.pendingClaims.length) return null;
  return (
    <div className="notice">
      <h3>{t('KP em conferência', 'KP awaiting confirmation')}</h3>
      {a.pendingClaims.map((p) => (
        <div key={p.pendingId} className="pending-claim-row">
          <p>
            <strong>{p.awardKP} KP</strong> · {MEMBER_MESSAGES.award_pending[lang === 'pt' ? 0 : 1]}
          </p>
          <p className="source">
            {t('Prazo:', 'Deadline:')} {new Date(p.expiresAt).toLocaleString(lang === 'pt' ? 'pt-BR' : 'en-US')}
          </p>
          <button className="button" disabled={a.busy} onClick={() => void a.claimReward(p.pendingId)}>
            {t('Confirmar KP', 'Confirm KP')}
          </button>
        </div>
      ))}
    </div>
  );
}

export function AccountWallet() {
  const a = useAccount();
  const {t, lang} = useHub();
  const kpActive = a.capabilities.rewards || a.capabilities.kpProgramState === 'active' || a.capabilities.kpProgramState === 'new_activity_paused';
  const fmt = (n: number) => new Intl.NumberFormat(lang === 'pt' ? 'pt-BR' : 'en-US').format(n);

  return (
    <section className="account-wallet">
      <h2>{t('Carteira de Karaca Points', 'Karaca Points Wallet')}</h2>
      <PendingReward />
      {!a.user ? (
        <>
          <p>{MEMBER_MESSAGES.member_required[lang === 'pt' ? 0 : 1]}</p>
          <button className="button secondary" onClick={() => a.open('login')}>
            {t('Entrar', 'Sign in')}
          </button>
        </>
      ) : !kpActive ? (
        <div className="notice">
          <p>{MEMBER_MESSAGES.kp_disabled[lang === 'pt' ? 0 : 1]}</p>
          <div className="account-actions">
            <Link className="button secondary" href={`/${lang}/conta/kp/`}>
              {t('Ver regras KP', 'View KP rules')}
            </Link>
            <Link className="button secondary" href={`/${lang}/conta/radar/`}>
              {t('Abrir meu Radar', 'Open my Radar')}
            </Link>
          </div>
        </div>
      ) : (
        <>
          {a.walletStatus === 'ready' && typeof a.balance === 'number' && typeof a.reserved === 'number' ? (
            <>
              <div className="wallet-metrics-grid">
                <div className="wallet-metric-box">
                  <span className="eyebrow">{t('SALDO DISPONÍVEL', 'AVAILABLE BALANCE')}</span>
                  <p className="account-balance">{fmt(a.balance)} KP</p>
                </div>
                <div className="wallet-metric-box">
                  <span className="eyebrow">{t('RESERVADO', 'RESERVED')}</span>
                  <p className="wallet-secondary-amount">{fmt(a.reserved)} KP</p>
                </div>
                <div className="wallet-metric-box">
                  <span className="eyebrow">{t('EM CONFERÊNCIA', 'PENDING CONFIRMATION')}</span>
                  <p className="wallet-secondary-amount">{fmt(a.pendingConfirmationKP)} KP</p>
                </div>
              </div>
              <h3>{t('Extrato oficial', 'Official activity')}</h3>
              <ul className="points-ledger">
                {a.history.length ? (
                  a.history.map((e) => (
                    <li key={e.id}>
                      <div>
                        <strong>{(lang === 'pt' ? e.titlePT : e.titleEN) || e.description || t('Movimentação', 'Activity')}</strong>
                        <br />
                        <small>
                          {new Date(e.createdAt).toLocaleDateString(lang === 'pt' ? 'pt-BR' : 'en-US')}
                          {e.supportRef ? ` · Ref: ${e.supportRef}` : ''}
                        </small>
                      </div>
                      <strong className="ledger-delta">
                        {e.amount > 0 ? '+' : ''}
                        {fmt(e.amount)} KP
                      </strong>
                    </li>
                  ))
                ) : (
                  <li>{t('Nenhuma movimentação ainda.', 'No activity yet.')}</li>
                )}
              </ul>
              {a.cursor && (
                <button className="button secondary" disabled={a.busy} onClick={() => void a.loadMore()}>
                  {t('Carregar mais movimentações', 'Load more activity')}
                </button>
              )}
            </>
          ) : (
            <div className="notice" role="status">
              <p>
                {a.walletStatus === 'loading'
                  ? t('Consultando carteira…', 'Loading wallet…')
                  : MEMBER_MESSAGES.wallet_failed[lang === 'pt' ? 0 : 1]}
              </p>
            </div>
          )}
          <button className="button secondary" onClick={() => void a.loadWallet()} disabled={a.walletStatus === 'loading'}>
            {t('Atualizar saldo', 'Refresh balance')}
          </button>
        </>
      )}
      <p className="source">
        {t(
          'KP é ponto promocional de fidelidade: não é moeda, não é vendido e não é convertido em dinheiro.',
          'KP is a promotional loyalty point: not currency, not sold and not convertible to cash.',
        )}
      </p>
    </section>
  );
}

export function AccountPanel() {
  const a = useAccount();
  const {t, lang, changeLanguage} = useHub();
  const [name, setName] = useState('');
  const [marketing, setMarketing] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    setName(a.user?.displayName || '');
    setMarketing(!!a.user?.marketingOptIn);
  }, [a.user?.id, a.user?.displayName, a.user?.marketingOptIn]);

  useEffect(() => {
    if (a.screen === 'delete_confirm') {
      setDeleteOpen(true);
    }
  }, [a.screen]);

  if (!a.user) {
    return (
      <section className="account-panel">
        <h2>{t('Perfil e conta', 'Profile and account')}</h2>
        {a.status !== 'ready' ? (
          <Availability />
        ) : (
          <div className="account-actions">
            <button className="button" onClick={() => a.open(a.onboardingRequired ? 'onboarding' : 'login')}>
              {a.onboardingRequired ? t('Concluir cadastro', 'Finish account') : t('Entrar', 'Sign in')}
            </button>
            {!a.onboardingRequired && a.capabilities.registration && (
              <button className="button secondary" onClick={() => a.open('register')}>
                {t('Criar conta', 'Create account')}
              </button>
            )}
          </div>
        )}
        <AccountFeedback />
      </section>
    );
  }

  const dirty = name.trim() !== (a.user.displayName || '').trim() || marketing !== Boolean(a.user.marketingOptIn);

  return (
    <section className="account-panel">
      <div className="account-identity">
        <UserAvatar name={a.user.displayName} email={a.user.email} src={a.user.avatarUrl} size={64} />
        <div>
          <h2>{a.user.displayName}</h2>
          <p>
            {a.user.email} · {t('E-mail confirmado', 'Verified email')}
          </p>
          {a.user.cpfMasked && <p className="source">CPF: {a.user.cpfMasked}</p>}
        </div>
      </div>

      <AvatarPicker />

      <form
        className="account-form"
        onSubmit={(e) => {
          e.preventDefault();
          void a.action(async () => {
            await a.patchProfile({displayName: name, marketingOptIn: a.user?.isMinor ? false : marketing});
            a.setNotice('preferences_saved');
          });
        }}
      >
        <label>
          {t('Nome de exibição', 'Display name')}
          <input
            value={name}
            required
            minLength={2}
            maxLength={60}
            onChange={(e) => setName(e.target.value)}
            autoComplete="nickname"
          />
        </label>
        <label>
          {t('Idioma da conta e navegação', 'Account and navigation language')}
          <select value={lang} onChange={(e) => void changeLanguage(e.target.value === 'en' ? 'en' : 'pt')}>
            <option value="pt">Português (Brasil)</option>
            <option value="en">English</option>
          </select>
        </label>
        {!a.user.isMinor && (
          <label className="account-check">
            <input type="checkbox" checked={marketing} onChange={(e) => setMarketing(e.target.checked)} />
            <span>{t('Receber novidades e avisos editoriais por e-mail (opcional)', 'Receive news and editorial updates by email (optional)')}</span>
          </label>
        )}
        <div className="account-actions">
          <button className="button" disabled={a.busy || !dirty}>
            {a.busy ? MEMBER_MESSAGES.saving[lang === 'pt' ? 0 : 1] : t('Salvar alterações', 'Save changes')}
          </button>
          {dirty && (
            <button
              type="button"
              className="quiet"
              onClick={() => {
                setName(a.user?.displayName || '');
                setMarketing(Boolean(a.user?.marketingOptIn));
              }}
            >
              {t('Cancelar edição', 'Cancel edits')}
            </button>
          )}
        </div>
      </form>

      <AccountFeedback />

      <div className="profile-sections-grid">
        <div className="profile-subcard">
          <h3>{t('Segurança e sessão', 'Security and session')}</h3>
          <p className="source">
            {t(
              'Gerencie seus fatores de autenticação ou encerre a sessão ativa neste navegador.',
              'Manage your authentication factors or sign out of the active session in this browser.',
            )}
          </p>
          <div className="account-actions">
            {securityEnabled && (
              <button type="button" className="button secondary" onClick={() => a.open('security')}>
                {t('Segurança e acesso', 'Security and access')}
              </button>
            )}
            <button type="button" className="button secondary" disabled={a.busy} onClick={() => void a.logout()}>
              {t('Sair desta sessão', 'Sign out of this session')}
            </button>
          </div>
        </div>

        <div className="profile-subcard">
          <h3>{t('Privacidade e dados', 'Privacy and data')}</h3>
          <p className="source">
            {t(
              'Exporte uma cópia estruturada dos seus dados, interesses, mochila, exploração e extrato KP.',
              'Export a structured copy of your profile, interests, backpack, exploration and KP ledger.',
            )}
          </p>
          <div className="account-actions">
            <button type="button" className="button secondary" disabled={a.busy} onClick={() => void a.exportData()}>
              {t('Exportar meus dados (JSON)', 'Export my data (JSON)')}
            </button>
            <a className="quiet" href="mailto:player.one@anderzilla.com">
              {t('Suporte: player.one@anderzilla.com', 'Support: player.one@anderzilla.com')}
            </a>
          </div>
        </div>
      </div>

      <details
        className="account-danger"
        open={deleteOpen}
        onToggle={(e) => setDeleteOpen((e.currentTarget as HTMLDetailsElement).open)}
      >
        <summary>{t('Excluir minha conta', 'Delete my account')}</summary>
        <p>{MEMBER_MESSAGES.delete_confirm[lang === 'pt' ? 0 : 1]}</p>
        <ul className="delete-retention-list">
          <li>
            {t(
              'Removidos imediatamente: perfil pessoal, nome, avatar, vínculo de CPF ativo, mochila, interesses, histórico de exploração e sessões.',
              'Removed immediately: personal profile, display name, avatar, active CPF profile, backpack, interests, exploration history and sessions.',
            )}
          </li>
          <li>
            {t(
              'Mantidos sob retenção mínima legal e antifraude: registros imutáveis de auditoria/extrato e bloqueios de segurança aplicáveis, sem uso comercial.',
              'Retained under minimum legal and anti-abuse rules: immutable audit/ledger records and applicable safety blocks, with zero commercial use.',
            )}
          </li>
        </ul>
        {a.error === 'reauth_required' && (
          <div className="account-error" role="alert">
            <p>{MEMBER_MESSAGES.reauth_required[lang === 'pt' ? 0 : 1]}</p>
            <button
              type="button"
              className="button secondary"
              onClick={() => {
                a.open('login');
              }}
            >
              {t('Confirmar acesso', 'Confirm access')}
            </button>
          </div>
        )}
        <form
          className="account-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (confirm) void a.remove('');
          }}
        >
          <label className="account-check">
            <input type="checkbox" required checked={confirm} onChange={(e) => setConfirm(e.target.checked)} />
            <span>
              {t(
                'Compreendo o que será removido e confirmo que desejo excluir minha conta.',
                'I understand what will be removed and confirm I want to delete my account.',
              )}
            </span>
          </label>
          <div className="account-actions">
            <button className="button secondary" disabled={a.busy || !confirm}>
              {t('Excluir conta', 'Delete account')}
            </button>
            <button
              type="button"
              className="quiet"
              onClick={() => {
                setConfirm(false);
                setDeleteOpen(false);
                if (a.screen === 'delete_confirm') a.open(null);
              }}
            >
              {t('Manter conta', 'Keep account')}
            </button>
          </div>
        </form>
      </details>
    </section>
  );
}
