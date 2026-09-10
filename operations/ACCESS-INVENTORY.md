# Inventário de acessos — 10/09/2026

**Direção atual:** Azure Static Web Apps Free é a hospedagem principal. Produção e homolog publicados; DNS web alterado na Wix, email Google preservado. Estado de HTTPS e acesso privado em [registro Azure](AZURE-RELEASE.md). As seções GCP abaixo registram o histórico anterior.

## Atualização — Google Cloud liberado parcialmente

Após o proprietário concluir etapas no console, a criação dos projetos `anderzilla-homolog` (727980282274) e `anderzilla-production` (710416906845) foi concluída com sucesso sob `player.one@anderzilla.com`. O erro de termos foi superado. O projeto inicial `lithe-resource-508205-a6` foi preservado.

A conta de faturamento visível, “Minha conta de faturamento”, informa moeda BRL e `open: false` (fechada). Não foi vinculada aos projetos. É necessário o proprietário reabrir/regularizar essa conta ou disponibilizar outra conta ativa. A causa do fechamento não foi determinada pela API.

Nenhum serviço Cloud Run, registry, imagem ou recurso de execução foi implantado. Projetos foram criados sem faturamento; conta/configuração padrão e recursos CodeMatrix preservados. Esta atualização substitui o bloqueio anterior por termos descrito nos registros históricos. A definição de orçamento adicional vs total permanece pendente.

Registro interno. Endereço informado, sessão autenticada e permissão operacional são evidências diferentes. Não contém tokens ou dados de pagamento.

| Recurso | Evidência | Estado e ação |
|---|---|---|
| Google `player.one@anderzilla.com` | Login gcloud concluído nesta sessão | Configuração isolada `anderzilla`; conta padrão CodeMatrix preservada. Listas de projetos, organizações e faturamento vazias. Criação de `anderzilla-homolog` e `anderzilla-production` falhou por termos de uso pendentes: **nenhum dos dois projetos existe por esta operação**. Proprietário precisa concluir onboarding/termos e disponibilizar faturamento. |
| Cloud Run ForgeKit legado | Consulta autenticada somente leitura | Serviço `forgekit` em projeto legado `forgekit-mm-3703`, região southamerica-east1; demo existente preservada. Migração não executada. |
| Domínio anderzilla.com | DNS público consultado | Nameservers Wix; correio Google. Acesso ao painel Wix não confirmado. Preservar MX/SPF/DKIM/DMARC ao alterar somente a hospedagem web. |
| `anderzilla.gameplay@gmail.com` | Informada pelo proprietário; mensagem histórica de assets de live encontrada em busca restrita | Incluída como conta adicional de criação/games. Login direto, propriedade do canal YouTube e permissões não verificados. Não vincular automaticamente ao canal. |
| `anderzilla@ymail.com` | Portal Microsoft autenticado | Microsoft 365 Personal ativo, R$51/mês; Xbox Game Pass Ultimate ativo, R$76,90/mês. OneDrive 1 TB. Copilot Pro aparece expirado em 23/07/2024. Não presumir GitHub Copilot ou crédito Azure incluído. |
| Azure | Portal autenticado da conta ymail | Azure subscription 1 ativa, permissão Owner, nenhum recurso listado. Portal informa 58 serviços gratuitos não utilizados e validade de serviços gratuitos até 09/05/2027. Não foi comprovado saldo monetário promocional. Nenhum recurso novo criado. |
| GitHub | gh CLI autenticado | `anderzilla`, repositório AnderZilla privado. Conector separado usa `AnderzillaDev`: não confundir identidades. Worktrees e branches locais preparados; execução remota de CI/OIDC não comprovada. |
| Google Drive/Gmail conectores | Perfil consultado | Conectados a outra conta pessoal. Busca limitada a referências AnderZilla encontrou assets históricos; não equivalem a acesso às contas do projeto. |
| Redes e lives | URLs confirmadas pelo proprietário e perfis lidos no Chrome | TikTok 10,3 mil seguidores; Instagram 77; YouTube 224 inscritos/43 vídeos; Twitch 2 mil seguidores arredondados; Kick 5. SOCIAL-CHANNELS.md contém evidência e limites. Painéis analíticos, receita e elegibilidade não verificados. |
| IA | Execuções nesta sessão | Três subagentes Codex e consulta real ao Claude CLI. Gemini e Copilot CLI não encontrados; benefícios Copilot atuais não confirmados. |

## Orçamento

O proprietário definiu teto inicial de R$150/mês; permanece pendente se adicional ou total. Se incluir Microsoft 365 + Xbox, restam **R$22,10/mês**. Se adicional, reservar até R$80 para nuvem/armazenamento/tráfego, R$20 para serviços operacionais e R$50 de contingência, como envelopes de planejamento, não previsão de fatura. Câmbio, impostos, domínio e renovação precisam entrar no controle quando aplicáveis.

Nenhum recurso pago novo foi ativado. Começar com ferramentas já disponíveis, produção orgânica e um único provedor principal. Alertas de orçamento não são um teto garantido de cobrança. Só parametrizar orçamento de nuvem após confirmar moeda e conta de faturamento.

## Acessos mínimos seguintes

1. Concluir termos/onboarding Cloud sob player.one e disponibilizar billing; confirmar projetos criados antes de executar infraestrutura.
2. Abrir YouTube Studio, Twitch dashboard, Kick dashboard, Instagram profissional e TikTok Studio nas contas corretas para inventário de audiência, região, recursos comerciais e permissões.
3. Confirmar relação entre gameplay Gmail e YouTube; usar convites/permissões de canal quando disponíveis, sem compartilhar senha.
4. Confirmar Wix/DNS e painel Gumroad para domínio, produto, preço real, arquivos entregues e métricas. Link comercial foi fornecido pelo proprietário; venda e entrega não foram testadas nesta fase.
5. Confirmar Gamertag Xbox e perfis Steam/Discord/PSN/Nintendo que deseje exibir. `@anderzilla` é uma indicação geral, não evidência de cada identificador.

Estado autenticado é um retrato desta sessão e deve ser revalidado antes de alterações. Fontes públicas de benefícios e integrações estão nos relatórios de pesquisa; valores de assinaturas acima vieram do portal autenticado.
