"use client";
import { useEffect, useState } from 'react';
import published from './cms-published.json';
import { useHub } from './HubProvider';
import { External } from './Primitives';
import { DemoBadge, findMedia, SafeMarkdown } from './Editorial';

type TextRecord = {isDemo?:boolean;coverMediaId?:string;slugPT?:string;slugEN?:string;id:string;titlePT:string;titleEN?:string;bodyPT?:string;bodyEN?:string;summaryPT?:string;summaryEN?:string;url?:string;priceMinor?:number;currency?:string;disclosurePT?:string;disclosureEN?:string;startsAt?:string;endsAt?:string;slug?:string};
export function CMSSections(){
  const {lang,t}=useHub();
  const [now,setNow]=useState(0);
  useEffect(()=>{setNow(Date.now());const timer=setInterval(()=>setNow(Date.now()),30000);return()=>clearInterval(timer)},[]);
  const localized=(row:TextRecord,key:'title'|'body'|'summary'|'disclosure')=>row[`${key}${lang==='pt'?'PT':'EN'}`]||row[`${key}PT`]||'';
  const campaigns=(published.campaigns as TextRecord[]).filter(row=>Date.parse(row.startsAt||'')<=now&&Date.parse(row.endsAt||'')>now);
  const offers=published.offers as TextRecord[];
  const pages=published.pages as TextRecord[];
  const badge=(row:TextRecord)=>row.isDemo?<DemoBadge english={lang==='en'}/>:null;
  const cover=(row:TextRecord)=>{const media=findMedia(row.coverMediaId);return media?<img className="article-cover" src={media.url} alt={(lang==='pt'?media.altPT:media.altEN)||''} loading="lazy"/>:null};
  return <>
    {campaigns.map(row=><section className="ad-placement" key={row.id}><div><p className="eyebrow">{t('PUBLICIDADE','ADVERTISEMENT')}</p>{badge(row)}<h2>{localized(row,'title')}</h2><p>{localized(row,'disclosure')}</p></div><External href={row.isDemo?'https://anderzilla.com':row.url!} className="button secondary" affiliate>{t('Conhecer','Explore')} ↗</External></section>)}
    {offers.length>0&&<section className="affiliate-area"><h2>{t('Loja & ofertas','Store & offers')}</h2><div className="affiliate-grid">{offers.map(row=><article className="affiliate-card" key={row.id}><div>{badge(row)}{cover(row)}<h3>{localized(row,'title')}</h3><p>{localized(row,'summary')}</p><p>{localized(row,'disclosure')}</p>{typeof row.priceMinor==='number'&&/^[A-Z]{3}$/.test(row.currency||'')&&<p>{new Intl.NumberFormat(lang==='pt'?'pt-BR':'en-US',{style:'currency',currency:row.currency}).format(row.priceMinor/100)}</p>}{row.isDemo?<p className="notice">{t('Demonstração · compra indisponível','Demo · purchase unavailable')}</p>:<External href={row.url!} className="button secondary">{t('Ver condições e comprar','View terms and buy')} ↗</External>}</div></article>)}</div></section>}
    {pages.map(row=><section className="return-band" id={`page-${row.slug}`} key={row.id}><div><h2>{localized(row,'title')}</h2>{badge(row)}<a className="button secondary" href={`/${lang}/pages/${(lang==='pt'?row.slugPT:row.slugEN)||row.slug||row.id}/`}>{t('Abrir página','Open page')} →</a></div></section>)}
  </>;
}
