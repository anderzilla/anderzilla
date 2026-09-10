# Template editorial AnderZilla

Base: [benchmark de dez referências](../research/BENCHMARK-10-SITES.md). Conceito navegável no worktree de código: `Z:/AnderZilla/prototypes/editorial/index.html`. É um estudo local, não uma rota publicada ou uma migração já aplicada a apps/web.

## Identidade proposta

Revista pessoal, curiosa e lúdica. Texto claro, títulos fortes, divisórias editoriais e ilustrações originais. O produto próprio acompanha o conteúdo em vez de ocupar o papel de única proposta da marca. Sem bibliotecas de tema ou ativos copiados dos sites estudados.

| Token | Valor | Uso |
|---|---|---|
| Papel | #f4f2eb | Fundo de leitura |
| Azul-grafite | #101b2c | Texto, cabeçalho de tabela e bloco StackPick |
| Texto secundário | #535d6d | Descrições e metadados |
| Amarelo Ghost | #f3d43c | Ações prioritárias e acentos |
| Azul Ghost | #183bbe | Área games e identidade |
| Vermelho do boné | #a73740 | Acentos da marca |
| Linha | #c5cbd2 | Separação visual; não comunica estado sozinha |

Arial/Helvetica e Georgia são fontes de sistema no conceito, sem download externo. A imagem AnderZilla Ghost fornecida pelo proprietário é o ativo principal já usado nas plataformas. Ela aparece como avatar, destaque e retrato; o arquivo original permanece intacto. O wordmark acompanha o personagem e não cria uma identidade substituta. Tipografia final pode ser refinada após escolha do visual, com licença adequada e orçamento de performance.

## Arquivos e operação

- `prototypes/editorial/index.html`: estrutura base, navegação e seletor de idioma.
- `prototypes/editorial/styles.css`: tokens, componentes e adaptações mobile.
- `prototypes/editorial/app.js`: copy PT/EN, telas e interações locais.
- `prototypes/editorial/assets/anderzilla-ghost.png`: cópia idêntica do ativo fornecido, SHA256 `D250940D7F8D8BF44875B5B5071D6983BEB79D2D73AB6590580E5664AF6256B6`.

Para abrir sem servidor, usar index.html diretamente no navegador. Para preview HTTP a partir de Z:/AnderZilla: `python -m http.server 4175 --bind 127.0.0.1 --directory prototypes/editorial`. Endereço: http://127.0.0.1:4175. Não há backend, cookies, SDK de analytics, pedido de dados pessoais ou chamadas de terceiros no carregamento do conceito.

Telas: `#home`, `#article`, `#stackpick`, `#channels`, `#sponsor`. Idioma `?lang=pt` ou `?lang=en`, preservado ao navegar. Filtros mudam o conteúdo local; links externos reais usam destino do canal, site atual ou Gumroad. O briefing comercial pode ser baixado em TXT após escolher formato; não é uma submissão de formulário.

## Conteúdo e limites

Comparações marcadas como publicadas apontam para páginas existentes em inglês. O conceito não revalida nem amplia as conclusões dessas páginas; elas precisam de revisão editorial própria antes do próximo lançamento. A pauta de teclado e o artigo de exemplo são identificados como propostos/demonstrativos. Não há notas de review, preços de afiliados, patrocinadores, depoimentos, contadores ou estado de live inventados.

A imagem Ghost é fornecida pelo proprietário. As formas auxiliares de circuito, teclado e terminal são originais CSS, não evidência de teste de equipamentos. No site final, artigos com experiência prática devem usar registros próprios. O protótipo inclui formatos comerciais propostos, sem preço, contrato ou captura de leads. Contato e recebimento ainda precisam ser validados antes de publicar a operação de patrocínio.

## Migração para a aplicação

Portar a estrutura para componentes React, com conteúdo separado dos componentes. Criar registros editoriais com ID, slug, idioma, traduções existentes, tema, formato, autoria, data de publicação/atualização, evidência (documentação/teste/opinião), fontes e vínculo comercial. Oferta deve separar loja, mercado, moeda, URL, data de verificação e estado de afiliação. Só `ativo` com URL validada habilita CTA afiliado.

Na implementação, usar /pt/ e /en/ com HTML indexável e relações entre traduções publicadas. O roteamento por hash/query do protótipo serve à apresentação; não é a estratégia de SEO final. Preservar /forgekit e /stackpick ou fornecer redirecionamentos deliberados. Novo conteúdo exige sitemap, canonical e metadados reais. Não criar versão inglesa vazia nem traduzir automaticamente sem revisão.

Validar responsividade, navegação por teclado, foco, contraste e links. Publicar primeiro em homologação, verificar acesso do proprietário e promover o artefato pelo processo Azure. O build de apps/web não foi alterado pela criação deste estudo. Não adicionar o protótipo ao diretório public/out da aplicação.

## Critérios de aceite do próximo lançamento

- Marca pessoal e temas compreensíveis na primeira tela.
- Conteúdo realmente publicado ou oculto da produção; nenhuma pauta fictícia preenchendo grade.
- PT/EN por URL e navegação acessível, com títulos que não cortam no mobile.
- Comparação separa fonte do fornecedor, julgamento editorial e resultado medido.
- ForgeKit mantém https://anderzilla.gumroad.com/l/edkel.
- Canais usam URLs confirmadas; dados de live e agenda só quando verificados.
- Patrocínio tem contato/recebimento testados e identificação comercial clara.
- Sem novas assinaturas ou infraestrutura paga como dependência do redesign.

## Verificação do conceito

JavaScript validado com node --check. Navegação e layout exercitados nas cinco telas, em PT e EN, nas larguras 320, 390, 768 e 1440px, sem overflow horizontal da página e com um título h1 por tela. Filtros de Gadgets/Tudo e seleção/download do briefing foram verificados; nenhum erro JavaScript de página foi registrado. Home desktop/mobile e artigo EN foram inspecionados por screenshot. Isso é uma verificação de protótipo, não auditoria completa de acessibilidade, desempenho ou publicação Azure.
