# Funções de usuários autenticados — inventário de 05/11/2026

**Atualização posterior do proprietário em 05/11/2026:** mochila, interesses e exploração também exigem autenticação e cadastro completo, assim como KP, carteira e missões. A coluna “Visitante” abaixo descreve a implementação observada antes dessa decisão, não a regra futura autorizada. Plano vigente: [área do jogador](../strategy/MEMBER-AREA.md) e [entrega](MEMBER-AREA-DELIVERY.md). Não oferecer migração/progresso local como comportamento novo.

## Escopo e evidência

Análise do código atual da branch codex/registration-phase1-20261104, registro REGISTRATION-PHASE1-20261104.md e probes públicos somente leitura. Não foram criadas/excluídas contas nem alterada produção nesta análise. Portal /pt/ respondeu200 e capabilities de produção respondeu provider=clerk, available=true, registration=true, minimumAge=18, minorAccessEnabled=false, rewards=false. Capabilities não prova todas as funções nem saúde do banco.

O registro operacional documenta cadastro e e-mail reais do proprietário em produção, bateria funcional em homologação e 64 testes aprovados na execução anterior. Não interpretar isso como todos os fluxos testados em todos os navegadores ou como execução nova da suíte nesta análise.

## Estados de acesso

1. Visitante: conteúdo público, links de lives, exploração, mochila/interesses/progresso locais.
2. Sessão Clerk com e-mail verificado, cadastro incompleto: somente completar cadastro, sair e fluxos de autenticação. Não concede perfil completo nem acesso pago.
3. Cadastro AnderZilla completo e ativo: CPF obrigatório, idade18+, termos vigentes; libera dados próprios e preferências persistentes.
4. Conta suspensa/excluída: acesso pessoal bloqueado no servidor. Login no fornecedor não restaura permissão.

Ser cadastrado não concede assinatura, compra ou administração. Permissões editoriais/CMS e papel anderzilla_reviewer de homologação são fronteiras separadas.

## Matriz funcional

| Função | Visitante | Cadastrado ativo | Situação comprovada / restante |
|---|---|---|---|
| Ler Radar, notícias, produtos e links públicos de lives | Sim | Sim | Público; login não necessário. Não há paywall implementado nesta fase. |
| Cadastro, confirmação de e-mail e login por código | Inicia | Sim | Publicado; cadastro real do proprietário documentado. Cadastro só termina após onboarding privado. |
| CPF, idade18+ e termos | Não | Obrigatórios | Backend valida checksum/duplicidade, idade e versão. CPF autodeclarado não prova titularidade na Receita. Menores bloqueados. |
| Minha conta, nome e CPF mascarado | Não | Sim | Implementado; fluxo real de cadastro e perfil documentado. CPF completo não é exibido nem armazenado como texto. |
| Alterar nome e consentimento de novidades | Não | Sim | PATCH próprio; teste remoto e navegador registrados. Opt-in não significa serviço de newsletter/campanha ativo. |
| Avatar | Não | Sim | Presets e upload com redução de imagem implementados; preset testado remotamente. Completar validação de upload real, formatos, limites e celular. |
| Idioma | Local/URL | Persistente | API e integração existem. Revisar mudança de idioma: savePreferences é disparado sem aguardar e logo depois há window.location.assign; risco de navegação cancelar gravação. Validar entre dispositivos. |
| Interesses | Local | Sincronizados | API/integracão e teste remoto registrados; validar navegador, novo login e segundo dispositivo. |
| Mochila/salvos | Local | Sincronizados | API/integracão e teste remoto registrados; validar adicionar/remover, reload e segundo dispositivo. Não há migração automática comprovada da mochila visitante. |
| Histórico de descobertas abertas | Local | Sincronizado | Campo opened conectado a PATCH; falta evidência ponta a ponta específica. Cada lista tem limite1000; definir comportamento ao atingir limite. |
| Exportar meus dados | Não | Sim | Testado em homologação por API e download; exportação sem CPF completo/segredos. Falta repetir produção com conta descartável apropriada. |
| Sair / revogar sessão | Não | Sim | SDK no navegador e endpoint de revogação; teste remoto recusou JWT após logout. Completar cenários multiabas/dispositivos. |
| Excluir conta | Não | Sim, com autenticação recente | Homologação testou confirmação, remoção no Clerk e limpeza SQL. Não excluir conta real do proprietário como teste. Validar experiência de reautenticação >5min e conclusão de falha externa. |
| Recuperar acesso | Login por código | Sim | Entrada por e-mail existe. Recuperação por senha, se usada, é do Clerk; não confundir passwordReset=false da API legada com ausência do login por código. Falta bateria própria de recuperação/reenvio/expiração em produção. |
| Alterar e-mail/senha e gerenciar sessões | Não | Preparado no SDK | UserProfile protegido por NEXT_PUBLIC_CLERK_SECURITY_ENABLED; não marcar liberado sem conferir artefato e testar alteração de e-mail + webhook + sessão. Google/Meta desativados. |
| Bloqueio/banimento | Não | Operador aplica | CLI administrativo e testes; usuário não tem endpoint para banir terceiros. Falta procedimento operacional de contestação/revisão e validar credencial administrativa separada. Banimento não é detecção automática de infração. |
| KP, carteira, extrato e missões oficiais | Não | Desativados | Existem UI/módulos legados, mas rewards=false e router Clerk não fornece rotas /api/points. Exigem projeto de integração, regras e antifraude; não são funções prontas para membros. |
| Quiz, desafios e progresso local | Sim | Sim | Continuam locais; não geram KP oficial nem direito pago. |
| Assinaturas, compras temporárias e canais de lives | Não implementado | Não implementado | Fases2–4: direitos de acesso independentes, cobrança/webhooks/expiração e proteção de mídia ainda necessários. |
| Comentários, chat privado, publicação por membro | Não identificado | Não identificado | Não foram encontrados como capacidades expostas pelo router de membros; não anunciar disponibilidade. |

## Prioridade para finalizar a fase1

1. Matriz de testes de produção controlada: perfil, avatar, preferências/salvos/histórico, logout e recuperação, Chrome/mobile e PT/EN. Exclusão e casos destrutivos só com conta descartável autorizada.
2. Fechar consistência das preferências: aguardar gravação antes de navegar ao trocar idioma; especificar mochila visitante → conta sem sobrescrita silenciosa; testar segundo dispositivo e limite1000.
3. Validar banco frio e loader/retry com SQL realmente pausado. Código de pre-warm e4 tentativas foi publicado; endpoint pronto com banco quente não comprova esse cenário.
4. Finalizar gestão de credenciais e sessões: decidir liberar UserProfile somente após testes de webhook/alteração de e-mail, colisão e reautenticação para exclusão.
5. Operação: testar retomada de exclusão pendente, rotina de atendimento/contestação, alertas e recuperação/backup. Implementação local de operador não comprova rotina operacional instalada.

Não iniciar KP ou monetização para chamar a fase1 de concluída. A conclusão exige evidência de todas as funções básicas de conta, não apenas cadastro bem-sucedido.

## Fontes do código

- services/identity/clerk_api.py: rotas e limites do modo Clerk.
- services/identity/clerk_auth.py e clerk_service.py: verificação, cadastro e ciclo de vida.
- services/identity/core.py: update_profile, export_data e limites de preferências.
- apps/web/src/components/account/AccountProvider.tsx e AccountUI.tsx: interface, SDK, loader, segurança e ações de conta.
- apps/web/src/components/hub/HubProvider.tsx: persistência autenticada vs local, idioma, salvos, interesses e opened.
- apps/web/src/components/account/OfficialMissions.tsx: UI condicionada a rewards.
- operations/REGISTRATION-PHASE1-20261104.md: resultados históricos e implantação.
