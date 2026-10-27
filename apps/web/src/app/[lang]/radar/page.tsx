import {BrandWordmark} from '@/components/BrandAssets';
import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import type {CSSProperties} from 'react';
import {articleUrl, colors, publishedRadar, type Discovery, type Language} from '@/components/hub/model';
import {findMedia} from '@/components/hub/Editorial';
import '@/components/hub/hub.css';

type Params = {lang: string};
const labels: Record<string, [string, string]> = {
  games: ['Games', 'Games'],
  consoles: ['Consoles', 'Consoles'],
  celulares: ['Celulares', 'Phones'],
  ia: ['IA', 'AI'],
  gadgets: ['Gadgets', 'Gadgets'],
  curiosidades: ['Curiosidades', 'Curiosities'],
};

export const dynamicParams = false;
export function generateStaticParams() {
  return [{lang: 'pt'}, {lang: 'en'}];
}

function language(lang: string): Language {
  if (lang !== 'pt' && lang !== 'en') notFound();
  return lang;
}

export async function generateMetadata({params}: {params: Promise<Params>}): Promise<Metadata> {
  const {lang} = await params;
  const pt = language(lang) === 'pt';
  const title = pt ? 'Radar' : 'Radar';
  const description = pt
    ? 'Notícias e apurações do Radar AnderZilla: games, consoles, celulares, IA e gadgets.'
    : 'AnderZilla Radar stories: games, consoles, phones, AI and gadgets.';
  return {
    title,
    description,
    alternates: {
      canonical: `/${lang}/radar/`,
      languages: {'pt-BR': '/pt/radar/', en: '/en/radar/'},
    },
    openGraph: {title, description, url: `/${lang}/radar/`, locale: pt ? 'pt_BR' : 'en_US'},
  };
}

function Cover({item, pt}: {item: Discovery; pt: boolean}) {
  const media = findMedia(item.coverMediaId);
  if (media) {
    return (
      <div className="art cms-cover">
        <img src={media.url} alt={(pt ? media.altPT : media.altEN) || ''} width={media.width} height={media.height} />
      </div>
    );
  }
  return <div className={`art ${item.category}`} aria-hidden="true" />;
}

export default async function RadarIndex({params}: {params: Promise<Params>}) {
  const {lang: rawLang} = await params;
  const lang = language(rawLang);
  const pt = lang === 'pt';
  const items = publishedRadar();
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: pt ? 'Radar AnderZilla' : 'AnderZilla Radar',
    inLanguage: pt ? 'pt-BR' : 'en',
    url: `https://anderzilla.com/${lang}/radar/`,
    mainEntity: {
      '@type': 'ItemList',
      itemListElement: items.map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        url: `https://anderzilla.com${articleUrl(item, lang)}`,
        name: pt ? item.titlePT : item.titleEN,
      })),
    },
  };
  return (
    <div className="hub radar-index" lang={pt ? 'pt-BR' : 'en'}>
      <a className="skip" href="#radar">{pt ? 'Pular para o conteúdo' : 'Skip to content'}</a>
      <script type="application/ld+json" dangerouslySetInnerHTML={{__html: JSON.stringify(schema).replace(/</g, '\\u003c')}} />
      <header>
        <a className="brand" href={`/${lang}/#home`}><BrandWordmark /></a>
        <nav aria-label={pt ? 'Navegação do Radar' : 'Radar navigation'}>
          <a href={`/${lang}/#home`}>{pt ? 'Início' : 'Home'}</a>
          <a href={pt ? '/en/radar/' : '/pt/radar/'} hrefLang={pt ? 'en' : 'pt-BR'} lang={pt ? 'en' : 'pt-BR'}>{pt ? 'Read in English' : 'Ler em português'}</a>
        </nav>
      </header>
      <main id="radar" className="wrap article-page" tabIndex={-1}>
        <p className="eyebrow">AnderZilla / Radar</p>
        <h1>{pt ? 'Radar' : 'Radar'}</h1>
        <p className="lede">
          {pt
            ? 'As notas publicadas do Radar, da mais recente para a mais antiga. Rascunhos ficam fora desta lista até a aprovação.'
            : 'Published Radar notes, newest first. Drafts stay off this list until they are approved.'}
        </p>
        <p className="source">{items.length} {pt ? 'notas' : 'stories'}</p>
        {items.length === 0 && <p className="empty">{pt ? 'Nenhuma nota publicada.' : 'No published stories.'}</p>}
        <ul className="feed" aria-label={pt ? 'Notas do Radar' : 'Radar stories'}>
          {items.map(item => {
            const archived = item.fact.startsWith('Arquivo');
            return (
              <li key={item.id} className="card" style={{'--cat': colors[item.category]} as CSSProperties}>
                <Cover item={item} pt={pt} />
                <div className="card-copy">
                  <div className="card-category">
                    <span>{labels[item.category]?.[pt ? 0 : 1] || 'AnderZilla'}</span>
                    {archived && <span className="archive">{pt ? 'ARQUIVO' : 'ARCHIVE'}</span>}
                    {item.updatedAt && <span className="archive">{pt ? 'ATUALIZADO' : 'UPDATED'}</span>}
                  </div>
                  <h3><a href={articleUrl(item, lang)}>{pt ? item.titlePT : item.titleEN}</a></h3>
                  <p>{pt ? item.summaryPT : item.summaryEN}</p>
                  <div className="card-bottom">
                    <small>
                      {item.sourceName}
                      <br />
                      <time dateTime={item.eventDate || item.published}>{item.eventDate || item.published}</time>
                      {item.verifiedAt && <> · {pt ? 'Apuração' : 'Verified'} {item.verifiedAt}</>}
                      {item.updatedAt && <> · {pt ? 'Atualizado em' : 'Updated'} {item.updatedAt}</>}
                    </small>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </main>
    </div>
  );
}
