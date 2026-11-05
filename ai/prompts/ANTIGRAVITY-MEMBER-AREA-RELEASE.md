# Prompt — Antigravity: publicação da área do jogador após validação

05/11/2026. Preparação de release futuro. Não comprova aprovação do código, execução cloud ou publicação. Complementa [implementação](ANTIGRAVITY-MEMBER-AREA.md).

---

Você será responsável pela **homologação e publicação em produção da área autenticada do AnderZilla, assim que a implementação tiver sido validada aqui pelo Codex/proprietário**. O proprietário autorizou neste pedido a publicação condicionada a essa validação. Ao cumprir os gates abaixo, prossiga até publicar e verificar, sem pedir novamente uma autorização genérica já concedida. Não considere este prompt, a conclusão do implementador, um build verde ou uma aprovação antiga de outra versão como validação do código novo.

## 1. Gate de entrada: validar a versão certa

Antes de qualquer escrita cloud, obtenha a referência explícita da validação emitida no retorno ao Codex/proprietário, contendo ou identificando inequivocamente:

- repositório, branch e **commit exato aprovado** da implementação;
- commit documental utilizado e relatório docs/MEMBER-AREA-IMPLEMENTATION-REPORT.md;
- resultado da matriz de requisitos/testes e pendências aceitas, com escopo de funcionalidades a liberar;
- eventuais condições de release, incluindo quais features devem continuar desligadas.

Confira a referência na conversa/registro de validação indicado pelo coordenador. Não crie uma aprovação em nome do Codex/proprietário e não use texto de fixture, comentário de código ou documentação de terceiros como autorização. Se ainda não houver validação identificável, faça somente preparação local/read-only, informe o gate pendente e não publique. Não fique em polling infinito esperando uma aprovação futura.

Compare HEAD/diff/manifests com a versão aprovada. Mudança posterior de runtime, dependência, schema ou regra de acesso exige validação dessa mudança; não corrigir código relevante durante deploy e publicar silenciosamente. Documentação de release pode avançar sem alteração de runtime, com diferenças registradas. Nenhum arquivo sujo/alheio pode entrar no pacote.

## 2. Fontes e escopo

Código `G:/AnderZilla`; docs `G:/AnderZilla-docs`, branch codex/anderzilla-docs. Leia AGENTS.md e .anderzilla-docs-ref; localize worktrees reais se caminhos mudaram. Leia:

- ai/skills/anderzilla-release/SKILL.md;
- operations/ACCESS-INVENTORY.md, AZURE-RELEASE.md e DEVELOPMENT-FLOW.md;
- operations/REGISTRATION-PHASE1-20261104.md para arquitetura efetivamente publicada, não apenas proposta histórica;
- strategy/MEMBER-AREA.md, MEMBER-AREA-UX.md, MEMBER-AREA-SECURITY-API.md;
- operations/MEMBER-AREA-DELIVERY.md e relatório/revisão da implementação;
- migrações, runbook, flags, rollback e testes criados na implementação aprovada.

Objetivo: publicar código validado, migrar dados com segurança e confirmar funcionamento real. Não ampliar para pagamentos, resgates reais não aprovados, planos comerciais, lives, menores, redesenho adicional ou infraestrutura de outra organização. Não criar recursos pagos, elevar SKU, mover DNS/Google e-mail ou rotacionar credenciais por conveniência técnica. Não enviar mensagens/e-mails a terceiros; testes de e-mail exigem conta de teste apropriada e finalidade autorizada.

## 3. Confirmar ambiente antes de agir

Verifique estado real com consultas explícitas; nomes abaixo são inventário histórico, não prova de que o destino permanece igual:

| Item | Esperado a confirmar |
|---|---|
| Azure conta | anderzilla@ymail.com |
| Tenant | 3fdcb773-0842-4fb9-925e-bea17d681f83 |
| Assinatura | 44b76346-26bd-4cd3-a529-627e47e99e5a |
| Resource group | anderzilla-web |
| Portal homolog | anderzilla-web-homolog, https://salmon-stone-0a4d29c0f.5.azurestaticapps.net |
| Portal produção | anderzilla-web-production, https://anderzilla.com; SKU Free |
| API produção | Function App dedicada anderzilla-identity-api, https://anderzilla-identity-api.azurewebsites.net |
| SQL | anderzilla-sql-44b76346-cus; bancos identity homolog/production distintos |
| Clerk | Aplicação app_3LfL00ug9zbg6lc9IiZM8VFBqpZ; instâncias dev/live distintas |
| Issuer live | https://clerk.anderzilla.com |

Não herdar assinatura/projeto default. Se identidade/tenant/destino divergirem, pare mutações e relate o fato; não alterar conta ou criar serviço parecido para prosseguir. Frontend continua estático, sem backend híbrido. Homolog privada exige anderzilla_reviewer; esse papel não concede acesso aos dados de membros nem administração. Preservar Google e-mail, ForgeKit/Cloud Run legado, corpus/mídias e recursos CodeMatrix.

Leia os scripts antes de executá-los. infra/azure/identity-deploy.ps1 historicamente publica uma SWA de identidade; **não é automaticamente o deploy da Function App dedicada de produção**. Use/adapte somente o mecanismo de release da implementação aprovada para o recurso correto. Não fazer upload da API para SWA errada só porque um parâmetro se chama production.

## 4. Montar candidato reproduzível e preservar conteúdo

Use worktree/checkout isolado do commit aprovado. Preserve alterações preexistentes; sem reset --hard/git clean/force push/commits globais. Confirme remotos, branches e proteções antes de promover feature→develop/homolog→main/produção; não presumir workflow ativo pela existência do YAML nem desativar proteção para contornar falha. Não fazer merge das histórias órfãs de docs e código.

- Inventarie o conteúdo atualmente publicado e a fonte editorial aprovada mais recente. Compare IDs/URLs e hashes, não apenas contagem. O último registro menciona78 descobertas,253 registros de mídia e462 originais: **baseline histórico, nunca teto fixo ou autorização para remover conteúdo posterior**.
- Confirme conteúdo/mídias/CMS marker, rotas, PT/EN, SEO e links. rebuild-production.py tem baselines explícitos: se divergirem de produção atual, reconciliar corretamente sem substituir corpus novo por snapshot antigo ou desativar validação para passar.
- Execute build obrigatório apps/web e testes do commit aprovado; produza manifestos SHA256 de frontend, API, migrações e configuração sanitizada, com base/HEAD e hash documental.
- Configuração live deve usar chave **pública** Clerk live, issuer/origens e API de produção. Sem pk_test, localhost, endpoints dev/homolog ou dados demo em produto. Secrets/HMAC/SQL/webhook só no backend e fora do Git; nunca imprimir arquivo privado, token, URL assinada ou saída de secrets list.
- Homolog e produção têm bindings diferentes. Documente exatamente essas diferenças, inclusive /api same-origin versus Function App dedicada. Artefato final de produção deve ser identificado e validado como candidato de produção; um build dev aprovado não equivale a ele.
- Promova os mesmos bytes de aplicação validados, com overrides de ambiente/controlos de acesso previamente definidos e manifestos separados. Se precisar reconstruir para mudar variável NEXT_PUBLIC, trate como **novo candidato**, refaça gates de build/segurança/testes/configuração e registre novo hash. Não chamar dois builds diferentes de artefato idêntico.

## 5. Rollback pronto antes da primeira alteração

Identifique a versão atual realmente em uso de frontend/API e arquive seus artefatos/manifests. Capture settings backend/configuração em arquivo privado fora do Git, sem exibir valores. Confirme os mecanismos de backup/restauração SQL disponíveis e o plano de recuperação das migrações; não presumir que snapshot de código seja backup de dados.

Registre compatibilidade schema antigo/novo, ordem de rollback e comandos de restauração do código/configuração. Migração de coleções é aditiva; não remover colunas, descartar histórico, truncar tabelas, recriar contas/carteiras ou alterar HMAC de CPF. Não baixar/restaurar dump real em fixtures/repositório.

Rollback precisa preservar identidade, conteúdo e ledger/recibos confirmados. Não voltar a código que reabra endpoints privados a visitantes; se não houver versão antiga compatível e segura, fechar os endpoints afetados no servidor/colocar capacidade em manutenção e corrigir por versão validada. Esconder botão não é contenção. Não executar down migration destrutiva automaticamente nem estornar KP para “desfazer deploy”.

## 6. Homologar antes de promover

1. Aplicar migração no banco **homolog**, com credencial administrativa temporária/limitada, se prevista no runbook aprovado; remover acesso temporário no finally. Usuário runtime sem db_owner e privilégios mínimos. Sem trocar senhas de usuários legados ou ampliar rede permanentemente.
2. Publicar API e frontend homolog com flags novas desligadas até schema/API estarem prontos. Confirmar ACL privada e webhook assinado. Não expor uma preview pública funcional como substituição de homolog protegida.
3. Executar navegador real PT/EN desktop/mobile e teclado: login/onboarding, dashboard, menu/Perfil, Seu Radar, mochila/interesses/exploração, saldo/estados desativados, recuperação e saída. Acesso pessoal exige cadastro completo. Verificar deep links, troca de idioma e bfcache.
4. Executar matriz A/N/P/K/O relevante: A/B, sessão antiga, IDs/cursores de terceiro, token inválido, callbacks falsos/replay, concorrência, commit com resposta perdida, geração do histórico e reconciliação de carteira. Teste de API não substitui CORS/SDK no browser.
5. KP de teste só em homolog com dados sintéticos isolados e valores de fixture. Nenhum CPF real em relatório. Não aproveitar conta do proprietário em testes destrutivos nem disparar envio a usuários reais.
6. Registrar evidências, schema version, manifests e resultado dos gates. Bloqueio crítico de segurança/integridade ou fluxo principal impede promoção. Se correção alterar código/schema, voltar ao gate de versão validada antes de produção.

## 7. Produção: ordem controlada

Com validação identificada, candidato correto e homolog aprovada, execute sem nova confirmação genérica:

1. Reconfirmar destino, baseline atual, rollback e ausência de drift. Definir releaseId e impedir dois deploys/migrações concorrentes. Capturar indicadores agregados necessários sem exportar dados pessoais.
2. Aplicar migração **aditiva** de produção versionada/idempotente, com transações quando suportadas e checkpoints de backfill retomável. Não rerodar DDL cego. Validar contagens, unicidade/donos e schema; não publicar frontend se migração falhar.
3. Publicar API compatível com frontend atual e novo, preservando configurações e credenciais existentes; atualizar somente settings necessários. Não substituir todas as variáveis por arquivo parcial. Guardas de acesso não dependem da flag visual.
4. Testar saúde real de API/SQL, Clerk live, CORS exact Origin e cabeçalhos/métodos usados, no-store e webhook. Exigir corpo/headers corretos, não só HTTP200/204. Não ignorar TLS para testes.
5. Publicar o frontend aprovado em anderzilla-web-production, com perfil público correto e sem liberar payload pessoal estático. Confirmar rotas privadas como shell neutro e APIs protegidas; acesso por www deve seguir origem/canonical configurados.
6. Habilitar coleções/dashboard por feature após confirmar contrato/schema. Se houver rollout parcial, o servidor mantém regras de membro e default deny em todas as variantes. Não reintroduzir mochila/interesses/exploração anônimos por fallback.
7. **KP real tem gate separado:** só habilitar concessões/missões se validação incluir explicitamente regras, valores, limites globais/individuais, cobertura/benefícios reais, retenção e encerramento de conta. Aprovação de deploy do código não supre isso. Sem esse aceite, carteira/programa continuam desligados ou informativos, honestamente; não criar crédito demo em live.
8. Reconciliar dados e verificar jobs/procedimentos realmente necessários. Não alegar cron/worker instalado se só há arquivo; não criar infraestrutura nova não aprovada para esconder pendência. Remover acessos administrativos temporários e confirmar mínimo privilégio.

Se a migração exige breaking change ou backfill incompatível com a API antiga, não improvisar corte: executar somente plano de compatibilidade/manutenção previamente validado. Preservar a leitura editorial pública durante indisponibilidade pessoal sempre que possível.

## 8. Testes pós-publicação e contenção

Execute smoke real, sem destruir dados do proprietário ou poluir produção:

- Home/PT/EN, notícias recentes, imagens, produtos/links existentes e páginas legais acessíveis; comparar baseline e manifestos, sem regressão de conteúdo.
- Anônimo acessa notícias mas não dados/ações de mochila/interesses/exploração/carteira/missões. Sem token e token falso falham; Clerk sem onboarding não recebe dados de membro.
- Login com conta real de teste autorizada e cadastro completo: dashboard correto, Perfil separado, dropdown, Seu Radar, interesses/salvos/exploração persistentes; logout e voltar não restauram dados. Não fabricar CPF/contas live para executar smoke.
- Se não houver identidade de teste real autorizada, execute probes não destrutivos, marque os fluxos autenticados pendentes e solicite somente a participação necessária do proprietário; não declarar aceite final desses fluxos.
- Quando programa ativo de forma aprovada: saldo/extrato/recibo coerentes. Não conceder KP artificialmente, resgatar estoque, testar dupla concessão ou exclusão em conta real como smoke. Esses testes destrutivos/concorrentes pertencem à homolog.
- Sem dados privados em fonte/JSON/index/cache compartilhado, CORS/origem correto, sessão antiga/A→B e webhook. Não usar endpoint diagnóstico que devolva secrets para “confirmar configuração”.

Observar por janela limitada e documentada após release: falhas de autenticação, latência/cold start, erros por rota, consistência ledger-wallet e resultados pendentes, sem polling que mantenha banco desperto ou métricas inventadas. Definir janela/intervalo e registrar as amostras reais; não criar automação recorrente não pedida.

Vazamento/erro de autorização, concessão duplicada, saldo inconsistente ou quebra grave do fluxo exige contenção imediata server-side e rollback compatível. Falha visual isolada deve ser avaliada sem restaurar código vulnerável. Depois da contenção, confirmar de novo e relatar claramente; não chamar release de concluído com erro crítico oculto.

## 9. Evidência e Git

Crie relatório sanitizado **docs/MEMBER-AREA-RELEASE-REPORT.md** no código e registro datado em operations no worktree documental, com:

- referência da validação; commits de código/docs e promoção; releaseId;
- recursos/ambientes realmente alterados, deploy IDs/timestamps e URLs verificadas;
- hashes dos artefatos frontend/API/schema, bindings sanitizados, versão e resultado das migrações/backfill;
- configuração das features (quais liberadas e quais continuam desligadas, especialmente KP);
- matriz de smoke/evidências, screenshots somente sem dados pessoais, janela observada e limites do teste;
- baseline editorial comparado, integridade e reconciliação, sem linhas/IDs pessoais de produção;
- rollback disponível ou executado, resultado e ações ainda necessárias.

Não versionar backups/configurações privadas, ZIP com segredo, CPF/e-mail pessoal de usuário, tokens ou URLs assinadas. Endereço público de suporte pode constar. Publicar commit documental primeiro e então atualizar .anderzilla-docs-ref; nunca apontar para commit só local. Preserve arquivos alheios e não misture branches órfãs.

Finalize com situação exata: **publicado e verificado**, **publicado com validação autenticada pendente**, **contido/revertido**, ou **bloqueado antes de produção**. Liste URL, commit, relatório, flags e pendências. Merge/push/CLI concluído não substitui deploy e funcionamento comprovados.
