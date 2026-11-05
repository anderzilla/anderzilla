# Área do jogador — implementação, testes e revisão

05/11/2026. Plano revisável, **nenhuma mudança de app/API/deploy é autorizada como já concluída por este arquivo**. Pedido atual é planejamento/documentação. Fontes: [produto](../strategy/MEMBER-AREA.md), [UX](../strategy/MEMBER-AREA-UX.md), [segurança/API](../strategy/MEMBER-AREA-SECURITY-API.md), [inventário anterior](AUTHENTICATED-FEATURES-20261105.md).

## Estado observado e correções necessárias

### Delegação de implementação

O proprietário pediu que o Antigravity execute o código e o Codex valide depois. Prompt canônico: [ANTIGRAVITY-MEMBER-AREA.md](../ai/prompts/ANTIGRAVITY-MEMBER-AREA.md). Delegação prevê branch isolada, cinco lotes e relatório reproduzível; não inclui publicação em produção antes da revisão. Esta referência não comprova que o Antigravity já executou o trabalho.

Publicação posterior foi autorizada pelo proprietário condicionada à validação aqui da versão exata. Prompt separado: [ANTIGRAVITY-MEMBER-AREA-RELEASE.md](../ai/prompts/ANTIGRAVITY-MEMBER-AREA-RELEASE.md). Não é autorização para antecipar deploy antes do gate, ativar KP sem regras/cobertura aprovadas ou declarar publicação sem evidência real.

| Evidência no código atual | Diferença para a decisão nova | Trabalho |
|---|---|---|
| HubProvider usa guestPlayer/localStorage para saved/opened/interests | Visitante ainda tem recursos agora exclusivos | Remover escrita/leitura/contadores anônimos e limpar legado; manter somente preferências públicas permitidas |
| Nome e Seu Radar apontam #profile; ProfilePage mistura blocos | Não existe separação painel/perfil nem menu pedido | Rotas/painel/menu/retorno pós-login e aliases |
| capabilities.rewards=false no Clerk e frontend | KP não está integrado para membros | Adaptador autenticado, regras, testes e feature gates; não só flag |
| Router nativo tem challenge/evidence e pending visitante | Pode reintroduzir fluxo sem conta | Exigir membro desde desafio/evidência; não reutilizar principal=None |
| pendingToken persiste em sessionStorage sem dono | Pode sobreviver à troca de usuário | Pendência server-side com dono; limpar legado; verificar autorização em todas as etapas |
| refresh e loadMore podem aplicar resposta sem validar geração da sessão | Resposta A pode repovoar UI após saída/entrada B | sessionEpoch+abort, cache por dono e testes de resposta atrasada |
| PATCH profile substitui listas JSON completas | Concorrência e limite1000 | Coleções versionadas/paginadas; migração aditiva e operações por item |
| changeLanguage chama save sem aguardar navegação | Preferência pode não persistir | Esperar confirmação ou decisão explícita de continuar sem salvar |
| Cópias “progresso neste navegador/sem conta” e KP legado | Texto/promoção contradizem gate novo | Revisar todos os CTAs, footer, quizzes, passaporte, salvo e carteira |
| services/rewards é referência local separada | Não prova integração cloud/ledger único | Reconciliar domínio/invariantes, sem implantar segunda carteira |

Esses pontos são observações de código para correção, não afirmação de exploração de produção ou vazamento comprovado.

## Ordem de entrega e dependências

### Lote1 — fronteiras e contratos

Implementar autorização central de membro, proteção de todos os endpoints atuais/propostos e remoção de geração anônima de progresso/pendência. Fixar sessão/caches/abort. Definir matriz editorial pública vs privada e validar artefatos exportados. Disponibilizar capacidades por feature sem dados pessoais.

Aceite: nenhuma ação privada persiste para visitante; A nunca lê/altera B; logout/expiração remove dados; fonte pública não contém payload privado. Só depois habilitar novas leituras pessoais.

### Lote2 — navegação, dashboard e perfil

Criar estrutura estática e guardas, menu/avatar, saldo neutro enquanto desligado e link Seu Radar correto. Separar Perfil de dashboard, compatibilizar links antigos, retorno pós-login seguro e estados por bloco. Aplicar manual visual PT/EN.

Aceite: login comum abre dashboard; intenção explícita retorna à ação; cadastro incompleto passa por onboarding; Perfil só por link/menu; mobile/teclado sem flash de dados.

### Lote3 — coleções pessoais e Radar

Migrar persistência para comandos consistentes, salvar/remover mochila, editar interesses, filtrar Radar e registrar/limpar exploração. Paginação, conflito entre dispositivos, conteúdo indisponível, exportação/exclusão integradas. Nenhuma migração de visitante silenciosa.

Aceite: persistência após reload/login em segundo dispositivo, sem vazamento após troca; nenhuma alteração salva por mensagem otimista sem confirmação; transição idioma confirmada.

### Lote4 — missões, KP e carteira

Integrar domínio à identidade Clerk completa, uma carteira autoritativa, desafio/evidência/claim idempotentes, extrato e recibos. Aprovar regras de missão, limites e cobertura do programa antes de ativar. Sem prêmio/estoque fictício. Se regras/economia não estiverem aprovadas, publicar UI privada informativa, mantendo concessões desligadas.

Aceite: missões reais determinísticas no piloto, zero crédito duplicado em concorrência/retry, zero saldo negativo, autoria de toda tentativa, reconciliação ledger-wallet e consulta de resultado incerto. Saldo no topo e dashboard deriva da mesma carteira.

### Lote5 — operação e liberação

Fechar recuperação, reautenticação, exclusão pendente e tratamento de saldo/reserva futuro, suporte, limites/cold start, logs privados e backup/restauração. Ensaiar rollback que preserve dados confirmados. Feature→homolog privada→produção com mesmo artefato validado e configurações de ambiente correspondentes. Nenhum plano pago ou mudança de DNS necessária por suposição.

## Cenários de teste obrigatórios

| ID | Cenário | Resultado exigido |
|---|---|---|
| A01 | Anônimo chama diretamente cada endpoint privado com/sem Origin forjado |401 em origem permitida;401/403 fail-closed em origem inválida, zero dados/efeitos; Origin não substitui sessão |
| A02 | Clerk válido sem CPF/onboarding tenta mochila/carteira/desafio |403 onboarding_required; só onboarding próprio disponível |
| A03 | JWT vencido, emissor/azp errado, sessão revogada, conta suspensa/deletada | Negação server-side e limpeza de UI; nenhum fallback guest pessoal |
| A04 | Conta A usa IDs/cursor/attempt/pending/receipt de B |404/negação indistinguível, zero leitura ou mutação de B |
| A05 | A request lento → logout → B entra → resposta A chega | Nenhum dado de A aparece; paginação/otimismo também descartados |
| A06 | Voltar histórico/bfcache, múltiplas abas, offline após saída | Não restaurar DOM/cache pessoal; revalidação e sinal de invalidação |
| A07 | HTML/out/RSC/bundle/search/sitemap/OG/cache e observabilidade | Sem dados pessoais, secrets, gabaritos privados ou URLs assinadas |
| A08 | Artigo salvo perde publicação/direito | API não revela metadata restrita; entrada genérica removível |
| A09 | Perfil/flags públicas/params tentam atribuir plano, saldo ou papel | Rejeição; nenhuma escalada de privilégio |
| N01 | Login direto, ação em artigo, onboarding incompleto e retorno externo malicioso | Dashboard por padrão; intenção válida confirmada; redirect externo recusado |
| N02 | Menu avatar, Seu Radar e chip KP em PT/EN/mobile/teclado | Destinos corretos, foco/labels, KP indisponível não vira0 |
| N03 |320px,200% zoom, leitor, redução movimento, nomes longos e empty states | Sem corte/overflow, contraste e ações compreensíveis |
| P01 | Salvar/remover repetido e concorrente, desfazer com falha | Sem duplicata, estado reconciliado e mensagem verdadeira |
| P02 | Temas editados em2 abas; navegação durante save de idioma | Conflito tratado, nenhuma sobrescrita silenciosa/cancelamento oculto |
| P03 | Radar sem temas/sem resultado e conteúdo fora do tema | CTA claro; nenhum falso “personalizado”, filtro não grava interesse |
| P04 | Exploração abrir/reabrir, limpar e evento anterior chega atrasado | Registro deduplicado, limpar só histórico; evento de geração antiga não repovoa, abertura posterior válida registra; nenhum crédito por abertura |
| P05 | Coleção >1000, cursor inválido, mesmo timestamp, categoria retirada | Paginação estável, limites explícitos, sem vazamento ou perda silenciosa |
| K01 | Anônimo/tentativa visitante legado em todas as etapas de missão | Sem início/evidência/pendência/claim sem membro completo |
| K02 | Duas claims simultâneas, duas chaves mesma ocorrência e replay | Um completion/efeito líquido; mesmo recibo ou conflito seguro |
| K03 | Mesma chave com payload diferente; hash/missão/award falsificados |409/negação; cliente nunca decide valor ou aprovação |
| K04 | Commit confirmado, resposta perdida inclusive sem operationId; reload/nova aba/novo login | Consulta pela chave anterior ou tentativa própria devolve resultado; sem conceder novamente/estornar sozinho; rascunho não enviado não é prometido |
| K05 | Tentativa ou pendência de confirmação expira, missão pausa/regra muda, cobertura esgota ou elegibilidade é revogada | Relógio servidor; reserva consumida/liberada uma vez; pausa de novos preserva confirmação coberta; manutenção tem regra de prazo/revisão; nenhuma promessa impossível |
| K06 | Falha entre completion/ledger/wallet e saldo insuficiente futuro | Rollback atômico e invariantes preservadas |
| K07 | Programa desligado, banco frio, limite/cold start ou429 | Sem saldo fake, sem polling infinito, retry limitado e nenhuma concessão local |
| K08 | Migração/rollback e reconciliação de extrato | Histórico confirmado preservado; uma carteira, nenhuma soma demo |
| K09 | Contas diferentes competem pelo último envelope/quota da campanha | Limite global respeitado; nenhuma pendência elegível sem reserva; mesma reserva não é consumida e liberada |
| O01 | Exportar/excluir depois das novas coleções e tentativa pendente | Somente dados próprios; limpeza/retencão consistente; sem apagar provas indevidas |
| O02 | Exclusão após >5min e falha no fornecedor | Reautenticar retorna à confirmação; acesso bloqueado, pendência recuperável |
| O03 | Telemetria/referer/URL/log/erro técnico | Sem CPF, token, respostas, preferências ou dados de outra conta |
| O04 | Missão publicada ou feature ligada antes de regras/cobertura/aceite | Gate impede ativação; nenhum CTA promete benefício inexistente |

Testar domínios reais de homolog e navegador de verdade para CORS e SDK; mocks não provam isso. Testes automatizados devem exercitar invariantes/concorrência, não apenas copiar implementação. Build apps/web obrigatório quando houver código tocado; nesta entrega documental não há novo build/deploy a alegar. Preservar corpus editorial e mídias em qualquer release.

## Checklist de revisão da documentação

- [x] Decisão nova referenciada em contas, backend e KP, sem regra anônima antiga com aparência vigente.
- [x] Cada função tem entrada, sucesso confirmado, vazio, falha, retry/consulta e saída.
- [x] Menu/destinos distintos: dashboard, perfil, Radar, exploração, KP, carteira e missões.
- [x] Nenhuma mensagem promete gravação/crédito/revogação antes de prova.
- [x] Identidade, autorização de conteúdo, propriedade de registro e feature gate são camadas separadas.
- [x] API alvo explicitamente proposta; runtime atual não descrito como já ampliado.
- [x] Valores de KP/catálogo/pagamentos/menores não ativados por documentação.
- [x] Limpeza de sessão cobre requests atrasados, abas, bfcache, paginação e tokens pendentes.
- [x] Manual visual e acessibilidade aparecem como critérios verificáveis, não apenas “estilo gamer”.

## Revisão final desta entrega documental

Revisão independente somente leitura por dois agentes, nos papéis canônicos anderzilla-reviewer/backend e anderzilla-frontend/reviewer, seguida de nova checagem após correções. Nenhum teste exploratório de produção nem implementação foi feito nesta etapa.

- Corrigidos: resposta antiga de sessão; retomada sem operationId recebido; reserva atômica de cobertura global; eventos antigos após limpar histórico;403 de seção vs bloqueio da conta; resultado incerto vs falha definitiva; crédito histórico vs saldo disponível; expiração de pendência; rascunho de quiz não persistido; Tab sem focus trap; mensagem de saída restrita à sessão atual; remoção de promessa de ativação KP.
- Ambos os revisores encerraram sem bloqueio documental restante nos respectivos escopos. Isso não aprova economia/estoque, prova segurança do código futuro ou substitui testes de homologação.
- Checklist acima revisado integralmente nesta entrega. Pendências de decisão antes de ativar KP: valores/regras/limites de missões e cobertura; retenção por finalidade; encerramento com saldo/reserva/pedido; procedimento de atendimento e revisão. Não é necessário escolher planos pagos para implementar o desenho.
- Artefatos de produto, UX, segurança e aceite constituem a fonte para a próxima IA; execução deve registrar commits, testes e ambientes reais por lote.
