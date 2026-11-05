# Cadastro fase 1 — execução e continuidade

Última atualização: 2026-11-04. **Em implementação, não publicado.**

## Onde continuar

- Código: `G:/AnderZilla`, branch `codex/registration-phase1-20261104`.
- Documentação: `G:/AnderZilla-docs`, branch `codex/anderzilla-docs`.
- Escopo/decisões: `strategy/ACCOUNTS-AND-ACCESS-PHASES.md`.
- Alterações preexistentes no código e na documentação devem ser preservadas; adicionar/commitar somente arquivos desta entrega.
- O worktree documental apontava para Z:; `git worktree repair G:/AnderZilla-docs` restaurou a associação ao repositório em G:, sem alterar conteúdo editorial.

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
- Nome do operador e contato público para privacidade/contas solicitados ao proprietário.
- Procedimento Clerk para consentimento parental verificável precisa ser confirmado antes de ativar menores, em especial abaixo de 16 anos.
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
