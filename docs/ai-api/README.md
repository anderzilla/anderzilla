# API para agentes de IA — fase 1 (diagnóstico e contrato)

Status: **rascunho**. Nada aqui foi implementado nem implantado, e nenhum recurso Azure foi criado.

## Diagnóstico do que existe (`services/cms`, `apps/admin`)

- 118 testes do `services/cms` passam (Python 3.12, dependências instaladas fora do repo).
- Domínio sólido e reaproveitável: coleções com campos fechados, validação (HTTPS público, slugs, datas com fuso, SEO, fontes 1–20), versão otimista (409), revisões, auditoria, snapshot de release com chave de idempotência.
- Autenticação hoje: cabeçalho de principal do Azure Static Web Apps (login Microsoft, papéis `anderzilla_admin|editor|commercial|rewards`) e OIDC de worker. **Não existe credencial para agente.**
- Estados de um registro: `draft`, `approved`, `archived`. Só registros aprovados entram no snapshot.
- Release termina em `queued`; o resto (build, homolog) é o operador rodando `services/publisher/run_release.py` à mão, e só publica o slot visual de homolog. **Não há promoção para produção nem rollback no CMS.**
- Mídia: base64 dentro do SQL, 2 MB por imagem, 32 MB no total, sem buscar imagem por URL.
- Não há coleção de banners (hoje `hero-banners.ts`), nem validação em modo simulação, nem comentários de revisão.
- A API gerenciada do SWA limita o corpo a 300 KB (2,9 MB no upload de mídia).

## O que o contrato acrescenta (`openapi.yaml`)

1. Chave por agente (hash, escopo, validade, revogável) e papel `anderzilla_agent`: cria rascunhos, sobe mídia e envia pacote; **nunca aprova nem publica**.
2. `articles:validate` (simulação), upsert idempotente de artigo, `media` por URL ou base64, `banners`.
3. **Submission** (pacote de alterações) com rodadas, comentários e solicitação de correções.
4. Aprovar, promover para produção e rollback: só credencial humana.

## Página de revisão (separada, protegida pela Azure)

Endereço planejado: `https://revisao.anderzilla.com` (SWA Free próprio, domínio personalizado), sem relação com o host da API.

- **Autenticação:** o mesmo login Microsoft/Azure do painel atual. A rota `/*` exige o papel `anderzilla_admin` (como em `apps/admin/public/staticwebapp.config.json`); anônimo é redirecionado ao login e recebe `noindex`. Chaves de agente **não** funcionam nesse host.
- **O que você vê:** lista de pacotes pendentes; cada item renderizado como o site mostra (alternância desktop 1440 px / mobile 390 px), fontes, créditos e licenças das imagens, e a comparação com a versão anterior quando for atualização.
- **O que você faz:**
  - **Aprovar** o pacote: aprova os registros de uma vez e enfileira o release em homolog.
  - **Comentar** em um registro ou campo específico e **Pedir correções**: o pacote vai para `changes_requested`.
  - Depois de conferir em homolog, **Promover para produção** (confirmação explícita) ou **Rollback**.
- **Como a IA recebe os comentários:** `GET /submissions/{id}/comments` (e o status). A IA corrige os rascunhos, chama `resubmit` e a rodada seguinte aparece na mesma página, com os comentários resolvidos marcados.
- A decisão humana nunca vem de um agente: as rotas de aprovação aceitam apenas o principal do SWA com `anderzilla_admin`.

## Fluxo

1. Agente lê `GET /schema`, monta o artigo e valida com `articles:validate`.
2. Sobe imagens (`/media`) e grava rascunhos (`/articles`, `/banners`).
3. Envia `POST /submissions` e informa o `reviewUrl` ao Anderson.
4. Anderson abre a página, comenta ou aprova. Se pediu correções, o agente lê os comentários e reenvia.
5. Aprovado: release em homolog; após a conferência, promoção para produção (humana) e verificação.

## Fase 2 — núcleo implementado (somente local, com testes)

Código em `services/cms/agent_api.py` (testes em `test_agent_api.py`; suíte completa do CMS: 133 passando, publisher: 25). Nenhum recurso Azure foi criado.

- **Chaves por agente:** `create_key`/`revoke_key` (só humano). A chave `azk_<id>_<segredo>` aparece uma vez; o banco guarda só o hash SHA-256, com escopo por coleção e validade (1–365 dias).
- **Rotas:** `handle(...)` implementa schema, `articles:validate`, artigos (upsert idempotente por `key`), mídia (base64 ou URL), banners, pacotes, comentários, pedir correções, reenviar, aprovar e status de release.
- **Banners:** nova coleção `banners` no `core.py` (imagem aprovada obrigatória; links internos `/…` ou HTTPS público).
- **Mídia por URL:** HTTPS na porta 443, lista de domínios obrigatória (`AGENT_MEDIA_HOSTS`; vazia rejeita tudo), só endereços públicos, sem redirecionamentos, 2 MB. Risco residual: o DNS pode mudar entre a checagem e o download, por isso a lista de domínios é obrigatória.
- **Aprovação humana:** só o principal do SWA com `anderzilla_admin` aprova, comenta e pede correções. Aprovar é atômico: se um registro falhar, os já aprovados voltam a rascunho. Um rascunho alterado depois do envio invalida o pacote (409).
- **Proteção de conteúdo no ar:** editar um artigo já aprovado o tira do ar até nova aprovação, então o servidor exige `allowEditPublished=true`.
- **Ainda não feito:** servidor HTTP, prévia privada (501), promoção e rollback (501, dependem do pipeline), página de revisão (fase 3), leitura do site a partir do banco (fase 3), conectores OpenAPI/MCP (fase 5).
- **Limitação do `validate`:** o domínio de validação levanta o primeiro erro; a simulação devolve um erro por chamada (campos obrigatórios ausentes vêm todos juntos na mesma mensagem).

## Fase 3 — página de revisão e banners do banco (somente local, com testes)

- **Banners no site:** o publisher (`import_snapshot.py`) agora publica a coleção `banners` em `cms-published.json` e `hero-banners.ts` os usa no carrossel antes do Karaca (fallback). Com `banners: []` o site é idêntico ao de hoje.
- **Prévia fiel:** `preview_site.py` constrói o site real com um snapshot em que os rascunhos do pacote contam como aprovados (`CMS.snapshot(overlay)`). Não grava nada no CMS nem publica. Se o pacote não for publicável, o motivo aparece na página (ex.: campo obrigatório ausente).
- **Servidor local:** `services/publisher/review_local.py` (porta 8788 = API + página; 8789 = prévia). Só loopback, token de pelo menos 32 caracteres vindo do ambiente (`REVIEW_LOCAL_TOKEN`), nunca no código.
- **Página de revisão:** `apps/review` (Next.js, exportação estática, tokens do manual de identidade): lista de pacotes, cada notícia/banner/imagem renderizados, alternância PT/EN, prévia fiel em iframe (desktop 1440 / mobile 390), comentários por registro e campo, **Pedir correções** e **Aprovar e enviar a homolog**. Em produção a rota `/*` exige o papel `anderzilla_admin` (login Microsoft).
- **Verificado de ponta a ponta no navegador** com um pacote de demonstração: lista, detalhe, prévia, comentário e pedido de correções. A prévia mostrou o banner do banco no carrossel e a notícia marcada como demonstração.
- **Limites conhecidos:**
  - Um site de prévia por vez no servidor local (o site usa caminhos absolutos); em Azure, cada prévia precisará de seu próprio endereço (fase 4).
  - O banco local de demonstração não tem as 71 notícias e as 242 imagens atuais, que vivem no banco Azure `anderzilla-cms-homolog`. A comparação com a produção (idêntico) só pode ser feita com acesso a esse banco; fica para a fase 4.
  - O iframe aponta para `http://127.0.0.1:8789`; o app ainda não tem implantação (sem SWA, sem API gerenciada).
  - Banner comercial: o campo `disclosure` aparece na faixa do banner.

## Decisões ainda abertas

- Papel novo `anderzilla_agent` e tabela de chaves (hash) no banco do CMS.
- Estados novos (`pending`, `changes_requested`, `rejected`, `published`) e tabelas de submissão e comentários.
- Hospedagem da API fora do SWA (Azure Functions, no estilo do `anderzilla-identity-api`) por causa do limite de corpo.
- Promoção a produção automatizada (GitHub Actions ou Functions). O `deploy.ps1` manual continua sendo o caminho vigente.
- Armazenamento de imagens em Blob em vez de base64 no SQL.
