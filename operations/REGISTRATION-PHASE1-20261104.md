# Cadastro fase 1 — execução e continuidade

Última atualização: 2026-11-04. **Em implementação, não publicado.**

## Onde continuar

- Código: `G:/AnderZilla`, branch `codex/registration-phase1-20261104`.
- Documentação: `G:/AnderZilla-docs`, branch `codex/anderzilla-docs`.
- Escopo/decisões: `strategy/ACCOUNTS-AND-ACCESS-PHASES.md`.
- Alterações preexistentes no código e na documentação devem ser preservadas; adicionar/commitar somente arquivos desta entrega.
- O worktree documental apontava para Z:; `git worktree repair G:/AnderZilla-docs` restaurou a associação ao repositório em G:, sem alterar conteúdo editorial.

**Decisão posterior do proprietário em 2026-11-04:** bloquear todos os menores de 18 anos nesta entrega. Implementação de vínculo parental adiada; nenhum endpoint, convite ou cadastro de menor será ativado nesta fase. O desenho abaixo de responsabilidade parental é histórico/requisito futuro, não escopo ativo.

## Evidência inicial

1. Azure CLI confirmou conta `anderzilla@ymail.com`, assinatura `44b76346-26bd-4cd3-a529-627e47e99e5a`, tenant `3fdcb773-0842-4fb9-925e-bea17d681f83`.
2. Existem SWAs web homolog/produção, recursos identity homolog/produção e Function App `anderzilla-identity-api`. Existência não comprova funcionamento.
3. GET `https://anderzilla-identity-api.azurewebsites.net/api/account/capabilities`, com Origin `https://anderzilla.com`, respondeu 200 e anunciou cadastro, senha e recuperação; Google e rewards desligados. Não foram criadas contas reais nesse teste.
4. O bundle público do portal não apresentou base de API substituída no build. GET capabilities no domínio público retornou 404. O fluxo publicado ainda não conecta o cadastro ao serviço.
5. Fonte desta branch está atrás do pacote local `.deploy/identity-func-fixed5.zip`: pacote tem recuperação e sessão após cadastro; fonte versionada não. **Não substituir produção pelo serviço legado desta branch.** Nova integração Clerk deve ter seleção explícita e artefato próprio com rollback.
6. Nenhum segredo foi impresso. Foram consultados nomes de settings, não os valores.

## Trabalho em curso

- Backend: modo Clerk bearer, validação de identidade no servidor, cadastro privado CPF, vínculo de responsável e testes adversariais.
- Frontend: SDK React compatível com export estático, login/registro gerenciados, completar cadastro, família e estados honestos quando integração não configurada.
- Coordenação: termos/privacidade, configuração operacional, testes integrados e documentação.

## Pendências externas conhecidas

- Painel Clerk abriu em tela de login; aplicação/chaves de produção ainda não confirmadas.
- Operador e contato confirmados pelo proprietário: Anderson Henrique Gonçalves; player.one@anderzilla.com.
- Menores: escopo adiado pelo proprietário; cadastro bloqueado para todos abaixo de 18 anos. Procedimento parental fica para entrega futura.
- Validar instâncias distintas de desenvolvimento e produção, domínio/DNS, métodos de entrada e envio de e-mails em ambiente real.

## Verificações

- Tentativa inicial `python -m unittest discover -s services/identity -v`: 25 testes, 15 erros por dependências locais ausentes (Argon2/google-auth). Não representa falha de produção nem valida a nova integração.
- Instalar dependências em ambiente isolado antes de repetir; registrar resultado final e comando exato aqui.
- Regras de release: feature → develop/homolog → main/produção; build da app tocada obrigatório; preservar corpus editorial/mídias e marcador CMS.

## Próximo agente

1. Ler este arquivo e a estratégia antes de mexer no código.
2. Confirmar estado Git e contratos reais dos módulos Clerk; não usar o pacote zip legado como fonte definitiva.
3. Não declarar cadastro em produção enquanto houver pendência externa ou testes reais não executados.
4. Atualizar este registro com commits, resultados, URLs verificadas, bloqueios e rollback após cada etapa.

## Atualização de implementação e painel

- Aplicação Clerk escolhida/criada pelo proprietário: `app_3LfL00ug9zbg6lc9IiZM8VFBqpZ`.
- Instância development: `ins_3LfL02LzigyjweId4LrMfRLsqU5`.
- Instância production criada para `anderzilla.com`: `ins_3LfLVsZrOTj3E1BBMXZIYif5EXB`.
- Plano observado no painel: Hobby. Nenhuma assinatura paga foi contratada.
- Em development, observados: e-mail obrigatório, verificação no cadastro por código, login por código e senha habilitados; proteção de senha comprometida ligada e mínimo 15 caracteres. Produção foi criada copiando configurações development; precisa de revalidação e DNS.
- Chave secreta production está no checklist de exibição única. Proprietário orientado a salvá-la fora do repositório em `C:/Users/ander/.codex/anderzilla-clerk-production.env`. Não presumir existência até verificar arquivo.
- CLI não autenticado no momento do probe. Proprietário orientado a executar `npx --yes clerk@latest auth login` para autenticar a ferramenta. Login do painel não equivale a login do CLI.
- A falha temporária `browser.user is unavailable` foi resolvida com reinicialização de `cua_repl` e seleção da aba IAB por ID. Não contornar controles de segurança usando automação alternativa.

### Validações locais concluídas

- `python -m unittest discover -s services/identity -q`, usando venv em `C:/Users/ander/AppData/Local/Temp/anderzilla-identity-phase1-venv`: **55 testes passaram**, incluindo JWT assinado, origem/emissor, CPF concorrente, idade exata no fuso São Paulo, bloqueio e exclusão, assinatura falsa/expirada de webhook e replay.
- Teste de webhook revelou incompatibilidade real: Svix atual verifica assinatura e retorna `None`; corrigido para interpretar JSON somente após verificação. Nunca processar retorno `None` como evento nem interpretar conteúdo antes de validar autenticidade.
- `npm run build` em `apps/web`: **188 páginas exportadas**, TypeScript e compilação aprovados. Build local ainda sem chaves/configuração final; não é pacote autorizado de produção nem prova de preservação do corpus ao publicar.
- Auditorias de dependências: npm sem vulnerabilidades conhecidas no probe após patches; pip-audit final sem vulnerabilidades conhecidas após atualização dos pins de TLS/JWT/requests. Logs privados em `.tmp/` não são provas de deploy.
- Tentativa de inventário SQL somente leitura no banco identity production expirou com TimeoutError; nenhuma linha de conta foi exibida, criada ou alterada. Contagem e migração de possíveis contas legadas continuam pendentes. Cadastro por e-mail legado não é vinculado automaticamente ao Clerk.

### Próximos passos imediatos

1. Confirmar salvamento privado da chave e autenticação CLI; não criar outra aplicação.
2. Ler registros DNS específicos da instância production e configurar no provedor atual, preservando e-mail Google.
3. Configurar chaves e webhook assinado, migrar apenas o banco identity, testar em homologação isolada e verificar contas legadas.
4. Build com variáveis públicas corretas e teste real de cadastro/e-mail, recuperação, perfil, exportação e exclusão; depois seguir fluxo de promoção e registrar rollback.

## Continuação — domínio pronto, homologação ainda em implantação

Esta seção substitui as pendências anteriores de login CLI, salvamento de chaves e DNS.

- CLI autenticado na conta player.one@anderzilla.com; aplicação existente vinculada. Chaves dev/live guardadas fora do Git, nunca no frontend nem nestes registros.
- Cinco CNAMEs adicionados na Wix: clerk → frontend-api.clerk.services; accounts → accounts.clerk.services; clkmail → mail.qqtnme9yx1ri.clerk.services; clk._domainkey → dkim1.qqtnme9yx1ri.clerk.services; clk2._domainkey → dkim2.qqtnme9yx1ri.clerk.services. TTL 1 hora. Registros web e Google MX/TXT preservados.
- `clerk deploy status --mode agent` confirmou DNS, mail e SSL completos. Painel mostra domínio Verified e certificados Issued. Isso prova configuração do Clerk, não entrega real de e-mail ao usuário.
- Dev e produção: login por código de e-mail, senha opcional; Google desativado até existir configuração OAuth de produção válida.
- Webhooks user.updated e user.deleted criados para homolog e produção. Segredos gravados apenas nos settings privados. Entrega real ainda não testada; manter NEXT_PUBLIC_CLERK_SECURITY_ENABLED=false.
- Homolog: schema aditivo aplicado ao banco anderzilla-identity-homolog, novo usuário contido anderzilla_clerk_runtime. Usuário legado preservado. Acesso Entra administrativo temporário removido ao final. Não repetir criação/rotação cegamente.
- Leitura de produção confirmou uma conta legada e usuário runtime sem db_owner. Não vincular por coincidência de e-mail nem apagar essa conta. Migração Clerk de produção não executada.
- Compatibilidade TLS python-tds/pyOpenSSL corrigida sem desativar validação da cadeia nem do hostname. Testes SAN ausente/divergente recusados.
- Suíte local atual: **60 testes aprovados**, incluindo aliases de settings e TLS. pip-audit dos requisitos atuais: nenhuma vulnerabilidade conhecida.
- API de homolog gerenciada SWA segue sem rota funcional (probe capabilities retornou 404). Upload anterior falhou com “Failed to deploy the Azure Functions”; ambiente Ready não prova API publicada. Ajustes: requirements na raiz, empacotamento Linux cp311, aliases AZ_ACCOUNT_ para prefixo IDENTITY_ reservado e tentativa com function.json explícito para evitar dependência de worker indexing. Esta última tentativa precisa de resultado registrado.
- Python 3.11 consta como suportado na documentação atual: https://learn.microsoft.com/en-us/azure/static-web-apps/languages-runtimes. Não reduzir TLS nem contratar plano pago para contornar falha sem diagnóstico.
- Produção permanece no serviço nativo existente; fase 1 **não concluída**. Build de 188 páginas e testes unitários não equivalem a cadastro em produção validado.

### Retomada concreta

1. Verificar resultado de `.tmp/clerk-homolog-binding-deploy.log` (não versionar logs ou settings). Script requer `-AzureCli az` nesta máquina; caminho portátil antigo não existe.
2. Exigir capabilities Clerk, SQL real, CORS, rejeição de tokens e assinatura/replay de webhook antes de testes de navegador. Não repetir upload inalterado após a mesma falha.
3. Validar fluxo dev em localhost:4027 ou homolog privada; loopback permitido somente em homolog. Contas sintéticas apenas em dev/homolog.
4. Preparar produção isolada após homolog: schema aditivo, novo runtime, PEM/JWKS live, HMAC estável e webhook; preservar settings/artefato antigos para rollback. Não guardar material privado no Git.
5. Preservar corpus recente do remoto AnderZilla-Web; rebuild-production.py tem baseline antigo. Promover feature → homolog → produção somente após testes reais, incluindo e-mail, CPF, saída, exportação e exclusão.

## Homologação publicada — continuação dos testes

- Upload nativo SWA retornou Succeeded após empacotamento com bindings HTTP explícitos. O CLI Node ficou sem progresso visível; diagnóstico pelo cliente oficial capturou resultado sem expor credencial. Staging em diretório temporário local.
- Encontrado defeito de inicialização real: dois decoradores HTTP na mesma função lançavam ValueError ao importar o módulo. Rotas agora têm wrappers separados; novo teste importa o entrypoint e exige dois triggers distintos.
- SWA substitui Authorization no salto interno. Frontend envia **X-AnderZilla-Authorization**; API continua validando JWT Clerk, emissor, origem e sessão. Em SWA ignora Authorization da plataforma. Função dedicada aceita o cabeçalho próprio e mantém compatibilidade com Authorization padrão. Teste de regressão cobre a separação.
- Probes remotos: capabilities200/providerclerk/availabletrue; me anônimo200; origem estranha403; bearer falso401; webhook falso400; webhook assinado200 com transação SQL; repetição200. Somente IDs sintéticos inexistentes em homolog, nenhuma pessoa criada/excluída por esses probes.
- Primeiro webhook válido retornou503 durante ativação do banco serverless; após SQL online e conexão validada, execução remota passou. Preservada configuração SQL gratuita com AutoPause. Não marcar cenário de banco frio resolvido; UX/retry ainda precisa de validação.
- **Atenção ao CORS real:** OPTIONS retorna204 sem Access-Control-Allow-* porque SWA intercepta o preflight. Status204 isolado não valida CORS. Tentativa com globalHeaders também não resolveu. Portanto o navegador local não consegue usar diretamente o hostname remoto com cabeçalho próprio; não declarar homolog web pronta por probes HTTP.
- Para testar o fluxo de UI sem mudar produção, servidor loopback localhost:4027 encaminha /api para homolog. Build local usa NEXT_PUBLIC_ACCOUNT_API_BASE=http://localhost:4027; isso é apenas ferramenta de teste, não artefato publicável. Resolver homolog web com mesma origem (API junto da SWA privada) ou Function App dedicada antes da promoção. Produção já usa Function App dedicada; validar CORS ali separadamente.
- Navegador carregou Clerk dev, gate18+, cadastro por e-mail e confirmação com código reservado de teste. Identidade sintética somente dev: anderzilla.phase1+clerk_test@example.com. Isso **não valida entrega real de e-mail**. Onboarding privado ainda em teste; nenhuma aprovação de termos reais pelo operador foi simulada.
- Build frontend com chaves públicas dev aprovado. Suíte atual: **64 testes aprovados**, incluindo import do host, cabeçalho de autenticação e erro503 com origem exata sem detalhes privados.
