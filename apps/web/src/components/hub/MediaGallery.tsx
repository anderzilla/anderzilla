'use client';
import { useState } from 'react';
import { findMedia, mediaCaption } from './Editorial';
export function MediaGallery({ids,english=false}:{ids?:string;english?:boolean}){
 const [playing,setPlaying]=useState<string|null>(null);
 return <div className="media-gallery">{(ids||'').split(',').filter(Boolean).map(id=>{
  const media=findMedia(id.trim());if(!media)return null;
  const title=(english?media.altEN:media.altPT)||'AnderZilla';
  let embed='';try{const u=new URL(media.url);if(['youtube.com','www.youtube.com','youtu.be'].includes(u.hostname)){const video=u.hostname==='youtu.be'?u.pathname.slice(1):u.searchParams.get('v');if(video&&/^[\w-]{11}$/.test(video))embed=`https://www.youtube-nocookie.com/embed/${video}`}}catch{}
  return <figure key={id}>
   {media.mediaType==='image'?<a className="gallery-image" href={media.url} target="_blank" rel="noopener noreferrer" aria-label={`${english?'Open full image':'Abrir imagem ampliada'}: ${title}`}><img src={media.url} alt={title} loading="lazy" width={media.width} height={media.height}/></a>:
    embed?(playing===id?<iframe src={embed} title={title} allowFullScreen referrerPolicy="strict-origin-when-cross-origin"/>:<button className="button secondary" onClick={()=>setPlaying(id)}>{english?'Load YouTube video':'Carregar vídeo do YouTube'} ▷</button>):
    media.mediaType==='video'&&/\.mp4(?:\?|$)/i.test(media.url)?<video src={media.url} controls preload="none" aria-label={title}/>:
    media.mediaType==='audio'?<audio src={media.url} controls preload="none" aria-label={title}/>:
    <a href={media.url} target="_blank" rel="noopener noreferrer">{title} ↗</a>}
    <figcaption>{[title, mediaCaption(media.credit, media.license)].filter(Boolean).join(' · ')}{media.sourceUrl&&<> · <a href={media.sourceUrl} target="_blank" rel="noopener noreferrer">{english?'Image source':'Fonte da imagem'} ↗</a></>}</figcaption>
  </figure>
 })}</div>
}
