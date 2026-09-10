import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { discoveries, type Discovery, type Language } from '@/components/hub/model';
import published from '@/components/hub/cms-published.json';
import { DemoBadge, findMedia, SafeMarkdown } from '@/components/hub/Editorial';
import '@/components/hub/hub.css';
import { MediaGallery } from '@/components/hub/MediaGallery';

type PageRecord=Discovery & {slug?:string;bodyPT?:string;bodyEN?:string};
type Params={lang:string;section:string;slug:string};
const pages=published.pages as PageRecord[];
const records=(section:string)=>section==='radar'?discoveries:section==='pages'?pages:[];
const slugOf=(item:PageRecord,lang:string)=>(lang==='pt'?item.slugPT:item.slugEN)||item.slug||item.id;
function get(p:Params){if(!['pt','en'].includes(p.lang))notFound();const item=records(p.section).find(x=>slugOf(x,p.lang)===p.slug);if(!item)notFound();return item as PageRecord}
const local=(r:PageRecord,key:'title'|'summary'|'seoTitle'|'seoDescription',lang:string)=>r[`${key}${lang==='pt'?'PT':'EN'}`]||'';
const path=(r:PageRecord,lang:string,section:string)=>`/${lang}/${section}/${slugOf(r,lang)}/`;
export const dynamicParams=false;
export function generateStaticParams(){return ['pt','en'].flatMap(lang=>['radar','pages'].flatMap(section=>records(section).map(item=>({lang,section,slug:slugOf(item,lang)}))))}
export async function generateMetadata({params}:{params:Promise<Params>}):Promise<Metadata>{
  const p=await params,item=get(p),media=findMedia(item.coverMediaId);
  const title=local(item,'seoTitle',p.lang)||local(item,'title',p.lang);
  const description=local(item,'seoDescription',p.lang)||local(item,'summary',p.lang);
  return {title,description,authors:item.author?[{name:item.author}]:[{name:'AnderZilla'}],
    alternates:{canonical:path(item,p.lang,p.section),languages:{'pt-BR':path(item,'pt',p.section),en:path(item,'en',p.section)}},
    robots:{index:!item.isDemo&&process.env.CMS_PREVIEW!=='1',follow:!item.isDemo},
    openGraph:{title,description,type:p.section==='radar'?'article':'website',url:path(item,p.lang,p.section),locale:p.lang==='pt'?'pt_BR':'en_US',images:media?[{url:media.url,alt:p.lang==='pt'?media.altPT:media.altEN}]:[]},
    twitter:{card:'summary_large_image',title,description,images:media?[media.url]:[]}};
}
export default async function Article({params}:{params:Promise<Params>}){
 const p=await params,item=get(p),pt=p.lang==='pt',media=findMedia(item.coverMediaId);
 const body=p.section==='radar'?(pt?item.fact:item.factEN):(pt?item.bodyPT:item.bodyEN)||'';
 const tags=(item.tags||'').split(',').filter(Boolean);
 return <div className="hub" lang={pt?'pt-BR':'en'}><a className="skip" href="#article">{pt?'Pular para o conteúdo':'Skip to content'}</a>
   <header><a className="brand" href={`/?lang=${p.lang}#home`}><img src="/hub/anderzilla-ghost.png" alt="AnderZilla Ghost" width="45" height="45"/><span className="wordmark">ANDER<span>ZILLA</span></span></a><nav aria-label={pt?'Navegação do artigo':'Article navigation'}><a href={`/?lang=${p.lang}#home`}>← Radar</a><a href={path(item,pt?'en':'pt',p.section)} lang={pt?'en':'pt-BR'}>{pt?'Read in English':'Ler em português'}</a></nav></header>
   <main id="article" className="wrap article-page" tabIndex={-1}><article>
     <p className="eyebrow">{item.category||'ANDERZILLA'} / {pt?'EXPLORAR':'EXPLORE'}</p>
     {item.isDemo&&<DemoBadge english={!pt}/>}
     <h1>{local(item,'title',p.lang)}</h1><p className="lede">{local(item,'summary',p.lang)}</p>
     <p className="source">{item.author||'AnderZilla'}{item.published&&<> · <time dateTime={item.published}>{item.published}</time></>}</p>
     {media&&<figure><img className="article-cover" src={media.url} width={media.width} height={media.height} alt={(pt?media.altPT:media.altEN)||''}/><figcaption>{media.credit} · {media.license}</figcaption></figure>}
     <SafeMarkdown body={body}/>
     <MediaGallery ids={item.mediaIds} english={!pt}/>
     {tags.length>0&&<ul className="editorial-tags" aria-label="Tags">{tags.map(tag=><li key={tag}>#{(published.taxonomies as {id:string;slug:string}[]).find(x=>x.id===tag)?.slug||tag}</li>)}</ul>}
     {item.url&&!item.isDemo&&<p><a href={item.url} rel="noopener noreferrer">{pt?'Fonte original':'Original source'}: {item.sourceName} ↗</a></p>}
     {item.isDemo&&<p className="notice">{pt?'Material fictício para avaliar o layout e o CMS. Não é notícia, evento confirmado, oferta ou promessa de recompensa.':'Fictional material to evaluate the layout and CMS. Not news, a confirmed event, an offer or a reward promise.'}</p>}
     <a className="button" href={`/?lang=${p.lang}#home`}>{pt?'Voltar às descobertas':'Back to discoveries'} →</a>
   </article></main></div>
}
