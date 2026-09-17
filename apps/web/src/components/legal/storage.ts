export const STORAGE_CHOICE_KEY='anderzilla-storage-choice-v1';
export const GUEST_STORAGE_KEY='anderzilla-hub-demo-v1';
export const STORAGE_EVENT='anderzilla-storage-preference';
export type StorageChoice={version:1;personalization:boolean;updatedAt:string};
export function storageChoice():StorageChoice|null {try{const value=JSON.parse(localStorage.getItem(STORAGE_CHOICE_KEY)||'null');return value?.version===1&&typeof value.personalization==='boolean'?value:null}catch{return null}}
export function rememberStorage(personalization:boolean){const value:StorageChoice={version:1,personalization,updatedAt:new Date().toISOString()};try{localStorage.setItem(STORAGE_CHOICE_KEY,JSON.stringify(value));if(!personalization)localStorage.removeItem(GUEST_STORAGE_KEY)}catch{}window.dispatchEvent(new CustomEvent(STORAGE_EVENT,{detail:value}));return value}
