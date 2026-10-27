import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import published from './cms-published.json';

export type PublicMedia = {id:string;url:string;previewUrl?:string;sourceUrl?:string;mediaType?:string;altPT?:string;altEN?:string;credit?:string;license?:string;width?:number;height?:number};
export function findMedia(id?:string){return (published.media as PublicMedia[]).find(item=>item.id===id)}
const RIGHTS = 'Direitos reservados ao titular.';
export function mediaCaption(credit?:string, license?:string){
  const parts = [credit, license].map(value => (value || '').trim()).filter(Boolean);
  const shown: string[] = [];
  for (const part of parts) {
    if (shown.some(previous => previous.includes(part) || (part.includes(RIGHTS) && previous.includes(RIGHTS)))) continue;
    shown.push(part);
  }
  return shown.join(' · ');
}
export function SafeMarkdown({body}:{body:string}){
  return <div className="editorial-body"><Markdown remarkPlugins={[remarkGfm]} skipHtml
    urlTransform={url=>/^(https:\/\/|mailto:|\/(?!\/)|#)/i.test(url)?url:''}
    components={{a:({href,children})=><a href={href} rel="noopener noreferrer">{children}</a>,
      img:({src,alt})=>typeof src==='string'&&src?<img src={src} alt={alt||''} loading="lazy" decoding="async"/>:null}}>{body}</Markdown></div>
}
export function DemoBadge({english=false}:{english?:boolean}){return <span className="demo-badge">{english?'DEMO · FICTIONAL EXAMPLE':'DEMO · EXEMPLO FICTÍCIO'}</span>}
