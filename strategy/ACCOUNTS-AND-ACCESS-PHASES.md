# Contas e acesso — decisões do proprietário

Atualizado em 2026-11-04. Escopo confirmado no chat de implementação de cadastro.

## Ampliação documental em 05/11/2026 — área do jogador

O proprietário determinou que mochila, interesses, exploração, KP, carteira e missões oficiais sejam exclusivos de sessão válida com cadastro completo. Login comum deve abrir dashboard, Perfil vira página separada, nome/avatar abre menu, Seu Radar mostra notícias conforme preferências e saldo KP aparece no topo quando habilitado e confirmado. O pedido desta etapa é **planejar e documentar**, sem ativar KP nem publicar redesign. Plano canônico: [MEMBER-AREA.md](MEMBER-AREA.md), [UX](MEMBER-AREA-UX.md), [segurança/API](MEMBER-AREA-SECURITY-API.md) e [entrega](../operations/MEMBER-AREA-DELIVERY.md). Esta decisão substitui qualquer orientação antiga de funções pessoais locais para visitantes; leitura editorial pública permanece aberta. Valores/regras econômicas e benefícios exigem aprovação própria antes da ativação.

## Fases

1. **Cadastro geral:** e-mail, CPF brasileiro obrigatório em PT/EN, confirmação de e-mail, login e funcionalidades básicas de conta. Serviços gratuitos serão definidos depois. Termos devem proibir práticas criminosas, abusivas e pornográficas e prever banimento permanente.
2. **Assinaturas do site:** conteúdos restritos/especiais; modalidades e planos serão definidos nessa fase.
3. **Acesso sob demanda:** compra de acesso temporário a eventos, lives e promoções, independentemente de assinatura do site.
4. **Assinaturas de canais de live:** assinatura de um, vários ou todos os canais; independente da assinatura do site. Alguns canais poderão integrar planos do site.

Somente a fase 1 está autorizada para implementação nesta entrega. Não criar planos, preços, pagamentos ou transmissão como parte dela. Identidade não equivale a direito de acesso comercial.

**Decisão posterior do proprietário em 2026-11-04:** bloquear todos os menores de 18 anos nesta entrega. Implementação de vínculo parental adiada; nenhum endpoint, convite ou cadastro de menor será ativado nesta fase. O desenho abaixo de responsabilidade parental é histórico/requisito futuro, não escopo ativo.

## Identidade escolhida

O proprietário escolheu **Clerk** em 2026-11-04. Portal permanece exportação estática Next/React no Azure Static Web Apps Free. API privada verifica bearer token Clerk e mantém o perfil local. Não usar middleware Next como fronteira de autorização de um site exportado.

Tabela consultada em https://clerk.com/pricing: Hobby gratuito, limite de 50.000 usuários retidos mensais por aplicação; sessão fixa de sete dias. Não presumir MFA, remoção de marca ou funções pagas incluídas. Nenhum plano pago foi autorizado.

CPF não deve ir para metadados públicos Clerk, URLs, analytics, logs ou armazenamento local. Validar dígitos no servidor não comprova titularidade. A finalidade e o prazo de retenção precisam constar na política. A proposta técnica usa HMAC com segredo externo para correspondência e unicidade, sem reter número completo em texto claro.

## Menores e responsável — adiado pelo proprietário

Requisito para entrega futura: menores poderão ter cadastro vinculado a pai/responsável já cadastrado, identificado pelo CPF, que assume a responsabilidade. A decisão vigente desta entrega é **18 anos ou mais**, sem exceções.

**Informar um CPF não constitui autorização.** O responsável precisa estar autenticado, com e-mail confirmado e cadastro adulto concluído, e confirmar o vínculo de forma explícita. O convite deve ser individual, temporário, de uso único e vinculado ao menor correto. Revogar responsabilidade bloqueia o acesso dependente e exige resolver o vínculo antes de reativar.

A autorização deve preceder a criação da identidade do menor no fornecedor. Os termos Clerk consultados em https://clerk.com/legal/standard-terms exigem evidência de consentimento parental verificável fornecida ao Clerk para dados de usuários abaixo de 16 anos. A implementação deve manter essa capacidade desligada até que o procedimento do fornecedor e a evidência estejam confirmados. Não apresentar feature flag como comprovação jurídica nem ativar automaticamente por existir CPF.

Referência pública: art. 14 da LGPD, https://normas.leg.br/?urn=urn:lex:br:federal:lei:2018-08-14;13709!art14_par1. O fluxo deve considerar o melhor interesse e não coletar dados do menor em uma tentativa pública antes do responsável.

## Operação e aceitação

- Identidade Clerk e cadastro AnderZilla são estados distintos. Conta autenticada sem CPF/aceite concluído não recebe acesso de membro.
- E-mail confirmado é obrigatório; campos de e-mail ou identificador enviados pelo navegador não têm autoridade.
- Banimento local impede acesso mesmo com sessão Clerk válida. Decisão administrativa precisa de motivo, autor, data e possibilidade de revisão de erro. Não alegar que HMAC de CPF garante impedir toda evasão por identidade falsa.
- Exclusão revoga acesso, remove avatar/preferências e aplica a política de retenção. Não apagar prova de sanção por consequência acidental de excluir perfil.
- Não migrar carteiras de demonstração nem habilitar KP/pagamentos nesta fase.
- Verificar registro, confirmação, reenvio, recuperação, saída, perfil, exportação, exclusão e bloqueios; incluir autenticação inválida, concorrência, tokens expirados/reutilizados, rejeição de menores e acesso entre contas. Aprovação parental fica adiada.
- Produção só está concluída após configuração real do Clerk, DNS necessário, API, migração SQL, build e teste real de e-mail/navegador. Testes com mocks não comprovam entrega de e-mail.

Estado de implementação e próximos passos: `../operations/REGISTRATION-PHASE1-20261104.md`.
