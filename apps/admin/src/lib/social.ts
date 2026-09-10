/** Preserve the reviewed caption and append only missing distribution metadata. */
export function socialCaption(caption:string,link:string,hashtags:string){
 const canonical=(value:string)=>value.replace(/[.,!?;:)]+$/,'').replace(/\/$/,'');
 const links=(caption.match(/https:\/\/[^\s]+/g)||[]).map(canonical);
 const present=new Set((caption.match(/#[\p{L}\p{N}_]+/gu)||[]).map(tag=>tag.toLocaleLowerCase()));
 const missing=hashtags.split(/\s+/).filter(tag=>{const key=tag.toLocaleLowerCase();if(!tag||present.has(key))return false;present.add(key);return true}).join(' ');
 return [caption,link&&!links.includes(canonical(link))?link:'',missing].filter(Boolean).join('\n\n');
}
