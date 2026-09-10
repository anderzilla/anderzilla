'use client';
import {useRef,useState} from 'react';
import {Entry,request} from '@/lib/cms';
import {socialCaption} from '@/lib/social';

export function SocialKit({data,media}:{data:Entry['data'];media:Entry[]}){
 const[notice,setNotice]=useState('');
 const socialImage=media.find(row=>row.id===data.socialMediaId&&row.status==='approved');
 const imageData=socialImage?.data.assetBase64?'data:image/webp;base64,'+socialImage.data.assetBase64:'';
 async function downloadPng(){try{const picture=new Image();picture.src=imageData;await picture.decode();const canvas=document.createElement('canvas');canvas.width=picture.naturalWidth;canvas.height=picture.naturalHeight;const context=canvas.getContext('2d');if(!context)throw new Error();context.drawImage(picture,0,0);const blob=await new Promise<Blob>((resolve,reject)=>canvas.toBlob(value=>value?resolve(value):reject(new Error()),'image/png'));const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download=String(data.slugPT||'anderzilla')+'-social.png';document.body.appendChild(anchor);anchor.click();anchor.remove();window.setTimeout(()=>URL.revokeObjectURL(url),1000);setNotice('Imagem PNG preparada para download.')}catch{setNotice('Não foi possível converter a imagem. Use o download WebP.')}}
 return <section className="quality"><h2>Kit social PT / EN</h2><p>Copie o texto revisado. As ações não publicam nas redes.</p><div className="actions">{(['PT','EN'] as const).flatMap(lang=>['Instagram','Facebook','Whatsapp'].map(channel=>{const caption=String(data['social'+channel+lang]||'');const hashtags=String(data['hashtags'+lang]||'');const slug=String(data['slug'+lang]||data.slug||'');const link=slug?`https://anderzilla.com/${lang.toLowerCase()}/radar/${slug}/`:'';const text=socialCaption(caption,link,hashtags);return <button key={channel+lang} type="button" disabled={!caption} onClick={async()=>{try{await navigator.clipboard.writeText(text);setNotice(`${channel} ${lang} copiado.`)}catch{setNotice('Não foi possível copiar. Selecione o texto nos campos abaixo.')}}}>Copiar {channel} {lang}</button>}))}</div>{imageData&&<div><img src={imageData} alt={String(socialImage?.data.altPT||'Card para redes')} style={{maxWidth:216,height:'auto'}}/><p><a href={imageData} download={String(data.slugPT||'anderzilla')+'-social.webp'}>Baixar WebP</a></p><button type="button" onClick={downloadPng}>Baixar PNG para redes</button></div>}<p role="status">{notice}</p></section>
}

type ImportImage={filename:string;contentBase64:string;altPT:string;altEN:string;credit:string;license:string};type ImportItem={key:string;data:Entry['data'];cover?:ImportImage;socialImage?:ImportImage};
export function NewsroomImport({token,onDone}:{token:string;onDone:()=>void}){
 const[approve,setApprove]=useState(false);const[input,setInput]=useState('');const[busy,setBusy]=useState(false);const[log,setLog]=useState<string[]>([]);const cancel=useRef(false);
 async function run(){setBusy(true);setLog([]);cancel.current=false;try{
  const manifest=JSON.parse(input);if(!Array.isArray(manifest.items)||!manifest.items.length||manifest.items.length>100)throw new Error('Use {"items":[...]} com 1–100 matérias.');
  const items=manifest.items as ImportItem[];const keys=new Set<string>();
  for(const item of items){if(!item.key||keys.has(item.key)||!item.data?.slugPT||!item.data?.slugEN||!item.data?.sourceUrl)throw new Error('Cada item precisa key única, slugPT, slugEN e sourceUrl.');keys.add(item.key)}
  const existing=(await request<{items:Entry[]}>('/admin/records/content',token)).items;
  const media=(await request<{items:Entry[]}>('/admin/records/media',token)).items;
  for(const [index,item] of items.entries()){
   if(cancel.current)break;
   const found=existing.find(row=>row.data.slugPT===item.data.slugPT||row.data.slugEN===item.data.slugEN);
   if(found){if(found.data.sourceUrl!==item.data.sourceUrl)throw new Error(`Slug existente com outra fonte: ${item.key}`);setLog(current=>[...current,`${index+1}/${items.length} ${item.key}: já cadastrado (${found.status}), preservado.`]);continue}
   const data={...item.data};
   for(const [field,reference] of [['cover','coverMediaId'],['socialImage','socialMediaId']] as const){const upload=item[field];if(!upload)continue;let image=media.find(row=>row.data.titlePT===upload.filename);if(!image){image=await request<Entry>('/admin/media-upload',token,{method:'POST',body:JSON.stringify(upload)});media.push(image)}if(image.status!=='approved'){image=await request<Entry>(`/admin/records/media/${image.id}/transition`,token,{method:'POST',body:JSON.stringify({version:image.version,action:'approve'})})}data[reference]=image.id}
   let row=await request<Entry>('/admin/records/content',token,{method:'POST',body:JSON.stringify({data})});existing.push(row);if(approve){row=await request<Entry>(`/admin/records/content/${row.id}/transition`,token,{method:'POST',body:JSON.stringify({version:row.version,action:'approve'})})}
   setLog(current=>[...current,`${index+1}/${items.length} ${item.key}: ${row.status==='approved'?'aprovado':'rascunho'} v${row.version} salvo com histórico.`]);
  }
  setLog(current=>[...current,cancel.current?'Interrompido. Cadastros concluídos foram preservados.':'Lote concluído. Revise e aprove as matérias no CMS.']);
 }catch(error){setLog(current=>[...current,error instanceof Error?error.message:'Falha na importação.'])}finally{setBusy(false);onDone()}}
 return <details className="quality"><summary>Importar lote editorial com histórico</summary><p>Cria rascunhos usando a API da sua sessão. Registros existentes são preservados por slug e fonte. Capas passam pela biblioteca validada. Cada etapa fica no histórico.</p><label>Manifesto JSON<input type="file" accept=".json,application/json" disabled={busy} onChange={async e=>{const file=e.target.files?.[0];if(file){if(file.size>15*1024*1024){setLog(['Arquivo excede 15 MB.']);return}setInput(await file.text())}}}/><textarea value={input} disabled={busy} onChange={e=>setInput(e.target.value)} rows={6} placeholder={'{"items":[{"key":"noticia","data":{...},"cover":{...}}]}'}/></label><label><input type="checkbox" checked={approve} disabled={busy} onChange={e=>setApprove(e.target.checked)}/>Aprovar matérias após importar (somente novos registros revisados)</label><div className="actions"><button type="button" disabled={busy||!input} onClick={run}>{busy?'Importando…':approve?'Importar e aprovar novos registros':'Importar como rascunhos'}</button>{busy&&<button type="button" onClick={()=>{cancel.current=true}}>Parar após este item</button>}</div><div role="status" aria-live="polite"><p>{log[log.length-1]}</p></div>{log.length>0&&<details><summary>Registro desta importação ({log.length})</summary><ol>{log.map((line,index)=><li key={index}>{line}</li>)}</ol></details>}</details>
}
