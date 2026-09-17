import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {CommercePage} from '@/components/commerce/CommercePage';
import {commerceRoutes,titles,type Lang} from '@/components/commerce/data';
type Params={lang:string;section:string};
export const dynamicParams=false;
export function generateStaticParams(){return ['pt','en'].flatMap(lang=>commerceRoutes.filter(r=>!r.includes('/')).map(section=>({lang,section})))}
function validate(p:Params){if(!['pt','en'].includes(p.lang)||!titles[p.section]||p.section.includes('/'))notFound();return p.lang as Lang}
export async function generateMetadata({params}:{params:Promise<Params>}):Promise<Metadata>{const p=await params,lang=validate(p);return {title:titles[p.section][lang==='pt'?0:1],alternates:{canonical:`/${lang}/${p.section}/`,languages:{'pt-BR':`/pt/${p.section}/`,en:`/en/${p.section}/`}}}}
export default async function Page({params}:{params:Promise<Params>}){const p=await params;return <CommercePage lang={validate(p)} route={p.section}/>}
