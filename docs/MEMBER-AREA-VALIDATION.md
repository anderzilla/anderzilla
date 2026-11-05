# Validação independente da entrega Antigravity

Data: 05/11/2026. Base entregue: `428816f`, branch `codex/member-area-antigravity`. Validação Codex após autorização expressa do proprietário para publicar, condicionada a resolver bloqueios reais.

## Resultado inicial

Os83 testes da entrega e o build passaram. Isso não bastou para aprovar o commit original: parte da matriz de UI verificava strings no código, e a migração002 divergia do schema usado no runtime. O commit428816f não deve ser publicado isoladamente.

## Correções para publicação

- Migração002 alinhada às definições Azure SQL canônicas, incluindo NVARCHAR compatível, nomes de colunas, tipos e constraints. Rollback destrutivo substituído por recusa explícita: preservar coleções e ledger.
- Resposta incorreta de missão grava estado failed antes de retornar rejeição; não permite reutilizar a mesma tentativa por rollback acidental.
- Versão de interesses e geração exata de exploração obrigatórias. Limpar/remover avança geração; eventos antigos/futuros recusados.
- Troca de subject/sessionId limpa estado antes da pintura e respostas verificam identidade/epoch antes e depois do JSON. Invalidação multiaba não reabre automaticamente uma sessão em encerramento.
- Confirmação e consulta de claim usam a mesma chave idempotente; pendência não é transferida entre contas.
- Campanha ausente não cria cobertura automática de500KP. Ocorrência padrão estável por missão, sem nova recompensa só por versão técnica.
- Retirada gravação automática de mochila no retorno ao artigo; confirmação explícita fica no fluxo central.
- Revalidação da mesma conta não desmonta formulário/lista durante salvar. Texto de exploração descreve abertura, sem alegar leitura; perfil não é anunciado como público.
- Detalhe de missão tem shell estático genérico com ID validado, sem depender de rebuild para cada nova missão. KP permanece desabilitado em produção.

## Evidências e limites

- Suíte local independente ampliada:88 testes aprovados, incluindo regressões novas de tentativa, campanha ausente, versão, geração e contrato de migração. Logs locais privados em .tmp/member-review-fixed-tests.log.
- Build original e builds de revisão aprovados; release exige novo manifesto do candidato final, sem tratar build de teste como artefato de produção.
- Migração aditiva aplicada em **homologação**, executando fluxo real pelo usuário SQL runtime: onboarding, dashboard, interesses, mochila, exploração/limpeza, carteira desativada e exportação. Todas as linhas sintéticas desse teste foram revertidas na transação. Administrador Entra temporário removido.
- Testes locais de navegador usam identidade sintética via helper de loopback; não comprovam login Clerk live ou CORS de produção. A verificação de produção deve registrar separadamente o que foi observado com sessão real.
- Não houve alteração de dados reais de usuários nesta validação. Não usar conta do proprietário para exclusão ou concessão artificial de KP.
- A identidade visual mais recente também está registrada em docs/brand/IDENTITY-RELEASE-2026.md (lettering e acentos quentes aprovados); preservar esse baseline, sem redesenhar marca.

## Escopo da liberação

Liberar dashboard, navegação/perfil e coleções pessoais somente após os builds finais e smoke de homologação/produção com manifests registrados. **KP/missões com concessão real ficam desligados**, aguardando regras, cobertura e aceite próprios. Código preparado de recompensas não é aprovação econômica nem catálogo ativo.

Preservar o corpus público e as mídias por comparação do sitemap/manifesto vigente; backup privado dos settings da Function App capturado antes do release e retenção PITR SQL de7 dias consultada. Publicação, hashes, schema e resultado final devem constar em MEMBER-AREA-RELEASE-REPORT.md. Não declarar a entrega inteira100% validada só por testes de fonte ou por respostaHTTP.
