'use client';
import {useState} from 'react';

export function ArticleShare({title,summary,path,english=false}:{title:string;summary:string;path:string;english?:boolean}){
 const [message,setMessage]=useState('');
 const url=`https://anderzilla.com${path}`;
 const text=`${title}\n${summary}\n${url}`;
 async function copy(){try{await navigator.clipboard.writeText(text);setMessage(english?'Link and summary copied.':'Link e resumo copiados.')}catch{setMessage(english?'Copy the address from your browser.':'Copie o endereço na barra do navegador.')}}
 async function share(){if(navigator.share){try{await navigator.share({title,text:summary,url})}catch(error){if((error as Error).name!=='AbortError')await copy()}}else await copy()}
 return <aside className="article-share" aria-label={english?'Share this article':'Compartilhar matéria'}>
  <strong>{english?'Send this discovery to your squad':'Manda essa descoberta pro squad'}</strong>
  <div className="share-actions">
   <button className="button" onClick={share}>{english?'Share':'Compartilhar'} ↗</button>
   <a className="button secondary" href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noopener noreferrer">WhatsApp</a>
   <a className="button secondary" href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`} target="_blank" rel="noopener noreferrer">Facebook</a>
   <button className="button secondary" onClick={copy}>{english?'Copy link + summary':'Copiar link + resumo'}</button>
  </div><p role="status" className="source">{message}</p>
 </aside>
}
