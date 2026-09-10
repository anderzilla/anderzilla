# AnderZilla — dossiê de preparação

## Atualização — Google Cloud liberado parcialmente

Após o proprietário concluir etapas no console, a criação dos projetos `anderzilla-homolog` (727980282274) e `anderzilla-production` (710416906845) foi concluída com sucesso sob `player.one@anderzilla.com`. O erro de termos foi superado. O projeto inicial `lithe-resource-508205-a6` foi preservado.

A conta de faturamento visível, “Minha conta de faturamento”, informa moeda BRL e `open: false` (fechada). Não foi vinculada aos projetos. É necessário o proprietário reabrir/regularizar essa conta ou disponibilizar outra conta ativa. A causa do fechamento não foi determinada pela API.

Nenhum serviço Cloud Run, registry, imagem ou recurso de execução foi implantado. Projetos foram criados sem faturamento; conta/configuração padrão e recursos CodeMatrix preservados. Esta atualização substitui o bloqueio anterior por termos descrito nos registros históricos. A definição de orçamento adicional vs total permanece pendente.

**10 de setembro de 2026.** AnderZilla é a marca pessoal de tecnologia, IA, games e gadgets de Anderson, com conteúdo descontraído, comunidade e receita própria. A atuação profissional permanece na CodeMatrix. O projeto começa em português e inglês, com ambição internacional e limite informado de R$150/mês.

## Resultado desta fase

Foram preparados inventário de contas, pesquisa de monetização, plano editorial, kit comercial, revisão entre IAs, agentes/skills/RAG locais e configuração de entrega. O polimento de vitrine existente mantém ForgeKit e StackPick como caminhos comerciais. A nova arquitetura editorial bilíngue está especificada, ainda não totalmente implementada no site.

**Publicação nova bloqueada:** o login Google correto funcionou, mas a criação dos projetos falhou por termos de uso pendentes. Billing não foi listado nessa conta. Nenhum projeto, serviço ou recurso pago novo foi criado nesta fase. A demo ForgeKit legada permanece disponível no ambiente existente.

## Ativos confirmados

- Domínio anderzilla.com, com DNS Wix e correio Google; acesso de administração DNS ainda não verificado.
- Conta Google de infraestrutura: player.one@anderzilla.com. Conta adicional de games/criação: anderzilla.gameplay@gmail.com, informada pelo proprietário.
- Conta Microsoft/Xbox anderzilla@ymail.com: Microsoft 365 Personal e Game Pass Ultimate ativos, total observado R$127,90/mês. Azure ativa com Owner e serviços gratuitos temporários; nenhum crédito monetário presumido.
- Cinco canais fornecidos pelo proprietário: [TikTok](https://www.tiktok.com/@anderzilla), [Instagram](https://www.instagram.com/anderzilla/), [YouTube](https://www.youtube.com/@anderzilla-tv), [Twitch](https://www.twitch.tv/anderzillacwb) e [Kick](https://kick.com/anderzilla). Leitura pública no Chrome mostrou 10,3 mil seguidores TikTok, 77 Instagram, 224 inscritos/43 vídeos YouTube, 2 mil seguidores Twitch (valor arredondado exibido) e 5 Kick. Painéis analíticos, emails administradores e receita não auditados. Esses números não medem audiência ativa nem se somam como pessoas únicas.
- Repositório GitHub privado AnderZilla, produto ForgeKit, comparativos StackPick, ferramentas locais Codex/Claude e ativos históricos de live referenciados por email. Direitos e atualidade dos assets precisam de revisão antes de reutilizar.

O [inventário operacional](operations/ACCESS-INVENTORY.md) diferencia login, permissão e pendências; o [mapa social](operations/SOCIAL-CHANNELS.md) registra cada canal sem inventar audiência.

## Estratégia de receita

O site deve transformar curiosidade em retorno recorrente: descoberta nas redes, conteúdo útil no hub e oferta contextual. Priorizar demonstrações próprias, comparativos com critérios e utilidade real; não construir uma vitrine genérica de links afiliados.

1. **ForgeKit:** CTA claro para [Gumroad](https://anderzilla.gumroad.com/l/edkel), demonstração, conteúdo entregue e limitações. Preço, entrega e vendas precisam de confirmação no painel.
2. **StackPick:** comparativos rastreáveis e atualizados; links oficiais enquanto afiliação não estiver aprovada. Identificar publicidade e conflitos comerciais.
3. **Patrocínios:** formatos de vídeo, live, newsletter futura e conteúdo patrocinado, vendidos com audiência e entregas verificáveis. Kit rascunhado sem depoimentos, marcas ou números inventados. Nenhuma prospecção enviada.
4. **Receita de plataformas:** habilitar assinaturas, apoio e anúncios apenas quando houver elegibilidade real. Twitch/Kick/YouTube têm requisitos e termos distintos; consultar [pesquisa](research/monetization.md) e [canais](operations/SOCIAL-CHANNELS.md).

Produzir em português e adaptar peças prioritárias ao inglês. Um conteúdo principal pode gerar cortes e posts para as cinco redes, respeitando formato, direitos de música/jogos e regras de multistream. Cadência é hipótese até informar horas disponíveis. [Plano editorial](strategy/EDITORIAL-90-DAYS.md) e [kit comercial](strategy/SPONSOR-KIT-DRAFT.md) são materiais para execução, sem promessa de receita.

## Tecnologia e operação

Cloud Run é o provedor principal proposto, sob a conta do domínio. Homologação privada e produção separadas, escala mínima zero e máxima inicial um por serviço. Limites reduzem exposição, mas não garantem teto de cobrança. Azure aproveita benefícios verificados em laboratório quando necessário; não duplicar produção por disponibilidade de conta.

Código está em `codex/anderzilla-foundation`; documentação e ferramentas de IA em branch órfã `codex/anderzilla-docs`, worktree irmão. O fluxo planejado é feature -> develop/homolog -> main/produção. Workflows e Terraform preparados não equivalem a pipelines remotos ou ambientes executados. Ver [fluxo](operations/DEVELOPMENT-FLOW.md) e [runbook](operations/CLOUD-RUN-RUNBOOK.md).

Foram criados seis perfis de agentes, quatro skills e um RAG local com busca/leitura delimitadas. Adaptadores locais para Codex/Claude apontam à documentação; o novo MCP requer recarregar sessão para descoberta pelo cliente. Microsoft Learn é documentação pública, não acesso a recursos Azure. Google Developer Knowledge permanece candidato dependente de configuração. Veja [operação de IA](ai/OPERATING-MODEL.md) e [revisão real entre IAs](decisions/AI-REVIEW.md).

## Decisões e lacunas

É necessário definir se R$150 é adicional ou inclui as assinaturas existentes; nesse segundo caso sobram R$22,10. Próximos acessos: onboarding/billing Google, painéis das cinco redes, Wix, Gumroad e identificadores de jogos. Nenhum endereço de email comprova automaticamente acesso ao canal ou licença de produto.

As fontes oficiais e limites da pesquisa estão nos relatórios de [monetização](research/monetization.md), [presença/jogos](research/gaming-presence.md) e [arquitetura](research/architecture-review.md). Falhas de leitura pública não foram convertidas em afirmações de ausência. O [plano por fases](strategy/ROADMAP.md) define o caminho para executar sem confundir preparação com publicação.
