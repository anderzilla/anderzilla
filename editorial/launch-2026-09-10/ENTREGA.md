# Acervo editorial de lançamento — entrega de 10/09/2026

60 matérias aprovadas no CMS Azure SQL: dez de Games, Consoles, Gadgets, IA, Celulares e Curiosidades/desenvolvimento. Textos e metadados PT/EN; 120 páginas de artigos. Distribuição editorial: 39 notícias, 10 explicadores, 10 análises documentais e um comparativo. Não são 60 lançamentos de hoje nem reviews de produtos testados pela redação.

Cada matéria tem título, introdução, corpo conciso, referências, data de apuração, contexto temporal, SEO, hashtags, capa e imagem vertical. O acervo reúne 71 referências e 360 textos sociais (Instagram, Facebook e WhatsApp, nos dois idiomas). As 120 artes próprias usam texto em português; não são fotos oficiais dos produtos.

## Acesso e estado real

- [CMS](https://victorious-mud-09355980f.3.azurestaticapps.net): Conteúdo → buscar matéria → Editar. Kit social e Histórico ficam no editor.
- [Prévia do portal](https://salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net): release c77440a8-558f-4780-a990-6438cf14e9f7, deployed, marcador online verificado.
- [Exemplo GTA 6](https://salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net/pt/radar/gta-vi-data-plataformas/).
- Produção não promovida. A prévia permanece sem indexação; links sociais apontam ao domínio canônico anderzilla.com e devem ser distribuídos depois da publicação correspondente em produção. Nenhum post social enviado.

## Histórico e revisão

Cadastro feito pelo importador operacional do CMS, usando o mesmo domínio, validações e auditoria do painel. Não houve INSERT editorial direto no SQL. As 60 matérias têm rascunho e aprovação; três ajustes finais de inglês geraram versões 3/4. Foram arquivados 21 registros de demonstração ou curadoria inicial, preservando suas revisões.

Os agentes fizeram revisão cruzada integral dos textos e legendas PT/EN, com nova consulta independente às fontes de maior impacto. As revisões detalham o escopo real: não houve reabertura independente de todas as fontes duas vezes. Uma primeira tentativa de publicação ficou failed antes do deploy porque a checagem esperava index.html em vez do formato .html usado pelo projeto; a checagem foi corrigida e a segunda release foi implantada.

## Verificação

- Build web passou, com 138 rotas estáticas, incluindo 120 artigos.
- Todas as 120 páginas passaram em título, canonical, noindex da prévia, JPEG social existente, JSON-LD e UTF-8.
- ZIP verificado: 60 capas JPG 1200×630, 60 cards PNG 1080×1350 e 60 kits Markdown, sem arquivos corrompidos ou imagens ausentes.
- Amostra visual independente: capa e vertical de seis categorias, sem cortes ou problemas de contraste. Template consistente, mas repetitivo; resumos nas miniaturas são secundários e menores que os títulos.
- Navegador real: homepage, busca GTA 6, artigo PT em desktop/celular 390×844, navegação EN, cópia real de link e resumo EN, filtro IA com dez matérias, carregamento de 12 para 24 resultados. Na amostra móvel, sem imagem quebrada ou overflow horizontal.
- CMS autenticado: campos e fontes, capa e vertical independentes, kit PT/EN, botão PNG, confirmação de cópia social e histórico de rascunho/aprovação.
- CMS/publisher: 30 e 18 testes passaram. Builds admin passaram. Proteção anônima das rotas administrativas permanece redirecionando ao login Microsoft.

## Melhorias implantadas

CMS: importação editorial em lote com histórico; fontes, datas, formato, SEO e kit social; upload de capa e vertical independentes; download PNG; cota de mídia calculada sem transferir a biblioteca inteira; validação de release com uma leitura por coleção dentro da transação. Ganho de tempo da última otimização ainda não medido em produção.

Portal: busca, filtros e carregamento progressivo, distribuição de categorias no feed, fontes e datas nos artigos, relacionados, compartilhamento nativo/WhatsApp/Facebook/cópia, canonical e idiomas alternativos, JSON-LD e imagens sociais JPEG. Verificação de aparência dentro dos aplicativos Instagram/Facebook/WhatsApp ainda depende do compartilhamento após promoção do domínio final.

As alterações de código permanecem no workspace compartilhado com a tarefa de automações; não foi criado commit misturando trabalho de outras tarefas.
