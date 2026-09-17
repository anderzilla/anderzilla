"use client";
import {useHub} from '../hub/HubProvider';
import {Catalog} from './Catalog';
import {flag,visible} from './data';
import './commerce.css';
export function CommerceHome(){const {lang,t}=useHub();const ads=visible('ad_placements');return <section className="commerce"><div className="heading"><h2>{t('Descobertas & produtos','Discoveries & products')}</h2><a href={`/${lang}/transparencia/`}>{t('Como ganhamos dinheiro','How we earn money')} →</a></div><nav className="commerce-markets" aria-label={t('Mercados','Markets')}>{flag('showMarketBr','br',true)&&<a href={`/${lang}/comercio/brasil/`}>{t('Área Brasil','Brazil area')} · BRL →</a>}{flag('showMarketIntl','intl',true)&&<a href={`/${lang}/comercio/internacional/`}>{t('Área Internacional','International area')} · USD →</a>}</nav><Catalog rows={visible('products')} type="products" lang={lang}/>{ads.length>0&&<><h2>{t('Publicidade','Advertising')}</h2><Catalog rows={ads} type="ad_placements" lang={lang}/></>}<p><a href={`/${lang}/parceiros/`}>{t('Afiliados e disclosure','Affiliates and disclosure')} →</a></p></section>}
