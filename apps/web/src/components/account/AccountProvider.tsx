"use client";
import {ClerkProvider,useAuth,useClerk} from '@clerk/react';
import {ptBR,enUS} from '@clerk/localizations';
import {createContext,useCallback,useContext,useEffect,useRef,useState,type ReactNode} from 'react';

export type AccountUser={id:string;email:string;emailVerified:boolean;displayName:string;language:'pt'|'en';interests:string[];saved:string[];opened:string[];marketingOptIn?:boolean;hasPassword?:boolean;avatarUrl?:string|null;isMinor?:boolean;guardianLinked?:boolean;cpfMasked?:string};
export type Capabilities={registration:boolean;emailPassword:boolean;google:boolean;meta:boolean;passwordReset:boolean;emailResend:boolean;rewards:boolean;minimumAge:number;termsVersion?:string;privacyVersion?:string;provider?:string;available?:boolean;minorAccessEnabled?:boolean};
export type Entry={id:string;amount:number;reservedAmount:number;description?:string;missionId?:string;createdAt:string};
function normalizeUser(row:any):AccountUser|null {if(!row||typeof row.id!=='string')return null;return {...row,language:row.lang==='en'?'en':'pt',saved:Array.isArray(row.saved)?row.saved:[],opened:Array.isArray(row.opened)?row.opened:[],interests:Array.isArray(row.interests)?row.interests:[]}}
function entries(rows:any[]):Entry[]{return rows.map(r=>({id:r.id,amount:r.available_delta,reservedAmount:r.reserved_delta,description:r.reason,missionId:r.reference_id,createdAt:typeof r.created_at==='number'?new Date(r.created_at*1000).toISOString():r.created_at}))}
export type PendingReward={pendingToken:string;evidenceRef:string;missionId:string;missionVersion:number;awardPreview:number;expiresAt:string;idempotencyKey:string};
export type AccountScreen='login'|'register'|'verify'|'forgot'|'reset'|'reward'|'onboarding'|'security'|null;
const disabled:Capabilities={registration:false,emailPassword:false,google:false,meta:false,passwordReset:false,emailResend:false,rewards:false,minimumAge:18};
const configuredBase=process.env.NEXT_PUBLIC_ACCOUNT_API_BASE?.replace(/\/$/,'')||'';
function approvedBase(){if(configuredBase==='/api')return '';try{const u=new URL(configuredBase);return u.protocol==='https:'||u.protocol==='http:'&&['localhost','127.0.0.1'].includes(u.hostname)?configuredBase:''}catch{return ''}}
const base=approvedBase();
const baseEnabled=configuredBase==='/api'||Boolean(base);
const clerkKey=process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY||'';
type AuthBridge={loaded:boolean;signedIn:boolean;getToken:()=>Promise<string|null>;signOut:()=>Promise<void>};
const signedOut:AuthBridge={loaded:false,signedIn:false,getToken:async()=>null,signOut:async()=>{}};
export class AccountError extends Error {constructor(public code:string){super(code)}}
function useAccountState(auth:AuthBridge){
 const authRef=useRef(auth);authRef.current=auth;
 const [profileStatus,setProfileStatus]=useState<'idle'|'loading'|'ready'|'blocked'|'error'>('idle'),[deletionPending,setDeletionPending]=useState(false);
 const [onboardingRequired,setOnboardingRequired]=useState(false),[authEnabled,setAuthEnabled]=useState(false);
 const [entry,setEntry]=useState<'adult'|'returning'|null>(null);
 const [capabilities,setCapabilities]=useState(disabled),[status,setStatus]=useState<'loading'|'ready'|'unavailable'>(baseEnabled?'loading':'unavailable');
 const [user,setUser]=useState<AccountUser|null>(null),[screen,setScreen]=useState<AccountScreen>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [reserved,setReserved]=useState<number|null>(null),[cursor,setCursor]=useState<string|null>(null);
 const [balance,setBalance]=useState<number|null>(null),[history,setHistory]=useState<Entry[]>([]),[walletStatus,setWalletStatus]=useState<'idle'|'loading'|'ready'|'error'>('idle');
 const [pending,setPending]=useState<PendingReward|null>(null);
 const userRef=useRef<AccountUser|null>(null);
 const commitUser=useCallback((value:AccountUser|null)=>{userRef.current=value;setUser(value)},[]);
 const profileRevision=useRef(0);
 const csrf=useRef('');const profileQueue=useRef<Promise<unknown>>(Promise.resolve());
 const request=useCallback(async(path:string,method='GET',body?:unknown,idempotencyKey?:string)=>{
  if(!baseEnabled)throw new AccountError('unavailable');
  const token=authRef.current.signedIn?await authRef.current.getToken():null;
  if(authRef.current.signedIn&&!token)throw new AccountError('session_expired');
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
  try{const response=await fetch(`${base}${path}`,{method,credentials:'omit',cache:'no-store',signal:controller.signal,headers:{Accept:'application/json',...(token?{'X-AnderZilla-Authorization':`Bearer ${token}`} :{}),...(idempotencyKey?{'Idempotency-Key':idempotencyKey}:{}),...(method!=='GET'?{'Content-Type':'application/json'}:{})},...(method!=='GET'?{body:JSON.stringify(body??{})}:{})});
   const data=await response.json().catch(()=>({}));if(!response.ok)throw new AccountError(typeof data.error?.code==='string'?data.error.code:typeof data.code==='string'?data.code:typeof data.error==='string'?data.error:response.status===401?'session_expired':response.status===429?'rate_limited':'request_failed');
   if(typeof data.csrfToken==='string')csrf.current=data.csrfToken;
   return data;
  }catch(e){if(e instanceof AccountError)throw e;throw new AccountError('network_error')}finally{clearTimeout(timer)}
 },[]);
 const refresh=useCallback(async()=>{setProfileStatus('loading');try{const data=await request('/api/account/me');const u=normalizeUser(data.account);commitUser(u);setOnboardingRequired(data.onboardingRequired===true);setProfileStatus('ready');return u}catch(e){commitUser(null);setOnboardingRequired(false);if(e instanceof AccountError&&['authentication_required','session_expired'].includes(e.code)){setProfileStatus('idle');return null}setProfileStatus(e instanceof AccountError&&e.code==='account_unavailable'?'blocked':'error');throw e}},[request,commitUser]);
 const reconnect=useCallback(async()=>{if(!baseEnabled){setStatus('unavailable');return}setStatus('loading');try{const data=await request('/api/account/capabilities');if(data.provider!=='clerk'||data.available!==true||!clerkKey)throw new AccountError('unavailable');setCapabilities({...disabled,...data,rewards:false});if(authRef.current.loaded&&authRef.current.signedIn)await refresh();setStatus('ready')}catch{setStatus('unavailable');commitUser(null)}},[request,refresh,commitUser]);
 useEffect(()=>{void reconnect()},[reconnect]);
 useEffect(()=>{if(!auth.loaded)return;if(!auth.signedIn){commitUser(null);setOnboardingRequired(false);return}void refresh().then(u=>{if(!u)setScreen('onboarding');else setScreen(null)}).catch(e=>setError(e instanceof AccountError?e.code:'request_failed'))},[auth.loaded,auth.signedIn,refresh,commitUser]);
 useEffect(()=>{try{const url=new URL(window.location.href);const mode=url.searchParams.get('account');if(mode==='register'||mode==='complete'||mode==='login')setScreen(mode==='register'?'register':'login');const previousEntry=sessionStorage.getItem('anderzilla-auth-entry');if(previousEntry==='adult'||previousEntry==='returning'){setEntry(previousEntry);setAuthEnabled(true)}}catch{}},[]);
 function enableAuth(kind:'adult'|'returning'){setEntry(kind);setAuthEnabled(true);try{sessionStorage.setItem('anderzilla-auth-entry',kind)}catch{}}
 const loadWallet=useCallback(async()=>{const owner=userRef.current?.id;setWalletStatus('loading');try{const [wallet,ledger]=await Promise.all([request('/api/points/wallet'),request('/api/points/ledger')]);if(userRef.current?.id!==owner)return;if(typeof wallet.available!=='number'||typeof wallet.reserved!=='number')throw new AccountError('invalid_response');setBalance(wallet.available);setReserved(wallet.reserved);setHistory(entries(Array.isArray(ledger.items)?ledger.items:[]));setCursor(ledger.nextCursor||null);setWalletStatus('ready')}catch{if(userRef.current?.id!==owner)return;setBalance(null);setReserved(null);setCursor(null);setHistory([]);setWalletStatus('error')}},[request]);
 useEffect(()=>{setBalance(null);setReserved(null);setCursor(null);setHistory([]);setWalletStatus('idle');if(user?.emailVerified&&capabilities.rewards)void loadWallet()},[user?.id,user?.emailVerified,capabilities.rewards,loadWallet]);
 useEffect(()=>{try{const value=JSON.parse(sessionStorage.getItem('anderzilla-pending-reward')||'null');if(value&&typeof value.pendingToken==='string'&&Date.parse(value.expiresAt)>Date.now())setPending(value);else sessionStorage.removeItem('anderzilla-pending-reward')}catch{}},[]);
 function rememberReward(value:Omit<PendingReward,'idempotencyKey'>){const reward={...value,idempotencyKey:crypto.randomUUID()};setPending(reward);try{sessionStorage.setItem('anderzilla-pending-reward',JSON.stringify(reward))}catch{}if(!user)open('reward');else setNotice('reward_pending')}
 function forgetReward(){setPending(null);try{sessionStorage.removeItem('anderzilla-pending-reward')}catch{}}
 function open(next:AccountScreen){setError('');setNotice('');setScreen(next)}
 async function action(operation:()=>Promise<unknown>){setBusy(true);setError('');setNotice('');try{await operation();return true}catch(e){setError(e instanceof AccountError?e.code:'request_failed');return false}finally{setBusy(false)}}
 const patchProfile=useCallback((patch:Partial<AccountUser>)=>{
  const owner=userRef.current?.id,revision=++profileRevision.current;
  if(userRef.current)commitUser({...userRef.current,...patch});
  const operation=profileQueue.current.catch(()=>{}).then(async()=>{
   if(!owner||userRef.current?.id!==owner)throw new AccountError('session_expired');
   const {language,...fields}=patch;
   try{const data=await request('/api/account/profile','PATCH',{...fields,...(language?{lang:language==='pt'?'pt-BR':'en'}:{})});if(userRef.current?.id===owner&&profileRevision.current===revision){if(data.account)commitUser(normalizeUser(data.account));else await refresh()}}
   catch(e){if(userRef.current?.id===owner&&profileRevision.current===revision)await refresh().catch(()=>{});throw e}
  });profileQueue.current=operation;return operation;
 },[request,refresh,commitUser]);
 async function savePreferences(patch:Partial<AccountUser>){setError('');try{await patchProfile(patch);setNotice('preferences_saved')}catch(e){setError(e instanceof AccountError?e.code:'request_failed')}}
 return {capabilities,status,user,onboardingRequired,profileStatus,deletionPending,authEnabled,authLoaded:auth.loaded,signedIn:auth.signedIn,entry,enableAuth,pending,rememberReward,screen,busy,error,notice,balance,reserved,history,cursor,walletStatus,open,setError,setNotice,request,refresh,reconnect,loadWallet,loadMore:()=>action(async()=>{if(!cursor)return;const data=await request(`/api/points/ledger?cursor=${encodeURIComponent(cursor)}`);setHistory(rows=>[...rows,...entries(data.items||[])]);setCursor(data.nextCursor||null)}),action,patchProfile,savePreferences,
  claimReward:()=>action(async()=>{if(!pending||!user?.emailVerified)throw new AccountError('email_not_verified');if(Date.parse(pending.expiresAt)<=Date.now()){forgetReward();throw new AccountError('reward_expired')}await request('/api/points/pending/claim','POST',{pendingToken:pending.pendingToken},pending.idempotencyKey);forgetReward();await loadWallet();setNotice('reward_claimed')}),
  login:async(_email:string,_password:string)=>{open('login');return false},
  register:async(_data:Record<string,unknown>)=>{open('register');return false},
  verify:async(_code:string,_email:string)=>{open('login');return false},
  resend:async(_email:string)=>{open('login');return false},
  logout:()=>action(async()=>{await profileQueue.current.catch(()=>{});await authRef.current.signOut();commitUser(null);setOnboardingRequired(false);setProfileStatus('idle');setDeletionPending(false);forgetReward();setNotice('signed_out')}),
  remove:(_password:string)=>action(async()=>{await profileQueue.current.catch(()=>{});try{await request('/api/account/delete','POST',{confirm:'DELETE'})}catch(e){if(e instanceof AccountError&&e.code==='deletion_pending'){setDeletionPending(true);commitUser(null);setOnboardingRequired(false);setProfileStatus('blocked');setScreen('onboarding')}throw e}try{await authRef.current.signOut()}catch{}commitUser(null);setOnboardingRequired(false);setProfileStatus('idle');setDeletionPending(false);forgetReward();setNotice('account_deleted')}),
  resetRequest:async(_email:string)=>{open('login');return false},
  resetConfirm:async(_email:string,_code:string,_password:string)=>{open('login');return false},
  completeOnboarding:(data:Record<string,unknown>)=>action(async()=>{await request('/api/account/onboarding','POST',data);await refresh();open(null);setNotice('profile_completed')}),
  exportData:()=>action(async()=>{const data=await request('/api/account/export');const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const anchor=document.createElement('a');anchor.href=url;anchor.download='anderzilla-account.json';anchor.click();URL.revokeObjectURL(url);setNotice('export_ready')}),
  social:async(_provider:'google'|'meta',_consent:Record<string,unknown>)=>{open('login');return false},
 };
}
const Context=createContext<ReturnType<typeof useAccountState>|null>(null);
function ClerkBridge({onChange}:{onChange:(auth:AuthBridge)=>void}){const {isLoaded,isSignedIn,getToken}=useAuth(),clerk=useClerk();useEffect(()=>{onChange({loaded:isLoaded,signedIn:!!isSignedIn,getToken:()=>getToken(),signOut:async()=>{await clerk.signOut()}})},[isLoaded,isSignedIn,getToken,clerk,onChange]);return null}
export function AccountProvider({children}:{children:ReactNode}){const [auth,setAuth]=useState<AuthBridge>(signedOut),value=useAccountState(auth);const [english,setEnglish]=useState(false);useEffect(()=>{setEnglish(/^\/en\//.test(window.location.pathname))},[]);const content=<Context.Provider value={value}>{children}</Context.Provider>;return value.authEnabled&&clerkKey?<ClerkProvider publishableKey={clerkKey} localization={english?enUS:ptBR} appearance={{variables:{colorPrimary:'#c2ff36',colorBackground:'#111b2d',colorForeground:'#f5f7ff',colorPrimaryForeground:'#080d19',colorNeutral:'#f5f7ff',colorInput:'#080d19',colorInputForeground:'#f5f7ff',colorMutedForeground:'#a9b6ce',colorDanger:'#ff5967',borderRadius:'12px'},elements:{rootBox:'account-clerk-root',cardBox:'account-clerk-card',card:'account-clerk-card',footerAction:'account-clerk-footer'}}} afterSignOutUrl={english?'/en/?account=login#profile':'/pt/?account=login#profile'}><ClerkBridge onChange={setAuth}/>{content}</ClerkProvider>:content}
export function useAccount(){const value=useContext(Context);if(!value)throw new Error('AccountProvider required');return value}
