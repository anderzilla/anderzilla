# Contas e personalização — gap em 17/09/2026

Análise solicitada pelo BRIEF 0, anterior às alterações de autenticação desta execução. Código observado, não auditoria de produção nem parecer jurídico.

## Rotas e superfícies

`model.ts` define `#home`, `#saved`, `#quiz`, `#profile`, `#channels`, `#sponsor`, `#live`, `#agenda`, `#points`, `#store`. Idioma: `?lang=pt|en`; categoria: `?category=…`. Artigos: `/[lang]/radar/[slug]`; páginas CMS: `/[lang]/pages/[slug]`. Trust/Commerce adiciona produtos, forgekit, stackpick, parceiros, patrocine, transparencia e hubs Brasil/Internacional em PT/EN. `/privacy` e `/terms` existentes são ingleses; rotas bilíngues de política/cookies e consentimento ainda são entrega do novo brief.

## Matriz

| Feature | Personaliza? | Dados locais hoje | Exige conta? | Sincronização proposta | Risco de privacidade a revisar |
|---|---|---|---|---|---|
| Idioma | Sim | Query URL; estado React | Não; conta para persistir entre dispositivos | Preferência explícita no perfil; URL prevalece na navegação | Baixo; preferência vinculada à conta |
| Interesses/feed | Sim | Seis categorias em `interests`; ranking no `Hub.tsx` | Não para explorar | Importação opcional; atualizar seleção versionada | Perfil de interesses; transparência e minimização |
| Mochila | Sim | IDs `saved` | Não localmente | Mesclar IDs válidos com confirmação; remoções precisam de regra de conflito | Histórico de interesses |
| Aberto/surpresa | Sim | IDs `opened`; evita repetir descoberta | Não | Sincronização opcional; retenção limitada | Histórico de leitura; não é prova de consumo humano |
| Quiz/missões | Sim | `quizDone`, `claims` adulteráveis | Somente crédito oficial exige sessão verificada | Servidor valida versão/evidência; token temporário e uso único | Antifraude proporcional; evitar coleta excessiva |
| Saldo/extrato | Sim | Soma de `pointRules` sobre claims | Sim para ledger oficial | API por sujeito autenticado; nunca aceitar saldo/award/accountId do navegador | Integridade e isolamento de conta |
| Perfil | Sim | Interesses; botão limpar dados locais | Conta para nome, email e gestão | API de nome/idioma/interesses/fuso; marketing separado | Identificação, exclusão/exportação e retenção |
| Store Points | Condicional | Catálogo demonstrativo, sem direito real | Conta e estoque para resgate futuro | Backend autoritativo; nenhuma conversão do saldo demo | Endereço/entrega somente quando necessário |
| Busca, filtro, canais, live, agenda, comércio | Não exige identidade | Busca/filtro React e configuração publicada | Não | Manter leitura e links públicos | Embeds/lojas têm contextos próprios |

## Quebras a prevenir

`HubProvider.tsx` grava `anderzilla-hub-demo-v1`; `claim()` e `completeQuiz()` adicionam claims no navegador e `balance` soma 25/100 KP. Apenas bloquear botões não protege crédito. Substituir a origem oficial do saldo e a conclusão de missão; manter anônimo jogando e personalizando. Perfil, teaser, Points e extrato devem distinguir demonstração, convite pendente, conta não verificada, saldo real e falha da API.

Não copiar `claims`, `quizDone` ou saldo local para ledger. Token pendente precisa de expiração, vínculo ao navegador, consumo único e revalidação da missão. Logout/revogação devem limpar dados de conta em memória; falha de rede não pode apresentar demo como saldo oficial.

## Evidências e dependências

- `apps/web/src/components/hub/{HubProvider,Hub,Rewards,model}.tsx|ts`: persistência, ranking, quiz/perfil/Store e contratos locais.
- `services/rewards/{README.md,core.py,schema.sql}`: domínio SQLite, ledger e anti-replay existentes; sem listener HTTP/Azure. Verificador padrão rejeita evidência. Reutilizar regras, implementar adaptador autenticado e persistência durável; testes SQLite não comprovam concorrência Azure SQL.
- Admin Entra e autenticação da demo ForgeKit não são conta visitante. Baseline não apresenta serviço público de identidade.
- Google depende de configuração OIDC real; email depende de remetente/entrega verificados. Instagram não foi verificado nesta análise: adiar botão até pesquisa oficial e configuração válidas.

UX: convidar após conquista, com Criar conta / Entrar / Agora não; preservar progresso local sem prometer crédito. Importação de preferências deve ser explícita e distinta de recompensa. Validar foco inicial, Escape, retorno de foco, reduced motion e PT/EN em 320–1440px. Revisão jurídica deve resolver idade mínima, finalidades, retenção e política KP; texto provisório não equivale a conformidade certificada.
