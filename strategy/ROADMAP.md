# Plano por fases

## Fase 1 — base e análise

Inventário autenticado, pesquisa oficial, canais confirmados, orçamento em dois cenários, direção pessoal separada da CodeMatrix, branches separadas e ferramentas de IA locais preparados. A vitrine recebeu o polimento anterior de ForgeKit/StackPick. A transformação completa em portal editorial bilíngue ainda precisa ser implementada.

Critério de saída: relatório e fontes versionados, builds das duas apps verificados e pendências explícitas. Termos/billing Google impedem publicação, mas não impedem preparar conteúdo, código e operação.

## Fase 2 — primeira versão editorial PT/EN

- Navegação: novidades, IA, games, gadgets, StackPick, produtos e parcerias; não criar páginas vazias só para completar menus.
- Implementar rotas de idioma, hreflang, canonical, sitemap e seleção de idioma; marcar traduções indisponíveis sem duplicar texto português como inglês.
- Publicar primeiro lote de conteúdo original revisado e uma demonstração real do ForgeKit. Usar plano EDITORIAL-90-DAYS.md como proposta, adequando à disponibilidade real do proprietário.
- Conectar links confirmados das redes; medir saídas/CTAs sem inventar integração de dados.
- Canal comercial com formulário ou email efetivamente testado, tipos de entrega e transparência de publicidade. Usar kit como rascunho, sem marcas ou métricas fictícias.

Critério de saída: páginas completas em ambos idiomas para os caminhos lançados, nenhum CTA falso e teste de compra/entrega pelo proprietário quando necessário.

## Fase 3 — homologação e produção

Após termos/billing: criar projetos isolados sob player.one, registry, identidades mínimas/OIDC, backend de estado e alertas. Homologação privada, produção pública somente quando pronta. Promover a mesma imagem aprovada; preservar demo legada e correio durante migração DNS. Executar runbook CLOUD-RUN-RUNBOOK.md e registrar URLs, revisões e rollback reais. Não usar os projetos CodeMatrix.

Azure fica como laboratório opcional enquanto benefícios gratuitos e limites forem confirmados. Evitar manter duas hospedagens equivalentes com teto tão pequeno.

## Fase 4 — audiência e receita em 90 dias

Semanas 1–2: medir base real dos canais, preparar primeira oferta e conteúdo; semanas 3–6: comparar formatos e CTAs; semanas 7–12: repetir os melhores resultados, testar patrocínio com dados reais e ampliar inglês conforme demanda. Cadência inicial sugerida depende das horas semanais, ainda não informadas.

Prioridade de receita: produto próprio -> afiliados aprovados e relevantes -> patrocínios pontuais -> recursos nativos de plataforma conforme elegibilidade. Publicidade programática é opção posterior quando retorno justificar impacto na experiência.

Não solicitar todos os programas indiscriminadamente: verificar aceitação Brasil, pagamento, audiência exigida e termos, depois selecionar ofertas que realmente aparecerão no conteúdo. Respeitar janela de reaplicação do PartnerStack indicada no contexto histórico.

## Fase 5 — integrações de jogos

Começar com links de perfil e Discord OAuth com escopos mínimos, se houver benefício ao visitante. Steam OpenID/Web API é candidato para biblioteca pública; Xbox requer avaliar programa/API e consentimento. PlayStation/Nintendo não devem depender de APIs não oficiais ou captura de credenciais. Integrações privadas de biblioteca/troféus só após confirmação de identificadores e viabilidade documentada.
