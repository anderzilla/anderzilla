# Plano do Centro de Controle AnderZilla

Planejamento de 10/09/2026, solicitado pelo proprietário. Nenhum painel, banco, integração ou assinatura foi ativado nesta etapa. Abrange o site pessoal de games, IA, tecnologia e gadgets, separado da CodeMatrix. Objetivo interno: aumentar retorno e receita sustentável por conteúdo útil/divertido; a interface pública apresenta conteúdo, benefícios e condições claras.

## Decisão recomendada

Criar **AnderZilla Control**, aplicação administrativa Next.js/TypeScript separada em apps/admin, com uma experiência única para CMS, mídia, eventos, comércio, Karaca Points, comunidade e operação. Reutilizar componentes acessíveis, tokens da marca e bibliotecas maduras; não escrever editor rich text, tabela e calendário do zero. Backend modular em APIs protegidas, mantendo o núcleo transacional separado dos cadastros editoriais. Site público apps/web continua estático.

Refine Core é candidato recomendado para tabelas, filtros, data provider e auth provider, condicionado a um spike Next/export/autenticação antes de adoção. Tiptap Core/StarterKit é candidato para editor por blocos controlados; colaboração em tempo real e extensões pagas ficam fora do MVP. Não usar builders hospedados ou planos Pro por padrão. [Refine Core](https://refine.dev/core/docs/), [providers](https://refine.dev/core/docs/guides-concepts/general-concepts/), [Tiptap](https://tiptap.dev/docs/editor/getting-started/overview).

A hipótese é economizar operação de infraestrutura, não eliminar custo de desenvolvimento/manutenção. Se o spike mostrar que a base administrativa/editorial própria exige complexidade excessiva, reavaliar CMS hospedado somente para editorial; não reescrever o ledger para caber num CMS.

| Alternativa | Avaliação neste contexto |
|---|---|
| Painel modular + bibliotecas | Recomendado: experiência e autorização integradas às recompensas e à arquitetura Azure planejada; exige implementação e manutenção incremental. |
| Payload | Bom alinhamento React/Next e CMS pronto, mas requer runtime servidor e adapters oficiais MongoDB/PostgreSQL/SQLite; não encaixa diretamente em export estático + Azure SQL. |
| Directus | Administração de dados pronta; requer operação de runtime e análise da licença atual. Não presumir acesso irrestrito gratuito pelo histórico do produto. |
| Sanity | Pode acelerar apenas editorial; limites de papéis/datasets/plano e um backend separado para operações sensíveis precisam entrar na decisão. Não colocar dados privados em datasets públicos. |

Fontes verificadas nesta revisão: [Payload deployment](https://payloadcms.com/docs/production/deployment), [bancos](https://payloadcms.com/docs/database/overview), [Directus planos/licenciamento](https://directus.com/pricing), [Sanity planos](https://www.sanity.io/pricing). Não instalar/provisionar plataforma concorrente antes do spike. Valores/licenças precisam de nova conferência na contratação.

## Navegação e experiência

Barra lateral com grupos recolhíveis: **Hoje / Conteúdo / Comunidade / Comércio / Análise / Operação**. Busca global e botão Criar no topo. Mostrar ambiente por texto persistente, não só cor. Identidade Ghost e neon contido; corpo com Space Grotesk, títulos Oxanium, alta densidade legível. O painel é ferramenta de trabalho, sem animações ou gamificação competindo com tarefas.

Página inicial prioriza pendências: revisão, tradução, mídia sem crédito, evento próximo, campanha vencendo, publicação falhando, pedido reservado e consumo próximo do limite. Cards financeiros e de audiência mostram período, fonte e atualização; fonte desconectada aparece como indisponível, nunca zero inventado.

| Módulo | Controle previsto |
|---|---|
| Conteúdo | Pautas, notícias, descobertas, artigos, reviews, curiosidades, StackPick, autores, categorias, tags, fontes, rumor/opinião/fato, autoria de teste próprio, datas, PT/EN, revisões, SEO, slug e redirecionamentos. |
| Mídias | Biblioteca, tags/pastas, miniaturas, dimensões/tamanho, hash/deduplicação, alt PT/EN, crédito/licença/fonte, ponto focal, usos/referências e variantes. Exclusão bloqueada se ainda publicada/referenciada. |
| Site | Home e ordem dos blocos, destaques, menus, rodapé, páginas, textos, canais, SEO global, OG, redirects e feature flags permitidas. Blocos aprovados e preview; sem executar HTML/JS livre. |
| Agenda/live | Calendário editorial e de eventos, tema, fuso, plataforma, URL validada, início/fim, cancelamento, recorrência futura, lembretes administrativos e observações de live com fonte/validade. |
| Loja/ofertas | Produtos próprios, assinaturas e ofertas externas, variantes quando necessárias, mídia, preço/moeda/região, prazo/condições, disponibilidade e links. Gumroad continua checkout inicial. |
| Karaca Points | Missões/quizzes e regras versionadas, limites/janelas, verificadores, consultas de carteira, extrato, anomalias e reconciliação. Ajuste por comando compensatório, nunca editar saldo/ledger. |
| Store Points | Recompensas, custo KP, unidades financiadas, regiões, termos, estoque disponível/reservado, pedidos, triagem, despacho, evidência e reconciliação de entrega incerta. |
| Publicidade/afiliados | Anunciantes, propostas/contratos referenciados, campanhas, placements, criativos, vigência, mercado, disclosure, aprovação, destino e entrega. Não executar scripts arbitrários de anunciantes. |
| Usuários/suporte | Contas, papéis, bloqueio com motivo, solicitações e histórico necessário ao atendimento, vínculos verificados de plataforma; comentários/moderação somente quando essa função existir. |
| Relatórios | Conteúdo e retorno, funis, campanhas, cliques agregados, vendas comprovadas, receitas estimadas/confirmadas/recebidas separadas, custos e economia KP. Exportações com filtros e permissão. |
| Integrações | Estado, última sincronização, erro, escopos, conta e ambiente. Provedores de pagamento/analytics/redes/IA conectados só após verificação; tokens não retornam ao navegador. |
| Operação | Publicações/jobs, auditoria, permissões, exportação/restauração, alertas, limites de mídia, orçamento, retenção, configurações e status do sistema. |

Todos os módulos terão: lista com busca/filtros salvos, paginação, detalhe, histórico, validação por campo, estado vazio/erro/sem acesso e atalhos. Formulários divididos em Essencial / Publicação / Idiomas / Avançado, com campos condicionais. Autosave de rascunho com versão, aviso de edição concorrente e comparação/restauração. Seleção em lote apenas para ações seguras; publicar/excluir/ajustar pontos exige revisão do efeito concreto. Tabelas adaptadas ao mobile para consulta/ações urgentes; desktop é a experiência principal de edição.

PT/EN lado a lado, tradução vinculada por ID. Tradução sugerida por IA tem autor/estado e revisão própria. Não publicar página vazia para idioma ausente. Busca global não revela existência de objeto sem autorização. Alvos acessíveis, foco e teclado testados. Links de detalhe e filtros devem ser compartilháveis, com autorização aplicada ao abrir.

## Três fluxos de referência

**Notícia:** criar pauta → redigir com fonte/data/mídia → revisar idioma → preview privado desktop/mobile → aprovar revisão → publicar → acompanhar job e URL efetiva. O editor não precisa editar Git ou abrir Azure. Salvar rascunho não significa publicar.

**Recompensa:** cadastrar item/termos → registrar estoque financiado → revisar custo KP/região/entrega → ativar → receber reserva → triagem → iniciar entrega → registrar evidência → concluir. Uma falha depois do início da entrega vai para reconciliação, sem reenvio/refund automático. Operador vê dados privados apenas quando necessários.

**Campanha/live:** cadastrar anunciante e evidência de aprovação → escolher criativo/placement/período/disclosure → preview → publicar → verificar exibição → acompanhar números existentes → encerrar → relatório. Agendar um evento não confirma que o canal está ao vivo.

## Arquitetura e fonte única

Proposta de organização: apps/web (público); apps/admin (controle); services/api (adaptadores HTTP/autorização); services/rewards (domínio transacional existente); packages/contracts (schemas/OpenAPI/snapshot); packages/ui (tokens e primitivas compartilhadas). Criar os pacotes quando houver compartilhamento real, não extrair tudo antecipadamente.

Admin estático em origem protegida separada, por exemplo admin.anderzilla.com no futuro; hostname é proposta, não DNS criado. API privada no mesmo contexto autenticado do admin; API visitante do portal pode usar outro recurso/identidade. Homolog e produção têm bancos, mídia privada, credenciais e identidades isolados. Validar limites de recursos/SKU e implantação antes de criar novas SWAs. Nenhuma string de conexão, credencial de publicação ou controle de autorização depende do cliente.

**Mudança planejada em relação ao backend anterior:** quando o CMS entrar em operação, Azure SQL passa a ser a fonte única editorial. Importar JSON/TS atual preservando IDs/slugs/fontes; validar e congelar edição manual paralela. Git mantém código, migrações e contratos. Conteúdo não será editado simultaneamente em banco e arquivos. Até a migração, o acervo atual permanece como está.

Tabelas adicionais: content_items, content_revisions, content_translations, sources, taxonomy, assets, asset_usages, page_compositions, events, channel_observations, products/offers, campaign_versions, placements, publication_releases/jobs, permissions/role_assignments, audit, integration_runs e analytics_aggregates. Domínio de pedidos/pontos mantém tabelas e restrições próprias. Soft delete não substitui política de retenção; registros financeiros/transacionais seguem política definida antes de operação real.

Revisão editorial: draft → in_review → approved → archived. Publicação: queued → building → validated → deploying → deployed/failed. Snapshot congela revisões aprovadas e inclui somente campos públicos. Worker builda Next, testa, publica artefato e confirma resultado autenticado com ID/hash. Repetição é idempotente. Última versão válida fica pública se o job falhar. Se houver retorno incerto do deploy, reconciliar versão publicada antes de repetir. Rollback editorial repromove snapshot anterior; não reverte carteira, pedidos ou estoque.

Preview de rascunho é autenticado e no-store, acessível a revisores autorizados. A URL visual pública atual nunca recebe rascunhos privados. Manter biblioteca compartilhada de blocos/renderização e comparar preview com o snapshot real. Ao implantar CMS, também concluir rotas editoriais /pt/ e /en/, artigos e metadados individuais; views atuais por hash não são arquitetura SEO final.

Functions gerenciadas SWA são HTTP-only. Publicação inicial é explícita com outbox/job persistente e retomada manual segura. Agendamento só fica ativo com executor comprovado. GitHub Actions pode ser executor editorial de melhor esforço, mas seu cron pode atrasar/ser descartado e roda na branch padrão; painel precisa mostrar atraso/falha. Publicação em horário garantido exigirá outra solução e orçamento. Worker de entrega de recompensa é separado do build editorial. [Limites SWA](https://learn.microsoft.com/en-us/azure/static-web-apps/apis-functions), [agendamento GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

Campanhas expiradas e live com validade precisam ser filtradas também na renderização de dados publicados para não depender só de um rebuild pontual. Remoções urgentes exigem republicação/invalidação e verificação; botão desativar não promete desaparecimento enquanto o artefato anterior estiver servido.

## Mídia e custo

SQL guarda metadados, não vídeos/binários. Planejar Azure Blob Storage com rascunhos privados e derivados públicos somente após aprovação. Upload autorizado por tempo curto, limitado por tamanho/tipo, detecção pelo conteúdo, nomes gerados, quotas e validação; nunca publicar arquivo só por extensão. Restringir SVG/HTML e tratar transformação de imagem em worker apropriado, não operação longa na API HTTP. Lixo/drafts não podem se tornar URLs públicas por enumeração.

MVP usa imagens otimizadas e vídeos/lives nas plataformas existentes por URL/embed. Hospedar originais de vídeo e transcodificar no Azure ficam fora do escopo inicial. Créditos/licenças e alt são campos de primeira classe. Remover mídia exige verificar snapshots publicados e referências; não quebrar artigo antigo ao apagar arquivo.

R$150/mês permanece teto de infraestrutura/ferramentas informado, não estimativa garantida de toda operação. Estoque/frete e anúncios pagos são orçamento separado. SQL free-offer requer elegibilidade e modo de pausa confirmados; Blob, egress, jobs, CI privado e telemetria também precisam ser medidos. Nenhum gasto novo nesta fase. Sem conexão de quota/receita, painel mostra indisponível. Conteúdo estático continua disponível se SQL pausar; admin e operações privadas apresentam503 e não inventam sucesso. [Oferta Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer?view=azuresql).

## Acesso e integridade

Papéis: proprietário, editor-chefe/publicador, autor, tradutor, comercial, operador de recompensas, suporte e analista. Uma pessoa pode acumular papéis; permissões são por ação/objeto/ambiente. Autor não publica por padrão; comercial não altera pontos; suporte não exporta endereços em massa; analista vê agregados. Proprietário atribui papéis com auditoria. Reautenticação/MFA para acesso administrativo conforme provedor verificado, sem presumir que login Microsoft por si prove essa proteção.

API verifica sessão, ownership, papel, versão e estado em toda ação. RBAC visual só organiza a tela. Mutações com proteção CSRF/Origin, limites de corpo/taxa e idempotência onde necessário. Segredos no servidor; mudanças sensíveis com motivo e trilha append-only. Exportação privada controlada/temporária, registro de acesso e retenção limitada. Usuário IA recebe escopo mínimo e propõe mudanças; não recebe owner nem credenciais de produção.

Não existe endpoint genérico de UPDATE ledger/saldo. Ajustes usam comandos com justificativa, limites e lançamentos compensatórios. Estoque é movimentação auditada com reserva atômica. Rollback do site não apaga auditoria ou resgates. Dados de entrega, códigos digitais e detalhes de contas não entram no RAG ou prompts para IAs externas.

## Relatórios úteis ao negócio

Separar alcance, retorno e resultado financeiro. Definições explícitas de visitante ativo, retorno7/30dias, conteúdo salvo, quiz concluído e missão validada. Primeiro medir com uma fonte confiável e consentimento/finalidade definidos; não instalar vários trackers.

Comercial: campanha/placement/período, exposição/clique quando realmente coletados, receita informada versus confirmada versus recebida e custos. Loja externa só importa pedidos por integração autorizada ou arquivo conciliado; não considerar clique como venda. KP: emitidos, disponíveis/reservados/consumidos, catálogo financiado, custo efetivo por resgate incluindo frete, fraude observada e retenção da coorte. KP não tem conversão fixa em reais presumida.

Começar por dados operacionais existentes; relatórios analíticos avançados vêm após coleta consistente. Gráficos mostram lacunas e origem, nunca testemunhos, conversões ou ROI sintéticos. Motor de recomendações/experimentos só depois de dados suficientes e sem premiar cliques publicitários.

## Execução por fases e critérios de saída

| Fase | Entrega | Critério de conclusão |
|---|---|---|
| 0 — Contratos e desenho | Sitemap do admin, protótipo navegável das3tarefas, RBAC, modelos, OpenAPI, spike editor/Refine/auth/SQL/mídia e orçamento | Riscos/limites confirmados; uma fatia vertical autenticada funcionando em homolog, sem pontos reais. |
| 1 — Fundação | apps/admin, shell, sessão/papéis, auditoria, tabelas/formulários reutilizáveis, flags e estados de erro | Testes de acesso por papel/objeto, teclado e ambiente; usuário não autorizado recebe negação na API. |
| 2 — CMS operacional | Conteúdo, mídia, PT/EN, fontes, revisões, blocos da home, preview e publicação | Proprietário publica uma descoberta sem editar arquivos; falha de build mantém versão anterior; rollback ensaiado. |
| 3 — Operação editorial/comercial | Eventos, lives, ofertas/Gumroad, afiliados, placements, campanhas e executor de agendamento se validado | Evento e campanha publicados/encerrados com verificação; diferenças de salvar/publicar e limites do cron visíveis. |
| 4 — Comunidade e KP | Contas, suporte, quizzes/missões, carteira, catálogo financiado, reservas e despacho | Testes reais do adaptador SQL: última unidade, replay, cross-account, cancelamento, entrega incerta e restore; piloto fechado antes de resgates públicos. |
| 5 — Relatórios e integrações | Dados operacionais, importação conciliada, painéis comerciais/retorno, exportações e alertas | Cada indicador tem origem/definição; erro de integração não se transforma em zero; dados privados protegidos. |
| 6 — Automação assistida | Rascunhos/tradução/SEO, sugestões de links, calendário e relatórios assistidos | Revisão humana e rastreabilidade; sem publicar automaticamente ou mudar estoque/saldo por saída de IA. |

Não prometer prazo fechado antes da fase0. Fases1–2 formam o primeiro CMS realmente utilizável; a plataforma completa é entrega progressiva, não uma única tela gigante. Paralelizar mídia/editor e eventos/comercial depois dos contratos, mantendo integração/revisão antes de avançar.

## Trabalho entre IAs

Consulta real desta etapa: Claude Code via CLI sem ferramentas, dois subagentes Codex (UX e arquitetura) e coordenação/revisão Codex. Gemini, Copilot, Meta, NVIDIA e Grok não foram consultados nesta etapa; dependem de acesso/modelo/canal verificado. Os papéis abaixo são plano de distribuição, não atividade já realizada.

| Participante | Responsabilidade planejada | Saída verificável |
|---|---|---|
| Codex coordenador | Arquitetura, contratos, integração, build/testes e release | PR por fatia, execução dos testes e URL de homolog |
| Claude Code | Domínio/API, migrações e revisão de integridade | Código/testes transacionais e revisão independente |
| Gemini | UX editorial, taxonomia, PT/EN e avaliação de descoberta | Protótipo/revisão com critérios e fontes |
| Copilot | Implementação localizada de formulários/listas e testes de integração | Patches pequenos contra contratos |
| Meta | Alternativas de linguagem, compreensão e atrito de navegação | Avaliação com cenário e problema observado |
| NVIDIA | Modelo identificado para revisão de schemas/edge cases ou avaliação em lote | Relatório reproduzível, com modelo e custo explicitados |
| Grok | Contestação de hipóteses de engajamento/comercial e casos adversariais | Hipóteses testáveis; fatos exigem fonte independente |

Não assumir equivalência de capacidade/licença entre marcas de IA; cada provedor passa por tarefa-piloto antes de receber código. Sem acesso, redistribuir a tarefa aos agentes disponíveis e registrar, sem bloquear o produto. Usar no máximo2–3 frentes de implementação simultâneas, um responsável por arquivo/módulo, contratos estáveis e branches isoladas; não duplicar o mesmo módulo em seis provedores.

Ciclo: especificação curta → contrato/schema → implementação → revisão por outro agente → testes → preview → integração. Prompts incluem objetivo do site, limites, escopo e arquivos permitidos; contexto via RAG restrito. MCP de conhecimento e documentação continuam somente leitura; eventual MCP de operação recebe ferramentas allowlist de rascunho/validação, sem SQL arbitrário ou permissão de publicar por padrão. Não instalar um MCP por marca de IA se a integração oficial existente resolver a tarefa. Não criar automações recorrentes/pagas nesta etapa.

Claude destacou risco de escopo/manutenção e separação dos dois tipos de loja. Adotado. Sua sugestão de Function Timer dentro do backend gerenciado foi rejeitada pelos limites oficiais HTTP-only; inferências de que qualquer CMS externo seria inviável e de custo/licença zero também não foram adotadas. A decisão foi por aderência ao projeto, não por votação entre IAs.

## Próxima entrega proposta

Protótipo do admin com dados claramente demonstrativos e três fluxos completos de UX: publicar PT/EN, operar recompensa e configurar campanha/evento. Em paralelo, spike privado de sessão + SQL + um rascunho persistido + snapshot + publicação. Nenhum menu deve parecer operacional antes da API correspondente; módulos futuros terão escopo/status explícitos. A aceitação do plano não equivale a ativação de produtos pagos, integração de contas de terceiros ou pontos resgatáveis.
