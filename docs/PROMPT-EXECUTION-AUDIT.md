# Auditoria dos prompts em docs

Data: 2026-09-17 (America/Sao_Paulo). Escopo: todos os 10 arquivos presentes em `docs/` no início da solicitação, comparados com o código local e as fontes canônicas de `Z:/AnderZilla-docs`. Este relatório não comprova estado de produção, aprovação de programas comerciais nem histórico de execução de outra sessão.

O usuário pediu executar `TRUST-AND-COMMERCE-CMS-PROMPT.md` e **verificar** os demais prompts. Portanto, roteiros, exemplos e comandos contidos nos outros documentos foram tratados como itens a auditar, sem autorização implícita para cadastros, outreach, compras ou publicação em produção.

## Inventário e situação inicial

| Documento | Natureza | Evidência no início desta execução | Tratamento |
|---|---|---|---|
| `TRUST-AND-COMMERCE-CMS-PROMPT.md` | Prompt principal | Havia ForgeKit e mecanismos genéricos de CMS/publicação; faltavam rotas Trust/Commerce e sete coleções comerciais com `market`. | Implementação executada nesta solicitação; conclusão e validações locais registradas abaixo. |
| `BRIEF-trust-commerce-br-intl.md` | Brief A, recorte do prompt principal | Rotas editoriais em `apps/web/src/app/[lang]/[section]/[slug]/page.tsx` aceitavam apenas `radar` e `pages`; hubs BR/INT e Trust ainda não existiam. | Incluído no prompt principal; não é outra tarefa a repetir. |
| `BRIEF-trust-commerce-cms-market.md` | Brief B, recorte do prompt principal | `services/cms/core.py` tinha `offers`, `affiliates` e `campaigns`; publisher exportava afiliados sem mercado. `market` do módulo de automação não supria o cadastro comercial. | Incluído no prompt principal: contrato, formulário, validação, preview e snapshot precisam concordar. |
| `BRIEF-trust-commerce-copy-br-intl.md` | Brief C, recorte editorial | Copy comercial existia no hub, mas não havia Trust nem hubs BR/INT dedicados. | Incluído no prompt principal: PT/EN, disclosure, mercado/moeda/loja e estados vazios. |
| `BRIEF-trust-commerce-live-karaca.md` | Anexo de regras ao brief C | `Community.tsx` já filtrava broadcast por `checkedAt`/`expiresAt`; `model.ts` mantinha broadcast nulo. `HubProvider.tsx` usava `anderzilla-hub-demo-v1`; `Rewards.tsx` informava ausência de resgates reais. | Parcial já existente; incorporar explicações à Trust. O anexo não autoriza transformar KP em produção. |
| `ROTEIRO-TORNAR-REAL.md` | Roadmap operacional em fases | Fase 1 corresponde aos briefs A/B/C. Há código editorial, CMS, worker e rewards, mas isso não comprova implantação nem operação comercial. | Parcial; pendências independentes listadas abaixo. Não executar automaticamente todas as fases. |
| `LOAD-SPLIT-trust-commerce.md` | Distribuição de responsabilidades | Referencia os mesmos briefs A/B/C e responsáveis externos. | Referência de coordenação, sem entrega adicional autônoma. Não comprova que mensagens ou atividades externas ocorreram. |
| `CANDIDATES-AFFILIATES-BR.md` | Lista de candidatos | O próprio documento registra nenhum ativo; exige aprovação e URL HTTPS verificada. | Não é prompt de implementação. Candidaturas e ativação continuam pendentes de evidência. |
| `MONETIZATION-PROCESS-REGISTER.md` | Registro vivo | Cópia local estava atrasada em relação à canônica: faltavam processos Karaca patrocinado/fornecimento e controle de automações; hubs/Trust ainda estavam especificados. | Sincronizar com a canônica e registrar avanço local sem declarar implantação. |
| `NEWSROOM-IMPORT.md` | Runbook de operação existente | `Newsroom.tsx` implementa importação, histórico e aprovação opcional desligada por padrão; `services/cms/import_newsroom.py` preserva registros por slug/fonte e oferece `--approve`; publisher suporta fontes e imagem social. | Implementação correspondente encontrada; não há manifesto solicitado ou importação pendente identificável neste documento. Operação real e produção não auditadas aqui. |

## Pendências além do prompt principal

1. **Release da Fase 1:** executar homologação, revisão visual e promoção Azure quando autorizadas. Código/build local não satisfaz o critério separado do roteiro “200 em produção”. Scripts em `infra/azure/` e workflows existentes são instrumentos, não prova de deploy.
2. **Validação comercial ForgeKit:** o roteiro ainda pede confirmação no painel de disponibilidade do ZIP e payout. A informação canônica de produto ativo não comprova uma nova auditoria do painel nesta sessão.
3. **Primeira afiliação BR/INT:** escolher candidatos, inscrever quando autorizado, obter aprovação e URL de tracking e só então cadastrar placement ativo com disclosure/mercado. Não há evidência documental suficiente para promover candidatos. PartnerStack permanece pausado até pelo menos 2026-09-21; chegar à data não constitui aprovação.
4. **Checkout BRL:** decisão Kiwify/Hotmart/Stripe BR e produto real ainda são planejamento; não há autorização para lançar ou contratar neste pedido.
5. **Distribuição e cadência:** agenda de lives confirmada, posts sociais, contatos comerciais e captura/envio/opt-out de newsletter dependem de operação específica. Código de canais, kit social ou página Patrocine não comprova execução dessas ações.
6. **Automação editorial:** `services/cms/automation.py`, `apps/admin/src/components/AutomationControl.tsx` e `services/automation-worker/` comprovam implementação parcial. A documentação canônica registra worker homolog privado, mas não fecha por si toda a Fase 4: bundle único, fonte editorial real → rascunho → revisão → publicação e relatório de cobertura exigem evidência própria. Planejamento de cortes não equivale a renderização de vídeo.
7. **Karaca em produção:** existem domínio e testes em `services/rewards/`, mas a interface pública permanece demo. Verba/coorte, autenticação e integração autoritativa pública, contratos, direitos, estoque e piloto continuam gates separados. Não concluir “backend inexistente”; a pendência é a operação integrada comprovada.
8. **Escala:** anúncios vendidos, receita nativa de plataformas e segundo produto continuam condicionados às evidências e decisões do roteiro. Homologação privada deve respeitar o papel `anderzilla_reviewer` exigido pelo AGENTS vigente; a formulação histórica “se precisar” do roteiro não revoga essa regra.

## Resultado da execução atual

- Implementadas 16 rotas (oito superfícies em PT/EN), incluindo hubs BR/INT, ForgeKit, produtos, StackPick, parceiros, patrocine e transparência. Links legados preservados com redirecionamentos Azure.
- Sete coleções comerciais integradas ao Admin/CMS/publisher, campos de mercado, flags, aprovação editorial, estados comerciais e snapshot público. API aceita nomes com `_`; pacote Azure inclui o novo módulo.
- 115 testes CMS e 24 publisher passaram. Importação do pacote API montado pela allowlist real passou com dependências isoladas. Dez verificações frontend exercitaram flags e fallback; as 16 páginas exportadas foram verificadas.
- Builds finais `npm run build` de `apps/web` e `apps/admin` passaram, incluindo export estático (web: 46 páginas totais). `git diff --check` passou. Nenhum build de ForgeKit era necessário: essa aplicação não foi alterada.
- Revisão visual em navegador local: hub Internacional PT desktop e catálogo EN em largura móvel 390px; filtro Brasil mostra vazio, Internacional restaura ForgeKit; sem overflow horizontal observado (375px úteis).
- Registro canônico e cópia local sincronizados; processos em `em_build` refletem implementação local sem implantação. Nenhuma candidatura, mensagem comercial, anúncio ou resgate real foi executado.
- Publicação Azure permanece pendente, conforme exclusão explícita do prompt. Antes da primeira publicação do CMS atualizado, migrar registros comerciais legados e cadastrar/aprovar ForgeKit: coleção `products` vazia desativa o fallback por decisão editorial. Ver [guia do editor](TRUST-COMMERCE-EDITOR-GUIDE.md).

Este inventário evita duplicar briefs: os cinco documentos de implementação são partes da mesma entrega Trust & Commerce. As outras pendências são predominantemente release, operação editorial/comercial e evolução de produto, não cinco prompts novos a executar em sequência.
