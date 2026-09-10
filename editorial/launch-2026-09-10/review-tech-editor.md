# Revisão cruzada — editor tech

Data: 10/09/2026. Revisor: agente editorial tech, independente da redação de games/consoles/gadgets.

## Escopo executado

- Leitura dos 30 textos PT de `games-consoles-gadgets.json`, dos 30 leads EN e das 30 legendas Instagram PT; inspeção de metadados, hashtags EN, fontes humanas, formatos e datas.
- Conferência independente em fontes primárias dos pontos de maior impacto de GTA VI, Modern Warfare 4, PHYSINT, Logitech MX Keypad, bundles Switch 2 e monitor ROG PG259QWS Ace.
- Os demais registros foram revisados quanto à coerência editorial e correspondência interna PT/EN; esta revisão não representa um novo teste prático de jogos ou dispositivos nem reabertura completa de todas as fontes.

## Resultado

Não identifiquei contradição factual nas seis fontes primárias reabertas. Os textos distinguem anúncio, acesso experimental, disponibilidade regional e teste próprio. As legendas têm perguntas próprias do assunto e hashtags pertinentes. Os itens antigos sobre Portal, dock Ally, Legion Go, Steam Deck, Superstrike e XREAL estão contextualizados como explicadores.

Conferências realizadas:

| Item | Evidência primária conferida | Resultado |
|---|---|---|
| GTA VI | https://www.rockstargames.com/VI | Data 19/11/2026, PS5 e Xbox Series; extended look 27/08. PC não listado. |
| Modern Warfare 4 | https://www.callofduty.com/ca/en/blog/2026/05/call-of-duty-modern-warfare-4-announcement | Comunicado 28/05, lançamento 23/10, PS5/Series/PC/Switch2, exclusão PS4/One, campanha/multiplayer/DMZ. |
| PHYSINT | https://news.xbox.com/en-us/2026/09/09/xbox-and-kojima-productions-expand-partnership-to-publish-physint/ | Parceria e cinema/TV confirmados; não apresenta data do jogo. Abertura falhou, busca oficial devolveu o comunicado integral. |
| Logitech MX Keypad | https://news.logitech.com/press-releases/news-details/2026/Logitech-Unveils-MX-Keypad-for-Developers-The-Customizable-Multi-App-AI-Control-Center/default.aspx | Data 08/09, personalização e integração dev/IA confirmadas. |
| Bundles Nintendo | https://www.nintendo.com/us/whatsnew/two-new-nintendo-switch-2-bundles-deliver-sun-soaked-sports-high-speed-thrills-and-extra-value/ | Mario Kart fim de setembro; Sports Resort 22/10; jogo digital e 90 dias NSO no anúncio americano. |
| ROG OLED | https://rog.asus.com/articles/gaming-monitors/new-245-inch-rog-monitors-bring-oled-panel-tech-to-the-esports-arena/ | 25/08, 24,5 polegadas, PG259QWS Ace Full HD/720 Hz confirmados. |

## Limites e refinamentos editoriais

1. **Players’ Choice e Tokyo Game Show:** as URLs iniciais deram erro de navegação. Após coordenação com o autor, reabri com sucesso https://blog.playstation.com/2026/ (título e data da vitória de Zero Company, 10/09) e https://news.xbox.com/en-us/2026/09/09/xbox-tokyo-game-show-broadcast-announce-2026/ (17/09 às19h JST =10hUTC =7hBrasília, canais oficiais). Os fatos centrais estão confirmados; o autor informou que incluirá as referências acessíveis. Não atribuir contagem de votos aos números de interação do índice.
2. **Conteúdo útil além do checklist:** boa parte do lote usa o mesmo desenvolvimento “o que observar / ainda não testamos / nossa leitura”. Isso preserva honestidade, mas recomenda-se variar futuras pautas com explicação de mecânica, comparação documental ou contexto de desenvolvimento. Os artigos não devem ser apresentados como reviews práticas.
3. **Variedade de fornecedores:** seis matérias de gadgets tratam do ecossistema ROG e várias vêm do mesmo evento. São produtos distintos, mas a distribuição na homepage deve alternar marcas e assuntos para evitar aparência de catálogo patrocinado. Não há relação comercial afirmada.
4. **Links sociais:** legendas prontas não significam posts enviados. O coordenador ainda deve resolver URLs definitivas e revisar cards renderizados antes de usar os materiais fora do site.

Nenhum JSON de outro autor foi modificado por esta revisão.

## Lote tech entregue pelo revisor

`ia-celulares-curiosidades.json`: 30 registros, 10 por categoria, PT/EN. Validação `services/cms/core.py validate(content, data, approved=True)` passou em 30/30 após a revisão recebida do editor games. Introduções entre 136 e 160 caracteres; slugs distintos por idioma; textos aproximadamente 190–225 palavras com fontes. Distribuição: 17 notícias, 8 análises, 4 explicadores, 1 comparação. Não são 30 lançamentos de hoje; publicações antigas são contextualizadas e identificadas.

Correções incorporadas: datas brasileiras anunciadas do iPhone18, separação evento25/comunicado26 do Galaxy S26, fonte global Xiaomi, ausência de datas editoriais presumidas em páginas de produto/cronologia, tradução de hashtags e labels EN, headlines de cards curtos, limitação de API no TypeScript7 e seu enquadramento como explicador. Imagens são instruções para cards conceituais próprios, sem supor direito de republicar fotos de fornecedores.


## Adendo: revisão integral do inglês

Concluída leitura de todos os 30 bodyEN e 90 textos sociais EN do lote games-consoles-gadgets, ampliando a revisão anterior dos leads. Não identifiquei contradições substantivas entre idiomas, placeholders no corpo, alegações de testes próprios ou traduções que alterem os fatos noticiados. O JSON não contém U+FFFD; caracteres estranhos no terminal eram efeito da codificação de exibição.

Correção pontual encaminhada ao coordenador para nova revisão no CMS: no registro rog-gladius-iv-ace, substituir o título inglês “ROG Gladius IV Ace focuses on adjustable weight and shape” por “ROG Gladius IV Ace focuses on weight tuning and ergonomics”, incluindo seoTitleEN e a primeira linha das três legendas EN. A formulação anterior pode sugerir ajuste físico do formato, enquanto o texto descreve peso ajustável e ergonomia. Slug só deve mudar com regeneração coerente das URLs; pode permanecer para preservar o endereço existente.

Os 60 tokens {urlEN} nas legendas Facebook/WhatsApp do arquivo de autoria precisam ser resolvidos pelo importador antes da distribuição, conforme fluxo do coordenador. Nenhum JSON foi alterado durante o cadastro. A repetição de “Documentary reporting” soa menos natural do que “Document-based reporting”, mas é refinamento estilístico, sem impacto factual ou bloqueio de lançamento. Não foi feita nova pesquisa de fatos já confirmados nesta etapa.
