"use client";
import published from './cms-published.json';
import { useHub } from './HubProvider';
import { DemoBadge } from './Editorial';

type TextRecord = {isDemo?:boolean;coverMediaId?:string;slugPT?:string;slugEN?:string;id:string;titlePT:string;titleEN?:string;bodyPT?:string;bodyEN?:string;summaryPT?:string;summaryEN?:string;url?:string;priceMinor?:number;currency?:string;disclosurePT?:string;disclosureEN?:string;startsAt?:string;endsAt?:string;slug?:string};
export function CMSSections(){
  const {lang,t}=useHub();
  const localized=(row:TextRecord,key:'title'|'body'|'summary'|'disclosure')=>row[`${key}${lang==='pt'?'PT':'EN'}`]||row[`${key}PT`]||'';
  const pages=published.pages as TextRecord[];
  const badge=(row:TextRecord)=>row.isDemo?<DemoBadge english={lang==='en'}/>:null;
  return <>
    {pages.map(row=><section className="return-band" id={`page-${row.slug}`} key={row.id}><div><h2>{localized(row,'title')}</h2>{badge(row)}<a className="button secondary" href={`/${lang}/pages/${(lang==='pt'?row.slugPT:row.slugEN)||row.slug||row.id}/`}>{t('Abrir página','Open page')} →</a></div></section>)}
  </>;
}
