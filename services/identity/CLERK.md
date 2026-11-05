# Contas gerenciadas — Clerk, fase 1

Estado: API Clerk publicada em homologação; domínio e TLS Clerk prontos. Navegador e publicação de produção ainda em validação. Fonte de decisões: `G:/AnderZilla-docs/strategy/ACCOUNTS-AND-ACCESS-PHASES.md`. Operação: `G:/AnderZilla-docs/operations/REGISTRATION-PHASE1-20261104.md`.

## Fronteiras

`IDENTITY_AUTH_PROVIDER=clerk` seleciona o contrato deste documento. O contrato nativo de `CONTRACT.md` é legado: cookies, senhas e Google OAuth próprios **não** autorizam o modo Clerk. Não publicar a fonte legada sobre o serviço existente sem reconciliação: o pacote publicado contém correções ausentes naquela fonte.

O portal continua estático. O SDK React obtém token Clerk e envia `X-AnderZilla-Authorization: Bearer ...` à API, com `credentials: omit`; SWA substitui o cabeçalho Authorization padrão. A API valida assinatura RS256, emissor exato, expiração, início de validade e origem autorizada (`azp`); confirma sessão ativa e e-mail primário verificado no backend Clerk. Dados de perfil e metadados recebidos do navegador não são prova de identidade. Cabeçalhos administrativos SWA não concedem acesso de membro. Em Functions dedicada, Authorization padrão também é aceito para clientes diretos.

SWA gerenciada intercepta OPTIONS sem os cabeçalhos CORS necessários a uma origem externa. Homolog web deve usar API na mesma origem ou uma Function App dedicada com CORS configurado. O proxy de loopback de teste não comprova CORS de uma publicação remota. Configurar globalHeaders não resolveu o preflight no probe real.

O cadastro local é independente da identidade Clerk. Enquanto não houver CPF, data de nascimento adulta e aceite da política vigente, o perfil permanece incompleto. Contas suspensas/excluídas são rejeitadas em cada acesso, mesmo com JWT válido.

## Contrato de conta

| Método | Rota | Autoridade e comportamento |
|---|---|---|
| GET | `/api/account/capabilities` | Público; informa `provider: clerk`, disponibilidade, versão dos termos, idade mínima 18 e rewards desligados. Não confirma saúde de SQL nem entrega de e-mail. |
| GET | `/api/account/me` | Sem bearer retorna visitante. Com bearer válido retorna perfil ou `onboardingRequired: true`. |
| POST | `/api/account/onboarding` | Bearer com e-mail verificado; recebe `cpf`, `displayName`, `birthDate`, `termsAccepted`, `termsVersion`, `privacyVersion`, `marketingOptIn`, `lang`. Idade calculada no servidor; menores de 18 rejeitados. |
| PATCH | `/api/account/profile` | Perfil próprio; campos permitidos pelo domínio de perfil. Não permite alterar CPF, identidade ou idade pelo navegador. |
| GET | `/api/account/export` | Dados da própria conta e cadastro; CPF mascarado, sem segredo HMAC. |
| POST | `/api/account/delete` | `confirm: DELETE`; exige autenticação recente. Bloqueia acesso e limpa perfil local antes de pedir exclusão no fornecedor. Falha externa vira `deletion_pending`, nunca sucesso simulado. |
| POST | `/api/account/logout` | Revoga a sessão autenticada no fornecedor. Interface usa a saída do SDK Clerk. |
| POST | `/api/account/webhooks/clerk` | Callback do fornecedor; verificar assinatura sobre corpo bruto e tolerância de tempo antes de processar. Não aceita bearer/Origin como substituto de assinatura. |

Login, confirmação/reenvio de e-mail, recuperação de senha e gestão das credenciais são fluxos do Clerk, não endpoints legados reimplementados. Métodos e políticas precisam ser configurados no painel e testados com envio real.

Não há endpoints de família/menores, pagamentos, assinaturas ou streaming nesta entrega. Não habilitar missões ou saldo local como direito oficial.

## CPF e idade

- Normalizar apenas o formato brasileiro aceito; validar os dois dígitos e rejeitar sequências repetidas no servidor.
- Guardar HMAC do número normalizado com segredo de pelo menos 32 caracteres e domínio de finalidade, mais os dois últimos dígitos para exibição mascarada. Não guardar número completo em texto claro.
- Índice único e transação protegem duplicidade concorrente. A validação não comprova titularidade nem consulta a Receita Federal.
- A data de nascimento é privada. A declaração de idade/CPF não constitui verificação documental de identidade.
- Não usar CPF em URLs, metadados Clerk, logs, fixtures com dados reais ou armazenamento de preferências no navegador.
- Não trocar `IDENTITY_CPF_HMAC_KEY` sem migração: uma troca cega quebra unicidade e correspondência das sanções.
- Cadastro abaixo de 18 anos bloqueado por decisão do proprietário, mesmo com autorização de responsável.

## Configuração privada

Backend, por ambiente:

- `IDENTITY_AUTH_PROVIDER=clerk`, `IDENTITY_ENV=homolog|production`.
- `IDENTITY_ALLOWED_ORIGIN`: origens HTTPS explícitas separadas por vírgula; sem wildcard. Produção inclui `https://anderzilla.com` e a origem www se ela puder executar a app.
- `IDENTITY_SQL_SERVER`, `IDENTITY_SQL_DATABASE`, `IDENTITY_SQL_USER`, `IDENTITY_SQL_PASSWORD`: banco identity separado do CMS e usuário contido dedicado. O novo modo usa `anderzilla_clerk_runtime`, separado do usuário legado `anderzilla_identity_runtime`; não rotacionar a credencial legada.
- `IDENTITY_CPF_HMAC_KEY`: aleatório, gerado fora do repositório, distinto entre ambientes.
- `CLERK_ISSUER`: emissor HTTPS exato da instância, sem barra final.
- `CLERK_SECRET_KEY`: chave secreta do ambiente correto; produção exige chave live.
- `CLERK_JWT_KEY`: chave pública PEM RSA da instância. Revisar procedimento de atualização durante rotação Clerk.
- `CLERK_WEBHOOK_SIGNING_SECRET`: segredo do endpoint de webhooks, guardado fora do Git.

Frontend, **no momento do build**:

- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: chave publicável da instância correta. Nunca colocar `sk_...` em variáveis `NEXT_PUBLIC_*`.
- `NEXT_PUBLIC_ACCOUNT_API_BASE`: origem HTTPS da API identity. Esta variável ausente produz estado indisponível no site estático; mudar setting no Azure depois do build não corrige um bundle já exportado.
- `NEXT_PUBLIC_CLERK_SECURITY_ENABLED=true`: só habilitar gestão de credenciais após configurar e testar o callback de exclusão no provedor.

As variáveis Clerk substituem SMTP/OAuth próprios para as contas novas. O serviço privado de perfil continua necessário. Não criar banco ou provedor de e-mail adicional por engano.

## Publicação e validação real

1. Entrar/criar a conta do proprietário no Clerk com identidade AnderZilla. Aceite de termos/entrada de novas credenciais é feito pelo proprietário quando exigido pela interface.
2. Criar instâncias de desenvolvimento e produção; usar plano gratuito. Confirmar e-mail obrigatório/verificado, proteção contra abuso, métodos de entrada e URLs de retorno.
3. Configurar domínio e DNS Clerk conforme os registros específicos da instância, preservando MX/SPF/DKIM/DMARC Google. Não adivinhar valores de DNS.
4. Preparar settings privados fora do repositório. Rodar `infra/azure/clerk-readiness.py` com `--environment`, `--settings` e opcionalmente `--check-azure`. O comando é somente leitura e não imprime valores.
5. Aplicar `schema.azure.sql` e `runtime-permissions.azure.sql` no banco identity correto; nunca no CMS. Operações administrativas usam credencial separada e não são HTTP público.
6. Publicar a API em homologação isolada. Configurar webhook Clerk assinado para ciclo de vida de usuários. Testar payload válido, assinatura falsa e repetição.
7. Executar testes unitários e build estático com chaves públicas de homologação; validar login, verificação/reenvio, recuperação, saída, perfil, exportação, exclusão e banimento com contas de teste autorizadas. Dados reais de CPF não entram em relatórios.
8. Testar Chrome e Safari/mobile, inclusive banco pausado. Timeout local não é prova de ausência de dados nem de mau funcionamento do Clerk.
9. Preparar artefato de produção com a instância live e conteúdo editorial/mídias atuais. Não publicar o `out` genérico com corpus desatualizado. Registrar manifesto e rollback.
10. Promover por feature → develop/homolog → main/produção. Confirmar domínio, HTTPS, conta real por e-mail e limpeza após exclusão. Só então marcar concluído.

## Sanções e recuperação operacional

O CLI `python -m services.identity.managed_operator` não é uma API pública. Usar credencial SQL administrativa separada, com permissões explícitas sobre sanções/auditoria, e nunca fornecer CPF/e-mail/tokens nos argumentos.

- `ban ACCOUNT_ID --actor OPERADOR --reason MOTIVO`: primeiro bloqueia localmente e registra sanção; depois solicita banimento no Clerk. Se Clerk falhar, o bloqueio local continua e a operação pode ser repetida.
- `pending-deletions`: lista IDs opacos de exclusões externas pendentes.
- `finish-deletion ACCOUNT_ID`: retoma exclusão remota e conclusão local.

Não executar sanções reais como teste. Erros de banimento precisam de revisão humana pelo canal `player.one@anderzilla.com`; não remover a lista de bloqueio por exclusão de perfil. Estado do cadastro é autoritativo, mas CPF autodeclarado não garante impedir toda evasão.

## Pendências que não podem ser simuladas

Aplicação/chaves Clerk, DNS, webhook configurado, migração SQL e envio real não são comprovados por build ou mocks. Uma próxima IA deve consultar o registro operacional e o estado atual antes de publicar ou declarar a fase concluída.

Compatibilidade TLS: `tds_tls.py` adapta a validação de hostname do python-tds à API atual do pyOpenSSL, usando service-identity sobre SANs cryptography. A cadeia de certificados permanece validada; ausência de SAN ou nome divergente é rejeitada.

## Teste local com homologação isolada

O helper `infra/azure/identity-local-homolog.py` serve `apps/web/out` em **127.0.0.1:4027** e encaminha somente `/api/` ao hostname fixo da identidade homolog. Rodar da raiz do repositório. Não expor esse servidor à rede.

Preparar o build com a chave **pública dev**, `NEXT_PUBLIC_ACCOUNT_API_BASE=http://localhost:4027` e `NEXT_PUBLIC_CLERK_SECURITY_ENABLED=false`; depois executar `npm run build` em apps/web e `python infra/azure/identity-local-homolog.py` na raiz. Abrir http://localhost:4027/pt/. A origem exata de loopback deve constar somente nos settings homolog. Esse artefato é exclusivo de teste e nunca deve ser promovido a produção.

Usar contas sintéticas Clerk dev com código reservado de teste. Não confundir sucesso desse código com envio real de e-mail. Não usar CPF real em fixtures, logs ou documentação.
