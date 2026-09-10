# CMS — operação editorial e publicação

Atualização 10/09/2026. Esta entrega substitui a interface inicial de cadastro simples. Código em `Z:/AnderZilla`; documentação nesta branch separada.

## Acessos e estado

- Painel homolog: https://victorious-mud-09355980f.3.azurestaticapps.net/
- Prévia pública: https://salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net/?lang=pt#home
- Acesso Microsoft, papéis do SWA e autorização por domínio no backend; não há senha própria do CMS. Conta proprietária convidada e login observado. Não presumir MFA obrigatório sem verificar política.
- SQL homolog: oferta gratuita com AutoPause no esgotamento, sem autorizar cobrança extra. Segredos exclusivamente em configuração privada e application settings; nunca no Git/RAG.

## Como o material chega ao site

1. Biblioteca de mídias: enviar JPEG/PNG/WebP até 2 MB; preencher alt PT/EN, crédito e licença. Servidor valida pixels, converte para WebP até 1600 px, remove metadados. Aprovar a mídia.
2. Conteúdo: preencher categoria, títulos, resumo, texto PT/EN, fonte/data, autor, slugs, SEO, tags e capa/galeria aprovada. Markdown tem toolbar e prévia; HTML arbitrário não executa.
3. Salvar cria rascunho ou nova revisão. Aprovar valida obrigatórios e referências. Editar aprovado o devolve a rascunho. Conflito de versão impede sobrescrita silenciosa.
4. Publicações: criar uma publicação congela os registros aprovados. Isso não equivale a site publicado. O operador executa `services/publisher/run_release.py --azure` com credenciais privadas da homologação.
5. Publisher cria staging isolado, extrai imagens verificando hash/caminho, gera dataset público por allowlist, executa build Next, publica no slot visual e verifica marcador por HTTP. Só então o estado vira deployed.
6. Falha antes do deploy marca failed; após envio incerto permanece deploying. `--reconcile --release-id ID` verifica marcador sem repetir publicação.

Publicador ainda é CLI de operador, sem worker remoto automático. Fila no painel não promete atualização imediata. Próxima fase deve automatizar a execução com identidade e segredos de escopo limitado, sem expor credenciais ao navegador.

## Mapa das áreas

| Cadastro | Destino público |
|---|---|
| Conteúdo | Radar, busca, filtro por seis temas, ticker e páginas /pt/radar/slug e /en/radar/slug |
| Biblioteca | Capa e galeria de artigos/páginas; ativos aprovados publicados em /media/hash.webp |
| Taxonomia | Tags aprovadas vinculadas e mostradas no artigo; os seis temas principais continuam estruturais |
| Eventos | Agenda e próxima live; exemplos DEMO não anunciam próxima live real |
| Ofertas | Loja & ofertas na home; DEMO sem botão de compra |
| Afiliados | Loot & upgrades; demonstração sem oferta/parceria ativa |
| Campanhas | Espaço home com intervalo de vigência e disclosure |
| Páginas | Blocos da home com link para /pt/pages/slug e /en/pages/slug |
| Missões/recompensas | Apenas definições explicitamente DEMO nas áreas Points/Store; nenhum crédito ou resgate real |

Vídeos/áudios/documentos usam URLs HTTPS. Galeria suporta imagem, MP4, áudio e links; YouTube por player de domínio permitido carregado após clique. Não existe upload/transcodificação de vídeo ou editor de áudio. Biblioteca inicial de uploads tem limite total de 10 MB no SQL para controlar custo; migrar binários para armazenamento próprio antes de escalar o acervo.

## Exemplos e qualidade

`services/cms/seed_examples.py --azure --approve` criou 15 registros determinísticos e idempotentes: seis artigos DEMO, imagem própria, tag, página, evento, oferta, afiliado, campanha, missão e recompensa. Reexecutar preserva edições existentes. Fontes editoriais reais anteriores permanecem separadas. Exemplos não são notícias reais, patrocínios ou estoque. Páginas DEMO recebem noindex/nofollow, não entram no sitemap; slot visual também envia noindex por header.

SEO: título/descrição PT/EN, canonical, hreflang, Open Graph/Twitter, URL própria, autoria, alt e sitemap de artigos reais. Não há promessa de ranqueamento. A revisão visual está em strategy/CMS-UX-AUDIT.md.

## Limites frente a WordPress/Joomla

Esta implementação não tem paridade integral: ainda faltam WYSIWYG por blocos, autosave, publicação agendada com worker, gestão de menus/layout global, crop/foco/variantes de imagem, lixeira/restauração pela UI, biblioteca paginada, redirects SEO, comentários/moderação, analytics de audiência, gestão de contas do portal e operação real de estoque/pontos. O editor atual é Markdown assistido com preview. Relatórios disponíveis são operacionais, não métricas inventadas de audiência ou receita.

## Empacotamento Azure

`swa deploy` 2.0.10 define SKIP_API_BUILD=true. O script infra/azure/deploy-admin.ps1 agora cria um pacote isolado com dependências Linux CPython3.11 em .python_packages/lib/site-packages; não copia virtualenv Windows. Antes disso, login funcionava mas consultas SQL retornavam 503 por dependências não empacotadas. Diagnóstico admin-only /api/admin/health retorna etapa/categoria/tipo de exceção sem mensagens ou segredos.

Referências: [SWA CLI](https://learn.microsoft.com/en-us/azure/static-web-apps/static-web-apps-cli), [Markdown seguro](https://github.com/remarkjs/react-markdown), [metadata Next](https://nextjs.org/docs/app/api-reference/functions/generate-metadata), [rede Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/connectivity-architecture?view=azuresql).

## Evidência da entrega

- Build apps/web gerou 44 páginas estáticas a partir do snapshot SQL, incluindo artigos PT/EN e páginas do CMS. Build apps/admin passou. ForgeKit não foi alterado.
- 16 testes CMS, 17 publisher/importador e 11 rewards passaram. Upload via HTTP local autenticado normalizou imagem 2200x1200 para WebP1600 e o rascunho de teste foi arquivado.
- Login Microsoft real e leitura de 12 artigos no SQL pela UI Azure confirmados após corrigir o pacote Linux; sem simulação de API neste smoke.
- Público revisado em 18 combinações de viewport/página: 1440/390/320, home/artigos PTEN/agenda/store/points. Sem overflow ou pageerror. Biblioteca e diagnóstico devem ser reavaliados depois de mudanças de dependências.
- Promoção de artefato CMS com containsDemo=true ou classificação ausente é bloqueada pelo prepare-artifact.ps1 em production. Nenhuma publicação no domínio principal nesta entrega.
- Auditoria npm encontrou 2 avisos transitivos existentes do PostCSS incluído pelo Next15 (moderado/alto). Não foi aplicada migração major automática; não se aceita CSS arbitrário no CMS. Resolver dependência e revalidar antes de declarar segurança de produção completa.
- Política de conexão SQL foi testada em Proxy e restaurada a Default; a mudança de rede não resolveu o erro. A correção efetiva foi empacotar as dependências da API.

Validação final Azure: biblioteca autenticada mostrou 1 imagem aprovada640x360 com alt/crédito/licença, após restaurar política Default. Última publicação do site: **408f7da8-6b7f-472a-afc2-028334e08b5e**, status deployed verificado por marcador HTTP, containsDemo=true. API rejeitou requisição anônima mesmo com cabeçalho de principal forjado (302 para login). O bloqueio de promoção DEMO para produção foi executado com fixture e passou.

O workflow visual anterior ainda constrói o fallback do repositório; não deve ser usado para publicar alterações editoriais enquanto não for conectado ao snapshot. A fonte operacional dos cadastros é SQL; o publisher monta o dataset somente em staging, preservando rascunhos e informações privadas fora do código público.
