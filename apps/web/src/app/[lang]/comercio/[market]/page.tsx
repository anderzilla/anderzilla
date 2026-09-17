import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {CommercePage} from '@/components/commerce/CommercePage';
import {titles,type Lang} from '@/components/commerce/data';
type Params={lang:string;market:string};
export const dynamicParams=false;
export function generateStaticParams(){return ['pt','en'].flatMap(lang=>['brasil','internacional'].map(market=>({lang,market})))}
function validate(p:Params){if(!['pt','en'].includes(p.lang)||!['brasil','internacional'].includes(p.market))notFound();return p.lang as Lang}
export async function generateMetadata({params}:{params:Promise<Params>}):Promise<Metadata>{const p=await params,lang=validate(p),r=`comercio/${p.market}`;return {title:titles[r][lang==='pt'?0:1],alternates:{canonical:`/${lang}/${r}/`,languages:{'pt-BR':`/pt/${r}/`,en:`/en/${r}/`}}}}
export default async function Page({params}:{params:Promise<Params>}){const p=await params;return <CommercePage lang={validate(p)} route={`comercio/${p.market}`}/>}
