# Auditoria UI/UX do CMS e conexão pública

10/09/2026. Revisão independente, somente leitura do código. Skills aplicadas: anderzilla-brand e anderzilla-frontend. Snapshot em desenvolvimento; correções posteriores devem ser verificadas novamente. Não certifica conformidade WCAG nem equivalência completa a WordPress/Joomla.

## Evidência executada

Playwright Chromium/Chrome em http://127.0.0.1:4181, larguras 1440, 390 e 320px, altura 900px. API interceptada exclusivamente dentro do navegador com fixture rotulada “DEMO — fixture isolada”; nenhum cadastro, publicação ou autenticação real foi alterado. Fluxos: dashboard, lista Conteúdo, criar rascunho, voltar à lista, Biblioteca de mídias, voltar pelo histórico do navegador. Screenshots locais ignoradas pelo Git em .cache/cms-audit-1440.png, .cache/cms-audit-390.png e .cache/cms-audit-320.png; mobile inspecionado visualmente.

Resultados: sem overflow horizontal de documento nas três larguras; campos têm labels e contraste visual coerente; formulário empilha em mobile; logout visível desktop e oculto 390/320; abrir editor deixa document.activeElement em BODY; voltar no navegador muda hash para #content, mas título permanece “Biblioteca de mídias”. Não houve teste de salvamento/API, concorrência, roles, entrega Azure ou leitor de tela nesta auditoria.

## Correções prioritárias

| Prioridade | Evidência | Impacto e ação |
|---|---|---|
| P1 | Control.tsx inicializa hash uma vez; teste back reproduz divergência URL/tela | Implementar navegação com histórico e guard de rascunho coerentes. URL, heading e módulo devem coincidir após back/forward, inclusive quando usuário cancela saída. |
| P1 | datetime-local converte por new Date(value); campo timezone separado não participa | Risco de agendar em horário diferente do pretendido. Fixar e indicar fuso efetivo ou converter usando fuso selecionado. Testar navegador UTC e America/Sao_Paulo com o mesmo evento. |
| P1 | import_snapshot.py transforma conteúdo sem slug/imageUrl; media é aceita mas não gera assets públicos | Campos aparentam controlar o site sem efeito final. Preservar/renderizar slug e imagem ou explicar expressamente indisponibilidade até integração. Não chamar mídia cadastrada de mídia publicada. |
| P2 | BODY após abertura de editor, sem skip link no admin | Focar heading ou primeiro campo no início da edição e heading/lista na navegação. Adicionar skip link e estados de carregamento acessíveis. |
| P2 | .exit display:none em max-width:680px; teste confirma | Oferecer saída da conta em menu de conta mobile. |
| P2 | Lista mostra PT/EN pela existência de título apenas | Título não comprova tradução concluída. Mostrar completude por campos obrigatórios/revisão e validação antes de aprovar. |
| P2 | Preview textual com pre e textarea Markdown | Não representa renderização final. Implementar preview seguro usando o mesmo renderer do público, preservando o rótulo textual enquanto isso não existir. |

## Referências funcionais de CMS

O objetivo não é clonar WordPress/Joomla inteiros; é permitir operação editorial sem dependência constante de desenvolvedor. WordPress oferece composição por blocos, inserção de mídia, configuração de imagem destacada/taxonomia/permalink e revisão de alterações. Referências oficiais: [editor de blocos](https://wordpress.org/documentation/article/wordpress-block-editor/), [configurações de blocos/posts](https://wordpress.org/documentation/article/work-with-blocks/), [edição de mídia](https://wordpress.org/documentation/article/edit-media/) e [revisões](https://wordpress.org/documentation/article/revisions/), consultadas em 10/09/2026. A documentação histórica oficial do [editor de artigos Joomla 3.10](https://docs.joomla.org/Help310%3AContent_Article_Manager_Edit/en) descreve edição, histórico e metadados; serve como referência funcional, não afirmação de versão atual.

| Capacidade | Estado observado AnderZilla | Próxima entrega recomendada |
|---|---|---|
| Editor | PT/EN lado a lado, textarea Markdown, salvar/aprovar separados | Toolbar semântica, links, listas, imagens, preview real; abas PT/EN mobile; resumo de validação |
| Mídia | URL, alt, crédito, licença; sem upload | Biblioteca com miniaturas, seleção em conteúdo, vínculo por ID, dimensões/tamanho e direitos; upload só com backend seguro |
| SEO | Slug simples, sem painel dedicado | Título/descrição SEO, canonical controlado, OG, slug único, preview de snippet e rota indexável por artigo/idioma |
| Taxonomia | Seis categorias hardcoded, sem tags | Tags e seleção de categoria administrável com slug/PT/EN; impedir exclusão de termo em uso sem migração |
| Revisões | Lista de versões, sem comparação/restauração visível | Diff e restaurar como nova revisão, nunca sobrescrever auditoria |
| Publicação | Fila e distinção rascunho/aprovado/entrega | Mostrar URL final e revisão publicada, erros acionáveis, acompanhar executor; publicar por ambiente explícito |
| Operação de listas | Busca local e filtro de status | Ordenação, paginação de API, filtros categoria/idioma, seleção em lote com confirmação proporcional |
| Contas/comunidade | Página sem operação completa observada | Roles, suporte, histórico de resgates e ações auditadas; não confundir cadastro de missão com emissão de KP |

## Conexão entre áreas

Pelo código inspecionado, conteúdo vira discoveries; eventos e afiliados alimentam model.ts. Páginas/ofertas/campanhas aparecem no snapshot, mas presença no JSON não comprova renderer e rota pública: verificar cada consumidor antes de declarar integração concluída. Mídia perde sua função visual no transform atual; missão/recompensa não deve entrar automaticamente em publicação sem autoridade do servidor e estoque. Menu, home/hero e canais sociais ainda precisam de contrato de configuração para serem administráveis sem edição de código.

O site público atual usa navegação por hash para áreas do hub. Isso é aceitável como preview, mas artigos próprios precisam de URLs estáticas por slug/idioma, metadata por página e links compartilháveis para sustentar descoberta orgânica. Dialog de resumo não substitui página editorial. Markdown deve ter renderização segura; não introduzir HTML arbitrário por conveniência do editor.

## Direção de qualidade

Paleta e Ghost mantêm identidade; dashboard comunica separação operacional. Para qualidade editorial superior, priorizar espaço de escrita, preview fiel e caminho claro “rascunho → revisão → publicação → abrir no site”. O formulário mobile atual fica muito longo porque exibe os dois corpos de texto integralmente; abas de idioma, grupos recolhíveis e ação salvar persistente melhoram uso sem esconder status ou erros. Ícones Unicode podem variar por plataforma; adotar família SVG consistente depois de fechar os fluxos.

Manter rótulos de demonstração visíveis no ambiente demonstrativo. Dados da fixture desta auditoria não são dados de audiência nem de operação real. Todos os pontos acima foram enviados ao coordenador; bugs concretos de navegação, foco, fuso e saída mobile também foram enviados ao agente CMS.

## Revalidação do site público após integração CMS

Preview Azure verificado em 10/09/2026: release **5d3dfb01-fc1f-4faa-b5d6-c8a64194b2e4**, snapshot SHA256 ded8aa04579f4d64e690bc6ed029832ef9c07fd30928089fa11ba8439b259ea7, obtidos do cms-release.json antes dos testes. URL: https://salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net.

Executado Playwright Chrome real, somente leitura pública: 18 combinações de 1440/390/320px × home, artigo PT /pt/radar/demo-gadgets/, artigo EN /en/radar/demo-gadgets-en/, agenda, Store Points e Karaca Points. Todas sem overflow horizontal, com um h1 e identificação demonstrativa. Nenhum pageerror. Rotas de artigo responderam200. Capas e imagens no corpo carregaram com alt localizado; Markdown apresentou heading, negrito e lista. Screenshot .cache/cms-article-preview-mobile.png inspecionada visualmente: hierarquia, legibilidade, créditos e rótulo DEMO claros. Algumas imagens da home estavam pendentes na medição inicial de250ms; espera pelo carregamento confirmou nenhuma imagem quebrada.

SEO dos artigos: título e descrição próprios, idioma pt-BR/en, canonical por slug e hreflang entre versões. Os exemplos têm meta robots noindex,nofollow e o preview inteiro entrega X-Robots-Tag noindex,nofollow,noarchive. A home mantém meta index,follow do artefato, mas o cabeçalho de preview é restritivo; não foi identificado bloqueio de noindex ausente. Canonical aponta ao domínio final por projeto de publicação, sem comprovar disponibilidade dessas páginas em produção.

**Superado no site público:** a lacuna anterior de perda de slug/imagem não descreve mais esta release; agora há artigos por idioma, capa/crédito e conteúdo formatado vindo do CMS. Há exemplos rotulados nas áreas inspecionadas. Essa verificação não confirma checkout, eventos reais, estoque resgatável nem emissão de pontos. Os achados anteriores do admin permanecem como registro histórico até revalidação específica do admin atualizado; não inferir resolução a partir dos testes do site público.
