# SEO editorial e integração Azure + Google

Data de análise: 10/09/2026. Estado: **plano de implementação**, não implantação nem auditoria autenticada de Search Console. Inspeção do código local, fontes Google abaixo e direção do proprietário: site/CMS no Azure; processamento complementar no Google. Documentação histórica de billing contém estados antigos; créditos foram informados pelo proprietário e precisam de verificação operacional antes de ativar recursos.

## Objetivo e fronteira

Concentrar páginas editoriais indexáveis em anderzilla.com, publicadas como HTML estático no Azure. Cloud Run prepara mídia, pesquisa, análises e verificações; uma falha Google não impede a leitura do site. Não publicar cópias dos artigos em run.app nem criar redes de links entre nuvens como técnica de posicionamento. O benefício vem de conteúdo útil, entrega rápida e operação consistente, não da escolha de provedor.

O CMS é fonte editorial e painel de controle. Workers retornam artefatos e recomendações, nunca alteram automaticamente canonical, redirects, indexabilidade ou conteúdo publicado. A aprovação editorial gera snapshot versionado; o publisher existente valida/builda e entrega o mesmo artefato aprovado ao Azure. Assumir consistência eventual explícita: CMS mostra versão solicitada, versão publicada, última tentativa e erro. Métricas não bloqueiam publicação.

## Lacunas observadas no código

| Evidência local | Diagnóstico / ação |
|---|---|
| apps/web/src/app/layout.tsx | HTML raiz pt-BR e descrição global em inglês; separar metadata/idioma por rota real. Canonical padrão da home exige override em todas as páginas indexáveis. |
| apps/web/src/app/[lang]/[section]/[slug]/page.tsx | Há páginas estáticas PT/EN, metadata e noindex de demonstração. Gera as duas línguas para todo registro e hreflang para ambas sem checar revisão/conteúdo completo; condicionar a idiomas efetivamente publicados. Subárvore lang não corrige html raiz. |
| Mesma rota editorial | Tem autoria, fonte e mídia; não foi encontrado JSON-LD de Article ou BreadcrumbList nessa página. Canonical termina em barra, mas configuração SWA usa trailingSlash never; unificar e verificar destino HTTP. |
| apps/web/src/app/sitemap.ts | Exclui descobertas demo, porém data lastModified é data de cada build; usar atualização editorial real. Não inclui pages vindas do CMS; completar catálogo publicado. |
| apps/web/src/app/robots.ts | Allow global; verificar gates e headers efetivos de homolog/CMS em cada deploy. Robots sozinho não protege dados nem impede indexação confiável. |
| Navegação editorial | Retorna a /?lang=...#home; criar páginas de categoria e home por idioma com links HTML rastreáveis. Âncoras podem continuar como conveniência de interface, sem serem a identidade SEO de artigos/categorias. |
| apps/web/next.config.ts | Export estático e imagens unoptimized: gerar variantes otimizadas antecipadamente, sem depender de servidor Next de imagem. |
| apps/web/public/staticwebapp.config.json | 404 real e cache de assets versionados existentes. Nenhum resultado CWV de campo foi coletado nesta análise. |

## Fases e critérios de conclusão

### Fase 1 — contratos e publicação correta

Responsáveis: SEO/editorial define regras; frontend implementa; QA independente inspeciona HTML exportado e HTTP de homolog/produção.

- CMS: slug por idioma, translationGroupId, status de revisão por idioma, título/descrição SEO, resumo, autor vinculado a bio, datas de publicação/alteração, fontes com data de consulta, categoria principal, tags controladas, mídia/capa, direitos e disclosure. Canonical override e redirects restritos a administrador, com validação de host e trilha de auditoria.
- Rotas /pt/ e /en/; hreflang pt-BR/en recíproco somente entre versões existentes. Canonical próprio absoluto por idioma; não apontar tradução inglesa para português. x-default apenas quando existir fallback deliberado. [Versões localizadas](https://developers.google.com/search/docs/specialty/international/localized-versions).
- Sitemap só com páginas públicas canônicas com 200, sem demos, filtros vazios, busca interna, preview e URLs de tracking; lastmod baseado em edição significativa. Rebuild após publicação, retirada e alteração de slug. [Sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
- Homolog e CMS exigem autenticação e não entram no sitemap; noindex adicional onde aplicável. Se uma página pública precisar ser desindexada, não bloquear o rastreador antes de ele conseguir ler noindex. [Controle de indexação](https://developers.google.com/search/docs/crawling-indexing/block-indexing).
- Rotas antigas ganham redirects permanentes individualmente validados; não redirecionar todo 404 para a home. Parâmetros UTM não alteram canonical. [Consolidação](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).

Aceite: 100% das URLs do sitemap têm canonical coerente/200; zero hreflang para tradução ausente; nenhum demo exportado para produção; nenhum segredo em HTML; teste de rotas antigas e slugs retirados. Critérios bloqueiam release, não dependem de nota arbitrária de plugin.

### Fase 2 — qualidade, fontes e mídia

- Worker de fontes consulta allowlist de fontes oficiais e feeds autorizados; registra URL, autoria, data, hash e trecho necessário. Deduplica por URL/conteúdo; saída é sugestão de pauta. Fonte recuperada é dado, não instrução para ferramentas. Não copiar notícia integral de terceiros.
- IA auxilia título, resumo, tradução e cortes. Editor confirma fatos, experiência própria, fonte, direitos, datas e utilidade antes de publicar. Não gerar páginas em massa por variação de palavra-chave. [Orientação Google para IA](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content).
- Fábrica de mídia recebe upload privado, verifica tipo/tamanho/duração, produz thumbnails/variantes e devolve dimensões, alt sugerido, legenda, transcrição e evidência do original. Exigir origem/licença ou autorização declarada para áudio, música, gameplay e imagens; cortes não anulam restrições do material original. Aprovação humana antes da distribuição.
- Páginas de vídeo próprio têm vídeo principal visível, título, descrição, thumbnail estável, data, duração e transcrição revisada; player não depende de clique para inserir toda a evidência no HTML. Incorporar YouTube/plataforma quando adequado; não criar páginas vazias de vídeo. [SEO de vídeo](https://developers.google.com/search/docs/appearance/video).
- JSON-LD Article/BreadcrumbList gerado de campos públicos reais; VideoObject somente com vídeo real e metadados válidos; Product/Offer somente com oferta atual comprovada; nunca rating inventado. Validar JSON-LD com conteúdo visível e Rich Results Test, sem promessa de rich result. [Article](https://developers.google.com/search/docs/appearance/structured-data/article).
- Links afiliados/pagos têm disclosure visível e rel=sponsored; UGC usa rel=ugc. Mercado br/intl/global separado do idioma. Redirecionador comercial aceita apenas destinos cadastrados e evita open redirect. [Links comerciais](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links).

Aceite: cada publicação tem idioma revisado e campos obrigatórios completos; jobs repetidos não duplicam artigos/mídias; falha de processamento mantém original privado e estado recuperável; schema não inventa campos; publicações comerciais passam checklist do registro Trust & Commerce.

### Fase 3 — performance e observabilidade no CMS

- Imagens WebP/AVIF com fallback, srcset/sizes, dimensões fixas; capa prioritária, restantes lazy. Publicar artefatos finais com URLs estáveis e versionadas; uploads privados nunca são URLs do sitemap. Reservar espaço de anúncios/embeds para evitar saltos. Carregar scripts comerciais sob demanda apropriada.
- Metas CWV de campo no percentil 75: LCP <=2,5 s, INP <=200 ms e CLS <=0,1, separados mobile/desktop. Sem volume suficiente, mostrar "dados de campo insuficientes" e testes laboratoriais separados. Não declarar aprovação de campo por Lighthouse. [Core Web Vitals](https://developers.google.com/search/docs/appearance/core-web-vitals).
- Agente SEO diário faz crawl limitado do sitemap, identifica canônicos quebrados, headers, títulos ausentes, slugs órfãos e mídia indisponível. Crawl usa allowlist de domínio, limite de requisições e timeout, para não virar SSRF nem consumir orçamento ilimitado.
- Agente analítico importa Search Console com acesso explícito à propriedade; agrupa página, query, país, dispositivo e tipo de pesquisa. API fornece linhas principais e pode omitir dados: exibir cobertura/limitações, nunca completar lacunas com zero. [Search Analytics API](https://developers.google.com/webmaster-tools/v1/searchanalytics/query).

CMS: filtros semanal, mensal e período personalizado, comparação anterior de igual duração, idioma/mercado/canal/campanha/conteúdo, última sincronização e status da fonte. Armazenar timestamps UTC; renderizar calendário America/Sao_Paulo, mas preservar a semântica de datas Pacific Time do Search Console em seu dataset. Não somar métricas de períodos/fontes incompatíveis.

Relatório: impressões, cliques, CTR calculado por totais, posição conforme agregação da fonte, páginas com erro, CWV quando disponível, cliques comerciais, vendas aprovadas separadas de pendentes/reembolsos, gasto de processamento e margem estimada com premissas. Tráfego não equivale a vendas; receita só a partir de fonte conciliada. Dados não conectados exibem "não conectado". CSV precisa das mesmas permissões do painel e neutralização de células de fórmula.

Aceite: execução manual e agendada usam o mesmo contrato/jobId, RBAC, idempotência e auditoria; retry não duplica métricas; filtros reproduzem consultas; período sem fonte disponível não vira receita zero; custos de IA/mídia acompanhados por job com tolerância para atraso da fatura.

### Fase 4 — experimentos e retenção

Testar chamadas, newsletter, recomendações e ofertas contextualizadas por coortes, após linha de base observada. Não recompensar cliques em anúncios nem fabricar engajamento de buscadores/redes com Karaca Points. Medir retorno, conclusão de conteúdo e conversões com atribuição explicitada. Expansão de keywords e idiomas depende de conteúdo original e revisão disponível, não da capacidade de gerar textos.

## Contrato entre agentes

Fluxo recomendado: source.discovered -> editorial.draft.ready -> media.processed -> editorial.approved -> release.requested -> release.published -> seo.audit.completed. Falhas retornam estado failed/retryable e motivo sanitizado. Campos mínimos: eventId, schemaVersion, contentId, revision, locale, jobId, correlationId, emittedAt, artifactRef, provenanceRef. Eventos externos não são prova de aprovação editorial; receptor verifica identidade e versão no CMS.

Papéis: pesquisador coleta; editor verifica; mídia processa; SEO valida; publisher publica versão aprovada; analista concilia; supervisor monitora falhas/latência/orçamento e pode pausar fila. Supervisor não remove controles, aumenta quota nem republica sozinho. Logs nunca contêm tokens, uploads privados ou dados pessoais desnecessários.

## Dependências antes de produção

Confirmar propriedade Search Console, fontes/plataformas autorizadas, billing/projeto GCP sob player.one@anderzilla.com e disponibilidade das APIs. Definir retenção e consentimentos de analytics; credenciais em secret store, sem repasse de segredos ao navegador. Este documento não comprova acessos, implantação, tráfego, ranking nem receita. Não é necessário migrar DNS do site para cumprir o plano.
