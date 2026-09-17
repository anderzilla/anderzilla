"use client";
import {createContext,useCallback,useContext,useEffect,useRef,useState,type ReactNode} from 'react';

export type AccountUser={id:string;email:string;emailVerified:boolean;displayName:string;language:'pt'|'en';interests:string[];saved:string[];opened:string[];marketingOptIn?:boolean;hasPassword?:boolean};
export type Capabilities={registration:boolean;emailPassword:boolean;google:boolean;meta:boolean;passwordReset:boolean;emailResend:boolean;rewards:boolean;minimumAge:number;termsVersion?:string;privacyVersion?:string};
export type Entry={id:string;amount:number;reservedAmount:number;description?:string;missionId?:string;createdAt:string};
function normalizeUser(row:any):AccountUser|null {if(!row||typeof row.id!=='string')return null;return {...row,language:row.lang==='en'?'en':'pt',saved:Array.isArray(row.saved)?row.saved:[],opened:Array.isArray(row.opened)?row.opened:[],interests:Array.isArray(row.interests)?row.interests:[]}}
function entries(rows:any[]):Entry[]{return rows.map(r=>({id:r.id,amount:r.available_delta,reservedAmount:r.reserved_delta,description:r.reason,missionId:r.reference_id,createdAt:typeof r.created_at==='number'?new Date(r.created_at*1000).toISOString():r.created_at}))}
export type PendingReward={pendingToken:string;evidenceRef:string;missionId:string;missionVersion:number;awardPreview:number;expiresAt:string;idempotencyKey:string};
export type AccountScreen='login'|'register'|'verify'|'forgot'|'reset'|'reward'|null;
const disabled:Capabilities={registration:false,emailPassword:false,google:false,meta:false,passwordReset:false,emailResend:false,rewards:false,minimumAge:18};
const configuredBase=process.env.NEXT_PUBLIC_ACCOUNT_API_BASE?.replace(/\/$/,'')||'';
function approvedBase(){try{const u=new URL(configuredBase);return u.protocol==='https:'||u.protocol==='http:'&&['localhost','127.0.0.1'].includes(u.hostname)?configuredBase:''}catch{return ''}}
const base=approvedBase();
export class AccountError extends Error {constructor(public code:string){super(code)}}
function useAccountState(){
 const [capabilities,setCapabilities]=useState(disabled),[status,setStatus]=useState<'loading'|'ready'|'unavailable'>(base?'loading':'unavailable');
 const [user,setUser]=useState<AccountUser|null>(null),[screen,setScreen]=useState<AccountScreen>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [reserved,setReserved]=useState<number|null>(null),[cursor,setCursor]=useState<string|null>(null);
 const [balance,setBalance]=useState<number|null>(null),[history,setHistory]=useState<Entry[]>([]),[walletStatus,setWalletStatus]=useState<'idle'|'loading'|'ready'|'error'>('idle');
 const [pending,setPending]=useState<PendingReward|null>(null);
 const userRef=useRef<AccountUser|null>(null);
 const commitUser=useCallback((value:AccountUser|null)=>{userRef.current=value;setUser(value)},[]);
 const profileRevision=useRef(0);
 const csrf=useRef('');const profileQueue=useRef<Promise<unknown>>(Promise.resolve());
 const request=useCallback(async(path:string,method='GET',body?:unknown,idempotencyKey?:string)=>{
  if(!base)throw new AccountError('unavailable');
  if(method!=='GET'&&!csrf.current)throw new AccountError('session_unavailable');
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
  try{const response=await fetch(`${base}${path}`,{method,credentials:'include',cache:'no-store',signal:controller.signal,headers:{Accept:'application/json',...(idempotencyKey?{'Idempotency-Key':idempotencyKey}:{}),...(method!=='GET'?{'Content-Type':'application/json'}:{}),...(method!=='GET'?{'X-CSRF-Token':csrf.current}:{})},...(method!=='GET'?{body:JSON.stringify(body??{})}:{})});
   const data=await response.json().catch(()=>({}));if(!response.ok)throw new AccountError(typeof data.error?.code==='string'?data.error.code:typeof data.code==='string'?data.code:typeof data.error==='string'?data.error:response.status===401?'session_expired':response.status===429?'rate_limited':'request_failed');
   if(typeof data.csrfToken==='string')csrf.current=data.csrfToken;
   return data;
  }catch(e){if(e instanceof AccountError)throw e;throw new AccountError('network_error')}finally{clearTimeout(timer)}
 },[]);
 const refresh=useCallback(async()=>{try{const data=await request('/api/account/me');const u=normalizeUser(data.account);commitUser(u);return u}catch(e){if(e instanceof AccountError&&['authentication_required','session_expired'].includes(e.code)){commitUser(null);return null}throw e}},[request,commitUser]);
 const reconnect=useCallback(async()=>{if(!base){setStatus('unavailable');return}setStatus('loading');try{const data=await request('/api/account/capabilities');setCapabilities({...disabled,...data});await refresh();setStatus('ready')}catch{setStatus('unavailable');commitUser(null)}},[request,refresh,commitUser]);
 useEffect(()=>{void reconnect()},[reconnect]);
 const callbackStarted=useRef(false);
 useEffect(()=>{if(status!=='ready'||callbackStarted.current)return;const url=new URL(window.location.href);if(url.searchParams.get('account')!=='google'&&!/^\/account\/callback\/?$/.test(url.pathname))return;callbackStarted.current=true;const code=url.searchParams.get('code'),state=url.searchParams.get('state');url.searchParams.delete('code');url.searchParams.delete('state');url.searchParams.delete('account');url.searchParams.delete('scope');window.history.replaceState(null,'',url);if(!code||!state){setError('oauth_failed');return}setBusy(true);void request('/api/account/oauth/google/callback','POST',{code,state}).then(()=>refresh()).then(()=>{window.location.hash='profile'}).catch(e=>setError(e instanceof AccountError?e.code:'oauth_failed')).finally(()=>setBusy(false))},[status,request,refresh]);
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
 return {capabilities,status,user,pending,rememberReward,screen,busy,error,notice,balance,reserved,history,cursor,walletStatus,open,setError,setNotice,request,refresh,reconnect,loadWallet,loadMore:()=>action(async()=>{if(!cursor)return;const data=await request(`/api/points/ledger?cursor=${encodeURIComponent(cursor)}`);setHistory(rows=>[...rows,...entries(data.items||[])]);setCursor(data.nextCursor||null)}),action,patchProfile,savePreferences,
  claimReward:()=>action(async()=>{if(!pending||!user?.emailVerified)throw new AccountError('email_not_verified');if(Date.parse(pending.expiresAt)<=Date.now()){forgetReward();throw new AccountError('reward_expired')}await request('/api/points/pending/claim','POST',{pendingToken:pending.pendingToken},pending.idempotencyKey);forgetReward();await loadWallet();setNotice('reward_claimed')}),
  login:(email:string,password:string)=>action(async()=>{await request('/api/account/login','POST',{email,password});const u=await refresh();open(u?.emailVerified?null:'verify')}),
  register:(data:Record<string,unknown>)=>action(async()=>{const {language,...fields}=data;await request('/api/account/register','POST',{...fields,lang:language==='en'?'en':'pt-BR'});await refresh();open('verify');setNotice('verification_sent')}),
  verify:(code:string,email:string)=>action(async()=>{await request('/api/account/verify','POST',{token:code});const u=await refresh();open(u?null:'login');setNotice('email_verified')}),
  resend:(email:string)=>action(async()=>{await request('/api/account/resend','POST',{});setNotice('verification_sent')}),
  logout:()=>action(async()=>{await profileQueue.current.catch(()=>{});await request('/api/account/logout','POST');commitUser(null);setBalance(null);setHistory([]);forgetReward();await refresh();setNotice('signed_out')}),
  remove:(password:string)=>action(async()=>{await profileQueue.current.catch(()=>{});await request('/api/account/delete','POST',{confirm:'DELETE',password});commitUser(null);setBalance(null);setHistory([]);forgetReward();await refresh();setNotice('account_deleted')}),
  resetRequest:(email:string)=>action(async()=>{await request('/api/account/password/reset','POST',{email});setNotice('reset_sent')}),
  resetConfirm:(email:string,code:string,password:string)=>action(async()=>{await request('/api/account/password/reset/confirm','POST',{email,code,password});open('login');setNotice('password_changed')}),
  exportData:()=>action(async()=>{const data=await request('/api/account/export');const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const anchor=document.createElement('a');anchor.href=url;anchor.download='anderzilla-account.json';anchor.click();URL.revokeObjectURL(url);setNotice('export_ready')}),
  social:(provider:'google'|'meta',consent:Record<string,unknown>)=>action(async()=>{const data=await request(`/api/account/oauth/${provider}/start`,'POST',consent);const url=new URL(data.url);if(url.protocol!=='https:'||!['accounts.google.com','www.facebook.com'].includes(url.hostname))throw new AccountError('invalid_response');window.location.assign(url.href)}),
 };
}
const Context=createContext<ReturnType<typeof useAccountState>|null>(null);
export function AccountProvider({children}:{children:ReactNode}){const value=useAccountState();return <Context.Provider value={value}>{children}</Context.Provider>}
export function useAccount(){const value=useContext(Context);if(!value)throw new Error('AccountProvider required');return value}
