"use client";
import {ClerkProvider, useAuth, useClerk} from '@clerk/react';
import {ptBR, enUS} from '@clerk/localizations';
import {createContext, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState, type ReactNode} from 'react';

export type AccountUser = {
  id: string;
  email: string;
  emailVerified: boolean;
  displayName: string;
  language: 'pt' | 'en';
  interests: string[];
  saved: string[];
  opened: string[];
  interestsVersion?: number;
  explorationGeneration?: number;
  marketingOptIn?: boolean;
  hasPassword?: boolean;
  avatarUrl?: string | null;
  isMinor?: boolean;
  guardianLinked?: boolean;
  cpfMasked?: string;
};

export type Capabilities = {
  registration: boolean;
  emailPassword: boolean;
  google: boolean;
  meta: boolean;
  passwordReset: boolean;
  emailResend: boolean;
  rewards: boolean;
  kpProgramState?: 'disabled' | 'active' | 'new_activity_paused' | 'maintenance' | 'closed';
  memberArea?: boolean;
  minimumAge: number;
  termsVersion?: string;
  privacyVersion?: string;
  provider?: string;
  available?: boolean;
  minorAccessEnabled?: boolean;
};

export type Entry = {
  id: string;
  amount: number;
  reservedAmount: number;
  description?: string;
  missionId?: string;
  missionVersion?: number;
  titlePT?: string;
  titleEN?: string;
  supportRef?: string;
  createdAt: string;
};

export type PendingClaimSummary = {
  pendingId: string;
  attemptId: string;
  missionId: string;
  missionVersion: number;
  awardKP: number;
  expiresAt: string;
  createdAt?: string;
};

export type PendingReward = {
  pendingToken: string;
  evidenceRef: string;
  missionId: string;
  missionVersion: number;
  awardPreview: number;
  expiresAt: string;
  idempotencyKey: string;
};

export type AccountScreen = 'login' | 'register' | 'verify' | 'forgot' | 'reset' | 'reward' | 'onboarding' | 'security' | 'delete_confirm' | null;

export type PostLoginIntent = {
  type: 'route' | 'save_article';
  path: string;
  discoveryId?: string;
  expiresAt: number;
};

const INTENT_KEY = 'anderzilla-post-login-intent';
const LEGACY_KEYS_LOCAL = ['anderzilla-hub-demo-v1', 'anderzilla-guest-player', 'anderzilla-wallet-cache'];
const LEGACY_KEYS_SESSION = ['anderzilla-pending-reward'];

export function sanitizeInternalReturnPath(rawPath: string | null | undefined, fallbackLang: 'pt' | 'en' = 'pt'): string {
  const defaultDashboard = `/${fallbackLang}/conta/`;
  if (!rawPath || typeof rawPath !== 'string') return defaultDashboard;
  const trimmed = rawPath.trim();
  if (!trimmed.startsWith('/') || trimmed.startsWith('//') || trimmed.includes('\\') || /https?:/i.test(trimmed)) {
    return defaultDashboard;
  }
  try {
    const parsed = new URL(trimmed, 'https://anderzilla.com');
    if (parsed.origin !== 'https://anderzilla.com') return defaultDashboard;
    const p = parsed.pathname;
    const allowedPrefix = /^\/(pt|en)\/(conta(\/(radar|perfil|mochila|interesses|exploracao|kp|carteira|missoes(\/[A-Za-z0-9_.-]+)?))?|radar(\/[A-Za-z0-9_.-]+)?)?\/?$/;
    if (!allowedPrefix.test(p)) return defaultDashboard;
    // Strip any suspicious query parameters that attempt to pass user authority or tokens
    const safeParams = new URLSearchParams();
    for (const [k, v] of parsed.searchParams.entries()) {
      if (['id', 'category', 'q'].includes(k) && /^[A-Za-z0-9_.-]{1,80}$/.test(v)) {
        safeParams.set(k, v);
      }
    }
    const qs = safeParams.toString();
    const normalizedPath = p.endsWith('/') ? p : `${p}/`;
    return qs ? `${normalizedPath}?${qs}` : normalizedPath;
  } catch {
    return defaultDashboard;
  }
}

export function savePostLoginIntent(intent: Omit<PostLoginIntent, 'expiresAt'>) {
  try {
    const safePath = sanitizeInternalReturnPath(intent.path, intent.path.startsWith('/en/') ? 'en' : 'pt');
    const payload: PostLoginIntent = {
      type: intent.type,
      path: safePath,
      ...(intent.discoveryId && /^[A-Za-z0-9_.:-]{1,128}$/.test(intent.discoveryId) ? {discoveryId: intent.discoveryId} : {}),
      expiresAt: Date.now() + 15 * 60 * 1000,
    };
    sessionStorage.setItem(INTENT_KEY, JSON.stringify(payload));
  } catch {}
}

export function consumePostLoginIntent(): PostLoginIntent | null {
  try {
    const raw = sessionStorage.getItem(INTENT_KEY);
    sessionStorage.removeItem(INTENT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PostLoginIntent;
    if (!parsed || typeof parsed !== 'object' || typeof parsed.expiresAt !== 'number' || parsed.expiresAt <= Date.now()) {
      return null;
    }
    const safePath = sanitizeInternalReturnPath(parsed.path, parsed.path?.startsWith('/en/') ? 'en' : 'pt');
    return {
      type: parsed.type === 'save_article' ? 'save_article' : 'route',
      path: safePath,
      discoveryId: typeof parsed.discoveryId === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(parsed.discoveryId) ? parsed.discoveryId : undefined,
      expiresAt: parsed.expiresAt,
    };
  } catch {
    return null;
  }
}

export function peekPostLoginIntent(): PostLoginIntent | null {
  try {
    const raw = sessionStorage.getItem(INTENT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PostLoginIntent;
    if (!parsed || typeof parsed.expiresAt !== 'number' || parsed.expiresAt <= Date.now()) {
      sessionStorage.removeItem(INTENT_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function purgeLegacyVisitorStorage() {
  try {
    for (const k of LEGACY_KEYS_LOCAL) localStorage.removeItem(k);
  } catch {}
  try {
    for (const k of LEGACY_KEYS_SESSION) sessionStorage.removeItem(k);
  } catch {}
}

function normalizeUser(row: any): AccountUser | null {
  if (!row || typeof row.id !== 'string') return null;
  return {
    ...row,
    language: row.lang === 'en' ? 'en' : 'pt',
    saved: Array.isArray(row.saved) ? row.saved : [],
    opened: Array.isArray(row.opened) ? row.opened : [],
    interests: Array.isArray(row.interests) ? row.interests : [],
    interestsVersion: typeof row.interestsVersion === 'number' ? row.interestsVersion : 1,
    explorationGeneration: typeof row.explorationGeneration === 'number' ? row.explorationGeneration : 1,
  };
}

function entries(rows: any[]): Entry[] {
  return rows.map((r) => ({
    id: r.id,
    amount: typeof r.availableDelta === 'number' ? r.availableDelta : r.available_delta,
    reservedAmount: typeof r.reservedDelta === 'number' ? r.reservedDelta : r.reserved_delta,
    description: r.reason,
    missionId: r.missionId || r.reference_id,
    missionVersion: r.missionVersion,
    titlePT: r.titlePT,
    titleEN: r.titleEN,
    supportRef: r.supportRef,
    createdAt: typeof r.created_at === 'number' ? new Date(r.created_at * 1000).toISOString() : (r.createdAt || r.created_at),
  }));
}

const disabled: Capabilities = {
  registration: false,
  emailPassword: false,
  google: false,
  meta: false,
  passwordReset: false,
  emailResend: false,
  rewards: false,
  kpProgramState: 'disabled',
  memberArea: false,
  minimumAge: 18,
};

const configuredBase = process.env.NEXT_PUBLIC_ACCOUNT_API_BASE?.replace(/\/$/, '') || '';
function approvedBase() {
  if (configuredBase === '/api') return '';
  try {
    const u = new URL(configuredBase);
    return u.protocol === 'https:' || (u.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(u.hostname))
      ? configuredBase
      : '';
  } catch {
    return '';
  }
}
function isLoopbackHost(): boolean {
  if (typeof window === 'undefined') return false;
  return ['localhost', '127.0.0.1'].includes(window.location.hostname);
}

const base = approvedBase();
const baseEnabled = configuredBase === '/api' || Boolean(base);
const clerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || '';

function isApiAvailable(): boolean {
  return baseEnabled || isLoopbackHost();
}

type AuthBridge = {
  loaded: boolean;
  signedIn: boolean;
  subject?: string | null;
  sessionId?: string | null;
  getToken: () => Promise<string | null>;
  signOut: () => Promise<void>;
};

const signedOut: AuthBridge = {
  loaded: false,
  signedIn: false,
  subject: null,
  getToken: async () => null,
  signOut: async () => {},
};

export class AccountError extends Error {
  constructor(public code: string, public status?: number) {
    super(code);
  }
}

declare global {
  interface Window {
    __ANDERZILLA_SYNTHETIC_TOKEN__?: string | null;
  }
}

function getSyntheticLoopbackToken(): string | null {
  if (typeof window === 'undefined') return null;
  if (!['localhost', '127.0.0.1'].includes(window.location.hostname)) return null;
  if (typeof window.__ANDERZILLA_SYNTHETIC_TOKEN__ === 'string' && window.__ANDERZILLA_SYNTHETIC_TOKEN__) {
    return window.__ANDERZILLA_SYNTHETIC_TOKEN__;
  }
  try {
    const t = sessionStorage.getItem('anderzilla-synthetic-test-token');
    return t || null;
  } catch {
    return null;
  }
}

function useAccountState(auth: AuthBridge) {
  const authRef = useRef(auth);
  authRef.current = auth;

  const sessionEpochRef = useRef(1);
  const [sessionEpoch, setSessionEpoch] = useState(1);
  const controllersRef = useRef<Set<AbortController>>(new Set());
  const blobUrlsRef = useRef<Set<string>>(new Set());
  const channelRef = useRef<BroadcastChannel | null>(null);
  const logoutPendingLocalRef = useRef(false);

  const [profileStatus, setProfileStatus] = useState<'idle' | 'loading' | 'waking' | 'ready' | 'blocked' | 'error'>('idle');
  const [deletionPending, setDeletionPending] = useState(false);
  const [logoutUnconfirmed, setLogoutUnconfirmed] = useState(false);
  const [reauthReturnScreen, setReauthReturnScreen] = useState<AccountScreen>(null);
  const [onboardingRequired, setOnboardingRequired] = useState(false);
  const [authEnabled, setAuthEnabled] = useState(false);
  const [entry, setEntry] = useState<'adult' | 'returning' | null>(null);
  const [capabilities, setCapabilities] = useState(disabled);
  const [status, setStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading');
  const [user, setUser] = useState<AccountUser | null>(null);
  const [screen, setScreen] = useState<AccountScreen>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [reserved, setReserved] = useState<number | null>(null);
  const [pendingConfirmationKP, setPendingConfirmationKP] = useState<number>(0);
  const [pendingClaims, setPendingClaims] = useState<PendingClaimSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [balance, setBalance] = useState<number | null>(null);
  const [history, setHistory] = useState<Entry[]>([]);
  const [walletStatus, setWalletStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [pending, setPending] = useState<PendingReward | null>(null);
  const [pendingIntentConfirmation, setPendingIntentConfirmation] = useState<PostLoginIntent | null>(null);

  const userRef = useRef<AccountUser | null>(null);
  const commitUser = useCallback((value: AccountUser | null) => {
    userRef.current = value;
    setUser(value);
  }, []);

  const profileRevision = useRef(0);
  const csrf = useRef('');
  const profileQueue = useRef<Promise<unknown>>(Promise.resolve());

  const clearPrivateState = useCallback((broadcast = false) => {
    const nextEpoch = sessionEpochRef.current + 1;
    sessionEpochRef.current = nextEpoch;
    setSessionEpoch(nextEpoch);
    for (const c of controllersRef.current) {
      try {
        c.abort();
      } catch {}
    }
    controllersRef.current.clear();
    for (const url of blobUrlsRef.current) {
      try {
        URL.revokeObjectURL(url);
      } catch {}
    }
    blobUrlsRef.current.clear();
    commitUser(null);
    setOnboardingRequired(false);
    setBalance(null);
    setReserved(null);
    setPendingConfirmationKP(0);
    setPendingClaims([]);
    setHistory([]);
    setCursor(null);
    setWalletStatus('idle');
    setPending(null);
    setPendingIntentConfirmation(null);
    purgeLegacyVisitorStorage();
    if (broadcast && channelRef.current) {
      try {
        channelRef.current.postMessage({type: 'session_invalidated', epoch: nextEpoch});
      } catch {}
    }
  }, [commitUser]);

  // Clean legacy anonymous localStorage & sessionStorage on initial mount
  useEffect(() => {
    purgeLegacyVisitorStorage();
  }, []);

  const request = useCallback(
    async (path: string, method = 'GET', body?: unknown, idempotencyKey?: string, extraHeaders?: Record<string, string>) => {
      if (!isApiAvailable()) throw new AccountError('unavailable');
      const startEpoch = sessionEpochRef.current;
      const startSubject = authRef.current.subject;
      const startSession = authRef.current.sessionId;
      const startOwner = userRef.current?.id || null;
      const synthToken = getSyntheticLoopbackToken();
      let token: string | null = null;
      if (synthToken) {
        token = synthToken;
      } else if (authRef.current.signedIn && !logoutPendingLocalRef.current) {
        token = await authRef.current.getToken();
      }
      if (authRef.current.signedIn && !logoutPendingLocalRef.current && !token && !synthToken) {
        throw new AccountError('session_expired', 401);
      }
      if (sessionEpochRef.current !== startEpoch || authRef.current.subject !== startSubject || authRef.current.sessionId !== startSession) {
        throw new AccountError('session_invalidated', 499);
      }
      const controller = new AbortController();
      controllersRef.current.add(controller);
      const timer = setTimeout(() => controller.abort(), 45000);
      try {
        const isBodyMethod = method !== 'GET' && method !== 'OPTIONS';
        const response = await fetch(`${base}${path}`, {
          method,
          credentials: 'omit',
          cache: 'no-store',
          signal: controller.signal,
          headers: {
            Accept: 'application/json',
            ...(token ? {'X-AnderZilla-Authorization': `Bearer ${token}`} : {}),
            ...(idempotencyKey ? {'Idempotency-Key': idempotencyKey} : {}),
            ...(extraHeaders || {}),
            ...(isBodyMethod ? {'Content-Type': 'application/json'} : {}),
          },
          ...(isBodyMethod ? {body: JSON.stringify(body ?? {})} : {}),
        });
        if (sessionEpochRef.current !== startEpoch || authRef.current.subject !== startSubject || authRef.current.sessionId !== startSession || (startOwner && userRef.current && userRef.current.id !== startOwner)) {
          throw new AccountError('session_invalidated', 499);
        }
        const data = await response.json().catch(() => ({}));
        if (sessionEpochRef.current !== startEpoch || authRef.current.subject !== startSubject || authRef.current.sessionId !== startSession) {
          throw new AccountError('session_invalidated', 499);
        }
        if (!response.ok) {
          const code =
            typeof data.error?.code === 'string'
              ? data.error.code
              : typeof data.code === 'string'
                ? data.code
                : typeof data.error === 'string'
                  ? data.error
                  : response.status === 401
                    ? 'session_expired'
                    : response.status === 429
                      ? 'rate_limited'
                      : 'request_failed';
          // Distinguish account-wide invalidation (401 or account_unavailable) from section-level 403
          if (response.status === 401 || code === 'authentication_required' || code === 'session_expired') {
            if (userRef.current) {
              clearPrivateState(true);
              setProfileStatus('idle');
            }
          } else if (code === 'account_unavailable' || code === 'account_suspended' || code === 'account_deleted') {
            clearPrivateState(true);
            setProfileStatus('blocked');
          }
          throw new AccountError(code, response.status);
        }
        if (typeof data.csrfToken === 'string') csrf.current = data.csrfToken;
        return data;
      } catch (e) {
        if (e instanceof AccountError) throw e;
        if ((e as any)?.name === 'AbortError' && sessionEpochRef.current !== startEpoch) {
          throw new AccountError('session_invalidated', 499);
        }
        throw new AccountError(typeof navigator !== 'undefined' && navigator.onLine === false ? 'offline' : 'network_error');
      } finally {
        clearTimeout(timer);
        controllersRef.current.delete(controller);
      }
    },
    [clearPrivateState],
  );

  const applyWalletSnapshot = useCallback((wallet: any) => {
    if (!wallet || typeof wallet.available !== 'number' || typeof wallet.reserved !== 'number') return;
    setBalance(wallet.available);
    setReserved(wallet.reserved);
    setPendingConfirmationKP(typeof wallet.pendingConfirmationKP === 'number' ? wallet.pendingConfirmationKP : 0);
    setPendingClaims(Array.isArray(wallet.pendingClaims) ? wallet.pendingClaims : []);
    setWalletStatus('ready');
  }, []);

  const refresh = useCallback(async () => {
    const startEpoch = sessionEpochRef.current;
    setProfileStatus('loading');
    for (let attempt = 0; attempt < 4; attempt++) {
      try {
        if (attempt > 0) {
          try {
            await request('/api/account/ready');
          } catch {}
        }
        const data = await request('/api/account/me');
        if (sessionEpochRef.current !== startEpoch) return null;
        const u = normalizeUser(data.account);
        if (userRef.current && u && userRef.current.id !== u.id) {
          // Account switch A -> B detected! Wipe A's state first.
          clearPrivateState(true);
        }
        commitUser(u);
        setOnboardingRequired(data.onboardingRequired === true);
        if (data.wallet) {
          applyWalletSnapshot(data.wallet);
        }
        setProfileStatus('ready');
        return u;
      } catch (e) {
        if (sessionEpochRef.current !== startEpoch) return null;
        if (e instanceof AccountError && e.code === 'session_invalidated') return null;
        if (e instanceof AccountError && ['temporarily_unavailable', 'network_error'].includes(e.code) && attempt < 3) {
          setProfileStatus('waking');
          await new Promise((r) => setTimeout(r, 2500));
          continue;
        }
        commitUser(null);
        setOnboardingRequired(false);
        if (e instanceof AccountError && ['authentication_required', 'session_expired'].includes(e.code)) {
          setProfileStatus('idle');
          return null;
        }
        setProfileStatus(e instanceof AccountError && e.code === 'account_unavailable' ? 'blocked' : 'error');
        throw e;
      }
    }
    return null;
  }, [request, commitUser, clearPrivateState, applyWalletSnapshot]);

  const reconnect = useCallback(async () => {
    if (!isApiAvailable()) {
      setStatus('unavailable');
      return;
    }
    setStatus('loading');
    try {
      const data = await request('/api/account/capabilities');
      const synth = Boolean(getSyntheticLoopbackToken());
      const loopback = isLoopbackHost();
      if (data.provider !== 'clerk' || data.available !== true || (!clerkKey && !synth && !loopback)) {
        throw new AccountError('unavailable');
      }
      setCapabilities({
        ...disabled,
        ...data,
        rewards: Boolean(data.rewards),
        kpProgramState: data.kpProgramState || (data.rewards ? 'active' : 'disabled'),
      });
      if ((authRef.current.loaded && authRef.current.signedIn) || synth) {
        await refresh();
      }
      setStatus('ready');
    } catch {
      setStatus('unavailable');
      commitUser(null);
    }
  }, [request, refresh, commitUser]);

  useEffect(() => {
    void reconnect();
  }, [reconnect]);

  // Multi-tab BroadcastChannel + bfcache (pageshow) + visibilitychange revalidation
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if ('BroadcastChannel' in window) {
      const ch = new BroadcastChannel('anderzilla-session-sync');
      channelRef.current = ch;
      ch.onmessage = (ev) => {
        const msg = ev.data;
        if (!msg || typeof msg !== 'object') return;
        if (msg.type === 'session_invalidated') {
          logoutPendingLocalRef.current = true;
          clearPrivateState(false);
          setProfileStatus('idle');
        } else if (msg.type === 'collections_updated' || msg.type === 'wallet_updated') {
          if (userRef.current && (!msg.accountId || msg.accountId === userRef.current.id)) {
            void refresh().catch(() => {});
          }
        }
      };
    }
    const onPageShow = (ev: PageTransitionEvent) => {
      if (ev.persisted) {
        // Restored from bfcache: immediately clear private DOM snapshot until revalidated!
        clearPrivateState(false);
        setProfileStatus('loading');
        void reconnect();
      }
    };
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        const synth = Boolean(getSyntheticLoopbackToken());
        if ((authRef.current.loaded && authRef.current.signedIn) || synth) {
          void refresh().catch(() => {});
        } else if (userRef.current) {
          clearPrivateState(false);
        }
      }
    };
    const onOffline = () => {
      if (!authRef.current.signedIn && !getSyntheticLoopbackToken()) {
        clearPrivateState(false);
      }
    };
    window.addEventListener('pageshow', onPageShow);
    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('pageshow', onPageShow);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('offline', onOffline);
      try {
        channelRef.current?.close();
      } catch {}
      channelRef.current = null;
    };
  }, [clearPrivateState, refresh, reconnect]);

  const lastIdentity = useRef({subject: auth.subject, sessionId: auth.sessionId});
  useLayoutEffect(() => {
    if (lastIdentity.current.subject !== auth.subject || lastIdentity.current.sessionId !== auth.sessionId) {
      lastIdentity.current = {subject: auth.subject, sessionId: auth.sessionId};
      if (auth.signedIn && auth.subject) logoutPendingLocalRef.current = false;
      clearPrivateState(false);
      setProfileStatus('loading');
    }
  }, [auth.subject, auth.sessionId, clearPrivateState]);

  useEffect(() => {
    const synth = Boolean(getSyntheticLoopbackToken());
    if (!auth.loaded && !synth) return;
    if (!auth.signedIn && !synth) {
      if (userRef.current) clearPrivateState(false);
      setOnboardingRequired(false);
      return;
    }
    if (logoutPendingLocalRef.current) return;
    void refresh()
      .then((u) => {
        if (!u) {
          setScreen('onboarding');
        } else {
          if (reauthReturnScreen) {
            setScreen(reauthReturnScreen);
            setReauthReturnScreen(null);
          } else {
            setScreen(null);
          }
          const intent = peekPostLoginIntent();
          if (intent && intent.type === 'save_article' && intent.discoveryId) {
            setPendingIntentConfirmation(consumePostLoginIntent());
          }
        }
      })
      .catch((e) => {
        if (e instanceof AccountError && e.code !== 'session_invalidated') {
          setError(e.code);
        }
      });
  }, [auth.loaded, auth.signedIn, auth.subject, auth.sessionId, refresh, clearPrivateState, reauthReturnScreen]);

  useEffect(() => {
    try {
      const url = new URL(window.location.href);
      const mode = url.searchParams.get('account');
      if (mode === 'register' || mode === 'complete' || mode === 'login') {
        setScreen(mode === 'register' ? 'register' : 'login');
      }
      const previousEntry = sessionStorage.getItem('anderzilla-auth-entry');
      if (previousEntry === 'adult' || previousEntry === 'returning') {
        setEntry(previousEntry);
        setAuthEnabled(true);
      }
    } catch {}
  }, []);

  function enableAuth(kind: 'adult' | 'returning') {
    logoutPendingLocalRef.current = false;
    setLogoutUnconfirmed(false);
    setEntry(kind);
    setAuthEnabled(true);
    try {
      sessionStorage.setItem('anderzilla-auth-entry', kind);
    } catch {}
  }

  const loadWallet = useCallback(async () => {
    const owner = userRef.current?.id;
    const epoch = sessionEpochRef.current;
    if (!owner) return;
    setWalletStatus('loading');
    try {
      const [wallet, ledger] = await Promise.all([request('/api/points/wallet'), request('/api/points/ledger')]);
      if (userRef.current?.id !== owner || sessionEpochRef.current !== epoch) return;
      if (typeof wallet.available !== 'number' || typeof wallet.reserved !== 'number') {
        throw new AccountError('invalid_response');
      }
      applyWalletSnapshot(wallet);
      setHistory(entries(Array.isArray(ledger.items) ? ledger.items : []));
      setCursor(ledger.nextCursor || null);
      setWalletStatus('ready');
    } catch {
      if (userRef.current?.id !== owner || sessionEpochRef.current !== epoch) return;
      setBalance(null);
      setReserved(null);
      setCursor(null);
      setHistory([]);
      setWalletStatus('error');
    }
  }, [request, applyWalletSnapshot]);

  useEffect(() => {
    if (!user?.id || !user.emailVerified) {
      setBalance(null);
      setReserved(null);
      setCursor(null);
      setHistory([]);
      setWalletStatus('idle');
      return;
    }
    if (capabilities.rewards || capabilities.kpProgramState === 'active' || capabilities.kpProgramState === 'new_activity_paused') {
      void loadWallet();
    }
  }, [user?.id, user?.emailVerified, capabilities.rewards, capabilities.kpProgramState, loadWallet]);

  function rememberReward(_value: Omit<PendingReward, 'idempotencyKey'>) {
    // Pending rewards are now authoritative and owned server-side in mission_pending_claims.
    void loadWallet();
    setNotice('reward_pending');
  }

  function forgetReward() {
    setPending(null);
    purgeLegacyVisitorStorage();
  }

  function open(next: AccountScreen) {
    setError('');
    setNotice('');
    setScreen(next);
    if (next && baseEnabled) void request('/api/account/ready').catch(() => {});
  }

  async function action(operation: () => Promise<unknown>) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await operation();
      return true;
    } catch (e) {
      if (e instanceof AccountError && e.code === 'session_invalidated') return false;
      setError(e instanceof AccountError ? e.code : 'request_failed');
      return false;
    } finally {
      setBusy(false);
    }
  }

  const patchProfile = useCallback(
    (patch: Partial<AccountUser>) => {
      const owner = userRef.current?.id;
      const epoch = sessionEpochRef.current;
      const revision = ++profileRevision.current;
      const {language, interests, saved, opened, interestsVersion, explorationGeneration, ...allowedFields} = patch;
      const operation = profileQueue.current
        .catch(() => {})
        .then(async () => {
          if (!owner || userRef.current?.id !== owner || sessionEpochRef.current !== epoch) {
            throw new AccountError('session_expired');
          }
          const payload = {
            ...allowedFields,
            ...(language ? {lang: language === 'pt' ? 'pt-BR' : 'en'} : {}),
          };
          const data = await request('/api/account/profile', 'PATCH', payload);
          if (userRef.current?.id === owner && sessionEpochRef.current === epoch && profileRevision.current === revision) {
            if (data.account) commitUser(normalizeUser(data.account));
            else await refresh();
          }
        });
      profileQueue.current = operation;
      return operation;
    },
    [request, refresh, commitUser],
  );

  async function savePreferences(patch: Partial<AccountUser>) {
    setError('');
    try {
      await patchProfile(patch);
      setNotice('preferences_saved');
      return true;
    } catch (e) {
      setError(e instanceof AccountError ? e.code : 'request_failed');
      return false;
    }
  }

  const notifySync = useCallback((type: 'collections_updated' | 'wallet_updated') => {
    try {
      channelRef.current?.postMessage({type, accountId: userRef.current?.id});
    } catch {}
  }, []);

  return {
    capabilities,
    status,
    user,
    sessionEpoch,
    onboardingRequired,
    profileStatus,
    deletionPending,
    logoutUnconfirmed,
    pendingIntentConfirmation,
    setPendingIntentConfirmation,
    authEnabled,
    authLoaded: auth.loaded || Boolean(getSyntheticLoopbackToken()),
    signedIn: (auth.signedIn || Boolean(getSyntheticLoopbackToken())) && !logoutPendingLocalRef.current,
    entry,
    enableAuth,
    pending,
    pendingClaims,
    pendingConfirmationKP,
    rememberReward,
    screen,
    busy,
    error,
    notice,
    balance,
    reserved,
    history,
    cursor,
    walletStatus,
    open,
    setError,
    setNotice,
    request,
    refresh,
    reconnect,
    loadWallet,
    notifySync,
    clearPrivateState,
    loadMore: () =>
      action(async () => {
        const owner = userRef.current?.id;
        const epoch = sessionEpochRef.current;
        if (!cursor || !owner) return;
        const data = await request(`/api/points/ledger?cursor=${encodeURIComponent(cursor)}`);
        if (userRef.current?.id !== owner || sessionEpochRef.current !== epoch) return;
        setHistory((rows) => [...rows, ...entries(data.items || [])]);
        setCursor(data.nextCursor || null);
      }),
    action,
    patchProfile,
    savePreferences,
    claimReward: (pendingId?: string, operationKey?: string) =>
      action(async () => {
        if (!user?.emailVerified) throw new AccountError('email_not_verified');
        const targetId = pendingId || pendingClaims[0]?.pendingId || pending?.pendingToken;
        if (!targetId) throw new AccountError('invalid_pending');
        const idemKey = operationKey || `claim-${targetId}`;
        await request('/api/points/pending/claim', 'POST', {pendingId: targetId}, idemKey);
        forgetReward();
        await loadWallet();
        notifySync('wallet_updated');
        setNotice('reward_claimed');
      }),
    login: async (_email: string, _password: string) => {
      open('login');
      return false;
    },
    register: async (_data: Record<string, unknown>) => {
      open('register');
      return false;
    },
    verify: async (_code: string, _email: string) => {
      open('login');
      return false;
    },
    resend: async (_email: string) => {
      open('login');
      return false;
    },
    logout: () =>
      action(async () => {
        // Immediately hide & clear private UI/state before awaiting remote revocation
        logoutPendingLocalRef.current = true;
        clearPrivateState(true);
        setProfileStatus('idle');
        setDeletionPending(false);
        try {
          sessionStorage.removeItem('anderzilla-synthetic-test-token');
          if (typeof window !== 'undefined') window.__ANDERZILLA_SYNTHETIC_TOKEN__ = null;
        } catch {}
        try {
          await request('/api/account/logout', 'POST', {}).catch(() => {});
          await authRef.current.signOut();
          setLogoutUnconfirmed(false);
          setNotice('signed_out');
        } catch {
          // Remote sign-out uncertain: keep local private data hidden and inform user!
          setLogoutUnconfirmed(true);
          setError('logout_unconfirmed');
        }
      }),
    remove: (_password: string) =>
      action(async () => {
        await profileQueue.current.catch(() => {});
        try {
          await request('/api/account/delete', 'POST', {confirm: 'DELETE'});
        } catch (e) {
          if (e instanceof AccountError && e.code === 'deletion_pending') {
            setDeletionPending(true);
            clearPrivateState(true);
            setProfileStatus('blocked');
            setScreen('onboarding');
          } else if (e instanceof AccountError && e.code === 'reauth_required') {
            setReauthReturnScreen('delete_confirm');
          }
          throw e;
        }
        logoutPendingLocalRef.current = true;
        try {
          sessionStorage.removeItem('anderzilla-synthetic-test-token');
          if (typeof window !== 'undefined') window.__ANDERZILLA_SYNTHETIC_TOKEN__ = null;
          await authRef.current.signOut();
        } catch {}
        clearPrivateState(true);
        setProfileStatus('idle');
        setDeletionPending(false);
        setNotice('account_deleted');
      }),
    resetRequest: async (_email: string) => {
      open('login');
      return false;
    },
    resetConfirm: async (_email: string, _code: string, _password: string) => {
      open('login');
      return false;
    },
    completeOnboarding: (data: Record<string, unknown>) =>
      action(async () => {
        await request('/api/account/onboarding', 'POST', data);
        await refresh();
        open(null);
        setNotice('profile_completed');
        const intent = consumePostLoginIntent();
        if (intent) {
          if (intent.type === 'save_article' && intent.discoveryId) {
            setPendingIntentConfirmation(intent);
          } else if (intent.path && typeof window !== 'undefined' && window.location.pathname !== intent.path) {
            window.location.assign(intent.path);
          }
        } else if (typeof window !== 'undefined' && !window.location.pathname.includes('/conta')) {
          const lang = window.location.pathname.startsWith('/en') ? 'en' : 'pt';
          window.location.assign(`/${lang}/conta/`);
        }
      }),
    exportData: () =>
      action(async () => {
        const owner = userRef.current?.id;
        const epoch = sessionEpochRef.current;
        const data = await request('/api/account/export');
        if (userRef.current?.id !== owner || sessionEpochRef.current !== epoch) {
          throw new AccountError('session_invalidated');
        }
        const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'}));
        blobUrlsRef.current.add(url);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = 'anderzilla-account.json';
        anchor.click();
        setTimeout(() => {
          URL.revokeObjectURL(url);
          blobUrlsRef.current.delete(url);
        }, 1000);
        setNotice('export_ready');
      }),
    social: async (_provider: 'google' | 'meta', _consent: Record<string, unknown>) => {
      open('login');
      return false;
    },
  };
}

const Context = createContext<ReturnType<typeof useAccountState> | null>(null);

function ClerkBridge({onChange}: {onChange: (auth: AuthBridge) => void}) {
  const {isLoaded, isSignedIn, userId, sessionId, getToken} = useAuth();
  const clerk = useClerk();
  useEffect(() => {
    onChange({
      loaded: isLoaded,
      signedIn: !!isSignedIn,
      subject: userId || null,
      sessionId: sessionId || null,
      getToken: () => getToken(),
      signOut: async () => {
        await clerk.signOut();
      },
    });
  }, [isLoaded, isSignedIn, userId, sessionId, getToken, clerk, onChange]);
  return null;
}

export function AccountProvider({children}: {children: ReactNode}) {
  const [auth, setAuth] = useState<AuthBridge>(signedOut);
  const value = useAccountState(auth);
  const [english, setEnglish] = useState(false);
  useEffect(() => {
    setEnglish(/^\/en(\/|$)/.test(window.location.pathname));
  }, []);
  const content = <Context.Provider value={value}>{children}</Context.Provider>;
  return value.authEnabled && clerkKey ? (
    <ClerkProvider
      publishableKey={clerkKey}
      localization={english ? enUS : ptBR}
      appearance={{
        variables: {
          colorPrimary: '#c2ff36',
          colorBackground: '#10182b',
          colorForeground: '#f4f7ff',
          colorPrimaryForeground: '#070b18',
          colorNeutral: '#f4f7ff',
          colorInput: '#070b18',
          colorInputForeground: '#f4f7ff',
          colorMutedForeground: '#a9b6ce',
          colorDanger: '#ff5967',
          borderRadius: '12px',
        },
        elements: {
          rootBox: 'account-clerk-root',
          cardBox: 'account-clerk-card',
          card: 'account-clerk-card',
          footerAction: 'account-clerk-footer',
        },
      }}
      afterSignOutUrl={english ? '/en/' : '/pt/'}
    >
      <ClerkBridge onChange={setAuth} />
      {content}
    </ClerkProvider>
  ) : (
    content
  );
}

export function useAccount() {
  const value = useContext(Context);
  if (!value) throw new Error('AccountProvider required');
  return value;
}
