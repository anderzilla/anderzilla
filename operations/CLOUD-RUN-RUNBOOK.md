# Cloud Run — worker de automação em homologação

## Estado operacional — 10/09/2026

O piloto privado `anderzilla-automation-worker` está ativo no projeto `anderzilla-homolog` (727980282274), região `southamerica-east1`, sob a identidade operacional `player.one@anderzilla.com`. Azure Static Web Apps continua hospedando o portal e o domínio; este worker apenas executa processos auxiliares e não altera o site público.

- URL autenticada: `https://anderzilla-automation-worker-kx7kuixj6q-rj.a.run.app`
- Revisão pronta: `anderzilla-automation-worker-00004-lzv`, com 100% do tráfego.
- Imagem imutável: `southamerica-east1-docker.pkg.dev/anderzilla-homolog/anderzilla-automation/worker@sha256:9fa9d7472040d9a609376a3936d99a85c00494c1bf7379dd7a15222ce3e13c72`.
- Runtime: `anderzilla-automation-runtime@anderzilla-homolog.iam.gserviceaccount.com`, sem papéis adicionais de projeto.
- Limites: zero instâncias mínimas, uma máxima, concorrência 1, 1 CPU, 512 MiB, timeout de plataforma 45 segundos e CPU por requisição.
- IAM: nenhuma concessão `allUsers` ou `allAuthenticatedUsers`. Smoke test anônimo retornou 403; chamada autenticada retornou 200.
- Processos do piloto: `editorial-package` determinístico e `seo-audit` determinístico. Não há chamada a LLM, publicação ou promessa de ranking. O `seo-audit` recebe uma execução persistida do CMS e devolve resultado autenticado com hash canônico.
- Validação real: 131 testes locais do worker e 108 do CMS; build Cloud Build `8446ded8-2f52-423e-a5a8-13e48fa0cd32`; auditoria ponta a ponta `c758b0ce-3071-46dd-843b-b8b17fd22a7a` concluída com HTTP 200, 8 verificações aprovadas, 3 alertas e 0 falhas.

O CMS Azure e o worker estão ligados sem chave JSON. O Cloud Run obtém um token OIDC da própria conta runtime e o envia em cabeçalho dedicado; o CMS valida assinatura Google, emissor, audiência, subject, email verificado e validade antes de conceder um lease. A fila mantém idempotência durável, lease de dois minutos, fencing token, no máximo três entregas e conclusão com hash canônico. A concorrência 1 também protege o cache transitório do endpoint direto. O allowlist é fixo aos hosts AnderZilla/Azure documentados e cada salto refaz a checagem de DNS público; não existe pinagem de IP, portanto o risco teórico de alteração de DNS permanece registrado.

O Cloud Scheduler `anderzilla-automation-poll` está habilitado em `southamerica-east1` e chama `/v1/poll` às 10h, 14h, 18h e 22h em `America/Sao_Paulo`. Ele usa a conta exclusiva `anderzilla-scheduler@anderzilla-homolog.iam.gserviceaccount.com`, com `roles/run.invoker` somente no serviço. Duas execuções manuais do agendador chegaram ao Cloud Run com HTTP 200. O intervalo reduz ativações e pode deixar uma execução aguardando até a próxima janela; o botão do CMS continua permitindo registrar a fila a qualquer momento.

O faturamento foi vinculado somente a `anderzilla-homolog`. As APIs Run, Artifact Registry, Cloud Build, IAM e Billing Budgets foram habilitadas nesse projeto. O orçamento `AnderZilla homolog Cloud Run` é de R$50/mês, com alertas em 50%, 80% e 100%; alertas não interrompem o consumo. `anderzilla-production` não foi vinculado nem alterado.

O repositório Artifact Registry `anderzilla-automation` e a conta runtime foram criados apenas em homologação. A conta de build padrão recebeu leitura somente no bucket de fontes, escrita somente nesse repositório e `logging.logWriter` no projeto, após o primeiro build falhar por falta de `storage.objects.get`.

As seções históricas abaixo descrevem a fundação e decisões anteriores. Quando houver conflito, este estado operacional é a evidência mais recente.

## Atualização — Google Cloud liberado parcialmente

Após o proprietário concluir etapas no console, a criação dos projetos `anderzilla-homolog` (727980282274) e `anderzilla-production` (710416906845) foi concluída com sucesso sob `player.one@anderzilla.com`. O erro de termos foi superado. O projeto inicial `lithe-resource-508205-a6` foi preservado.

A conta de faturamento visível, “Minha conta de faturamento”, informa moeda BRL e `open: false` (fechada). Não foi vinculada aos projetos. É necessário o proprietário reabrir/regularizar essa conta ou disponibilizar outra conta ativa. A causa do fechamento não foi determinada pela API.

Nenhum serviço Cloud Run, registry, imagem ou recurso de execução foi implantado. Projetos foram criados sem faturamento; conta/configuração padrão e recursos CodeMatrix preservados. Esta atualização substitui o bloqueio anterior por termos descrito nos registros históricos. A definição de orçamento adicional vs total permanece pendente.

Verificado localmente em 10/09/2026. Código: `Z:/AnderZilla/infra/gcp`; workflows: `Z:/AnderZilla/.github/workflows`. Terraform validado com provider oficial Google 7.46.1, registrado no lockfile. Nenhum projeto, faturamento, IAM remoto ou serviço foi criado nesta etapa. A identidade autorizada é `player.one@anderzilla.com`; o campo Terraform registra intenção, não comprova controle da conta.

## Arquitetura e limites

São exigidos dois projetos GCP **já existentes**, distintos, com IDs iniciados por `anderzilla-`, informados pelo operador: homolog e production. Não usar automaticamente o projeto legado ForgeKit ou recursos CodeMatrix. Cada projeto terá Artifact Registry Docker `anderzilla`, conta runtime `anderzilla-web-runtime` sem concessão de papéis e um serviço `anderzilla-web-<ambiente>`. As APIs Run, Artifact Registry e IAM são geridas por Terraform e preservadas em destroy.

Cada serviço usa 1 CPU, 512Mi, CPU ociosa liberada/cobrança por requisições, zero instâncias mínimas e uma máxima, timeout 60s e concorrência 40. Tanto limite por serviço quanto por revisão são configurados. Esses parâmetros reduzem consumo, mas não garantem teto financeiro nem disponibilidade sob carga. Custos também incluem armazenamento de imagens, transferência e logs; mudanças de revisão podem ter comportamentos transitórios. Ver [limites de instâncias Cloud Run](https://cloud.google.com/run/docs/configuring/max-instances).

Homolog não recebe `allUsers`. Production também começa privada; acesso público requer `production_public=true` em plano revisado. Ingress aceita tráfego de rede externo, porém IAM exige autenticação enquanto não houver concessão pública. Não existe IAP, domínio ou balanceador provisionado. Não importar um serviço previamente público sem revisar seu IAM: o módulo não remove concessões herdadas ou externas. Deletion protection permanece ativa; o repositório tem prevent_destroy.

Imagens são referenciadas por digest, no registry do próprio projeto. Cleanup mantém as dez versões recentes e remove versões com mais de 30 dias fora da retenção. Isso pode limitar rollback antigo: preservar fora da limpeza qualquer release que precise retenção maior antes de publicar política em produção.

## Pré-requisitos externos antes do primeiro deploy

1. Login CLI de `player.one@anderzilla.com` confirmado na auditoria coordenada; listagens de projetos e billing retornaram vazias. Isso comprova autenticação, não autorização de infraestrutura. Confirmar organização, visibilidade, IDs/números dos dois projetos, regiões, billing e autorização antes do bootstrap. Nunca recorrer ao default CodeMatrix para contornar ausência de acesso. `owner_identity` e `GCP_OWNER_IDENTITY` são guardas declarativas: exigir evidência IAM/organização/billing dos IDs aprovados; igualdade de strings não comprova propriedade.
2. Definir o orçamento com o proprietário. Existe referência a R$150, mas ainda é necessário esclarecer se inclui assinaturas existentes ou é verba adicional. Não converter isso em autorização para consumo sem limite.
3. Preparar armazenamento de state privado com acesso limitado e locking suportado. O template não fixa backend porque ainda não existe destino aprovado; executar init com configuração do backend antes de aplicar. State/plan/tfvars locais são ignorados; lockfile deve acompanhar código. Nunca manter state no ramo de documentação.
4. Configurar previamente GitHub Environments `homolog` e `production` com restrições de branches, aprovação de produção e pessoas autorizadas. Verificar disponibilidade dessas proteções para o plano de repositório privado. Nomear environment no YAML **não cria proteção**. Impedir bypass administrativo quando possível. Proteger main/develop com CI e revisão.
5. Criar fora deste template o WIF pool `anderzilla-github`, provider `github` e SA `anderzilla-deployer` em cada projeto. Não criar chaves JSON. Restringir condição do provider ao ID numérico do repositório e do proprietário, ref adequada e subject `repo:OWNER/REPO:environment:AMBIENTE`; obter valores reais do GitHub antes de configurar. Nunca aceitar apenas nome livre de organização como fronteira de confiança.
6. Conceder à identidade federada impersonação `roles/iam.workloadIdentityUser` somente na SA de deploy do ambiente. Conceder ao deploy Artifact Registry writer somente no repositório, Run developer no escopo necessário, Service Account User somente na runtime SA e leitura mínima para checar projeto. A SA de produção também necessita Artifact Registry reader no registry homolog e permissões Run viewer para conferir serviço/revisão homolog; não recebe escrita no homolog. Não dar Owner/Editor nem permissões de IAM write ao deploy. Operador Terraform usa permissões de infraestrutura separadas. Validar permissões efetivas na primeira homologação. Referência: [Google GitHub auth](https://github.com/google-github-actions/auth).

Configurar estas variáveis GitHub: `ANDERZILLA_HOMOLOG_PROJECT_ID` e `ANDERZILLA_PRODUCTION_PROJECT_ID` como allowlist aprovada, mais `ANDERZILLA_HOMOLOG_REGION` para localizar o artefato de origem; por environment, `GCP_PROJECT_ID`, `GCP_PROJECT_NUMBER`, `GCP_REGION`, `GCP_DEPLOY_SERVICE_ACCOUNT`, `GCP_WIF_PROVIDER`, `GCP_OWNER_IDENTITY`. Não são segredos. SA deve ser `anderzilla-deployer@PROJECT_ID.iam.gserviceaccount.com`; provider deve ser `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/anderzilla-github/providers/github`. O workflow compara esses valores antes do OAuth e verifica projeto/conta novamente após autenticar. Revisores devem verificar que variáveis de environment não sobrescrevem indevidamente a allowlist.

## Bootstrap sem dependência circular da primeira imagem

Terraform exige digest real para criar os serviços, mas antes do primeiro push o registry precisa existir. O caminho de bootstrap é explícito e não foi executado:

1. Operador autorizado habilita APIs e cria **somente** o registry Docker `anderzilla` nos projetos existentes, pela interface oficial ou CLI com conta/projeto/região explícitos. Isso é bootstrap pontual, não segunda fonte de configuração permanente. Preparar WIF e permissões acima.
2. Publicar os workflows na branch padrão pelo fluxo de revisão. workflow_dispatch precisa existir na branch padrão para ficar disponível. Executar `bootstrap-image` em develop/homolog: compila, constrói e publica imagem com label de commit. Integrar esse commit em main por PR. Executar `bootstrap-image` em main/production com `homolog_digest` do summary: copia exatamente a imagem homolog, verifica ancestralidade do commit e igualdade de digest, sem rebuild. Nesse modo inicial não exige Cloud Run homolog existente e não atualiza serviço algum. A exceção permite preencher os dois digests reais antes do primeiro Terraform apply; não representa homologação ou autorização para exposição pública.
3. Preencher `owner_identity` e `environments` em arquivo tfvars local ignorado. Cada ambiente tem `project_id`, `region` e `image` no formato `REGION-docker.pkg.dev/PROJECT/anderzilla/web@sha256:DIGEST_REAL`. Não usar zeros, tags latest ou IDs sugeridos como se fossem recursos reais.
4. Importar cada registry existente para `google_artifact_registry_repository.web["homolog"]` / `["production"]` com ID `projects/PROJECT/locations/REGION/repositories/anderzilla`. Importação requer os mesmos inputs reais. APIs habilitadas podem ser geridas pela declaração sem recriação. Verificar todo plano para impedir replacement, destruição ou projeto inesperado.
5. Executar plan, revisar e aplicar apenas após confirmar alvo e orçamento. Esse passo cria runtime SAs e serviços privados com as imagens iniciais. Conferir URI, IAM, limites, readiness e conta runtime. Homolog é acessível somente por usuário com Run invoker e autenticação/proxy apropriados.

A estratégia de bootstrap mantém digest obrigatório e evita imagem fictícia. Não usar `terraform -target` como rotina de operação nem ignorar validações para iniciar recursos.

## Releases e rollback

CI roda em PRs e pushes para main/develop e executa npm ci/build para web e forgekit com Node 22. O ramo de documentação não dispara esse CI. Deploy é manual, exclusivo de web: homolog exige develop e é o único ambiente que compila/constrói imagem. Production exige main e input `homolog_digest`; copia o artefato homolog para seu próprio registry, recusando qualquer alteração do digest, sem reconstruir. Não usa source build nem Cloud Build. Conferir alinhamento de versão Node entre CI e Dockerfile antes do primeiro release.

Para release de produção, o workflow confirma que a revisão homolog está pronta, corresponde à última criada, recebe 100% do tráfego e usa exatamente o digest solicitado. Lê da própria imagem o SHA de origem e exige que seja ancestral de main. Isso comprova inclusão do commit, não identidade com todo o HEAD atual: o summary registra o commit realmente promovido. Revisores devem aprovar esse commit específico e os testes funcionais autenticados de homolog. Readiness não substitui smoke test, revisão editorial ou validação de compra. A cópia por Docker foi desenhada para a imagem de plataforma única produzida pelo workflow; mudança futura para multiarch exige promoção preservando manifestos e novo teste.

Existe concorrência entre os ambientes: homolog pode avançar depois da verificação. A promoção permanece fixada no digest validado, portanto não captura a imagem nova. Aprovação deve nomear digest e commit, não apenas dizer “última homolog”.

Modo `release` chama `gcloud run services update --image=...` com projeto, região e conta explícitos. `update` exige serviço existente e altera a imagem, sem criar serviço nem modificar IAM. Terraform controla demais configurações e ignora mudança da imagem, client e client_version para não desfazer releases. A configuração de tráfego aponta para latest; verificar esse estado antes de liberar ambiente importado. Registrar SHA/digest/resultado no log de release e testar rota pública ou autenticada conforme ambiente.

Rollback: selecionar digest previamente aprovado ainda retido, conferir projeto/serviço/conta e usar a mesma atualização de imagem. Não reutilizar tags mutáveis nem fazer rollback para imagem removida. Após rollback, testar readiness e conteúdo, registrar motivo e corrigir código em branch. Nenhum workflow de rollback automático ou monitor foi provisionado.

## Orçamento e condição de abertura pública

Criar monitor de orçamento com alertas escalonados para o gasto dos dois projetos e responsável identificado antes da publicação. **Monitor com alertas não é hard cap**: alertas podem chegar depois do consumo e não interrompem faturamento. Limite de uma instância tampouco garante R$150. A documentação atual distingue alertas e recursos de spend cap em preview; não pressupor elegibilidade ou cobertura. Ver [Cloud Billing budgets](https://cloud.google.com/billing/docs/how-to/budgets).

Sem confirmação do teto disponível, billing, WIF, proteções GitHub e leitura de custos, manter somente a fundação local. Não duplicar infraestrutura em Azure nesta fase. Assinatura Azure ativa identificada em outra parte da auditoria não significa crédito confirmado nem necessidade de segundo ambiente cloud.

## Verificação desta entrega

- Terraform fmt, init com `-backend=false` e validate: executados localmente, sem plan/apply e sem leitura de cloud.
- Provider selecionado e assinado por HashiCorp: google 7.46.1; lockfile criado.
- YAML e contratos básicos do workflow: verificados localmente; nenhum job GitHub executado.
- Builds de apps e teste Docker completo: responsabilidade da validação final coordenada; registrar resultado real, não inferir sucesso deste runbook.
- IAM efetivo, deploy OIDC, custo e funcionamento remoto: pendentes dos pré-requisitos; o template não representa serviço ativo.


## Atualização da auditoria final

A tentativa de criar os dois projetos falhou por termos Google Cloud pendentes. Nenhum projeto foi criado. O operador deve concluir o onboarding com player.one e então confirmar billing e IDs reais.

`infra/gcp/plan.ps1 -VarFile <arquivo-local>` oferece plan com token temporário explícito da configuração anderzilla, restaurando a variável de ambiente ao terminar. Não grava token nem executa apply. O backend de estado tem autenticação própria a configurar e verificar; não assumir que esse wrapper resolve acesso ao backend. Plan ainda não foi executado, pois faltam projetos, billing e imagens reais.

Dockerfiles e CI usam Node 22. O script legado ForgeKit foi substituído por atualização de serviço existente com conta/projeto/região e digest explícitos; não cria IAM público nem injeta segredo de exemplo. A infraestrutura Terraform desta fase cobre web, não migra automaticamente o ForgeKit legado.
