# Karaca Points e Store Points

Direção autorizada pelo proprietário: identidade **Karaca!**, pontos ganhos no site e usados exclusivamente na Store Points. Produtos fornecidos pelo proprietário. Sem compra de pontos ou checkout em dinheiro. Assinaturas, produtos digitais e gadgets são categorias planejadas, não estoque confirmado.

## Implementado no playtest 04

Rotas #points e #store, CTA na home, carteira demonstrativa, extrato, missões e categorias da loja em PT/EN. Uma missão concede 25 KP demo por selecionar três interesses; outra concede 100 KP demo por concluir corretamente o quiz. Cada missão concede uma única vez, inclusive após recarregar. Repetir quiz não acumula. Limpar dados locais limpa também os pontos. Valores são hipóteses de UX, não tabela definitiva. LocalStorage não é segurança: a demonstração pode ser adulterada, não concede direitos, não migra saldo para produção e não aceita resgates reais.

## Estrutura para produção — a implementar

Autenticação e API autoritativa obrigatórias antes de pontos resgatáveis. O cliente nunca informa saldo, valor de recompensa, elegibilidade ou resultado definitivo de quiz. Não premiar cliques em publicidade, compras afiliadas ou simples recargas. Validar participação editorial por atividade verificável; não afirmar que abrir uma página prova leitura. Missões versionadas, limites por conta e janela temporal, revisão de comportamento automatizado e canal de contestação. Começar por missões educativas determinísticas; sem sorteios ou prêmios aleatórios nesta especificação.

Modelo de dados:
- accounts: id, identidade autenticada, estado, país elegível quando necessário.
- missions: id, version, condições verificáveis, awardKP inteiro positivo, janela, limite, estado.
- completions: accountId, missionVersion, occurrenceKey, evidenceRef, verifiedAt; chave única dos três primeiros impede repetição.
- ledger: id, accountId, deltaAvailable, deltaReserved, reason, referenceId, idempotencyKey único, createdAt. Append-only; correções por lançamentos compensatórios.
- rewards: id, traduções PT/EN, costKP inteiro positivo, tipo, região, termos, estoque disponível, estado draft/active/paused, versão. Ativar somente com produto e entrega confirmados.
- redemptions: id, accountId, rewardVersion, costSnapshot, estado, idempotencyKey único por conta, timestamps. Dados de entrega separados com acesso restrito. Códigos digitais nunca em catálogo público, logs ou Git.

Fluxo transacional: validar conta, produto ativo, região, saldo e estoque; reservar KP e uma unidade na mesma transação; criar pedido pending_review. Aprovação leva a fulfilling; confirmação de entrega consome reserva e leva a fulfilled. Rejeição/cancelamento antes da entrega devolve pontos e unidade exatamente uma vez. Falha de entrega fica em revisão, sem repetir emissão de código ou liberar estoque já entregue. Concorrência e retries não podem produzir saldo negativo, duplicar concessão ou vender duas vezes a última unidade. Cada transição registra ator e motivo. Idempotency key ligada ao hash do payload; reutilização com payload diferente deve falhar.

Contratos propostos: GET /api/points/wallet, GET /api/points/ledger com paginação, GET /api/missions, POST /api/missions/{id}/complete (evidência verificada no servidor), GET /api/rewards, POST /api/redemptions (rewardId + versão + idempotency key), GET /api/redemptions/{id}. Toda leitura de conta deriva a identidade da sessão, não de accountId enviado pelo navegador. Administração separada por papel, auditoria e autenticação reforçada; nunca conceder papel por interface cliente.

## Operação e sustentabilidade

Antes de ativar catálogo: proprietário define produto exato, licença e possibilidade de transferir, duração e região da assinatura, unidades, custo total incluindo envio, cobertura geográfica, prazo de entrega e suporte. Não presumir que assinaturas pessoais existentes possam ser revendidas ou transferidas. Não assumir renovação automática. A UX final precisa mostrar condições antes de confirmar. Regulamento, privacidade, idade/elegibilidade e mercados precisam de revisão própria antes do lançamento; este documento não determina enquadramento jurídico.

Manter orçamento de recompensas separado do teto de infraestrutura de R$150/mês. Nenhuma compra autorizada por esta implementação. Definir envelope de recompensas com estoque financiado antes de emitir pontos reais. Medir custo por usuário retido, passivo de pontos, taxa de resgate e margem observada; ajustar apenas regras futuras de modo transparente, sem prometer prêmio ilimitado. Patrocínios podem financiar estoque quando contratados e identificados, sem parceiros presumidos.

Entrega incremental: (1) playtest local atual; (2) migrar UX aprovada para apps/web, conta/API/ledger persistente em homolog, sem saldo público; (3) testes transacionais e de autorização, catálogo privado e entrega manual ensaiada; (4) piloto limitado com estoque real e regras publicadas. Backend Azure e banco ainda não provisionados; validar plano, capacidade, custo e integração com Static Web Apps antes de escolher serviços. A documentação é preparação, não implantação.

Critérios de aceite do backend: duas requisições simultâneas na última unidade; replay de conclusão e resgate; sessão de outra conta; saldo insuficiente; falha entre reserva e criação; cancelamento repetido; evento fora da janela; entrega falhando; ledger reconciliado; nenhum segredo em respostas. Build obrigatório de apps/web quando a migração tocar a aplicação.
