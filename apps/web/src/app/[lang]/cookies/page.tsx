import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {LegalPage,legalTitles} from '@/components/legal/LegalPage';
export const dynamicParams=false;
export function generateStaticParams(){return [{lang:'pt'},{lang:'en'}]}
function language(lang:string){if(lang!=='pt'&&lang!=='en')notFound();return lang}
export async function generateMetadata({params}:{params:Promise<{lang:string}>}):Promise<Metadata>{const {lang}=await params;language(lang);return {title:legalTitles.cookies[lang==='en'?1:0],alternates:{canonical:`/${lang}/cookies/`,languages:{'pt-BR':'/pt/cookies/',en:'/en/cookies/'}}}}
export default async function Page({params}:{params:Promise<{lang:string}>}){const {lang}=await params;return <LegalPage lang={language(lang)} route="cookies"/>}
