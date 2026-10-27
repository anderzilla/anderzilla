import { BrandWordmark } from "@/components/BrandAssets";
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { discoveries, type Discovery, type Language } from '@/components/hub/model';
import published from '@/components/hub/cms-published.json';
import { DemoBadge, findMedia, mediaCaption, SafeMarkdown } from '@/components/hub/Editorial';
import '@/components/hub/hub.css';
import { MediaGallery } from '@/components/hub/MediaGallery';
import { ArticleShare } from '@/components/hub/ArticleShare';

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
    openGraph:{title,description,type:p.section==='radar'?'article':'website',url:path(item,p.lang,p.section),locale:p.lang==='pt'?'pt_BR':'en_US',...(p.section==='radar'?{publishedTime:item.published,modifiedTime:item.verifiedAt||item.published}:{}),images:media?[{url:media.previewUrl||media.url,width:media.width,height:media.height,alt:p.lang==='pt'?media.altPT:media.altEN}]:[]},
    twitter:{card:'summary_large_image',title,description,images:media?[media.previewUrl||media.url]:[]}};
}
export default async function Article({params}:{params:Promise<Params>}){
 const p=await params,item=get(p),pt=p.lang==='pt',media=findMedia(item.coverMediaId);
 const body=p.section==='radar'?(pt?item.fact:item.factEN):(pt?item.bodyPT:item.bodyEN)||'';
 const tags=(item.tags||'').split(',').filter(Boolean);
 const displayTags=tags.length?tags.map(tag=>(published.taxonomies as {id:string;slug:string}[]).find(x=>x.id===tag)?.slug||tag):(pt?item.hashtagsPT:item.hashtagsEN)?.split(/\s+/).filter(Boolean).map(tag=>tag.replace(/^#/,''))||[];
 const types:Record<string,[string,string]>={news:['Notícia','News'],analysis:['Análise documental','Documentary analysis'],comparison:['Comparação documental','Documentary comparison'],explainer:['Entenda','Explainer'],rumor:['Rumor em apuração','Unconfirmed report']};
 const type=types[item.editorialType||''];
 const categoryLabel=({games:['Games','Games'],consoles:['Consoles','Consoles'],celulares:['Celulares','Phones'],ia:['IA','AI'],gadgets:['Gadgets','Gadgets'],curiosidades:['Curiosidades','Curiosities']} as Record<string,[string,string]>)[item.category]?.[pt?0:1]||'AnderZilla';
 const related=discoveries.filter(x=>x.id!==item.id&&x.category===item.category&&!x.isDemo).slice(0,3);
 const schema={'@context':'https://schema.org','@type':item.editorialType==='news'?'NewsArticle':'Article',headline:local(item,'title',p.lang),description:local(item,'summary',p.lang),inLanguage:pt?'pt-BR':'en',datePublished:item.published,dateModified:item.updatedAt||item.verifiedAt||item.published,author:{'@type':'Organization',name:item.author||'AnderZilla',url:'https://anderzilla.com'},publisher:{'@type':'Organization',name:'AnderZilla',url:'https://anderzilla.com'},mainEntityOfPage:`https://anderzilla.com${path(item,p.lang,p.section)}`,...(media?{image:new URL(media.previewUrl||media.url,'https://anderzilla.com').href}:{}),citation:item.sources?.map(source=>source.url)||[item.url]};
 return <div className="hub" lang={pt?'pt-BR':'en'}><a className="skip" href="#article">{pt?'Pular para o conteúdo':'Skip to content'}</a>
   {!item.isDemo&&<script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(schema).replace(/</g,'\\u003c')}}/>}
   <header><a className="brand" href={`/${p.lang}/#home`}><BrandWordmark /></a><nav aria-label={pt?'Navegação do artigo':'Article navigation'}><a href={`/${p.lang}/radar/`}>← Radar</a><a href={path(item,pt?'en':'pt',p.section)} lang={pt?'en':'pt-BR'}>{pt?'Read in English':'Ler em português'}</a></nav></header>
   <main id="article" className="wrap article-page" tabIndex={-1}><article>
     <p className="eyebrow">{categoryLabel} / {type?type[pt?0:1]:(pt?'EXPLORAR':'EXPLORE')}</p>
     {item.isDemo&&<DemoBadge english={!pt}/>}
     <h1>{local(item,'title',p.lang)}</h1><p className="lede">{local(item,'summary',p.lang)}</p>
     <p className="source">{item.author||'AnderZilla'}{item.published&&<> · <time dateTime={item.published}>{item.published}</time></>}</p>
     {item.verifiedAt&&<p className="source">{pt?'Apuração':'Verified'}: <time dateTime={item.verifiedAt}>{item.verifiedAt}</time>{item.eventDate&&<> · {pt?'Data do anúncio ou evento':'Announcement or event date'}: <time dateTime={item.eventDate}>{item.eventDate}</time></>}</p>}
     {item.updatedAt&&<p className="source">{pt?'Atualizado em':'Updated'}: <time dateTime={item.updatedAt}>{item.updatedAt}</time></p>}
     {media&&<figure><a className="article-cover-link" href={media.url} target="_blank" rel="noopener noreferrer" aria-label={`${pt?'Abrir imagem ampliada':'Open full image'}: ${(pt?media.altPT:media.altEN)||''}`}><img className="article-cover" src={media.url} width={media.width} height={media.height} alt={(pt?media.altPT:media.altEN)||''}/></a><figcaption>{mediaCaption(media.credit, media.license)}{media.sourceUrl&&<> · <a href={media.sourceUrl} target="_blank" rel="noopener noreferrer">{pt?'Fonte da imagem':'Image source'} ↗</a></>}</figcaption></figure>}
     <SafeMarkdown body={body}/>
     <MediaGallery ids={item.mediaIds} english={!pt}/>
     {!!item.sources?.length&&<details className="article-sources"><summary>{pt?'Fontes e contexto da apuração':'Sources and reporting context'} ({item.sources.length})</summary><ul>{item.sources.map(source=><li key={source.url}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.name} ↗</a>{source.publishedAt&&<time dateTime={source.publishedAt}> · {source.publishedAt}</time>}{source.note&&pt&&<p>{source.note}</p>}</li>)}</ul></details>}
     {displayTags.length>0&&<ul className="editorial-tags" aria-label="Tags">{displayTags.map(tag=><li key={tag}>#{tag}</li>)}</ul>}
     {item.url&&!item.isDemo&&<p><a href={item.url} rel="noopener noreferrer">{pt?'Fonte original':'Original source'}: {item.sourceName} ↗</a></p>}
     {item.isDemo&&<p className="notice">{pt?'Material fictício para avaliar o layout e o CMS. Não é notícia, evento confirmado, oferta ou promessa de recompensa.':'Fictional material to evaluate the layout and CMS. Not news, a confirmed event, an offer or a reward promise.'}</p>}
     {!item.isDemo&&<ArticleShare title={local(item,'title',p.lang)} summary={local(item,'summary',p.lang)} path={path(item,p.lang,p.section)} english={!pt}/>}
     {related.length>0&&<section className="article-related"><h2>{pt?'Continua no radar':'More on your radar'}</h2><ul>{related.map(record=><li key={record.id}><a href={path(record,p.lang,'radar')}>{local(record,'title',p.lang)} →</a></li>)}</ul></section>}
     <a className="button" href={`/${p.lang}/radar/`}>{pt?'Voltar ao Radar':'Back to Radar'} →</a>
   </article></main></div>
}

