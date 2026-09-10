# AnderZilla — revisão independente de arquitetura e estratégia

Data: 10 de setembro de 2026. Natureza: recomendação de planejamento; nenhum recurso cloud foi alterado nesta revisão. Fontes locais lidas: AGENTS.md, docs/CONTEXT.md, docs/BRIEF-polish-vitrine.md, .codex/instructions.md, .codex/project.json, Dockerfiles dos dois aplicativos e apps/forgekit/AGENTS.md. Valores financeiros abaixo são envelopes de planejamento, nunca previsão de receita nem cotação de serviços.

## Decisão central

AnderZilla deve ser uma publicação pessoal sobre experimentar tecnologia e se divertir: IA aplicada, games, gadgets e ferramentas de desenvolvedor. CodeMatrix continua responsável pelo posicionamento de consultoria e serviços profissionais. O site precisa transmitir experiência real sem parecer uma agência. A credibilidade pode aparecer em uma bio breve e nas demonstrações; um catálogo de competências corporativas não deve dominar a página inicial.

O pedido atual substitui duas premissas antigas do repositório: inglês exclusivo e apresentação essencialmente séria de vitrine. A nova direção é PT/EN, personalidade e entretenimento com qualidade editorial. ForgeKit continua uma oferta comercial concreta, mas dentro de uma seção de produtos. StackPick passa a ser uma série de comparações úteis baseada em experiência e fontes, e não a razão de existir de todo o site.

A estratégia mais agressiva sustentável é aumentar a quantidade de experimentos úteis por mês e melhorar sua conversão. Multiplicar fornecedores, servidores, agentes e publicações automáticas não mede esse resultado. A restrição inicial de R$150 mensais exige disciplina de arquitetura e de pauta.

## Evidências, desconhecidos e acesso

Os documentos locais registram dois aplicativos Next.js e um deployment anterior de ForgeKit no projeto forgekit-mm-3703. Há imagens Docker em múltiplos estágios e execução sem root. Na leitura inicial não existia diretório .github; portanto não havia evidência local dessa esteira antes do trabalho atual. Isso não demonstra ausência de automações externas.

O agente coordenador informou que o CLI Google tem contas pessoais/CodeMatrix e projeto padrão CodeMatrix, mas não player.one@anderzilla.com; Azure CLI estava ausente. Também informou divergência entre identidade GitHub do CLI e do conector. Esses são achados do inventário paralelo, não autenticações realizadas por esta revisão. É fundamental fixar conta e projeto explicitamente em cada operação, sem reutilizar o contexto padrão de CodeMatrix.

Não há nesta análise prova de créditos Azure, licenças de GitHub Copilot, audiência, receita, associação a programas de afiliados ou permissões de publicação social. A posse de um endereço Microsoft e de uma assinatura Xbox não deve entrar no plano financeiro como crédito de infraestrutura. Benefícios e validade precisam ser observados na conta correta. As condições públicas de conta gratuita Azure dependem de elegibilidade, prazo e limites; não confirmam qualquer benefício individual. [Microsoft: conta gratuita e cobranças](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/avoid-charges-free-account).

## Infraestrutura mínima de homologação e produção

Recomendo Google Cloud como nuvem principal, controlada pela identidade AnderZilla. Azure permanece uma opção documentada para experimentos que tenham benefício comprovado ou necessidade específica. Duas nuvens ativas duplicariam controle de acesso, faturamento, diagnóstico, implantação e superfície de falha antes de existir demanda que justifique isso.

Criar homologação e produção isoladas, preferencialmente em projetos próprios, com identidades de execução distintas. O custo do isolamento deve ser avaliado pelos serviços usados, não pelo simples número de projetos. Começar com instâncias mínimas zero, cobrança adequada a requisições e limite conservador de escala. Homologação deve exigir autenticação e não ter checkout real, dados reais de assinantes ou indexação pública. A documentação Cloud Run confirma o uso de autenticação/IAM em serviços privados. [Cloud Run: autenticação](https://docs.cloud.google.com/run/docs/authenticating/overview).

A implantação deve construir uma imagem identificada por digest, validá-la em homologação e promover esse mesmo artefato para produção. Rollback significa redirecionar para a revisão anterior conhecida. Não construir uma segunda imagem silenciosamente no momento de promover. Aprovações de produção e permissões devem ser verificadas contra o plano GitHub disponível; não assumir que todo recurso de proteção existe no repositório privado atual.

Preferir OIDC/Workload Identity Federation entre GitHub Actions e Google Cloud, restrito ao repositório, ambiente e identidade esperados. Evitar chaves JSON persistentes no GitHub. O fluxo oficial troca a identidade OIDC por credenciais temporárias. Azure oferece padrão equivalente caso seja adotado depois. [Google: federação para pipelines](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines), [GitHub: OIDC no Azure](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure).

Usar páginas pré-renderizadas e imagens otimizadas. Vídeos e lives ficam nas plataformas de distribuição; armazenar e servir vídeo bruto no hub consumiria orçamento sem resolver a descoberta de audiência. Não acrescentar banco relacional, Redis, Kubernetes, busca vetorial hospedada ou balanceamento multirregional nesta fase. O Dockerfile ForgeKit usa SQLite de exemplo no build: isso não comprova persistência de dados em produção e precisa ser auditado antes de oferecer qualquer fluxo stateful real.

## R$150: orçamento operacional e limite técnico

Como envelope inicial, reservar R$80 para infraestrutura, builds, armazenamento e transferência; R$20 para APIs pontuais; R$50 para margem de variação. Se assinaturas existentes precisarem entrar nesse mesmo teto, reduzir os envelopes antes de habilitar consumo. Não comprometer toda a reserva com publicidade. Preços dependem de região, uso, câmbio, tributos e modalidade; usar a calculadora e a tabela oficiais após definir o projeto. [Cloud Run: preços](https://cloud.google.com/run/pricing).

Configurar alertas de 50%, 80% e 100%, revisão semanal de consumo, retenção limitada de logs e imagens antigas e nenhuma instância mínima permanente sem necessidade medida. Limitar escala reduz explosões de capacidade, mas não transforma a fatura inteira em custo fixo. Quando toda a capacidade fica ocupada, requisições podem falhar; acompanhar esse efeito antes de aumentar limites. [Cloud Run: limites de instâncias](https://docs.cloud.google.com/run/docs/configuring/max-instances-limits).

Uma atualização importante: a documentação atual oferece spend cap budgets em preview e inclui Cloud Run. O escopo é um projeto e um serviço; usa estimativas brutas, tem atraso de aplicação, permite cobrança excedente e não interrompe todos os custos persistentes. Avaliar disponibilidade e configurar abaixo do teto com reserva; não apresentar isso como garantia matemática de R$150. Budgets apenas de alerta não limitam consumo. [Google: spend caps](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps), [Google: budgets e alertas](https://docs.cloud.google.com/billing/docs/how-to/budgets).

No Azure, limites dependem do tipo de assinatura; pay-as-you-go não oferece o mesmo spending limit das contas com créditos. Alertas e eventual automação precisam ser desenhados à parte. Essa diferença reforça a necessidade de conferir o benefício efetivo antes de ativar outra nuvem. [Microsoft: spending limit](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/spending-limit).

## Documentação separada e IA reproduzível

Atender ao pedido de uma branch documental com worktree próprio: estratégia, decisões, pesquisas, inventário sem segredos, playbooks, prompts e skills canônicos ficam ali. Não fazer merge indiscriminado dessa branch no código. Vincular cada ciclo de desenvolvimento a um commit conhecido da documentação para que uma decisão possa ser reconstruída depois.

Existe uma tensão prática: GitHub Actions e infraestrutura executável precisam acompanhar o código que implantam. Recomendo manter workflows, Dockerfiles e scripts de implantação no fluxo de desenvolvimento, e documentação de arquitetura e ferramentas editoriais na branch documental. Para ferramentas de IA usadas no desenvolvimento, utilizar bootstrap local que leia a revisão documental fixada. Assim a separação solicitada não torna o build dependente de arquivos ocultos de uma máquina.

Começar com quatro papéis, acionados por tarefa: pesquisador que coleta evidências; editor que transforma experiência em roteiro PT/EN; revisor comercial que valida links e alegações; engenheiro que implementa e verifica. Eles podem ser executados por recursos já disponíveis, sem contratar quatro plataformas. Cada tarefa deve declarar entrada, saída, responsável final e condição de conclusão. Nenhum agente publica por inferência, envia propostas comerciais sem autorização ou usa uma recomendação recebida como fato.

RAG inicial deve ser um acervo Markdown/JSON indexado localmente, com URL, data, autor, nível de confiança, prazo de revisão e distinção entre informação pública e privada. Busca textual basta enquanto funciona. Adicionar embeddings somente quando perguntas reais demonstrarem falhas recorrentes de recuperação. Não indexar caixas de email inteiras, tokens ou dados de clientes da CodeMatrix. Medir dez perguntas de referência antes e depois de qualquer mudança de busca. MCP deve ser criado para uma lacuna concreta; um conector já funcional não precisa de um servidor duplicado.

## Arquitetura editorial e PT/EN

Estrutura sugerida: Explorar, IA, Games, Gadgets, StackPick, Produtos, Sobre e Patrocine. A página inicial deve responder rapidamente o que vale experimentar, o que foi testado e qual é a opinião de AnderZilla. Um espaço comercial explícito facilita patrocinadores sem transformar todo artigo em anúncio.

Usar /pt/ e /en/ com URLs próprias, seletor acessível, canonical coerente e hreflang recíproco apenas para traduções existentes. Não obrigar redirecionamento por IP nem depender de cookie para que o buscador encontre outro idioma. Português brasileiro pode usar pt-BR; inglês pode ser genérico quando não houver mercado regional específico. Publicar tradução somente após revisão; uma pauta exclusiva pode existir em um idioma. A recomendação acompanha as orientações oficiais de URLs por idioma e variantes localizadas. [Google: sites multilíngues](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites), [Google: versões localizadas](https://developers.google.com/search/docs/specialty/international/localized-versions).

Planejar duas séries principais inicialmente: testes de IA para diversão/produtividade e games/gadgets realmente usados. Cada teste pode gerar artigo, vídeo principal, cortes e newsletter. Isso é reutilização de pesquisa própria, com adaptação narrativa. Automação de dezenas de vídeos genéricos seria uma aposta frágil: YouTube exige originalidade e inclui conteúdo repetitivo ou produzido em massa entre problemas de monetização. [YouTube: políticas de monetização](https://support.google.com/youtube/answer/1311392?hl=en).

## Monetização: forte, mensurável e diversificada

Prioridade comercial: produto próprio adequado à pauta; afiliados aprovados e pertinentes; pacotes diretos de patrocínio; depois receita de plataformas e publicidade programática. ForgeKit tem URL comercial documentada, mas vendas e conversão não foram verificadas aqui. Preservar compra Gumroad e demo corretas, e testar se o público de cada conteúdo realmente tem intenção de comprar esse produto.

Não colocar todas as categorias de afiliados em toda página. Registrar programa, mercado atendido, aprovação, validade dos termos, janela de atribuição, comissões confirmadas, regras de divulgação e responsável pela revisão. Uma recomendação editorial precisa continuar defensável mesmo se outro fornecedor pagar mais. Patrocinadores devem comprar formato e distribuição transparentes, sem comprar conclusões positivas.

O canal comercial pode começar como página Patrocine/Sponsor com proposta editorial, formatos oferecidos, contato e formulário enxuto. O media kit inicial deve mostrar exemplos reais e o que pode ser entregue, sem números de audiência inventados. Oferecer um piloto de integração em vídeo, newsletter ou live, com relatório de resultado, antes de contratos longos. Contatar potenciais patrocinadores é uma etapa posterior com autorização explícita para envio.

Concentração deve ser medida por canal de descoberta e fonte pagadora. Como gatilho interno proposto, investigar quando uma plataforma origina mais de 60% das visitas ou um parceiro mais de 40% da receita. Esses percentuais são critérios de gestão, não benchmarks. Email opt-in e visitas recorrentes ajudam a criar relação própria; não garantem estabilidade sozinhos. A margem deve descontar taxas, reembolsos, ferramentas e tempo, evitando confundir receita bruta com renda pessoal.

## Plano de 90 dias e decisões de continuidade

Dias 1–14: confirmar identidades, projetos e benefícios; organizar branches/worktrees; fixar teto; preparar homologação e produção; instrumentar cliques comerciais e inscrições; revisar marca e navegação PT/EN. Saída: checklist com evidência de acesso e pipeline reprodutível. Só então declarar infraestrutura pronta.

Dias 15–30: publicar quatro peças originais de boa qualidade, com versões inglesas das mais promissoras; produzir cortes; organizar página comercial e ficha de cada afiliado aprovado. Medir horas por peça, retenção dos vídeos, cliques qualificados e retorno ao site. Cadência é proposta inicial, ajustável ao tempo disponível.

Dias 31–60: comparar duas séries editoriais; testar posição de CTA, descrição de benefícios e uma oferta de captura de email. Usar UTMs sem dados pessoais. Medir conversão por idioma e por intenção, receita líquida por mil visitas e receita por hora investida. Não declarar vencedor de A/B com meia dúzia de cliques; quando a amostra for pequena, usar entrevistas e sinais qualitativos explicitamente identificados.

Dias 61–90: concentrar esforço nas séries que trazem retorno e audiência recorrente; apresentar pilotos a patrocinadores autorizados; revisar recompra, reembolso e custo operacional; decidir quais ferramentas merecem assinatura. Meta de processo: 100% dos links comerciais rastreáveis, 100% das alegações verificáveis e prestação semanal do orçamento. Não há meta de faturamento confiável antes da linha de base. Expandir nuvem, idiomas, agentes ou canais apenas quando remover um gargalo medido.

## Contraponto final

O maior risco não é uma hospedagem pequena. É um projeto virar plataforma tecnológica, redação multilíngue, comunidade, canal de games e operação comercial completos antes de demonstrar uma série que as pessoas querem acompanhar. A infraestrutura proposta deixa portas abertas sem financiar complexidade prematura. A vantagem de AnderZilla será opinião pessoal demonstrável, entretenimento e utilidade; a IA deve multiplicar essa experiência e sua distribuição, preservando a autoria e a confiança.
