# Trust & Commerce — operação editorial

Implementação local do prompt em 17/09/2026. Publicação de código/CMS e entrega em Azure são etapas distintas; este trabalho não executa deploy.

## Rotas e mercados

Os dois idiomas (`pt` e `en`) têm `/produtos`, `/forgekit`, `/comercio/brasil`, `/comercio/internacional`, `/stackpick`, `/parceiros`, `/patrocine` e `/transparencia`, sempre sob `/{lang}`. Idioma não seleciona mercado: conteúdo `br` pertence ao Brasil, `intl` ao Internacional e `global` pode aparecer nos dois. Os caminhos antigos `/forgekit` e `/stackpick` continuam disponíveis.

## Cadastro no Admin

| Coleção | Uso |
|---|---|
| `products` | Produtos próprios, preço em centavos, moeda, loja, checkout e demonstração |
| `affiliate_placements` | Links aprovados de afiliados, mercado e identificação comercial |
| `ad_placements` | Publicidade identificada, aprovação e vigência |
| `sponsor_packages` | Escopos de patrocínio, sem inventar marcas, contratos ou métricas |
| `trust_blocks` | Textos de transparência em português e inglês |
| `feature_flags` | Visibilidade dos recursos por mercado |
| `market_hubs` | Títulos, resumos e conteúdo dos hubs Brasil/Internacional |

Campos comuns: `market`, `status` comercial e textos PT/EN. Ofertas e chamadas comerciais usam `currency`, `store`, `ctaUrl`, `disclosureKey`, `disclosurePT` e `disclosureEN` conforme o tipo. `approvalReference` é referência interna de evidência, não um lugar para credenciais ou documentos pessoais; não integra o JSON público.

`status` comercial (`candidate`, `active`, `paused`, `ended`) não é a aprovação editorial do registro. Aprovar um rascunho não transforma um candidato em parceiro contratado. Registros inativos não geram chamadas comerciais públicas.

Os módulos antigos `offers`, `affiliates` e `campaigns` permanecem no Admin para consulta/migração, mas seus registros não são mais exibidos no hub nem exportados como ofertas públicas. Recrie os registros revisados nas novas coleções; essa transição é intencional para não publicar links sem o novo contrato.

Antes da primeira publicação com o CMS atualizado, cadastre ForgeKit em `products` com `slug=forgekit`, `market=intl`, `currency=USD`, `store=Gumroad`, preço `14900` e os links oficiais. O fallback conhecido só existe para snapshots antigos sem a coleção `products`; uma coleção vazia é uma decisão editorial de não exibir produtos. Para um banco **local**, `python services/cms/seed_commerce.py --database CAMINHO_LOCAL` cria esse produto como rascunho de maneira idempotente; não aprova nem publica. No ambiente remoto, use o Admin e revise as condições atuais.

## Editar e publicar

1. Entre no Admin com papel autorizado e confira o ambiente mostrado no cabeçalho.
2. Abra a coleção e crie/edite o registro. Escolha o mercado explicitamente; preencha PT e EN, moeda/loja quando aplicáveis e disclosure próximo da oferta.
3. Para afiliados/anúncios, confira a aprovação real e o destino HTTPS antes de definir o estado comercial `active`. Mantenha candidatos como `candidate` e programas suspensos como `paused`.
4. Salve o rascunho e use a prévia do editor para revisar o conteúdo. A prévia não constitui publicação nem substitui conferir o site gerado.
5. Aprove a revisão. Em **Publicações**, crie a publicação com as revisões aprovadas. A fila e seu snapshot são persistidos pelo CMS existente.
6. O executor existente importa o snapshot, valida campos públicos, constrói o site e acompanha a entrega. Só `deployed`, com verificação do destino, significa publicação concluída. `queued` ou `approved` não significam que o visitante já vê a alteração.
7. Confira PT/EN nos dois mercados e a moeda/loja/disclosure de cada CTA. Um conteúdo global aparece nos mercados habilitados; trocar idioma preserva a página/mercado.

O executor em `services/publisher/run_release.py` publica no destino visual isolado já configurado. A promoção homolog → produção continua pelo fluxo Azure do projeto; não é realizada por salvar um registro. Ocultar/arquivar requer uma nova publicação para retirar conteúdo do artefato servido.

## Flags

Chaves previstas: `showProducts`, `showAffiliatesBr`, `showAffiliatesIntl`, `showAds`, `showSponsor`, `showPointsStore`, `showMarketBr`, `showMarketIntl`. Cadastre a chave e o mercado, mantenha o registro comercial `active` e altere `enabled` para ligar/desligar a apresentação. Aprovar e publicar também são necessários para flags.

Karaca Points permanece demonstrativo, sem compra de pontos, saque ou resgate real. Habilitar apresentação não provisiona carteira, estoque ou permissões de recompensas.

## Evidência e limites

- Validação CMS/publisher: 115 testes CMS e 24 testes publisher passaram. O pacote montado com a lista real de arquivos de `infra/azure/deploy-admin.ps1` importou API, domínio comercial e Azure Function com as dependências isoladas. O script inclui `commerce.py`; a API aceita as novas coleções com `_`.
- Builds finais de `apps/web` e `apps/admin` passaram. Export web contém as 16 rotas comerciais; redirecionamentos legados estão no artefato Azure. Revisão no navegador confirmou layout desktop, filtro BR/INT em inglês e ausência de overflow na largura móvel testada.

- Em 17/09/2026, leitura pública do Gumroad retornou HTTP 200, produto ForgeKit e preço estruturado USD 149,00. A demo Cloud Run também retornou HTTP 200. Isso não verifica pagamento, entrega do ZIP nem payout do operador.
- A demo legada ainda contém texto “Polar-ready” nos metadados; sua migração é independente das páginas do hub implementadas aqui.
- Brasil: narrativa BRL, com C6/PIX como operação interna. Internacional: USD e destino Wise conforme os meios permitidos pela plataforma; Gumroad/PayPal não é promessa de depósito direto em Wise. Nenhum dado bancário integra o cadastro público.
- Nenhum candidato afiliado, patrocinador ou anúncio foi ativado por esta implementação. PartnerStack continua pausado; 21/09/2026 é a primeira data prevista para reavaliar candidatura, sem ativação automática.
- Inventário dos demais documentos: [PROMPT-EXECUTION-AUDIT.md](PROMPT-EXECUTION-AUDIT.md).
