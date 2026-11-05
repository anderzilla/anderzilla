# Prompt de execução — Antigravity / área do jogador AnderZilla

Preparado em 05/11/2026. Código e evidências para revisão posterior no Codex. Este arquivo não comprova execução, aprovação final ou implantação.

---

Você será responsável por **implementar a área autenticada do AnderZilla**, seguindo integralmente a documentação canônica. Conclua os lotes de código, migrações preparadas, testes e relatório. Não entregue apenas plano, protótipo ou interface com dados fictícios. O Codex fará revisão independente depois; deixe tudo reproduzível no Git.

## 1. Divisão de responsabilidades

- **Antigravity:** frontend, backend, contratos, migrações aditivas preparadas, testes e documentação técnica. Integrar e revisar o próprio trabalho antes de devolver.
- **Codex:** validação posterior de aderência, segurança, fluxos, visual e evidências. Não afirme que essa revisão já aconteceu para seu código.
- **Proprietário:** decide regras/economia de KP e autoriza promoção após revisão. Não inventar valores, recompensas, estoque ou aprovação.
- Nesta execução, não fazer merge em develop/main nem publicar em produção. Não executar migrações cloud, mudar secrets/DNS/permissões ou criar recursos/planos pagos. Prepare scripts e homologação para execução posterior; valide localmente com fixtures sintéticas.
- Falta de decisão comercial ou acesso cloud não bloqueia todo o código: conclua partes independentes, mantenha a capacidade afetada desligada e registre a validação pendente. Não simule conclusão.

## 2. Fontes e preparação Git

Código: `G:/AnderZilla`. Documentação: `G:/AnderZilla-docs`, branch `codex/anderzilla-docs`. Z: em arquivos antigos é alias histórico; encontre o worktree real sem copiar o dossiê para o código.

1. Leia AGENTS.md, .anderzilla-docs-ref, status/log dos dois worktrees. Plano revisado no commit documental `4e213a2350bbb2ff09a03e2a0d5205f30f5fe337`; o ponteiro atual pode incluir este prompt em commit posterior. Confira conteúdo/ancestralidade; não faça downgrade.
2. Leia integralmente, na documentação:
   - DOSSIER.md, strategy/BRAND-AND-PRODUCT.md, operations/ACCESS-INVENTORY.md;
   - strategy/BRAND-MANUAL.md;
   - **strategy/MEMBER-AREA.md**;
   - **strategy/MEMBER-AREA-UX.md**;
   - **strategy/MEMBER-AREA-SECURITY-API.md**;
   - **operations/MEMBER-AREA-DELIVERY.md**, incluindo toda a matriz de testes;
   - strategy/ACCOUNTS-AND-ACCESS-PHASES.md, strategy/KARACA-POINTS.md, strategy/BACKEND-AND-DATA.md;
   - operations/REGISTRATION-PHASE1-20261104.md e operations/AUTHENTICATED-FEATURES-20261105.md para separar histórico e situação real;
   - papéis ai/agents/anderzilla-frontend.md, anderzilla-backend.md, anderzilla-brand.md, anderzilla-reviewer.md e respectivas skills canônicas.
3. Crie `codex/member-area-antigravity` a partir da implementação atual de cadastro, confirmando HEAD/base. Se existir, inspecione antes de reutilizar. Prefira worktree isolado. Não partir de main antigo e perder cadastro ou corpus recente.
4. Preserve alterações preexistentes nos dois worktrees. Não usar reset --hard, git clean, checkout destrutivo, git add . ou incluir arquivos alheios nos commits. Não limpar diretórios recursivamente para preparar ambiente.

Pedido atual/documentos MEMBER-AREA prevalecem sobre comportamento antigo de visitante. A indicação “planejamento, não implementar nesta entrega” dos documentos refere-se à entrega documental anterior; este prompt delega a implementação local. Restrições de privacidade, economia e publicação continuam vigentes.

## 3. Resultado obrigatório

Mochila, interesses, exploração, KP, carteira e missões oficiais exigem **sessão válida, e-mail confirmado e cadastro AnderZilla completo, adulto18+ e ativo**. Notícias e categorias públicas permanecem abertas. Sessão Clerk não equivale a cadastro completo, assinatura, compra ou administração.

- Login comum abre **dashboard em blocos**; onboarding incompleto vem antes. Intenção privada explícita pode retomar destino permitido com confirmação da ação.
- **Perfil separado:** nome, avatar, idioma, consentimentos, segurança, exportação e exclusão; acessível pelo menu/link autenticado.
- Nome/avatar abre menu: Painel, Seu Radar, Mochila, Interesses, Exploração, Karaca Points, Carteira, Missões oficiais, Perfil e Sair, conforme plano.
- **Seu Radar** abre lista de notícias pelos interesses declarados, nunca Perfil. Sem temas/resultados, oferecer escolha e alternativa pública identificada.
- **Saldo KP no topo**: disponível confirmado e link Carteira; desconhecido não vira0. Programa desligado tem estado neutro, sem “em breve” ou saldo fake.
- Dashboard: boas-vindas, Radar, KP/carteira, mochila, missão elegível/retomável, exploração e interesses; estados por bloco, sem CPF/e-mail desnecessário.
- Slugs/aliases, deep links, voltar/avançar, PT/EN, mobile, teclado e foco devem funcionar. Nenhum flash de dados durante verificação/saída/troca de conta.

## 4. Lotes — implementar todos

### Lote1: autorização e sessão

Guard central de membro completo em toda leitura/mutação privada, incluindo listas, tentativa, evidência, claim e resultado. Dono deriva da sessão validada no servidor, nunca de accountId/papel/saldo do cliente.

Remova funcionalidades pessoais de visitante em guestPlayer/localStorage, quizDone/claims/passaporte e pendingToken sem dono. Limpe legado sem importar dados anônimos/KP demo. Preserve só idioma/acessibilidade/consentimento público permitido.

Use geração da sessão/subject e AbortController para refresh, paginação, PATCH otimista, exportação, carteira e missões. Logout, A→B, expiração, suspensão/exclusão limpam DOM/store/caches/rascunhos e descartam respostas atrasadas. Cubra multiabas e bfcache.403 de elegibilidade de missão bloqueia aquela ação; não derruba a conta inteira.

### Lote2: dashboard, menu e Perfil

Implemente componentes/rotas completos do plano. Corrija redirects Clerk/onboarding hoje direcionados ao perfil. Menu disclosure com links normais, Tab, Escape e foco restaurado; sem role=menu incompleto/focus trap no dropdown. Retorno pós-login com allowlist interna; nenhum open redirect ou escrita silenciosa.

Mantenha portal Next exportado estaticamente. Shell pode ser genérico; dados privados nunca entram em HTML/out, RSC, índices, sitemap ou OpenGraph.

### Lote3: coleções e Radar

Implemente contratos com persistência por conta, paginação e conflito versionado; evite substituir listas concorrentes inteiras. Migração SQL aditiva, backfill por conta, compatibilidade e rollback preparados, sem execução cloud nesta etapa.

- Mochila: salvar/remover idempotentes, desfazer, busca/filtro, indisponibilidade sem metadata privada, reconciliação de resultado incerto.
- Interesses: escolher/cancelar/salvar, zero temas válido, conflito entre dispositivos; aguardar confirmação antes de navegar na troca de idioma.
- Radar: união dos temas e notícias mais recentes; filtro temporário não altera interesses; publicação/permissões e disclosure preservados.
- Exploração: primeira/última abertura confirmada, sem alegar leitura; limpar/remover com geração/versão que rejeite evento antigo em trânsito. Abrir conteúdo não concede KP.
- Integre coleções à exportação/exclusão. Não deixar listas legadas e modelo novo como fontes divergentes.

### Lote4: missões, KP e carteira

Integre identidade Clerk completa a uma única fonte de carteira/ledger. services/rewards é referência, não API cloud pronta nem segunda carteira. Não copiar challenge/evidence legados com principal=None; dono obrigatório desde iniciar até creditar.

Implemente desafio → evidência → pendência coberta → confirmação → receipt/extrato, com pausa, expiração, limites, validação negativa e recuperação. Servidor decide aprovação, valor, regra/versão/ocorrência, elegibilidade e prazo; nunca cliente.

Cobertura/quotas globais e individuais devem resistir à concorrência. Reserve cobertura ao validar pendência; consuma/libere uma vez. Completion, ledger, wallet, consumo e receipt são transacionais. Mesma chave/outro payload falha; mesma ocorrência/outra chave não duplica. Pausa de novas participações preserva pendências válidas cobertas conforme regra.

Resultado deve ser consultável por chave conhecida **antes do POST**, mesmo se operationId nunca chegou. Reload/login recupera tentativa/pendência/recibo pelo servidor; não prometer recuperar respostas ainda não enviadas nem guardar token privado em storage.

Regras/valores configuráveis, draft e feature desligada se não aprovados. Valores sintéticos exclusivamente em testes, nunca produto. Concluir código não depende de inventar orçamento/estoque. Resgates reais, pagamentos, assinaturas e lives ficam fora desta implementação; preserve contratos/limites futuros sem vitrine falsa.

### Lote5: acabamento e operação

Feche banco frio, offline, falha parcial, retry limitado, timeout antes/depois do commit, expiração, reautenticação de exclusão, exclusão pendente e perda de direito de conteúdo. Sem polling para manter banco desperto ou fila invisível de crédito offline.

Prepare scripts, fixtures exclusivas de teste, reconciliação ledger-wallet, rollback, flags e instruções de homologação. Arquivo preparado não prova worker/timer/pipeline instalado. Não publique produção nem ative KP real.

## 5. Visual, linguagem e segurança

- Manual obrigatório: Ghost original intacto, ANDER branco/ZILLA vermelho, navy/lime/pink, Oxanium/Space Grotesk, tokens/cards/espaçamento do manual. Sem redesign genérico ou métricas inventadas.
- PT/EN completos; gamer moderado. “Guardado na mochila”, “Radar ajustado. Bora descobrir?”, “Ainda não conseguimos confirmar essa mudança. Vamos conferir?”. Não exibir erros literais, SQL/token/servidor, culpar usuário/site ou prometer gravação/crédito sem confirmação.
- Meta WCAG2.2AA: foco, teclado/leitor, alvos44px,320px, zoom200%, contraste verificado e redução de movimento; não depender só de cor/emoji.
- Esconder card não protege API/mídia. Permissões antes de devolver metadados restritos. Login não concede plano/compra/canal. Não implementar perfil público/ranking por suposição.
- APIs privadas no-store, cache em memória por dono/geração. Sem dados pessoais em logs/analytics/RAG, secrets/CPF em Git, token em URL ou service worker com dados privados. Não copiar configurações/banco reais para testes.
- Preserve Clerk/CORS, X-AnderZilla-Authorization e inclua PUT/DELETE/cabeçalhos de versão/idempotência usados.204 isolado não comprova preflight funcional.
- Sem backend híbrido no portal, novos serviços pagos, troca de provedor ou alteração de ForgeKit/corpus/mídias/CodeMatrix. Nunca desabilitar TLS/autorização para obter teste verde.

## 6. Testes e evidências

Exercite integralmente operations/MEMBER-AREA-DELIVERY.md. Mapeie **cada ID A01–A09, N01–N03, P01–P05, K01–K09, O01–O04** a teste/evidência/resultado. Não executado = pendente com motivo, não aprovado por existir um teste.

Cobrir anônimo/incompleto/suspenso/excluído; token inválido/revogado; A usando recursos/cursores/tentativas/recibos de B; resposta A depois de B entrar; bfcache/multiabas; conteúdo perde acesso; conflito/paginação; evento antigo após limpar; replay/claims concorrentes; contas disputando última cobertura; resposta perdida sem operationId; expiração/liberação única; falha entre operações transacionais; exportação e exclusão segura.

Execute suítes existentes relevantes identity/rewards, testes novos significativos, typecheck e **npm run build em apps/web**. Registre comandos/ambiente/exit code/resumo. Audite dependências alteradas; explique problemas materiais. Execute navegador local PT/EN, desktop/mobile e teclado, com backend/fixtures de teste. Separe claramente mock/local de SDK/e-mail real/CORS e cloud ainda não exercitados. Não usar produção ou conta real do proprietário para testes destrutivos.

Não marcar pronto porque botão existe, mock passou ou build gerou páginas. Não remover testes relevantes nem esconder falha no relatório.

## 7. Handoff para o Codex

Crie **docs/MEMBER-AREA-IMPLEMENTATION-REPORT.md** no código, sem PII/secrets, contendo:

1. Branch/base/HEAD, hash documental usado e commits por lote.
2. Matriz requisito → arquivo/rota/API/migração → teste/evidência → implementado/testado/pendente.
3. Contratos realmente implementados e diferenças justificadas do plano; não mudar requisito silenciosamente.
4. Comandos/resultados e screenshots PT/EN desktop/mobile, inclusive vazios/erros/foco, com dados sintéticos identificados e caminhos dos artefatos.
5. Migrações/backfill/compatibilidade/rollback/reconciliação/flags: distinguir preparado de executado. Sem URLs de pacote assinadas ou configurações privadas.
6. Como iniciar localmente, usar identidades sintéticas, simular falhas e repetir testes de acesso/concorrência. Credenciais de fixture não podem funcionar em cloud.
7. Pendências/riscos por severidade, separando falta de código, falta de teste cloud e falta de regra comercial.
8. Ambientes alterados. Esperado: local/teste; produção não alterada; nenhum KP real ativado.

Atualize documentação canônica apenas no escopo da entrega e preserve mudanças alheias. Se alterar documentos, publique primeiro o commit na branch documental correspondente; só então fixe esse hash em .anderzilla-docs-ref e publique a branch de código. Não entregar ponteiro para commit que só existe na sua máquina. Se push documental estiver bloqueado, preserve commits, informe IDs e mantenha no código a última referência documental publicada até resolver. Commits explícitos por lote. Faça push da branch de implementação se remoto disponível; se bloqueado, preserve commits locais e explique. PR opcional deve ser **draft**, sem merge, com validação/limites reais.

Resposta final: o que implementou, o que testou de fato, pendências, branch/HEAD, relatório e instruções para revisão Codex. Não dizer “100% pronto” com gaps ocultos. Entregar resultado concreto pronto para revisão, sem promoção a produção.
