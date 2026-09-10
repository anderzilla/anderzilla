# CMS editorial — implantação em homologação

Data: 10/09/2026. Deploy real concluído pelo script `infra/azure/deploy-admin.ps1`, SWA CLI 2.0.10, exit 0.

- URL: https://victorious-mud-09355980f.3.azurestaticapps.net
- Recurso: anderzilla-admin-homolog, SKU Free, assinatura 44b76346-26bd-4cd3-a529-627e47e99e5a. Guard confirmou conta anderzilla@ymail.com e tenant autorizado.
- Fonte: base Git bb5e093 com alterações de trabalho editoriais e automações coordenadas. Não representa commit fechado.
- Pacote API: `.deploy/admin-api-14d3f9871e634e3e95f403623175c162`, dependências Linux CPython3.11 e automation.py incluídos.
- SHA256 apps/admin/out/index.html: E0F246FE2C030DA6FFB89AD424333FBDCA5716F91EEE390736FB8D8E2CDCC23F.
- Validação anterior: 28 testes CMS, 18 publisher e build admin completo. SQL runtime com TLS validado: health ready; agregado de quota de mídias conferido com contagem anterior.
- Smoke após deploy: /, /api/session, /api/admin/health, /api/admin/records/content e /api/admin/automation/processes retornaram 302 para login Microsoft quando anônimos. A configuração converte 401 em 302; não houve exposição anônima.
- Smoke autenticado posterior será realizado na sessão Microsoft existente; nenhum cookie foi extraído para o operador.

O pacote inclui campos de apuração/fontes e kits sociais, importador de manifesto pela UI, capas e imagens sociais na biblioteca, cópia de textos e download do card vertical. O deploy não criou as 60 matérias e não publicou o portal público. A importação editorial e o publisher seguem etapas separadas.

Rollback não executado: reconstruir uma revisão anterior validada em checkout isolado e reaplicar o deploy somente ao recurso admin homolog, mantendo dados e schemas aditivos. Validar compatibilidade dos campos novos antes de permitir edições por uma API antiga; preferir correção progressiva se houver incompatibilidade. Não apagar registros, revisões ou tabelas como parte de rollback de aplicação.

## Refinamento social posterior

Redeploy real concluído em 10/09/2026, pacote .deploy/admin-api-4bef6da15f5b4ff387e7e3fee4b46553. API idêntica por hash ao pacote anterior. Painel remove duplicação de URL/hashtags já presentes na legenda e oferece download PNG da imagem social por conversão local no navegador; armazenamento CMS permanece WebP. Quatro casos de composição e build admin passaram. Smoke anônimo / e /api/session: 302 para login. SHA256 do index.html: 9ACA6F473E860937BA3F26E666152A457E2D2E0D25CCC88A61CA459D1A9DCBC6. Smoke do download autenticado fica para a sessão do proprietário.

## Correção dos seletores de imagem

Novo deploy real concluído: pacote .deploy/admin-api-2b528363ba6d4bc8a8c25018929f1afe. Control.tsx agora usa field.key em valor, alteração, prévia e remoção dos seletores coverMediaId/socialMediaId; nome acessível usa field.label. Verificações dos dois seletores passaram em todos esses comportamentos e build admin passou. Smoke anônimo /api/session: 302 login. SHA256 index: 1D05A5E4145FEDA0F27DF69D586271EE8FB46680D2CE1CA09D841D21CA66A2E7. Nenhum schema ou registro foi alterado por esta correção.
## Otimização da validação de publicação

Deploy real concluído após o publisher confirmar a publicação c77440a8-558f-4780-a990-6438cf14e9f7. Pacote admin-api-5f4f92bd5c424f11a3782377d4f37128. Somente core.py difere da API anterior; todos os sete arquivos empacotados correspondem por SHA256 às fontes locais. Core SHA256: 3DA5F41587B2E7C0AD50FA5CA3FC199453A9DDC692B1EBDC17967FB1C462E127. Index do painel SHA256: 1D05A5E4145FEDA0F27DF69D586271EE8FB46680D2CE1CA09D841D21CA66A2E7.

CMS.release agora carrega cada coleção uma vez dentro da transação e resolve referências no índice temporário. Cache não atravessa transações nem afeta save(). Testes confirmam uma leitura por coleção, ausência de consultas individuais de referências, equivalência integral ao snapshot anterior, idempotência sem novas leituras, detecção de slugs duplicados e mídia arquivada após uma publicação anterior. 30 testes CMS e 18 publisher passaram. Nenhuma release adicional foi criada para testar desempenho; o ganho temporal em produção não foi medido.

Smoke anônimo após deploy: /, /api/session, /api/admin/releases e /api/admin/health retornaram302 para login Microsoft. Não houve alteração de schema, cadastros ou configuração de autenticação.