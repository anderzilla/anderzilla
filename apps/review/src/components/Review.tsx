'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ApiError, api, collectionLabel, parseSources, previewUrl, safeHref, statusLabel } from '@/lib/api';
import type { Comment, Detail, Item, Media, PreviewState, Submission } from '@/lib/api';

const TOKEN_KEY = 'anderzilla-review-token';
const reviewable = (status: string) => status === 'pending' || status === 'changes_requested';

function fmt(value: string) {
  try {
    return new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
  } catch {
    return value;
  }
}

export function Review() {
  const [token, setToken] = useState('');
  const [route, setRoute] = useState('');
  const [needLogin, setNeedLogin] = useState(false);
  const [ready, setReady] = useState(false); // never call the API before the stored token has been read
  useEffect(() => {
    try { setToken(sessionStorage.getItem(TOKEN_KEY) || ''); } catch { /* storage can be blocked */ }
    const sync = () => setRoute(location.hash.replace(/^#\/?/, ''));
    sync();
    setReady(true);
    addEventListener('hashchange', sync);
    return () => removeEventListener('hashchange', sync);
  }, []);
  const saveToken = (value: string) => {
    setToken(value);
    try { sessionStorage.setItem(TOKEN_KEY, value); } catch { /* ignore */ }
    setNeedLogin(false);
  };
  const detailId = route.startsWith('s/') ? route.slice(2) : '';
  return (
    <div className="shell">
      <a className="skip-link" href="#main">Pular para o conteúdo</a>
      <header className="top">
        <a href="#/" aria-label="AnderZilla — Revisão"><img src="/brand/lettering.webp" alt="AnderZilla" width={200} height={56} /></a>
        <span className="tag">Revisão de conteúdo</span>
      </header>
      <main id="main">
        {!ready ? <p className="loading">Carregando…</p> : needLogin ? <Login onToken={saveToken} /> : detailId ? <DetailView id={detailId} token={token} onAuth={() => setNeedLogin(true)} /> : <ListView token={token} onAuth={() => setNeedLogin(true)} />}
      </main>
    </div>
  );
}

function Login({ onToken }: { onToken: (value: string) => void }) {
  const [value, setValue] = useState('');
  return (
    <section className="panel login">
      <h1>Entrar na revisão</h1>
      <p>Em produção o acesso é pelo login Microsoft da sua conta. Neste servidor local, informe o token gerado fora do código-fonte.</p>
      <form onSubmit={(event) => { event.preventDefault(); onToken(value.trim()); }}>
        <label>Token local<input type="password" autoComplete="off" value={value} onChange={(event) => setValue(event.target.value)} /></label>
        <button className="primary" type="submit" disabled={value.trim().length < 32}>Entrar</button>
      </form>
    </section>
  );
}

function useCall(token: string, onAuth: () => void) {
  return useCallback(async <T,>(path: string, init?: RequestInit) => {
    try {
      return await api<T>(path, token, init);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) onAuth();
      throw error;
    }
  }, [token, onAuth]);
}

function ListView({ token, onAuth }: { token: string; onAuth: () => void }) {
  const call = useCall(token, onAuth);
  const [items, setItems] = useState<Submission[] | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    call<{ items: Submission[] }>('/v1/submissions').then((result) => setItems(result.items)).catch((e) => setError(e.message));
  }, [call]);
  return (
    <>
      <h1>Pacotes para revisão</h1>
      <p className="lead">O que as IAs prepararam. Nada vai ao ar sem a sua aprovação aqui.</p>
      {error && <div className="error" role="alert">{error}</div>}
      {items === null && !error && <p className="loading">Carregando…</p>}
      {items?.length === 0 && <section className="panel empty"><h2>Nada aguardando</h2><p>Quando uma IA enviar um pacote, ele aparece aqui.</p></section>}
      <ul className="cards">
        {items?.map((item) => (
          <li key={item.id}>
            <a className="card pack" href={`#/s/${item.id}`}>
              <span className={`badge ${item.status}`}>{statusLabel[item.status] || item.status}</span>
              <strong>{item.records.length} {item.records.length === 1 ? 'registro' : 'registros'} · rodada {item.round}</strong>
              <small>{item.note || 'Sem observação do agente.'}</small>
              <small>Atualizado em {fmt(item.updatedAt)}</small>
            </a>
          </li>
        ))}
      </ul>
    </>
  );
}

function DetailView({ id, token, onAuth }: { id: string; token: string; onAuth: () => void }) {
  const call = useCall(token, onAuth);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => call<Detail>(`/v1/submissions/${id}/items`).then(setDetail).catch((e) => setError(e.message)), [call, id]);
  useEffect(() => { load(); }, [load]);

  if (error && !detail) return <><a href="#/">← Pacotes</a><div className="error" role="alert">{error}</div></>;
  if (!detail) return <p className="loading">Carregando…</p>;
  const { submission, items, comments, referencedMedia } = detail;
  const open = comments.filter((comment) => !comment.resolved && comment.round === submission.round);
  const canReview = reviewable(submission.status);

  async function act(path: string, success: string, confirmText?: string) {
    if (confirmText && !confirm(confirmText)) return;
    setBusy(true); setError(''); setNotice('');
    try {
      await call(path, { method: 'POST', body: '{}' });
      setNotice(success);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <a href="#/">← Pacotes</a>
      <div className="head">
        <div>
          <h1>Pacote de {submission.agentName || submission.agentId}</h1>
          <p className="lead">{submission.note || 'Sem observação do agente.'}</p>
        </div>
        <div className="meta">
          <span className={`badge ${submission.status}`}>{statusLabel[submission.status] || submission.status}</span>
          <small>Rodada {submission.round} · enviado em {fmt(submission.createdAt)}</small>
        </div>
      </div>
      {error && <div className="error" role="alert">{error}</div>}
      {notice && <div className="notice" role="status">{notice}</div>}

      <PreviewPanel id={id} token={token} onAuth={onAuth} enabled={canReview} />

      {items.map((item) => (
        <ItemCard key={item.id} item={item} media={referencedMedia} comments={comments.filter((comment) => comment.recordId === item.id)} submissionId={id} canComment={canReview} call={call} onChange={load} setError={setError} />
      ))}

      <section className="panel decision" aria-labelledby="decision">
        <h2 id="decision">Decisão</h2>
        {canReview ? (
          <>
            <p>
              {open.length > 0 ? `${open.length} comentário(s) aberto(s) nesta rodada.` : 'Sem comentários nesta rodada.'} Aprovar publica apenas em homologação; produção exige outra confirmação sua.
            </p>
            <div className="actions">
              <button className="primary" disabled={busy || submission.status !== 'pending'} onClick={() => act(`/v1/submissions/${id}/approve`, 'Aprovado. Release enfileirado para homologação.', `Aprovar ${items.length} registro(s) e enfileirar o release em homolog?\n\nProdução continua exigindo uma segunda confirmação.`)}>Aprovar e enviar a homolog</button>
              <button className="warn" disabled={busy || submission.status !== 'pending' || open.length === 0} onClick={() => act(`/v1/submissions/${id}/request-changes`, 'Correções enviadas. A IA vai ler os comentários e reenviar.')}>Pedir correções à IA</button>
            </div>
            {submission.status === 'changes_requested' && <small>Aguardando a IA reenviar o pacote corrigido.</small>}
          </>
        ) : submission.releaseId ? <p>Release <code>{submission.releaseId}</code> criado. Promoção para produção é um passo separado.</p> : <p>Este pacote não está mais em revisão.</p>}
      </section>
    </>
  );
}

function ItemCard({ item, media, comments, submissionId, canComment, call, onChange, setError }: {
  item: Item; media: Media[]; comments: Comment[]; submissionId: string; canComment: boolean;
  call: <T>(path: string, init?: RequestInit) => Promise<T>; onChange: () => void; setError: (value: string) => void;
}) {
  const d = item.data;
  const [lang, setLang] = useState<'PT' | 'EN'>('PT');
  const [field, setField] = useState('');
  const [text, setText] = useState('');
  const image = (id?: string) => media.find((row) => row.id === id);
  const cover = d.coverMediaId ? image(d.coverMediaId) : undefined;
  const banner = d.imageMediaId ? image(d.imageMediaId) : undefined;
  const fields = Object.keys(d).filter((key) => key !== 'imageDataUrl');

  async function send() {
    setError('');
    try {
      await call(`/v1/submissions/${submissionId}/comments`, { method: 'POST', body: JSON.stringify({ collection: item.collection, recordId: item.id, ...(field ? { field } : {}), text }) });
      setText(''); setField('');
      onChange();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <article className="panel item" aria-label={`${collectionLabel[item.collection] || item.collection}`}>
      <div className="item-top">
        <span className="badge">{collectionLabel[item.collection] || item.collection}</span>
        <small>versão {item.version}</small>
        {item.collection === 'content' && (
          <div className="seg" role="group" aria-label="Idioma">
            {(['PT', 'EN'] as const).map((l) => <button key={l} aria-pressed={lang === l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)}>{l}</button>)}
          </div>
        )}
      </div>

      {item.collection === 'content' && (
        <div className="news">
          {cover?.imageDataUrl && <figure><img src={cover.imageDataUrl} alt={cover.altPT || ''} /><figcaption>Crédito: {cover.credit || '—'}</figcaption></figure>}
          <div>
            <p className="eyebrow">{String(d.category || '').toUpperCase()} · {d.editorialType || 'news'} · {d.publishedAt}</p>
            <h2>{d['title' + lang]}</h2>
            <p className="summary">{d['summary' + lang]}</p>
            <div className="markdown"><ReactMarkdown>{String(d['body' + lang] || '')}</ReactMarkdown></div>
            <h3>Fontes</h3>
            <ul className="sources">
              <li>{safeHref(d.sourceUrl) ? <a href={safeHref(d.sourceUrl)!} target="_blank" rel="noopener noreferrer nofollow">{d.sourceName}</a> : d.sourceName} <small>(fonte principal)</small></li>
              {parseSources(d.sources).map((s) => <li key={s.url}>{safeHref(s.url) ? <a href={s.url} target="_blank" rel="noopener noreferrer nofollow">{s.name}</a> : s.name}{s.note && <small> — {s.note}</small>}</li>)}
            </ul>
            <details><summary>SEO e redes</summary>
              <dl><dt>Slug</dt><dd>{d['slug' + lang] || '—'}</dd><dt>Título SEO</dt><dd>{d['seoTitle' + lang] || '—'}</dd><dt>Descrição SEO</dt><dd>{d['seoDescription' + lang] || '—'}</dd><dt>Hashtags</dt><dd>{d['hashtags' + lang] || '—'}</dd></dl>
            </details>
          </div>
        </div>
      )}

      {item.collection === 'banners' && (
        <div className="banner-mock">
          {banner?.imageDataUrl && <img src={banner.imageDataUrl} alt={banner.altPT || ''} />}
          <div>
            <p className="eyebrow">ANDERZILLA{d.disclosure ? ` · ${d.disclosure}` : ''}</p>
            <h2>{d['title' + lang]}</h2>
            <p>{d['text' + lang]}</p>
            {(d['cta' + lang]) && <span className="cta">{d['cta' + lang]}</span>}
            <dl><dt>Link</dt><dd>{safeHref(d['link' + lang]) ? <a href={d['link' + lang]} target="_blank" rel="noopener noreferrer nofollow">{d['link' + lang]}</a> : String(d['link' + lang] || '—')}</dd><dt>Período</dt><dd>{String(d.startsAt || '').slice(0, 10)} → {String(d.endsAt || '').slice(0, 10) || 'sem fim'}</dd><dt>Ordem</dt><dd>{d.order ?? 0}</dd></dl>
            <div className="seg" role="group" aria-label="Idioma do banner">
              {(['PT', 'EN'] as const).map((l) => <button key={l} aria-pressed={lang === l} className={lang === l ? 'on' : ''} onClick={() => setLang(l)}>{l}</button>)}
            </div>
          </div>
        </div>
      )}

      {item.collection === 'media' && (
        <div className="news">
          {d.imageDataUrl && <figure><img src={d.imageDataUrl} alt={d.altPT || ''} /></figure>}
          <dl><dt>Alt PT</dt><dd>{d.altPT}</dd><dt>Alt EN</dt><dd>{d.altEN}</dd><dt>Crédito</dt><dd>{d.credit}</dd><dt>Licença</dt><dd>{d.license}</dd><dt>Fonte</dt><dd>{safeHref(d.sourceUrl) ? <a href={d.sourceUrl} target="_blank" rel="noopener noreferrer nofollow">{d.sourceUrl}</a> : d.sourceUrl}</dd><dt>Tamanho</dt><dd>{d.width}×{d.height}px</dd></dl>
          <p className="fine">A licença é declarada pela IA. Confira a fonte antes de aprovar.</p>
        </div>
      )}

      <div className="comments">
        <h3>Comentários para a IA</h3>
        {comments.length === 0 && <small>Nenhum comentário neste registro.</small>}
        {comments.map((comment) => (
          <p key={comment.id} className={comment.resolved ? 'comment done' : 'comment'}>
            <small>Rodada {comment.round}{comment.field ? ` · ${comment.field}` : ''}{comment.resolved ? ' · resolvido' : ''}</small>
            {comment.text}
          </p>
        ))}
        {canComment && (
          <form onSubmit={(event) => { event.preventDefault(); send(); }}>
            <label>Campo (opcional)<select value={field} onChange={(event) => setField(event.target.value)}><option value="">Registro inteiro</option>{fields.map((key) => <option key={key} value={key}>{key}</option>)}</select></label>
            <label>O que corrigir<textarea value={text} maxLength={2000} rows={3} onChange={(event) => setText(event.target.value)} placeholder="Ex.: título muito longo; use a fonte oficial." /></label>
            <button type="submit" disabled={!text.trim()}>Adicionar comentário</button>
          </form>
        )}
      </div>
    </article>
  );
}

function PreviewPanel({ id, token, onAuth, enabled }: { id: string; token: string; onAuth: () => void; enabled: boolean }) {
  const call = useCall(token, onAuth);
  const [state, setState] = useState<PreviewState>({ state: 'none' });
  const [device, setDevice] = useState<'desktop' | 'mobile'>('desktop');
  const [scale, setScale] = useState(1);
  const [error, setError] = useState('');
  const box = useRef<HTMLDivElement>(null);
  const width = device === 'desktop' ? 1440 : 390;
  const height = device === 'desktop' ? 900 : 780;

  const refresh = useCallback(() => call<PreviewState>(`/v1/submissions/${id}/preview`).then(setState).catch((e) => setError(e.message)), [call, id]);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (state.state !== 'building') return;
    const timer = setInterval(refresh, 2500);
    return () => clearInterval(timer);
  }, [state.state, refresh]);
  useEffect(() => {
    const element = box.current;
    if (!element) return;
    const fit = () => setScale(Math.min(1, element.clientWidth / width));
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(element);
    return () => observer.disconnect();
  }, [width, state.state]);

  async function start() {
    setError('');
    try { setState(await call<PreviewState>(`/v1/submissions/${id}/preview`, { method: 'POST', body: '{}' })); } catch (e) { setError((e as Error).message); }
  }
  async function open() {
    setError('');
    try { setState(await call<PreviewState>(`/v1/submissions/${id}/open-preview`, { method: 'POST', body: '{}' })); } catch (e) { setError((e as Error).message); }
  }

  return (
    <section className="panel preview" aria-labelledby="prev">
      <div className="item-top">
        <h2 id="prev">Prévia fiel do site</h2>
        <div className="seg" role="group" aria-label="Tamanho da tela">
          <button className={device === 'desktop' ? 'on' : ''} aria-pressed={device === 'desktop'} onClick={() => setDevice('desktop')}>Desktop 1440</button>
          <button className={device === 'mobile' ? 'on' : ''} aria-pressed={device === 'mobile'} onClick={() => setDevice('mobile')}>Mobile 390</button>
        </div>
      </div>
      <p>O site real é construído com este pacote como se já estivesse aprovado. Nada é publicado.</p>
      {error && <div className="error" role="alert">{error}</div>}
      {state.state === 'failed' && <div className="error" role="alert">{state.error || 'A prévia falhou.'}</div>}
      <div className="actions">
        <button className="primary" onClick={start} disabled={!enabled || state.state === 'building'}>{state.state === 'building' ? 'Construindo…' : state.state === 'ready' ? 'Gerar de novo' : 'Gerar prévia'}</button>
        {state.state === 'ready' && !state.active && <button onClick={open}>Abrir esta prévia</button>}
        {state.state === 'ready' && state.active && <a className="link" href={previewUrl + '/'} target="_blank" rel="noopener noreferrer">Abrir em outra aba</a>}
      </div>
      {state.state === 'ready' && state.active && (
        <div ref={box} className="frame-box" style={{ height: height * scale }}>
          <iframe title="Prévia do site" src={previewUrl + '/'} width={width} height={height} sandbox="allow-scripts allow-same-origin" style={{ transform: `scale(${scale})`, transformOrigin: 'top left', width, height }} />
        </div>
      )}
    </section>
  );
}
