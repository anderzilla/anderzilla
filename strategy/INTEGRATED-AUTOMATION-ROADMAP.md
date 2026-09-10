# Desenvolvimento integrado Azure + Google — 10/09/2026

Estado: plano de execução e ferramentas locais; nenhum novo serviço cloud ou agendamento ativado por esta entrega. Azure continua responsável pelo portal/CMS. Google usa exclusivamente player.one@anderzilla.com e projeto explicitamente confirmado. Créditos, validade e cotas precisam de consulta antes do primeiro deploy. Teto de planejamento R$150/mês; não assumir que crédito amplie esse teto.

## Fases e gates
| Fase | Entrega | Critério de aceite | Dependências |
|---|---|---|---|
| 0 — inventário e contratos | Confirmar versões do CMS, provedores, credenciais por canal, direitos de mídia, orçamento e fontes; catálogo de processos | Cada integração tem responsável, estado verificado, escopo OAuth e custo; contrato versionado e testes de autorização | Nenhuma implantação |
| 1 — controle no CMS | Processos, execuções, conectores, fontes, auditoria, agenda e orçamento; executar/pausar/cancelar/reexecutar | Duplo clique e redelivery executam efeito uma vez; usuário sem papel não aciona processo; falha Google não derruba leitura do portal | 0 |
| 2 — conteúdo e SEO | Fontes cadastradas -> pauta -> rascunho PT/EN -> revisão -> publicador Azure; auditor técnico | Fonte/data/direitos em cada rascunho; publicação e sitemap verificados; zero publicação automática por padrão | 1 |
| 3 — ofertas e lives | Ofertas reais, links identificados, overlays OBS, agenda e eventos de plataformas | Overlay funciona sem credenciais no navegador; desativar campanha remove oferta; eventos duplicados não duplicam métricas | 1 |
| 4 — fábrica de cortes | Upload retomável, validação, transcrição, sugestão de cortes, render, legendas e aprovação | Vídeo próprio completa pipeline; progresso/cancelamento/retenção testados; custo por minuto conhecido | 1 + armazenamento aprovado |
| 5 — relatórios | Semanal, mensal, intervalo personalizado, comparação, CSV e snapshots | Totais reconciliados com origem; fuso, moeda, atraso e cobertura visíveis; relatório vazio não inventa receita | 2–4 |
| 6 — pós-venda e expansão | Webhooks de pagamento, benefícios, experimentos de ferramentas IA; Points só após integração transacional | Assinatura do webhook, estorno, replay, saldo/estoque concorrente e revogação testados | Receita/demanda medidas + 1 |
| 7 — operação contínua | Alertas, filas mortas, restauração, limites e revisão de custos | Simulação de indisponibilidade, token expirado e cota esgotada; recuperação documentada | Todas as anteriores |

Executar por pequenos incrementos em feature -> homolog -> produção. Cada fase exige evidência de teste e revisão independente; duração será estimada após inventário. Não prometer implementação de toda a plataforma nesta entrega documental.

## Arquitetura e ferramentas a implementar
CMS/API Azure é fonte de verdade para configurações, permissões, runs e aprovação. SQL existente exige avaliação de consumo antes de aumentar carga. Transação grava run + outbox; dispatcher entrega comando autenticado à fila Google; workers gravam resultados privados no Google; dispatcher Azure busca resultados autenticados e os aplica à inbox. Sem escrita direta de worker no banco CMS. Inbox/outbox únicas por event_id; run_id, correlation_id e idempotency_key atravessam logs, eventos e relatórios. Entrega at-least-once, efeitos idempotentes, não promessa de exactly-once na rede.

Cloud Run Services para APIs rápidas; Jobs para renderização/transcrição por lote. Pub/Sub ou Cloud Tasks após avaliar ordem/retry e custo, Scheduler para tick de agenda; escolher um mecanismo de despacho por workflow. Estado durável em SQL e objetos em bucket privado, nunca disco efêmero do container. Upload direto via URL assinada curta emitida após autorização CMS; objetos passam por quarentena, inspeção real de formato, limites, malware e direitos antes de processar. Sem proxy de vídeos pelo Azure ou banco SQL.

Service identities distintas por ambiente/workflow, menor privilégio, segredos em cofre e rotação. Federação de identidades Azure->Google quando suportada pelo executor escolhido; validar emissor/audiência/expiração e replay. Não confiar em headers de identidade SWA recebidos diretamente de origem pública. Não expor endpoints administrativos de execução sem autenticação. CORS não autentica. Rotas health não revelam segredos.

Implementar adapters de plataforma, provedor IA, storage, filas, eventos e observabilidade atrás de contratos. Timeouts, retries exponenciais limitados com jitter, dead-letter, cancelamento cooperativo e circuit breaker por origem. Políticas e limites são código determinístico; IA sugere textos/trechos, nunca decide saldo, pagamento, permissões ou autopagamento. Não criar um LLM permanente por serviço.

Ferramentas locais desta fase: ai/automation/planner.py e seu catálogo WORKFLOWS validam pedidos e produzem planos sem executar. MCP de conhecimento existente permanece somente leitura; futuro MCP operacional exporá list_processes/get_run/create_draft/request_run/cancel_run/get_report com as MESMAS permissões e auditoria da API, sem SQL/shell/URL arbitrários. Não conectar MCP operacional até existir API autenticada testada.

## Agentes operacionais propostos
- Coordenador: transforma ações/agenda CMS em runs versionados e controla dependências.
- Conectores: consulta APIs/RSS autorizados, cursores e limites; não contorna login ou coleta proibida.
- Editorial: sugere pautas/resumos com fontes; PT/EN revisados por humano.
- Mídia: executa estágios de cortes, armazena artefatos e metadados de direitos.
- Comercial: verifica campanhas aprovadas, validade/preços com timestamp e disclosure; não inventa parceiros.
- SEO: audita artefato público, links, metadados e indexação, gera tarefas de correção.
- Analista: agrega evidências por período e moeda, separa cliques de conversões confirmadas.
- Controle: monitora fila, saúde, custos, credenciais e atrasos; alerta com deduplicação, sem upgrades automáticos.
Esses papéis são definições para desenvolvimento, não daemons instalados.

## Multi-IA para desenvolvimento
Coordenador Codex controla interfaces, integração e evidências. Delegar backend/contratos, CMS UX, mídia, SEO e revisão a agentes com arquivos exclusivos. Autor do módulo não é o único revisor. Claude pode revisar decisões com briefing sanitizado; Gemini/Copilot/Meta/NVIDIA/Grok são opcionais apenas após comprovar acesso, termos e custo. Não há obrigação de chamar todos: rotear por competência/custo e registrar modelo real, entrada sanitizada, saída e decisão. Nenhum provedor externo recebe credenciais, dossiê completo ou dados pessoais. Acesso indisponível vira pendência explícita, não execução fictícia.

## Agendas sugeridas, ainda desativadas
Fontes a cada 6h; links comerciais diariamente; status de live por webhook quando disponível e polling limitado durante janela configurada; saúde a cada 5min só para serviços ativados; SEO após publicação + semanal; relatório semanal segunda 09h e mensal dia 1 09h America/Sao_Paulo. Custom sob demanda. Deduplicar período+workflow+versão, permitir backfill, registrar atraso. Ativar somente depois do gate da fase, com controles no CMS e custo observado.

## Orçamento e sucesso
Envelopes propostos dentro de R$150: R$30 execução/filas; R$30 storage/tráfego; R$40 inferência; R$50 reserva. São alocações, não preços ou garantia. Reavaliar se teto inclui assinaturas pessoais. Min instances 0 para serviços sob demanda; começar max 1 e concorrência medida; cotas de vídeos/minutos/tokens por dia e usuário. Alertas de orçamento não são teto rígido: ledger de reserva antes do job e reconciliação posterior bloqueiam novos pedidos quando envelope se esgota; considerar atraso da fatura. Não usar GPU inicialmente.

Métricas: margem confirmada por campanha, receita líquida após estorno, custo por conteúdo/corte, conversão onde rastreável, retorno de usuários, impressões/cliques orgânicos e tempo editorial economizado. Sem garantia de ranking ou faturamento.

## Especificações vinculadas
- AUTOMATION-CMS-CONTROL.md: UX, APIs, dados e relatórios.
- CROSS-CLOUD-SEO.md: entregas SEO e critérios verificáveis.
- ../ai/automation/README.md: ferramenta local de planejamento.
