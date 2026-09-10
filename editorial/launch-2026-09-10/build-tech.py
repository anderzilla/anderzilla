import json, re, unicodedata
from pathlib import Path

OUT = Path(__file__).parent
items = []
def slug(s):
    return re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-')
def add(cat,key,pt,en,sp,se,bp,be,url,name,date,tags,hookpt,hooken,ctapt,ctaen,motif,kind='noticia',extra=None):
    sources=[{'name':name,'url':url,'eventDate':date}]+(extra or [])
    sourcept='\n\nFontes: '+ ' · '.join('['+s['name']+']('+s['url']+')' for s in sources)+'. Checagem: 10/09/2026. Análise documental; sem teste próprio.'
    sourceen='\n\nSources: '+ ' · '.join('['+s['name']+']('+s['url']+')' for s in sources)+'. Checked September 10, 2026. Document-based reporting; no hands-on test.'
    hashtags=['#AnderZilla']+['#'+x for x in tags]
    items.append({'key':key,'data':{'titlePT':pt,'titleEN':en,'summaryPT':sp,'summaryEN':se,'bodyPT':bp+sourcept,'bodyEN':be+sourceen,'category':cat,'sourceName':name,'sourceUrl':url,'publishedAt':'2026-09-10','slugPT':slug(pt),'slugEN':slug(en),'seoTitlePT':pt,'seoTitleEN':en,'seoDescriptionPT':sp,'seoDescriptionEN':se,'author':'Redação AnderZilla','isDemo':False},'social':{'hashtags':hashtags,'instagramPT':hookpt+'\n\n'+ctapt+' Leia a matéria no AnderZilla pelo link da bio.\n\n'+' '.join(hashtags),'instagramEN':hooken+'\n\n'+ctaen+' Read the story on AnderZilla through the bio link.\n\n'+' '.join(hashtags),'facebookPT':hookpt+' '+ctapt+' {urlPT}','facebookEN':hooken+' '+ctaen+' {urlEN}','whatsappPT':pt+'\n'+hookpt+'\n{urlPT}','whatsappEN':en+'\n'+hooken+'\n{urlEN}'},'evidence':{'checkedAt':'2026-09-10','eventDate':date,'editorialType':kind,'sources':sources,'testedByAnderZilla':False,'commercialRelationship':'none','translationReview':'PT/EN adaptados e revisados pelo agente editorial; revisão independente solicitada ao coordenador','sourceBudget':'Fatos parafraseados de forma breve; desenvolvimento e critérios editoriais originais. Sem reprodução de release.'},'visual':{'headline':pt,'subline':sp,'motif':motif,'rights':'Criar card original conceitual, sem fotos, logos, interfaces ou render de produto de terceiros. Identificar como arte editorial.'}})

add('ia','gpt-6-astra','GPT-6 Astra: o que muda para quem cria com IA','GPT-6 Astra: what changes for people building with AI',
'A nova geração da OpenAI aposta em tarefas completas no computador. Entenda o anúncio, o que observar e por que benchmark não é teste do seu projeto.',
'OpenAI’s new generation targets complete computer workflows. Understand the announcement, what to evaluate and why benchmarks cannot test your own project.',
'''A OpenAI apresentou o GPT-6 Astra em 3 de setembro, com foco em programação e operação de computadores. A empresa anunciou distribuição gradual e mostrou avaliações próprias. Isso confirma um lançamento; não comprova que toda conta já recebeu o modelo ou que qualquer projeto vai ganhar velocidade.

Para quem cria um jogo pequeno ou mantém um app depois do expediente, a pergunta interessante é outra: a IA consegue fechar o ciclo? Entender um bug, alterar o código, executar o teste e mostrar o resultado vale mais que uma resposta bonita no chat.

Nossa leitura editorial é usar uma tarefa conhecida como referência. Escolha um defeito reproduzível, guarde a versão inicial e defina como reconhecer a correção. Observe também se o agente mudou arquivos fora do escopo e se você consegue explicar o que entrou no diff. Tempo de revisão faz parte do trabalho.

Karaca, um modelo novo pode abrir possibilidades legais. Mas o melhor primeiro experimento continua pequeno: algo que você entende, consegue desfazer e sabe verificar. Qual tarefa repetitiva do seu projeto seria uma boa candidata?''',
'''OpenAI introduced GPT-6 Astra on September 3, emphasizing coding and computer operation. The company announced a gradual rollout and published its own evaluations. That establishes a launch, not universal account access or a guaranteed speed boost for every project.

If you build small games or maintain a side app after work, the useful question is whether an agent can complete the loop. Understanding a bug, changing the code, running a test and showing the result matters more than an impressive chat response.

Our editorial approach is to start with a task you already understand. Choose a reproducible defect, keep the original version and decide what a successful fix should look like. Check whether the agent touched unrelated files and whether you can explain the resulting diff. Review time belongs in the workload too.

A new model can unlock interesting experiments. The best first experiment is still small enough to understand, reverse and verify. Pick one repetitive job in your project and compare the complete process, rather than judging the first answer alone.''',
'https://openai.com/index/gpt-6-astra/','OpenAI — anúncio Astra','2026-09-03',['IA','GPT6','Dev'],
'Seu teste de IA termina na resposta ou no app funcionando?','Does your AI test end at the answer or at a working app?',
'Salve os critérios para o próximo experimento.','Save these criteria for your next experiment.', 'Órbitas e janelas abstratas conectadas; um caminho fecha um ciclo, sem logotipo.',extra=[{'name':'OpenAI — data de lançamento','url':'https://openai.com/index/safety-overview-gpt-6-astra/','eventDate':'2026-09-03'}])

add('ia','claude-fable-mythos-51','Claude Fable 5.1 e Mythos 5.1: entenda a diferença','Claude Fable 5.1 and Mythos 5.1: understand the difference',
'A Anthropic lançou dois nomes para a mesma base de modelo, com acesso e proteções diferentes. Veja o que importa antes de comparar ferramentas de IA.',
'Anthropic introduced two names for one underlying model with different safeguards and access. Here is what matters before comparing AI tools.',
'''A Anthropic anunciou Claude Fable 5.1 e Mythos 5.1 em 1º de setembro. Segundo a empresa, eles compartilham o modelo base, mas têm proteções diferentes: Fable tem disponibilidade geral; Mythos depende de programas de acesso confiável.

O detalhe evita uma confusão comum no feed. Um nome adicional nem sempre significa uma arquitetura totalmente diferente ou uma opção que qualquer assinante pode selecionar. Produto, condições de acesso e configuração precisam entrar na comparação.

Para um dev, isso muda o jeito de montar um teste justo. Use a mesma tarefa, os mesmos arquivos e critérios equivalentes; registre a configuração de esforço e a ferramenta que acompanha o modelo. Um agente que pode executar testes não está na mesma situação de um chat que recebe apenas um trecho de código.

Também vale olhar para o custo do resultado aceito, incluindo tentativas e revisão, em vez de transformar uma tabela de benchmark em campeonato definitivo. Nossa sugestão editorial é começar por um bug conhecido ou uma refatoração curta. O anúncio é relevante; o veredito sobre seu fluxo vem da execução verificável.''',
'''Anthropic announced Claude Fable 5.1 and Mythos 5.1 on September 1. According to the company, they share an underlying model but use different safeguards: Fable is generally available, while Mythos requires participation in trusted-access programs.

That distinction clears up a common feed-level misunderstanding. Another model name does not necessarily mean an entirely different architecture or an option every subscriber can select. Product packaging, access conditions and configuration belong in the comparison.

For developers, a fair trial starts with the same task, files and acceptance criteria. Record the effort setting and the tools surrounding the model. An agent able to execute tests is not facing the same conditions as a chat window given a single code snippet.

It also helps to measure the cost of an accepted result, including retries and review, instead of treating a benchmark table as a final tournament ranking. Our editorial suggestion is a familiar bug or a short refactor. The announcement deserves attention; the verdict on your workflow should come from a result you can actually verify.''',
'https://www.anthropic.com/claude-fable-and-mythos-5-1','Anthropic — Fable e Mythos 5.1','2026-09-01',['Claude','IA','Programacao'],'Dois nomes de IA podem esconder uma diferença de acesso, não de base.','Two AI names can reflect access differences rather than different foundations.','Compartilhe com quem compara modelos só pelo nome.','Share with someone who compares models by name alone.','Dois portais abstratos com núcleo comum e fechaduras distintas.')

add('ia','gemini-38-flash','Gemini 3.8 Flash chega: compare o fluxo, não só o placar','Gemini 3.8 Flash arrives: compare workflows, not just scores',
'Google anunciou Gemini 3.8 Flash e uma variante Cyber em setembro. Para devs, a avaliação útil combina qualidade, tempo e trabalho de revisão.',
'Google announced Gemini 3.8 Flash and a Cyber variant in September. For developers, useful evaluation combines quality, time and review effort.',
'''O Google anunciou Gemini 3.8 Flash e 3.8 Flash Cyber em 2 de setembro. A divulgação destaca avanços em programação e tarefas com agentes. As promessas e resultados apresentados pertencem ao fornecedor; ainda não fizemos uma avaliação própria.

O ritmo de lançamentos deixa qualquer pessoa com a sensação de que seu setup ficou velho durante o café. Para projetos pessoais, trocar de modelo só pelo número pode gastar mais tempo do que economiza. Uma melhoria precisa aparecer no trabalho que você realmente faz.

Um bom teste editorial seria pedir uma correção pequena com três condições: preservar o comportamento existente, incluir uma verificação relevante e explicar o que mudou. Depois, avaliar o resultado executado. Uma resposta rápida que exige três reparos pode ser menos útil que outra um pouco mais lenta e correta de primeira.

Registre ainda quais ferramentas estavam disponíveis e quantas intervenções foram necessárias. Assim, a comparação deixa de ser torcida por marca e vira informação reproduzível. A variante Cyber também não deve ser tratada como sinônimo de acesso irrestrito. Consulte as condições oficiais do produto antes de desenhar um fluxo em torno dela.''',
'''Google announced Gemini 3.8 Flash and 3.8 Flash Cyber on September 2. The announcement emphasizes improvements in coding and agent workflows. Its performance claims come from the vendor; we have not run an independent evaluation.

The release pace can make a perfectly useful setup feel outdated before your coffee gets cold. For side projects, switching models because the number changed may take more time than it saves. An improvement needs to show up in the work you actually do.

A useful editorial trial would ask for a small fix with three conditions: preserve existing behavior, add a meaningful check and explain the change. Then inspect the executed result. A fast answer requiring three repairs may be less useful than a slightly slower answer that works the first time.

Record the available tools and the number of interventions too. That turns brand loyalty into a comparison someone else can reproduce. The Cyber variant should not be interpreted as unrestricted access either. Read the official product conditions before designing a workflow around it, and judge the complete task rather than the opening response.''',
'https://blog.google/innovation-and-ai/models-and-research/gemini-models/3-8-flash-and-3-8-flash-cyber/','Google — Gemini 3.8','2026-09-02',['Gemini','IA','Dev'],'Modelo novo toda hora: como saber se vale mudar seu fluxo?','Another model release: how do you tell whether switching is worthwhile?','Use os critérios da matéria no próximo teste.','Use the story’s criteria in your next trial.','Raio abstrato atravessando três checkpoints: qualidade, tempo, revisão.')

add('ia','qwen38-flash-next','Qwen3.8-Flash-Next: pesos abertos não significam PC leve','Qwen3.8-Flash-Next: open weights do not mean a lightweight PC model',
'O novo Qwen abre seus pesos e antecipa uma arquitetura futura. Entenda por que parâmetros ativos não contam toda a história do hardware necessário.',
'The new Qwen opens its weights and previews a future architecture. Active parameters alone do not describe the hardware needed to run a model.',
'''O time Qwen publicou Qwen3.8-Flash-Next em 26 de agosto. O modelo multimodal usa uma arquitetura MoE, com 6 bilhões de parâmetros ativos por token e uma base total muito maior. Os pesos foram disponibilizados para a comunidade.

O número menor chama atenção, especialmente para quem sonha em colocar IA no PC gamer. Só que parâmetros ativos descrevem parte do cálculo, não uma promessa sobre memória total. Antes do download, a conversa precisa passar pelo formato dos pesos, pelo runtime e pelo tamanho do contexto pretendido.

Nossa proposta de avaliação é começar pelo objetivo: conversar localmente, analisar imagens ou integrar uma ferramenta? Depois, consultar a documentação da configuração específica e verificar armazenamento, RAM e VRAM. Não dá para concluir que uma GPU comum executará o modelo apenas lendo o nome Flash.

Também separe o modelo distribuído do serviço hospedado: eles podem oferecer ferramentas e configurações diferentes. O anúncio é interessante para quem acompanha a engenharia de IA da China e para devs que gostam de explorar alternativas. A expectativa correta é uma oportunidade de pesquisa, sem inventar compatibilidade ou desempenho que ainda não medimos.''',
'''The Qwen team released Qwen3.8-Flash-Next on August 26. The multimodal model uses a mixture-of-experts architecture with six billion active parameters per token and a much larger total foundation. Its weights were made available to the community.

That smaller number is eye-catching if you want to run AI on a gaming PC. Active parameters describe part of the computation, however, not a promise about total memory requirements. Before downloading, consider the weight format, runtime and intended context size.

Our evaluation approach starts with the actual goal: local conversation, image analysis or a tool integration? Then consult documentation for that specific configuration and check storage, system memory and VRAM. The word Flash alone cannot establish that an ordinary graphics card will run the model.

Keep the distributed model separate from the hosted service as well: their tools and configurations can differ. This is an interesting release for people following AI engineering in China and developers exploring alternatives. Treat it as a research opportunity, without inventing compatibility or performance we have not measured on real hardware.''',
'https://qwen.ai/blog?id=qwen3.8-flash-next','Qwen Team — Flash-Next','2026-08-26',['Qwen','IA','PCGamer'],'Cabe no PC? O número de parâmetros ativos não responde sozinho.','Will it fit your PC? Active parameter counts cannot answer that alone.','Salve antes de escolher seu próximo modelo local.','Save this before choosing your next local model.','Blocos grandes de memória alimentando seis pequenos circuitos iluminados.')

add('ia','qwen-image-3','Qwen-Image-3.0: texto bonito na imagem ainda pede revisão','Qwen-Image-3.0: attractive text in an image still needs review',
'A geração de imagens da Qwen mira layouts e texto mais detalhados. Para posts e interfaces, o desafio continua sendo revisar o que a arte afirma.',
'Qwen’s image model targets detailed layouts and text. For posts and interfaces, the challenge remains checking what the finished image actually says.',
'''A Qwen apresentou o Qwen-Image-3.0 em 21 de julho. Entre os destaques declarados estão layouts complexos e renderização de texto em 12 idiomas. Esta matéria retoma esse lançamento para discutir uma pergunta prática: a arte está bonita ou também está correta?

Para um dev montando a divulgação do seu jogo, uma imagem convincente pode economizar uma etapa de rascunho. Mas botões que parecem reais, textos pequenos e números inventados podem transformar um mockup em promessa que o produto não cumpre.

Uma revisão útil começa no conteúdo. Confira cada palavra, data, unidade e nome antes de avaliar a paleta. Depois, abra o arquivo no tamanho em que ele será visto no celular: detalhes que funcionam ampliados podem desaparecer no feed. Mantenha o texto essencial também na legenda ou na página, onde ele é acessível e corrigível.

Nossa leitura é tratar a geração visual como parte de um processo editorial, com direção e conferência. Não executamos testes com esse modelo nem assumimos licença para imagens de terceiros. Se a peça representar algo conceitual, deixe isso claro em vez de vendê-la como captura de um produto pronto.''',
'''Qwen introduced Qwen-Image-3.0 on July 21. The company highlighted complex layouts and text rendering in 12 languages. We are revisiting that release to ask a practical question: does the artwork merely look convincing, or is its content correct too?

For a developer preparing a small game announcement, generated imagery can help with an early draft. But realistic-looking buttons, tiny text and invented numbers can turn a mockup into a promise the product does not fulfill.

A useful review starts with the content. Check every word, date, unit and name before judging the palette. Then open the file at its expected phone size: details that work when enlarged may disappear in a feed. Keep essential wording in the caption or on the page too, where it remains accessible and easier to correct.

Our editorial view is that image generation belongs within a process that includes direction and verification. We have not tested this model or assumed permission to reuse third-party images. If an image represents a concept, label it clearly instead of presenting it as a screenshot of a finished product.''',
'https://qwen.ai/blog?id=qwen-image-3.0','Qwen Team — Image 3.0','2026-07-21',['Qwen','IA','Design'],'A imagem ficou incrível. Você conferiu cada palavra dela?','The image looks great. Did you check every word in it?','Envie para quem cria posts e mockups.','Send this to someone making posts and mockups.','Mosaico tipográfico abstrato com lupa destacando uma letra; sem simular produto.',kind='explicador')

add('ia','mistral-agentic-search','Mistral Agentic Search: por que buscar uma vez pode não bastar','Mistral Agentic Search: why one retrieval pass may not be enough',
'A busca da Mistral permite procurar e verificar informações em etapas. Entenda a proposta e o que cobrar de uma resposta baseada em documentos.',
'Mistral’s search layer finds and checks information in multiple steps. Understand the approach and what to expect from document-grounded answers.',
'''A Mistral anunciou Agentic Search em 20 de agosto. A proposta é uma busca em várias etapas, na qual a IA procura, inspeciona e verifica informação em documentos. É um anúncio de produto, não evidência de acerto garantido sobre qualquer arquivo.

Imagine a documentação de um jogo: a regra geral está num capítulo, a exceção numa tabela e a atualização em outra página. Encontrar um parágrafo parecido com a pergunta não basta para resolver essa combinação. Esse é o tipo de problema que torna a recuperação de informação tão importante quanto a redação da resposta.

Para avaliar uma solução assim, escolha perguntas com respostas conhecidas e algumas que o acervo não consegue responder. Exija referência ao trecho que sustenta a conclusão. Uma resposta que admite a lacuna pode ser melhor que outra cheia de confiança e sem apoio.

Nossa recomendação editorial é verificar também permissões e versões dos documentos. Um assistente não deveria atravessar pastas que o usuário não pode ler. O ganho interessante é navegar um acervo complicado com menos trabalho manual, mantendo um caminho claro de volta à evidência. Sem isso, a interface elegante só deixa o erro mais convincente.''',
'''Mistral announced Agentic Search on August 20. The product uses a multistep process in which an AI searches, inspects and checks information in documents. That is a product announcement, not evidence of guaranteed accuracy across every collection.

Imagine a game’s documentation: the general rule is in one chapter, an exception sits in a table and an update appears elsewhere. Finding a paragraph that resembles the question will not resolve that combination. This is where information retrieval becomes as important as writing the answer.

To evaluate a system like this, choose questions with known answers and include some the collection cannot answer. Require a reference to the passage supporting each conclusion. An answer that acknowledges a gap can be more useful than a confident response without evidence.

Our editorial recommendation is to check document permissions and versions too. An assistant should not cross into folders its user cannot read. The interesting gain is navigating a complicated collection with less manual work while preserving a clear path back to the evidence. Otherwise, a polished interface can simply make errors look more convincing.''',
'https://mistral.ai/news/agentic-search/','Mistral — Agentic Search','2026-08-20',['Mistral','RAG','IA'],'Sua IA cita o documento ou só parece conhecer a resposta?','Does your AI cite the document, or merely sound informed?','Salve as perguntas para avaliar seu próximo assistente.','Save these questions for evaluating your next assistant.','Labirinto de documentos com trilha e três marcadores de verificação.')

add('ia','shieldstral','Shieldstral: moderação de IA que recebe regras em linguagem comum','Shieldstral: AI moderation that accepts plain-language rules',
'A Mistral publicou um classificador multimodal com pesos abertos. Para comunidades gamer, a pergunta é como testar regras sem apagar o contexto.',
'Mistral released an open-weights multimodal classifier. For gaming communities, the useful question is how to test rules without losing context.',
'''A Mistral lançou Shieldstral em 4 de agosto. Segundo o anúncio, é um classificador multimodal de 3 bilhões de parâmetros que recebe políticas em linguagem natural, com pesos sob Apache 2.0. A proposta é avaliar conteúdo de acordo com regras definidas pelo produto.

Numa comunidade gamer, contexto muda tudo. Uma conversa sobre a violência de um jogo não equivale automaticamente a ameaçar outra pessoa. Da mesma forma, uma frase curta aparentemente inocente pode fazer parte de uma sequência de assédio. Nosso ponto editorial é que uma classificação isolada não explica toda a situação.

Antes de automatizar moderação, monte exemplos representativos em português, incluindo gíria, ironia, mensagens legítimas e violações claras. Registre quais decisões seriam apenas sinalizadas para revisão e quais poderiam limitar conteúdo. Permita contestar erros e mantenha histórico da regra aplicada.

Não testamos a precisão do Shieldstral em comunidades brasileiras. O lançamento interessa por tornar a política uma entrada explícita do sistema, mas isso não elimina a necessidade de avaliar falsos positivos. Uma comunidade saudável precisa de regras compreensíveis e aplicação consistente; o modelo é uma ferramenta dentro desse processo.''',
'''Mistral released Shieldstral on August 4. Its announcement describes a three-billion-parameter multimodal classifier accepting plain-language policies, with weights released under Apache 2.0. The idea is to evaluate content against rules defined by the product.

In a gaming community, context matters. Discussing violence in a game does not automatically amount to threatening another person. An apparently harmless short phrase may also belong to a longer harassment pattern. Our editorial point is that an isolated classification cannot explain the entire situation.

Before automating moderation, assemble representative examples in the community’s language, including slang, irony, legitimate messages and clear violations. Decide which results should only be flagged for review and which could limit content. Let people challenge mistakes and preserve the version of the rule applied.

We have not tested Shieldstral’s accuracy in Brazilian communities. The release is interesting because it makes policy an explicit input, but that does not remove the need to evaluate false positives. A healthy community needs understandable rules and consistent enforcement. The model is a tool within that process, not a substitute for it.''',
'https://mistral.ai/news/shieldstral/','Mistral — Shieldstral','2026-08-04',['IA','ComunidadeGamer','Mistral'],'Moderar uma comunidade exige entender contexto, não só palavras.','Community moderation requires context, not just keywords.','Compartilhe com quem administra uma comunidade.','Share with someone running a community.','Balões abstratos passando por um filtro com saída de revisão humana.')

add('ia','claude-marca-texto','Marca d’água no texto do Claude: o que ela pode indicar','Claude text watermarking: what it can actually indicate',
'A Anthropic explicou sua marca d’água estatística. Ela não é um caractere escondido nem prova absoluta de autoria: entenda os limites da proposta.',
'Anthropic explained its statistical text watermark. It is neither a hidden character nor absolute proof of authorship. Here are the practical limits.',
'''Em 14 de agosto, a Anthropic detalhou uma marca d’água para textos de futuros modelos Claude. Segundo a explicação, o método cria um padrão estatístico nas escolhas de palavras, sem acrescentar caracteres ocultos. A detecção indica probabilidade de participação do modelo, não uma certeza universal de autoria.

Isso importa para quem publica tutorial, roteiro de vídeo ou texto de divulgação. Procurar um símbolo invisível e apagá-lo não corresponde ao mecanismo descrito. E transformar qualquer detector em juiz automático pode gerar conclusões que a própria evidência não sustenta.

Nossa leitura editorial é separar três perguntas: quem assumiu responsabilidade pelo conteúdo, quais ferramentas participaram e se os fatos foram verificados. Uma marca técnica responde, no máximo, a parte da segunda pergunta. Ela não valida fontes, não testa código e não transforma um texto errado em informação confiável.

Para compartilhar uma análise de detecção, preserve o contexto e a incerteza. Não acuse uma pessoa com base em um print isolado. Para criar conteúdo, mantenha suas referências e revisões: um histórico editorial claro oferece informação útil mesmo quando o sinal estatístico é fraco ou indisponível.''',
'''On August 14, Anthropic described watermarking for text from future Claude models. Its explanation says the method creates a statistical pattern in word choices without adding hidden characters. Detection indicates a likelihood of model involvement, not universal certainty about authorship.

That matters when you publish a tutorial, video script or product announcement. Looking for an invisible symbol to delete does not match the described mechanism. Treating any detector as an automatic judge can also produce conclusions the evidence itself cannot support.

Our editorial reading separates three questions: who takes responsibility for the content, which tools contributed and whether the facts were checked. A technical watermark can address only part of the second question. It does not validate sources, test code or turn an incorrect article into reliable information.

If you share a detection result, preserve its context and uncertainty. Do not accuse someone on the basis of a single screenshot. When creating content, keep your references and revision history: a clear editorial record remains useful even when a statistical signal is weak or unavailable.''',
'https://www.anthropic.com/news/claude-text-watermark','Anthropic — watermark de texto','2026-08-14',['Claude','IA','CriacaoDeConteudo'],'Um detector de IA não substitui um histórico editorial.','An AI detector cannot replace an editorial record.','Salve para a próxima discussão sobre autoria.','Save this for the next authorship discussion.','Ondas estatísticas sob linhas de texto, sem marca invisível literal.')

add('ia','gemini-apps-conectados','Gemini ganha conexões com apps: a novidade está no fluxo','Gemini adds app connections: the real change is the workflow',
'Google anunciou novas conexões do Gemini com serviços de criação e organização. Veja por que permissões e confirmação também fazem parte da experiência.',
'Google announced more Gemini connections for creative and organizational services. Permissions and confirmation are part of the experience too.',
'''O Google anunciou em 12 de agosto novas conexões para o Gemini, incluindo serviços como Wix, Granola e Otter.ai. A distribuição foi prevista para as semanas seguintes, com disponibilidade dependente do serviço e do mercado. Um anúncio global não garante que cada integração apareça na sua conta.

O lado interessante para quem mantém um projeto pessoal é diminuir a distância entre conversar e agir. Resumir uma reunião e levar uma alteração até o site pode ser útil; copiar manualmente a mesma informação entre várias telas costuma quebrar o ritmo de criação.

Nossa avaliação editorial começaria por uma tarefa de leitura, usando informação que pode ser compartilhada com o serviço. Depois, verificaríamos o que o assistente entendeu e quais dados foram envolvidos. Antes de permitir alterações, seria preciso saber onde conferir o resultado e como corrigir um erro.

Conectar tudo de uma vez não é um objetivo por si só. O bom fluxo resolve uma necessidade concreta com permissões proporcionais e um resultado visível. Não acessamos essas integrações nesta reportagem. Vale conferir a lista oficial e escolher uma conexão que realmente evite trabalho repetitivo no seu projeto.''',
'''Google announced new Gemini connections on August 12, including services such as Wix, Granola and Otter.ai. The rollout was planned over the following weeks, with availability depending on the service and market. A global announcement does not guarantee every integration appears in your account.

For someone maintaining a personal project, the interesting change is a shorter path from conversation to action. Summarizing a meeting and carrying a change into a website could be useful; repeatedly copying information between screens often interrupts creative work.

Our editorial evaluation would start with a reading task using information suitable for sharing with the service. We would then check what the assistant understood and which data were involved. Before allowing edits, we would want a clear place to inspect the result and a way to correct mistakes.

Connecting everything is not an objective in itself. A good workflow solves a concrete problem with proportionate permissions and a visible outcome. We did not access these integrations for this report. Check the official list and choose a connection that removes genuinely repetitive work from your project.''',
'https://blog.google/innovation-and-ai/products/gemini-app/new-connected-apps-services-gemini-august-2026/','Google — apps conectados ao Gemini','2026-08-12',['Gemini','IA','Produtividade'],'Qual troca entre apps mais quebra seu ritmo de criação?','Which app handoff interrupts your creative flow the most?','Use essa pergunta para escolher sua primeira integração.','Use that question to choose your first integration.','Janelas genéricas ligadas por linhas com nós de permissão.')

add('ia','claude-cientistas','Claude para cientistas: acesso ampliado não é descoberta pronta','Claude for scientists: broader access is not an instant discovery',
'A Anthropic abriu um programa de acesso para pesquisadores. Entenda o anúncio e por que computação disponível não dispensa evidência reproduzível.',
'Anthropic opened a program expanding researcher access. Understand the announcement and why available compute does not replace reproducible evidence.',
'''A Anthropic anunciou em 27 de agosto 10 mil vagas iniciais de assinaturas gratuitas ou com desconto para cientistas. O programa tem critérios de elegibilidade; não é uma gratuidade geral para qualquer conta. A empresa também anunciou expansão do apoio a projetos científicos.

Para quem acompanha IA além dos geradores de memes, o ponto interessante é o trabalho que existe antes de uma descoberta. Organizar dados, documentar um experimento e revisar scripts pode consumir uma parte enorme do esforço. Apoio computacional faz sentido quando ajuda a tornar esse caminho mais claro e verificável.

Nossa leitura não é que um plano de IA substitui formação ou revisão científica. Uma conclusão precisa sobreviver à checagem dos dados e do método. Um gráfico bem desenhado e uma explicação segura podem esconder uma hipótese errada com a mesma facilidade que num projeto de software.

Se você participa de pesquisa, consulte os critérios e condições na página oficial antes de planejar o uso. Se acompanha por curiosidade, procure notícias que expliquem o que foi demonstrado e o que continua em estudo. O salto mais interessante não é uma promessa de respostas mágicas, e sim mais capacidade de testar boas perguntas.''',
'''Anthropic announced an initial 10,000 free or discounted subscription seats for scientists on August 27. Eligibility requirements apply; this is not a general free offer for every account. The company also announced broader support for scientific projects.

If you follow AI beyond meme generators, the interesting part is the work preceding a discovery. Organizing data, documenting an experiment and reviewing scripts can absorb a substantial amount of effort. Computing support is useful when it makes that process clearer and more verifiable.

Our editorial reading is not that an AI subscription replaces expertise or scientific review. A conclusion must survive checks of the underlying data and method. A polished graph and a confident explanation can hide a mistaken assumption just as easily as they can in a software project.

Researchers should consult the official eligibility and program conditions before planning around the offer. Curious readers should look for reporting that explains what was demonstrated and what remains under investigation. The interesting advance is not a promise of magical answers, but greater capacity to test good questions and preserve enough evidence for others to examine the result.''',
'https://www.anthropic.com/news/expanding-support-for-scientists','Anthropic — apoio a cientistas','2026-08-27',['IA','Ciencia','Claude'],'Mais acesso à IA ajuda quando a pergunta vem acompanhada de método.','More AI access helps when the question comes with a method.','Compartilhe com quem curte ciência e tecnologia.','Share with someone interested in science and technology.','Constelação de pontos de dados e frascos abstratos; nenhuma alegação médica.')

def save():
    for item in items:
        d=item['data']; s=item['social']; e=item['evidence']
        d.update({'sources':json.dumps([{'name':x['name'],'url':x['url'],'publishedAt':x['eventDate']} for x in e['sources']],ensure_ascii=False),'verifiedAt':'2026-09-10','eventDate':e['eventDate'],'editorialType':{'noticia':'news','explicador':'explainer','comparacao':'comparison','analise':'analysis'}.get(e['editorialType'],e['editorialType']),'hashtagsPT':' '.join(s['hashtags']),'hashtagsEN':' '.join(s['hashtags'])})
        translations={'#IA':'#AI','#Programacao':'#Programming','#ComunidadeGamer':'#GamingCommunity','#CriacaoDeConteudo':'#ContentCreation','#Produtividade':'#Productivity','#Ciencia':'#Science','#Celulares':'#Smartphones','#Dobraveis':'#Foldables','#Comparativo':'#Comparison','#Privacidade':'#Privacy','#Bateria':'#Battery','#FotografiaMobile':'#MobilePhotography','#Fotografia':'#Photography','#Seguranca':'#Security','#MouseGamer':'#GamingMouse','#Robotica':'#Robotics'}
        for old,new in translations.items():
            d['hashtagsEN']=d['hashtagsEN'].replace(old,new)
            s['instagramEN']=s['instagramEN'].replace(old,new)
        s['hashtagsPT']=d['hashtagsPT']; s['hashtagsEN']=d['hashtagsEN']
        source_rows=json.loads(d['sources'])
        if item['key']=='galaxy-s26-privacy': source_rows[0]['publishedAt']='2026-02-26'
        if item['key'] in {'xiaomi17ultra','oneplus15-165hz','unitree-robos-fabrica'}:
            source_rows[0].pop('publishedAt',None)
            source_rows[0]['note']='Página sem data editorial confirmada; consultada em 2026-09-10. A data do evento está separada no registro.'
        d['sources']=json.dumps(source_rows,ensure_ascii=False)
        if item['key']=='typescript7-go':
            d['editorialType']='explainer'
            d['bodyPT']=d['bodyPT'].replace('O time relata ganhos de velocidade em builds completos.','O time relata ganhos de velocidade em builds completos. A versão 7.0 não expõe API; ferramentas que dependem dela podem exigir convivência com o TypeScript 6.0.')
            d['bodyEN']=d['bodyEN'].replace('The team reports faster full builds.','The team reports faster full builds. Version 7.0 has no API; tools depending on it may require TypeScript 6.0 alongside it.')
            e['editorialType']='explicador'
        d['bodyEN']=d['bodyEN'].split('\n\nSources:')[0]+'\n\nSources: '+' · '.join('['+x['name'].split(' — ')[0]+']('+x['url']+')' for x in e['sources'])+'. Checked September 10, 2026. Document-based reporting; no hands-on test.'
        for a,b in [('instagram','Instagram'),('facebook','Facebook'),('whatsapp','Whatsapp')]:
            for lang in ['PT','EN']:
                d['social'+b+lang]=s[a+lang]
        headline,subline=CARDS.get(item['key'],(d['titlePT'],d['summaryPT']))
        item['visual']['headline']=headline; item['visual']['subline']=subline
    (OUT/'ia-celulares-curiosidades.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')

CARDS={
'gpt-6-astra':('GPT-6 Astra','Da resposta ao trabalho verificado'),
'claude-fable-mythos-51':('Claude 5.1','Mesma base, acessos diferentes'),
'gemini-38-flash':('Gemini 3.8 Flash','Qualidade, tempo e revisão'),
'qwen38-flash-next':('Qwen Flash-Next','Pesos abertos, hardware em pauta'),
'qwen-image-3':('Qwen-Image 3.0','A arte ficou bonita. E correta?'),
'mistral-agentic-search':('Busca em etapas','O caminho de volta à fonte'),
'shieldstral':('Shieldstral','Moderação precisa de contexto'),
'claude-marca-texto':('Texto com marca','Probabilidade não é certeza'),
'gemini-apps-conectados':('Gemini conectado','Menos troca entre apps'),
'claude-cientistas':('IA na ciência','Mais acesso, método sempre'),
'iphone18pro':('iPhone 18 Pro','Câmera com abertura variável'),
'iphone17e-contexto':('iPhone 17e','O espaço também conta'),
'pixel11-tensor':('Pixel 11','IA que cabe na rotina?'),
'pixel11-pro-fold':('Pixel 11 Pro Fold','Você abriria quantas vezes?'),
'galaxy-fold8-comparacao':('Fold8 × Ultra','O formato vem antes do nome'),
'galaxy-s26-privacy':('Privacy Display','Quem está olhando a tela?'),
'honor-magic-v6':('HONOR Magic V6','Capacidade não é autonomia'),
'xiaomi17ultra':('Xiaomi 17 Ultra','Confira a versão primeiro'),
'oppo-findx9ultra':('Find X9 Ultra','Zoom com contexto'),
'oneplus15-165hz':('165 Hz ≠ 165 FPS','Painel e jogo são diferentes'),
'typescript7-go':('TypeScript 7','Go dentro do compilador'),
'npm-trusted-publishing':('npm e OIDC','Caminhos de publicação'),
'github-secrets-merge':('Segredos no PR','Uma nova trava antes do merge'),
'godot-mouse-polling':('Mouse e engasgos','Godot corrige cenário no Windows'),
'codeql-go127':('CodeQL atualizado','Alerta novo ou novo endereço?'),
'raspberrypi-radio':('Rádio com Python','Um projeto fora da tela'),
'unitree-robos-fabrica':('Robôs fazem robôs?','O que existe fora do clipe'),
'honor-robot-phone':('Robot Phone','Uma ideia em movimento'),
'xiaomi-vision-gran-turismo':('Vision Gran Turismo','China tech encontra os games'),
'model-hardware-standard':('IA no mundo físico','Interfaces também precisam de limites')}

add('celulares','iphone18pro','iPhone 18 Pro anunciado: câmera variável é o destaque','iPhone 18 Pro announced: variable aperture takes the spotlight',
'Apple apresentou iPhone 18 Pro e Pro Max em 9 de setembro. A câmera tem abertura variável; pré-venda e chegada às lojas ainda estavam por vir na checagem.',
'Apple unveiled iPhone 18 Pro and Pro Max on September 9. Variable aperture leads the camera changes; preorders and retail launch were still ahead at review.',
'''A Apple anunciou iPhone 18 Pro e Pro Max em 9 de setembro. A câmera principal Fusion de 48 MP passa a ter abertura variável; o chip é o A20 Pro. O Brasil está explicitamente incluído na pré-venda de 12 de setembro e na disponibilidade anunciada para 18 de setembro.

Para quem grava gameplay, setup ou bastidores, o interesse da câmera vai além da resolução. Ter mais controle sobre a captura pode ajudar a construir uma linguagem visual consistente, mas o anúncio sozinho não demonstra como o aparelho se comporta numa sala escura ou gravando por muito tempo.

Nossa lista para uma avaliação futura incluiria transições de exposição, áudio perto de um teclado, aquecimento e praticidade de levar os arquivos ao editor. Uma amostra produzida pela marca também não substitui uma comparação com as mesmas condições de luz e enquadramento.

Em 10 de setembro, portanto, o fato é o anúncio. Ainda não cabe falar em teste AnderZilla, autonomia comprovada ou estoque disponível nas lojas. Se o seu celular já atende bem, acompanhe avaliações verificáveis antes de decidir: o recurso mais interessante é o que melhora um problema real na sua criação.''',
'''Apple announced iPhone 18 Pro and Pro Max on September 9. The 48MP Fusion main camera gains variable aperture, and the phones use A20 Pro. Brazil is explicitly included in announced September 12 preorders and September 18 availability.

For people filming gaming setups or behind-the-scenes clips, the camera story extends beyond resolution. More capture control could help create a consistent visual style, but an announcement cannot demonstrate behavior in a dim room or during a long recording.

Our future evaluation checklist would include exposure transitions, audio beside a keyboard, heat and the practicality of moving files into an editor. Brand-produced samples also cannot replace a comparison using the same lighting and framing.

As of September 10, the established event is the announcement. This is not an AnderZilla hands-on review, a verified battery test or confirmation of retail stock. If your current phone works well, follow verifiable testing before deciding. The most interesting feature is the one that solves a real problem in your creative process.''',
'https://www.apple.com/newsroom/2026/09/apple-debuts-iphone-18-pro-and-iphone-18-pro-max/','Apple — iPhone 18 Pro','2026-09-09',['iPhone18Pro','Apple','Celulares'],'Abertura variável no celular: controle criativo merece mais atenção que o número de megapixels.','Variable aperture on a phone: creative control deserves more attention than megapixel counts.','Compartilhe com quem grava conteúdo no celular.','Share with someone who shoots on a phone.','Íris fotográfica abstrata abrindo, com faixas de luz e sem desenho do aparelho.')

add('celulares','iphone17e-contexto','iPhone 17e: MagSafe e 256 GB mudam qual conversa?','iPhone 17e: what do MagSafe and 256GB actually change?',
'Lançado em março, o iPhone 17e entra no radar de quem quer criar e jogar. Veja os recursos documentados e os critérios para avaliar uma troca.',
'Released in March, iPhone 17e remains relevant to creators and mobile players. Review its documented features and criteria for considering an upgrade.',
'''Apresentado em 2 de março, o iPhone 17e reúne A19, MagSafe e armazenamento inicial de 256 GB, segundo a Apple. A tela é OLED de 6,1 polegadas. Este é um olhar sobre um lançamento anterior de 2026, não uma novidade anunciada nesta semana.

O armazenamento merece uma conversa menos glamourosa e mais útil. Games, gravações e projetos de vídeo competem pelo mesmo espaço; para um criador, capacidade livre pode resolver mais incômodos que um acabamento diferente. Só não existe número mágico que atenda todos os usos.

Antes de comparar, veja quanto espaço você ocupa hoje e quanto costuma apagar ou transferir por mês. Avalie também se acessórios magnéticos resolvem algo no seu setup: fixar o aparelho para gravar, carregar numa mesa ou organizar o uso diário. O nome de um recurso não torna a compra necessária.

Não testamos desempenho sustentado nem autonomia do 17e. Nossa leitura documental é que o conjunto merece avaliação por rotina, e não apenas por ser uma entrada mais acessível dentro de uma família. Para decidir uma troca, compare a oferta local vigente e o que seu aparelho atual já entrega; o preço de lançamento não é uma promoção atual.''',
'''Introduced on March 2, iPhone 17e combines A19, MagSafe and 256GB of starting storage, according to Apple. It has a 6.1-inch OLED display. This is a look at an earlier 2026 release, not a product announced this week.

Storage deserves a less glamorous but more useful conversation. Games, recordings and video projects compete for the same space; for a creator, available capacity may resolve more frustration than a different finish. There is no single capacity figure that suits everyone.

Before comparing phones, check how much space you use and how often you delete or transfer files. Also consider whether magnetic accessories solve an actual setup problem: positioning a phone for recording, charging at a desk or organizing daily use. A feature name does not make a purchase necessary.

We have not tested sustained performance or battery life on the 17e. Our document-based view is that the combination deserves evaluation against your routine, rather than simply its position within an Apple lineup. Compare current local offers and the capabilities of your existing phone before upgrading; a launch price is not a current discount.''',
'https://www.apple.com/ie/newsroom/2026/03/apple-introduces-iphone-17e/','Apple — iPhone 17e','2026-03-02',['iPhone17e','Apple','MobileGaming'],'Espaço para games e vídeos: o upgrade começa pelo seu uso real.','Room for games and video: a useful upgrade starts with your actual needs.','Salve para organizar sua próxima comparação.','Save this for your next phone comparison.','Blocos de armazenamento e anel magnético abstrato sobre fundo azul.',kind='analysis')

add('celulares','pixel11-tensor','Pixel 11: Tensor G6 e IA precisam funcionar na sua rotina','Pixel 11: Tensor G6 and AI need to fit your routine',
'A família Pixel 11 foi anunciada em agosto com Tensor G6 e recursos Gemini. Entenda o que perguntar sobre idioma, mercado e utilidade antes do hype.',
'The Pixel 11 family arrived in August with Tensor G6 and Gemini features. Ask about language, market and everyday usefulness before following the hype.',
'''O Google apresentou Pixel 11, Pixel 11 Pro e Pixel 11 Pro XL em 12 de agosto, com Tensor G6 e integração ao Gemini. A empresa destaca mudanças de câmera e construção. Recursos de IA podem variar por país, idioma e condições de acesso.

Para um público que joga e cria, a pergunta não é quantas vezes o release menciona inteligência artificial. É se o aparelho reduz um atrito recorrente: organizar uma ideia, registrar uma cena ou recuperar informação sem fazer malabarismo entre apps.

Uma comparação útil começa pela sua língua e pelos serviços que você já usa. Depois, passe às necessidades básicas: tela confortável, comunicação, armazenamento e bateria. Um recurso chamativo que não está disponível na sua região não compensa sozinho uma lacuna no uso diário.

Não testamos esta geração nem confirmamos sua venda oficial no Brasil. Também não tomamos demonstrações promocionais como prova de qualidade de foto. Nossa sugestão editorial é registrar três tarefas habituais e procurar avaliações que mostrem essas tarefas de ponta a ponta. É uma maneira mais honesta de entender a proposta Pixel do que escolher o maior número ou a promessa mais vistosa.''',
'''Google introduced Pixel 11, Pixel 11 Pro and Pixel 11 Pro XL on August 12, with Tensor G6 and Gemini integration. The company highlights camera and construction changes. AI features may vary by country, language and access conditions.

For people who play and create, the useful question is not how often the announcement says artificial intelligence. It is whether the phone removes recurring friction: organizing an idea, capturing a scene or retrieving information without juggling multiple apps.

A helpful comparison starts with your language and existing services. Then consider the essentials: a comfortable screen, communication, storage and battery life. A striking feature unavailable in your region cannot, by itself, compensate for a gap in daily use.

We have not tested this generation or confirmed official Brazilian retail availability. Promotional demonstrations are not proof of photographic quality either. Our editorial suggestion is to list three everyday tasks and look for evaluations showing those tasks from beginning to end. That is a more honest way to assess the Pixel proposition than choosing the largest number or the most spectacular promise on a launch page.''',
'https://blog.google/intl/es-es/productos/dispositivos/serie-pixel-11-tu-pixel-mas-personal-hasta-la-fecha/','Google — série Pixel 11','2026-08-12',['Pixel11','Google','Celulares'],'IA no celular precisa combinar com seu idioma e sua rotina.','Phone AI needs to fit your language and your routine.','Compartilhe os critérios com quem está escolhendo um Android.','Share these criteria with someone choosing an Android phone.','Chip abstrato conectado a câmera e três cartões de tarefas.',extra=[{'name':'Google — restrições de recursos Pixel','url':'https://blog.google/products-and-platforms/devices/pixel/new-pixel-devices-2026/','eventDate':'2026-08-12'}])

add('celulares','pixel11-pro-fold','Pixel 11 Pro Fold: menos peso, mais perguntas úteis','Pixel 11 Pro Fold: less weight, more useful questions',
'O dobrável do Google foi anunciado com desenho mais leve e fino. Nossa análise explica como comparar conforto e multitarefa sem fingir teste prático.',
'Google announced a thinner, lighter foldable. Our analysis explains how to compare comfort and multitasking without pretending to have tested it.',
'''Anunciado em 12 de agosto, o Pixel 11 Pro Fold é descrito pelo Google como quase 10% mais leve e cerca de 1 mm mais fino que o antecessor. O conjunto inclui Tensor G6 e 16 GB de RAM. São informações do fabricante, não medições nossas.

Em um dobrável, peso e espessura entram no uso de uma forma muito concreta: segurar uma sessão de leitura, assistir algo no transporte ou apoiar o aparelho para acompanhar documentação. Por isso, o formato precisa justificar o espaço que ocupa no bolso e no orçamento.

Nossa comparação documental começaria por duas listas: o que você faria com a tela fechada e o que realmente exigiria abri-la. Se quase tudo fica na primeira, vale questionar o benefício de carregar uma segunda experiência. Se você alterna documentos e comunicação o tempo todo, a proposta merece um teste presencial.

Não concluímos que o Fold substitui um tablet ou que roda jogos melhor que um celular tradicional. Também faltam medições próprias de dobradiça, autonomia e aquecimento. O anúncio tem um argumento claro de portabilidade; o valor desse argumento depende da frequência com que a tela maior resolveria alguma coisa para você.''',
'''Announced on August 12, Pixel 11 Pro Fold is described by Google as almost 10% lighter and approximately one millimeter thinner than its predecessor. It includes Tensor G6 and 16GB of RAM. These are manufacturer specifications, not our measurements.

On a foldable, weight and thickness affect concrete activities: holding it through a reading session, watching something on public transport or following documentation. The format therefore needs to justify the space it occupies in your pocket and budget.

Our document-based comparison would start with two lists: tasks you would perform with the screen closed and tasks that genuinely require opening it. If nearly everything belongs to the first list, question the benefit of carrying a second experience. If you constantly alternate between documents and communication, the proposition deserves an in-person trial.

We are not concluding that the Fold replaces a tablet or runs games better than a conventional phone. We also lack our own hinge, battery and temperature measurements. The announcement makes a clear portability argument; its value depends on how often the larger screen would solve a real problem for you.''',
'https://blog.google/intl/en-in/products/hardware/googles-most-sophisticated-foldable-pixel-11-pro-fold/','Google — Pixel 11 Pro Fold','2026-08-12',['Pixel11','Dobraveis','Android'],'Quantas vezes por dia você realmente abriria um dobrável?','How often would you actually unfold your phone each day?','Use a pergunta antes de comparar fichas técnicas.','Ask that question before comparing specifications.','Duas placas abstratas articuladas com linhas de peso e escala.',kind='analysis')

add('celulares','galaxy-fold8-comparacao','Galaxy Z Fold8 e Fold8 Ultra: compare o formato antes do nome','Galaxy Z Fold8 vs Fold8 Ultra: compare the shape before the name',
'Samsung colocou propostas diferentes nos dobráveis de julho. Entenda a comparação documental entre formato, peso e tela, sem inventar um vencedor.',
'Samsung’s July foldables take different approaches. Compare documented shape, weight and screen differences without inventing a universal winner.',
'''A Samsung apresentou a linha em 22 de julho. Na documentação, Fold8 tem tela interna de 7,6 polegadas e pesa 201 g; Fold8 Ultra combina 8 polegadas e 215 g. Os números ajudam a comparar tamanho, mas não medem sozinhos conforto ou produtividade.

O primeiro critério desta comparação é o formato. Uma área maior pode favorecer documentos e múltiplas janelas, enquanto proporções diferentes mudam o jeito de exibir vídeo e jogos. Isso não significa que cada aplicativo aproveite automaticamente cada centímetro da tela.

O segundo é a rotina com o aparelho fechado. Escrever uma mensagem com uma mão e abrir rapidamente um mapa são atividades mais frequentes que uma demonstração perfeita de multitarefa. O terceiro é o custo completo na sua região, incluindo assistência e acessórios relevantes; não usamos conversão direta de preço estrangeiro como oferta brasileira.

O resultado é um mapa de decisão, não um pódio: priorize tamanho e ergonomia de acordo com as tarefas que você repete. Ainda não fizemos testes com os aparelhos. Antes de escolher pelo Ultra no nome, experimente segurar os dois e verifique se os apps importantes para você funcionam bem no formato desejado.''',
'''Samsung introduced the lineup on July 22. Its documentation lists a 7.6-inch inner screen and 201g weight for Fold8, versus eight inches and 215g for Fold8 Ultra. Those numbers help compare size but do not independently measure comfort or productivity.

The first criterion in this comparison is shape. A larger area may suit documents and multiple windows, while different proportions change how video and games appear. That does not mean every app automatically uses every inch effectively.

The second criterion is everyday closed-phone use. Typing one-handed or quickly opening a map happens more often than a perfect multitasking demonstration. Third comes the complete cost in your region, including support and relevant accessories; a currency conversion is not a local retail offer.

The result is a decision framework, not a podium: prioritize size and ergonomics according to the tasks you repeat. We have not tested either phone. Before choosing the Ultra label, try holding both and check whether your important apps work well in the format you prefer. The more impressive specification is only useful if it improves those ordinary moments.''',
'https://news.samsung.com/global/galaxy-unpacked-july-2026-a-first-look-at-galaxy-z-fold8-ultra-galaxy-z-fold8-and-galaxy-z-flip8','Samsung — primeiros detalhes Fold8','2026-07-22',['GalaxyZFold8','Samsung','Comparativo'],'Ultra no nome não escolhe o formato ideal por você.','An Ultra label cannot choose the right shape for you.','Salve a comparação antes de visitar uma loja.','Save the comparison before visiting a store.','Dois retângulos articulados de proporções diferentes, cotas editoriais sem render.',kind='comparacao')

add('celulares','galaxy-s26-privacy','Galaxy S26 Ultra: privacidade de tela vira recurso de hardware','Galaxy S26 Ultra: screen privacy becomes a hardware feature',
'A Samsung apresentou Privacy Display no S26 Ultra em fevereiro. Entenda por que privacidade visual e segurança dos seus dados são perguntas diferentes.',
'Samsung introduced Privacy Display with S26 Ultra in February. Visual privacy and the security of your data are related but different questions.',
'''Em comunicado publicado em 26 de fevereiro, após o evento do dia 25, a Samsung destacou Privacy Display no Galaxy S26 Ultra, um recurso de privacidade integrado à tela. Retomamos o lançamento por uma ideia útil: parte da experiência de usar um celular acontece com outras pessoas olhando ao redor.

No ônibus, num evento ou numa mesa compartilhada, reduzir a exposição visual pode ser relevante para mensagens e trabalho. Mas isso não equivale a proteger uma conta contra senha fraca, aplicativo malicioso ou envio de dados ao destino errado. São problemas diferentes, com soluções diferentes.

Nossa avaliação futura observaria legibilidade frontal, efeito para quem está ao lado e comportamento em conteúdos claros e escuros. Para gamers, também caberia testar como o recurso combina com brilho, cores e sessões prolongadas. O fato de existir na ficha técnica não responde a essas perguntas.

Não medimos o efeito do Privacy Display e não declaramos o S26 Ultra mais seguro que concorrentes. A proposta merece atenção porque leva uma preocupação cotidiana ao hardware. Se ela combina com sua rotina, procure demonstrações comparáveis e teste presencialmente; se você quase nunca usa o aparelho em ambientes compartilhados, talvez outro critério pese mais.''',
'''In a statement published February 26, following the February 25 event, Samsung highlighted Privacy Display on Galaxy S26 Ultra, a privacy feature built into the screen. We are revisiting the release for a practical idea: part of using a phone happens while other people are nearby.

On public transport, at an event or at a shared desk, limiting visual exposure may matter for messages and work. That is not equivalent to protecting an account against a weak password, malicious app or information sent to the wrong destination. Those are different problems requiring different measures.

A future evaluation would examine straight-on readability, the view from beside the user and behavior with bright and dark content. For players, it would also be useful to test brightness, color and longer sessions. A specification sheet does not answer those questions.

We have not measured Privacy Display or declared S26 Ultra more secure than competing phones. The idea deserves attention because it brings an everyday concern into hardware. If it fits your routine, look for comparable demonstrations and try it in person. If you rarely use your phone around others, another criterion may matter more.''',
'https://news.samsung.com/global/samsung-unveils-galaxy-s26-series-the-most-intuitive-galaxy-ai-phone-yet','Samsung — Galaxy S26','2026-02-25',['GalaxyS26','Samsung','Privacidade'],'Privacidade de tela não é a mesma coisa que segurança de conta.','Screen privacy is not the same as account security.','Envie para quem usa o celular no transporte ou em eventos.','Send this to someone using a phone in shared spaces.','Feixe de tela central legível com laterais abstratas escurecidas.',kind='explicador',extra=[{'name':'Samsung Business — evento','url':'https://insights.samsung.com/2026/02/25/samsung-unpacked-february-2026-full-replay-and-highlights/','eventDate':'2026-02-25'}])

add('celulares','honor-magic-v6','HONOR Magic V6: bateria grande entra na disputa dos dobráveis','HONOR Magic V6: a larger battery joins the foldable debate',
'O lançamento da HONOR na Malásia destacou uma bateria de silício-carbono. Entenda o que a capacidade informa e o que ainda exige teste de uso real.',
'HONOR’s Malaysian launch highlighted a silicon-carbon battery. Understand what capacity tells you and what still requires real-world testing.',
'''A HONOR lançou o Magic V6 na Malásia em 4 de junho, após sua apresentação no MWC. A configuração divulgada tem bateria de silício-carbono de 6.660 mAh e Snapdragon 8 Elite Gen 5. Disponibilidade e configurações de outros mercados precisam de confirmação local.

Uma bateria grande é um argumento fácil de entender para quem joga longe da tomada. Só que mAh não é uma medida direta de horas de gameplay. Tela, brilho, conexão, jogo e gerenciamento térmico fazem parte da experiência que realmente queremos conhecer.

Nossa proposta de teste comparativo manteria o mesmo jogo e as mesmas condições, registrando consumo, temperatura e estabilidade ao longo da sessão. Para criação, acrescentaria gravação e transferência de vídeo. O importante é evitar comparar uma estimativa de reprodução de vídeo com uma partida exigente como se fossem a mesma atividade.

Ainda não tivemos o aparelho em mãos. O Magic V6 entra no radar pela tentativa de combinar formato dobrável e capacidade de bateria, não por uma autonomia que possamos prometer. Se você considera importar, verifique a versão exata, assistência e compatibilidade dos serviços; um anúncio em outro país não estabelece cobertura ou garantia no Brasil.''',
'''HONOR launched Magic V6 in Malaysia on June 4 following its MWC presentation. The announced configuration includes a 6,660mAh silicon-carbon battery and Snapdragon 8 Elite Gen 5. Availability and configurations elsewhere require local confirmation.

A large battery is an understandable argument for anyone playing away from a socket. But milliamp-hours are not a direct measurement of gaming hours. Screen behavior, brightness, connectivity, the game and thermal management all contribute to the experience we actually want to assess.

Our comparison would keep the game and conditions consistent while recording consumption, temperature and stability over a session. For creators, we would add video recording and file transfer. The key is not to compare a video-playback estimate with demanding gameplay as if they were equivalent activities.

We have not used this phone. Magic V6 deserves attention for combining a foldable format with substantial battery capacity, not for battery life we can promise. If you are considering an import, verify the exact version, support and service compatibility. An announcement in another country cannot establish local warranty coverage or the experience you will receive.''',
'https://www.honor.com/global/news/honor-magic-v6-launch/','HONOR — lançamento Magic V6 na Malásia','2026-06-04',['HONORMagicV6','Dobraveis','Bateria'],'mAh alto chama atenção. Quantas horas de jogo ele entrega?','A big mAh number catches the eye. How many gaming hours does it deliver?','Guarde a pergunta para comparar testes de bateria.','Keep that question in mind when comparing battery tests.','Célula de bateria entre duas superfícies articuladas, padrão carbono abstrato.',kind='analysis')

add('celulares','xiaomi17ultra','Xiaomi 17 Ultra: confira a versão antes de comparar a câmera','Xiaomi 17 Ultra: check the version before comparing cameras',
'A estreia global ocorreu em fevereiro, após a apresentação chinesa. Versão, câmera e suporte importam mais que misturar fichas de países diferentes.',
'The global debut followed the Chinese announcement. Version, camera and support matter more than mixing specifications from different countries.',
'''A Xiaomi apresentou a série 17 globalmente em 28 de fevereiro, após o anúncio chinês do Ultra em dezembro de 2025. O FAQ global descreve bateria típica de 6.000 mAh e Snapdragon 8 Elite Gen 5. Datas e versões diferentes não devem virar uma ficha técnica misturada.

Para quem acompanha celulares da China, esse cuidado é essencial. O mesmo nome comercial pode aparecer em páginas destinadas a públicos distintos. Antes de comparar, anote modelo completo, região e configuração. Isso vale tanto para uma review quanto para a página de uma loja.

Na câmera, nossa avaliação priorizaria situações concretas: pessoas em movimento, luz de ambiente e consistência entre lentes. Uma foto estática de vitrine diz pouco sobre gravar seu setup ou registrar um evento cheio de gente. Também interessa quanto trabalho sobra para editar e compartilhar.

Não produzimos imagens com o aparelho nem classificamos sua câmera acima de concorrentes. O foco aqui é organizar a comparação documental para evitar promessas erradas. Se o anúncio despertou interesse, procure amostras originais da versão pretendida e confirmação de assistência local. Marca de câmera e número de megapixels são pontos de partida, não uma conclusão pronta.''',
'''Xiaomi introduced the 17 series globally on February 28, following the Ultra’s Chinese announcement in December 2025. The global FAQ lists a typical 6,000mAh battery and Snapdragon 8 Elite Gen 5. Different dates and versions should not become a mixed specification sheet.

That distinction matters when following phones from China. The same commercial name can appear on pages serving different markets. Before comparing, record the complete model, region and configuration. This applies to reviews and retailer listings alike.

For camera evaluation, we would prioritize concrete situations: moving people, indoor light and consistency between lenses. A static showroom image says little about filming a gaming setup or recording a crowded event. The amount of editing and sharing work afterward matters as well.

We have not shot with this device or ranked its camera above competitors. The goal is to organize a document-based comparison without importing incorrect promises. If the announcement interests you, seek original samples from the intended version and confirmation of local support. Camera branding and megapixel counts are starting points, not ready-made conclusions about quality or value.''',
'https://www.mi.com/global/support/faq/details/KA-667490/','Xiaomi — FAQ global 17 Ultra','2026-02-28',['Xiaomi17Ultra','Celulares','Fotografia'],'Antes de comparar celulares da China, confirme qual versão está na ficha.','Before comparing phones from China, confirm which version the specs describe.','Compartilhe com quem pesquisa um aparelho importado.','Share with someone researching an imported phone.','Duas fichas regionais abstratas convergindo para uma lente central.',kind='analysis',extra=[{'name':'Xiaomi — anúncio chinês','url':'https://www.mi.com/global/discover/article?id=5825','eventDate':'2025-12-25'},{'name':'Xiaomi — anúncio global','url':'https://www.mi.com/global/discover/article?id=5972','eventDate':'2026-02-28'}])

add('celulares','oppo-findx9ultra','OPPO Find X9 Ultra: zoom óptico merece um teste honesto','OPPO Find X9 Ultra: optical zoom deserves a fair test',
'A OPPO levou o Find X9 Ultra a novos mercados em 2026. A teleobjetiva de 10x chama atenção, mas o resultado precisa ser comparado em condições iguais.',
'OPPO brought Find X9 Ultra to more markets in 2026. Its 10x telephoto stands out, but results need comparison under matching conditions.',
'''O Find X9 Ultra amplia a disputa de câmeras entre celulares de 2026. A OPPO documenta uma teleobjetiva óptica de 10x com 50 MP e bateria de 7.050 mAh. No Japão, anunciou início de vendas em 8 de julho. Esta data é regional, não brasileira.

O alcance interessa para fotografar detalhes sem chegar perto, inclusive em eventos. Mas zoom não é uma régua única de qualidade. A pergunta prática é o que acontece com movimento, pouca luz e o enquadramento que você realmente consegue manter ao segurar o aparelho.

Um comparativo justo usaria a mesma cena e distância, preservaria os arquivos originais e identificaria a ampliação aplicada. Também separaria captura óptica de recorte e processamento. Sem isso, duas imagens bonitas lado a lado podem comparar situações muito diferentes.

Não usamos o Find X9 Ultra nesta reportagem e não damos nota de câmera. A leitura documental aponta uma proposta voltada à criação, que precisa ser confrontada com tamanho, rotina de edição e suporte local. Para compartilhar uma foto impressionante como evidência, mostre também como ela foi feita. O contexto deixa a comparação muito mais útil que uma disputa de slogans.''',
'''Find X9 Ultra expands the 2026 smartphone camera debate. OPPO documents a 50MP 10x optical telephoto and a 7,050mAh battery. In Japan, the company announced sales beginning July 8. That date applies to that market, not automatically to others.

The reach is interesting for capturing distant details, including at events. But zoom is not a single ruler for quality. The practical question is what happens with motion, dim light and the framing you can actually maintain while holding the phone.

A fair comparison would use the same scene and distance, preserve original files and identify the magnification applied. It would also separate optical capture from cropping and processing. Otherwise, two attractive images placed side by side might represent very different conditions.

We did not use Find X9 Ultra for this report and are not assigning a camera score. The documentation suggests a creation-focused proposition that still needs to be weighed against size, editing routine and local support. When sharing an impressive photo as evidence, show how it was made too. Context makes the comparison much more useful than competing slogans.''',
'https://www.oppo.com/jp/newsroom/press/findx9ultra-release/','OPPO Japão — lançamento Find X9 Ultra','2026-07-08',['OPPO','FotografiaMobile','Celulares'],'Zoom impressionante só vira comparação quando as condições aparecem.','Impressive zoom becomes a comparison only when the conditions are visible.','Salve os critérios para avaliar fotos de reviews.','Save these criteria for assessing review photos.','Dez anéis concêntricos convergindo em detalhe abstrato; sem foto de amostra.',kind='analysis')

add('celulares','oneplus15-165hz','OnePlus 15 e tela de 165 Hz: não confunda painel com FPS','OnePlus 15 and its 165Hz display: panel speed is not game FPS',
'O OnePlus 15, lançado em 2025, continua rendendo uma boa pergunta gamer: por que uma tela rápida não garante a mesma taxa de quadros em todo jogo?',
'The OnePlus 15, launched in 2025, raises a useful gaming question: why does a fast screen not guarantee the same frame rate in every game?',
'''O OnePlus 15 foi lançado na América do Norte em novembro de 2025. A página oficial descreve tela de até 165 Hz, Snapdragon 8 Elite Gen 5 e bateria de 7.300 mAh. Retomamos o aparelho como explicador, sem tratar um lançamento antigo como notícia desta semana.

Hz descreve a frequência de atualização da tela; FPS descreve quantos quadros o jogo produz. São números relacionados, mas não intercambiáveis. A fluidez depende também do software e da estabilidade ao longo da sessão, não apenas do máximo impresso na caixa.

Para comparar um celular gamer, procure o nome e a versão do jogo, a configuração gráfica e a duração do teste. Vale mais uma medição sustentada do que um pico rápido. Observe ainda temperatura e consumo: desempenho que muda muito quando o aparelho aquece merece contexto.

Não medimos o OnePlus 15 nem afirmamos que determinado jogo roda a 165 FPS nele. A proposta tem especificações que chamam atenção, mas nossa conclusão é metodológica: escolha pelas experiências documentadas que importam para você. Uma tela rápida pode ser útil sem transformar todos os games em uma vitrine de taxa máxima.''',
'''OnePlus 15 launched in North America in November 2025. The official page lists a display reaching up to 165Hz, Snapdragon 8 Elite Gen 5 and a 7,300mAh battery. We revisit it as an explainer, not as a product released this week.

Hertz describes display refresh frequency; frames per second describes the frames a game produces. The figures are related but not interchangeable. Smoothness also depends on software and consistency throughout a session, rather than just the maximum printed on the box.

When comparing gaming phones, look for the game and version, graphics settings and test duration. Sustained measurements tell you more than a brief peak. Temperature and consumption matter too: performance that changes significantly as a device warms up needs context.

We have not measured OnePlus 15 performance or claimed that a particular title runs at 165 FPS on it. The specifications are attention-grabbing, but our conclusion concerns the method: choose according to documented experiences that matter to you. A fast panel can be useful without turning every game into a showcase of its maximum refresh rate.''',
'https://www.oneplus.com/us/15','OnePlus — especificações 15','2025-11-13',['OnePlus15','MobileGaming','FPS'],'165 Hz na tela não garante 165 FPS no seu game.','A 165Hz screen does not guarantee 165 FPS in your game.','Envie para aquele amigo que só compara o número da caixa.','Send this to a friend comparing only the numbers on the box.','Duas linhas de tempo abstratas: atualização de tela e quadros renderizados.',kind='explicador',extra=[{'name':'OnePlus — anúncio América do Norte','url':'https://www.oneplus.com/us/press/press-release/oneplus-launches-the-oneplus-15--the-ultimate-performance-flagship-smartphone-for-north-america','eventDate':'2025-11-13'}])

add('curiosidades','typescript7-go','TypeScript 7: por que um compilador escrito em Go importa','TypeScript 7: why a compiler written in Go matters',
'O TypeScript 7 estreou em julho com uma base nativa em Go. Para devs, a oportunidade está no tempo de desenvolvimento, não numa mudança de linguagem do app.',
'TypeScript 7 arrived in July with a native Go foundation. The opportunity is faster development work, not a requirement to change your application language.',
'''A Microsoft lançou TypeScript 7 em 8 de julho, com o compilador reimplementado em Go. O time relata ganhos de velocidade em builds completos. Isso diz respeito à ferramenta que analisa o projeto; não transforma automaticamente o código da sua aplicação em Go.

É uma distinção pequena que evita muita confusão. Quem desenvolve um site ou um jogo web continua interessado em tipos, erros e integração com o editor. A mudança de implementação importa quando reduz o intervalo entre editar e descobrir um problema.

Nossa proposta de avaliação é medir um projeto conhecido antes e depois da atualização. Separe instalação, checagem de tipos, build e testes, pois uma etapa mais rápida pode não ser o gargalo principal. Registre também a máquina usada e verifique ferramentas que dependem diretamente do compilador.

Não medimos ganhos no AnderZilla e não reproduzimos a promessa de velocidade como resultado garantido. O lançamento é relevante para repositórios que sofrem com espera e feedback lento. Para um projeto pequeno que já responde rápido, a melhor decisão pode vir da compatibilidade e da manutenção. O número que interessa é o tempo poupado no seu ciclo completo de trabalho.''',
'''Microsoft released TypeScript 7 on July 8 with its compiler reimplemented in Go. The team reports faster full builds. This concerns the tool analyzing your project; it does not automatically turn application code into Go.

That small distinction prevents a lot of confusion. Developers building websites or browser games still care about types, errors and editor integration. The implementation change becomes useful when it shortens the interval between editing and discovering a problem.

Our evaluation approach is to measure a familiar project before and after upgrading. Separate installation, type checking, building and testing, because a faster stage may not be the main bottleneck. Record the machine used and check tools that depend directly on the compiler.

We have not measured gains in AnderZilla and do not present the speed claim as a guaranteed result. The release matters for repositories struggling with waiting and slow feedback. For a small project that already responds quickly, compatibility and maintenance may guide the decision. The useful number is time saved across your complete development loop, including any migration work.''',
'https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/','Microsoft — TypeScript 7','2026-07-08',['TypeScript','Dev','Programacao'],'TypeScript escrito em Go não significa reescrever seu app em Go.','TypeScript being written in Go does not mean rewriting your app in Go.','Compartilhe com quem vive esperando o build terminar.','Share with someone always waiting for a build.','Dois trilhos de compilação abstratos, um cronômetro sem números inventados.')

add('curiosidades','npm-trusted-publishing','npm ganha múltiplas configurações de publicação confiável','npm gains multiple trusted publishing configurations',
'A atualização de setembro permite separar fluxos de publicação no npm. Entenda a mudança e por que permissões adicionais precisam de revisão.',
'September’s npm update lets maintainers separate publishing workflows. Understand the change and why additional permissions deserve careful review.',
'''O GitHub anunciou em 3 de setembro que pacotes npm podem ter múltiplas configurações de trusted publishing via OIDC. Cada configuração é independente: a publicação é autorizada se corresponder a uma delas. A mudança permite organizar diferentes fluxos sem depender de uma configuração única.

Para quem mantém uma biblioteca ou ferramenta de modding, isso aproxima a publicação da organização real do projeto. Uma versão de teste e uma estável podem seguir caminhos distintos. O cuidado é não interpretar várias permissões como uma barreira que exige passar por todas: na regra anunciada, elas são alternativas.

Nossa sugestão editorial é desenhar quais repositórios, workflows e ambientes realmente precisam publicar. Dê um nome compreensível a cada caminho e remova configurações que perderam função. Um histórico claro ajuda a explicar de onde veio uma versão quando aparece um problema.

Não configuramos publicação de pacotes nesta reportagem. O valor da novidade é facilitar um processo rastreável, mas ela não torna qualquer workflow confiável por definição. Antes de aplicar no seu projeto, confira a documentação e teste o caminho pretendido com uma versão de pré-lançamento. O objetivo é publicar com menos improviso e saber exatamente quem pode chegar ao registro.''',
'''GitHub announced on September 3 that npm packages can have multiple OIDC trusted-publishing configurations. Each configuration is independent: publishing is authorized if it matches any one of them. The change allows different workflows without relying on a single configuration.

For maintainers of libraries or modding tools, that brings publishing closer to a project’s actual organization. Prerelease and stable versions can follow separate paths. The important distinction is that several permissions do not create a barrier requiring every condition to match: the announced configurations are alternatives.

Our editorial suggestion is to map which repositories, workflows and environments genuinely need publishing access. Give each path an understandable name and remove configurations that no longer serve a purpose. A clear history helps explain where a version came from when something goes wrong.

We did not configure package publishing for this report. The update can make a process easier to trace, but it does not make every workflow trustworthy by definition. Read the documentation and test the intended path with a prerelease first. The goal is less improvisation and a clear understanding of who can publish to the registry.''',
'https://github.blog/changelog/2026-09-03-multiple-trusted-publishing-configurations-for-npm/','GitHub — trusted publishing npm','2026-09-03',['npm','Dev','OpenSource'],'Duas permissões alternativas não formam uma trava dupla.','Two alternative permissions do not form a double lock.','Salve antes de reorganizar a publicação da sua biblioteca.','Save this before reorganizing your library’s publishing process.','Três caminhos independentes chegando a um pacote abstrato.')

add('curiosidades','github-secrets-merge','GitHub testa bloqueio de merge quando um PR expõe segredos','GitHub previews merge blocking for pull requests exposing secrets',
'Uma regra em prévia pública pode impedir merges com alertas de segredos pendentes. Veja a diferença entre detectar um problema e resolver uma exposição.',
'A public-preview rule can block merges with unresolved secret alerts. Understand the difference between detecting a problem and resolving an exposure.',
'''O GitHub anunciou em 9 de setembro uma regra de repositório para bloquear merges de pull requests que introduzem alertas de segredos. A prévia pública exige GitHub Secret Protection ou Advanced Security. A regra verifica a conclusão da análise e alertas pendentes introduzidos pelo PR.

Para devs, é um lembrete oportuno: um token pode entrar num arquivo de configuração ou exemplo aparentemente inocente. Ver o problema antes da integração ajuda, mas não apaga o fato de que uma credencial real foi exposta em algum lugar.

Nossa leitura editorial é tratar o alerta como início da investigação. Entenda qual informação entrou, quem teve acesso e qual procedimento de correção se aplica ao serviço. Apagar uma linha do diff não deve ser confundido com invalidar uma credencial comprometida.

O recurso também precisa ser configurado e pode envolver permissões de exceção. Não habilitamos a regra nem verificamos elegibilidade de nenhuma conta nesta matéria. Para um projeto pessoal, o passo útil é conhecer o fluxo atual de revisão e decidir onde essa proteção acrescentaria cobertura. Automação boa torna o erro visível e a resposta rastreável; não substitui a responsabilidade de resolver a causa.''',
'''GitHub announced a repository rule on September 9 that can block merging pull requests introducing secret-scanning alerts. The public preview requires GitHub Secret Protection or Advanced Security. The rule checks scan completion and unresolved alerts introduced by the PR.

For developers, this is a timely reminder: a token can enter an apparently harmless configuration file or example. Spotting it before integration helps, but does not erase the fact that a real credential was exposed somewhere.

Our editorial reading treats the alert as the start of an investigation. Understand what information was included, who could access it and which remediation procedure applies to the service. Deleting a line from a diff should not be confused with invalidating a compromised credential.

The feature also needs configuration and may involve bypass permissions. We did not enable it or verify any account’s eligibility for this story. For a personal project, the useful next step is understanding the current review process and deciding where the protection would add coverage. Good automation makes an error visible and the response traceable; it does not replace responsibility for addressing the cause.''',
'https://github.blog/changelog/2026-09-09-block-pull-requests-with-exposed-secrets-from-merging/','GitHub — bloqueio de merge por segredos','2026-09-09',['GitHub','Dev','Seguranca'],'Apagar um token do código não é a mesma coisa que invalidá-lo.','Deleting a token from code is not the same as invalidating it.','Compartilhe com quem revisa PRs no seu projeto.','Share with someone reviewing your project’s pull requests.','Ramificações de código com uma chave abstrata parada antes da junção.')

add('curiosidades','godot-mouse-polling','Godot corrige engasgos com mouse rápido no Windows','Godot fixes Windows stutter linked to high-polling mice',
'Um relatório do Godot explica a correção para mouses de alta frequência. A novidade liga um detalhe do periférico à estabilidade dos quadros no jogo.',
'A Godot report explains a fix for high-polling mice. The update connects a peripheral setting with the stability of the game’s frame delivery.',
'''Em 24 de agosto, o Godot detalhou uma correção para problemas de desempenho com mouses de alta frequência no Windows, presente a partir do Godot 4.7.2. O relatório usa alta frequência para taxas de pelo menos 2 kHz e mostra avaliações do próprio projeto.

É uma curiosidade que conecta diretamente gamers e devs. Um periférico pensado para responder mais rápido também produz um fluxo maior de eventos. O software precisa lidar com esse trabalho sem prejudicar as outras tarefas que mantêm o jogo fluido.

Se você cria um jogo, uma verificação útil é comparar a mesma cena com o mouse parado e em movimento, registrando tempos de quadro. Depois, repetir em diferentes taxas suportadas pelo periférico. Mudar várias opções ao mesmo tempo torna difícil descobrir a causa de uma melhora ou piora.

Não medimos a correção no AnderZilla e não prometemos ganho universal de FPS. Ela diz respeito a um cenário específico, que merece entrar na lista de diagnóstico quando mover o mouse provoca engasgos. Para quem só joga, vale procurar a versão do jogo e o changelog do desenvolvedor: atualizar o editor não atualiza automaticamente um jogo já distribuído.''',
'''On August 24, Godot detailed a Windows performance fix for high-polling mice, included from Godot 4.7.2. The report defines high polling here as rates of at least 2kHz and presents measurements made by the project.

This connects gamers and developers directly. A peripheral designed to respond faster also generates more input events. Software must handle that work without disrupting the other tasks keeping a game smooth.

If you develop a game, a useful check compares the same scene with the mouse stationary and moving while recording frame times. Repeat at different polling rates supported by the peripheral. Changing several settings at once makes it harder to identify the cause of an improvement or regression.

We have not measured this fix in AnderZilla and do not promise a universal FPS increase. It addresses a specific scenario worth including in troubleshooting when mouse movement causes stutter. Players should check the game version and developer’s changelog: updating an editor does not automatically update a game that has already been distributed. That distinction matters before assuming a fix has reached your installed title.''',
'https://godotengine.org/article/fixing-high-polling-rate-mice-on-windows/','Godot — mouse polling no Windows','2026-08-24',['Godot','PCGamer','MouseGamer'],'O game engasga quando você move o mouse? Esse detalhe merece investigação.','Does your game stutter when you move the mouse? This detail deserves a look.','Envie para quem desenvolve ou joga no PC.','Send this to someone developing or playing on PC.','Mouse abstrato enviando pulsos para linha de quadros irregular que se estabiliza.')

add('curiosidades','codeql-go127','CodeQL amplia suporte a Go 1.27 e ajusta alertas','CodeQL adds Go 1.27 support and refines alerts',
'O CodeQL 2.26.4 trouxe suporte de linguagem e ajustes de detecção em setembro. Entenda por que um alerta que muda de lugar não é automaticamente um bug novo.',
'CodeQL 2.26.4 brought language support and detection updates in September. An alert moving location does not automatically indicate a new software defect.',
'''O GitHub anunciou em 3 de setembro o CodeQL 2.26.4, com suporte a Go 1.27 e ajustes nas detecções de segurança. No Rust, a localização de alertas de fluxo de dados ficou mais precisa; alguns podem aparecer como novos enquanto os anteriores são fechados.

Para quem acompanha o painel de segurança de um projeto, esse detalhe evita sustos e leituras erradas. A ferramenta pode melhorar a forma de apontar um problema que já existia. Uma mudança na contagem precisa ser investigada antes de virar conclusão sobre a qualidade de uma atualização do app.

Nossa orientação editorial é comparar o trecho afetado, o caminho de dados e a versão do analisador. Leia o contexto do alerta e registre por que ele foi corrigido ou descartado. A contagem isolada funciona mal como placar de segurança, especialmente quando o detector também está mudando.

Não executamos CodeQL sobre um repositório para esta matéria. A notícia interessa por mostrar que análise automatizada também é software em evolução. Se você mantém uma biblioteca ou jogo com serviços online, acompanhe tanto as mudanças no seu código quanto as da ferramenta que o inspeciona. Isso ajuda a separar descoberta nova, localização nova e problema realmente introduzido.''',
'''GitHub announced CodeQL 2.26.4 on September 3, adding Go 1.27 support and security-detection refinements. In Rust, data-flow alert locations became more precise; some alerts may appear as new while earlier ones close.

That detail helps developers avoid misreading a project’s security dashboard. A tool may improve how it points to a problem that already existed. A change in the count needs investigation before becoming a conclusion about the quality of an application update.

Our editorial advice is to compare the affected code, data path and analyzer version. Read the alert’s context and record why it was fixed or dismissed. An isolated count makes a poor security score, especially when the detector is changing too.

We did not run CodeQL against a repository for this report. The news matters because automated analysis is itself evolving software. If you maintain a library or a game with online services, follow changes both in your code and in the tool inspecting it. This helps distinguish a newly discovered issue, a newly located alert and a defect actually introduced by a recent change.''',
'https://github.blog/changelog/2026-09-03-codeql-2-26-4-improves-github-actions-security-detections/','GitHub — CodeQL 2.26.4','2026-09-03',['CodeQL','GoLang','Dev'],'Um alerta novo no painel pode ser uma localização mais precisa de algo antigo.','A new dashboard alert can be a more precise location for an existing issue.','Salve para a próxima revisão do seu painel de segurança.','Save this for your next security dashboard review.','Mapa de código com pino reposicionado e lupa, sem interface de fornecedor.')

add('curiosidades','raspberrypi-radio','Raspberry Pi vira rádio com botões: projeto para sair do chat','Raspberry Pi becomes a radio with knobs: a project beyond chat',
'Um tutorial oficial mostra um rádio online com controles físicos. A ideia combina Python e eletrônica numa interface simples de entender e explorar.',
'An official tutorial builds an internet radio with physical controls. It combines Python and electronics in an interface that is easy to understand and explore.',
'''A Raspberry Pi publicou em 3 de setembro um tutorial de rádio online com dois potenciômetros: um para estação e outro para volume. O projeto usa Python, GPIO Zero e um conversor analógico-digital MCP3008. É uma publicação técnica recente, não um produto pronto anunciado para venda.

O charme está em transformar código em algo que você pode girar com a mão. Para quem passa o dia em telas, uma interface com poucos controles ajuda a enxergar a relação entre entrada, processamento e resultado. Também rende um bom projeto para explicar tecnologia sem começar por uma parede de siglas.

Antes de montar, confira a lista completa de componentes e as instruções elétricas na fonte. Planeje um protótipo pequeno e uma forma de testar cada parte separadamente. Primeiro entender a leitura do controle; depois ligar essa leitura à função desejada é mais fácil de diagnosticar do que montar tudo de uma vez.

Não construímos o circuito nesta matéria e não estimamos um custo brasileiro sem cotação. A proposta é indicar um caminho documentado para um fim de semana maker. Se você já tem componentes compatíveis, pode ser uma oportunidade de reaproveitamento; se não tem, comece pela leitura e pela lista do que realmente falta.''',
'''Raspberry Pi published an internet-radio tutorial on September 3 using two potentiometers: one for station selection and another for volume. The project uses Python, GPIO Zero and an MCP3008 analog-to-digital converter. This is a recent technical publication, not a ready-made retail product.

Its appeal is turning code into something you can control with your hand. For people spending their days on screens, a simple physical interface makes the relationship between input, processing and output easier to see. It can also explain technology without opening with a wall of acronyms.

Before building, consult the complete component list and electrical instructions in the source. Plan a small prototype and a way to check each part separately. Understanding the control reading before connecting it to the intended function is easier to troubleshoot than assembling everything at once.

We did not build the circuit for this article or estimate local costs without quotations. The goal is to highlight a documented weekend maker project. If you already own compatible components, it may offer a reuse opportunity. Otherwise, start with the tutorial and a list of what you actually need.''',
'https://www.raspberrypi.com/news/build-an-internet-radio/','Raspberry Pi — rádio online','2026-09-03',['RaspberryPi','Python','Maker'],'Um botão de volume físico pode ser seu próximo projeto em Python.','A physical volume knob could be your next Python project.','Envie para quem curte um projeto de fim de semana.','Send this to someone who enjoys weekend projects.','Dois círculos de controle, onda sonora e placa abstrata; não desenhar circuito técnico.')

add('curiosidades','unitree-robos-fabrica','Unitree testa robôs na fabricação de outros robôs','Unitree tests robots in the manufacturing of other robots',
'A fabricante chinesa descreve testes de seu modelo de IA na própria fábrica. Entenda por que uma demonstração não equivale a autonomia industrial completa.',
'The Chinese manufacturer describes AI-model testing in its own factory. A demonstration does not establish complete industrial autonomy.',
'''Na cronologia oficial, a Unitree registra que apresentou o UnifoLM-X1-0 em 13 de fevereiro e o colocou em testes na própria instalação de fabricação de robôs. A empresa descreve tarefas de montagem e produção. A informação é uma declaração do fabricante, não uma auditoria independente da operação.

Robôs ajudando a fabricar robôs parece uma frase de ficção científica, mas a pergunta interessante é bem concreta: quais etapas eles executam e em quais condições? Um vídeo de sucesso não mostra necessariamente todas as tentativas, intervenções e preparações que vieram antes.

Nossa leitura editorial pede três informações para avaliar demonstrações desse tipo: tarefa delimitada, taxa de conclusão e necessidade de ajuda humana. Sem esse contexto, é fácil transformar um avanço real numa promessa muito maior do que a evidência permite.

Não visitamos a fábrica nem verificamos capacidade de produção. O registro vale como janela para o desenvolvimento de robótica na China e como convite a olhar além de coreografias impressionantes. Para acompanhar a área com qualidade, procure resultados repetíveis, descrição de falhas e comparações de tarefa. É aí que uma demonstração deixa de ser apenas um clipe compartilhável e passa a informar o que a tecnologia consegue fazer.''',
'''Unitree’s official timeline records that it introduced UnifoLM-X1-0 on February 13 and deployed it for testing at its own robot-manufacturing facility. The company describes assembly and production tasks. This is a manufacturer statement, not an independent operational audit.

Robots helping manufacture robots sounds like science fiction, but the interesting question is concrete: which steps do they perform, and under what conditions? A successful video does not necessarily reveal all preceding attempts, interventions and preparation.

Our editorial reading asks for three things when evaluating demonstrations: a bounded task, completion rate and the amount of human assistance required. Without that context, a real advance can easily become a promise much larger than the evidence supports.

We have not visited the factory or verified production capacity. The record offers a window into robotics development in China and an invitation to look beyond impressive choreography. Follow repeatable results, descriptions of failures and task-level comparisons. That is where a demonstration becomes more than a shareable clip and starts explaining what the technology can actually do under known conditions.''',
'https://www.unitree.com/about/','Unitree — cronologia oficial','2026-02-13',['Robotica','ChinaTech','IA'],'Robôs montando robôs: a pergunta boa é o que acontece fora do clipe.','Robots assembling robots: the useful question is what happens outside the clip.','Compartilhe com quem acompanha robótica.','Share with someone following robotics.','Braço mecânico abstrato aproximando duas peças geométricas, sem copiar robô real.',kind='analysis')

add('curiosidades','honor-robot-phone','HONOR Robot Phone: quando o celular começa a se mover','HONOR Robot Phone: when the phone starts moving',
'A HONOR mostrou uma visão de celular com movimento no MWC. A ideia rende discussão sobre captura e interação, mas não comprova um produto pronto no Brasil.',
'HONOR previewed a motion-enabled phone concept at MWC. It raises questions about capture and interaction without proving local retail readiness.',
'''No MWC, em 1º de março, a HONOR apresentou uma prévia do Robot Phone e seu primeiro robô humanoide. A empresa descreveu o celular como exploração de IA incorporada, movimento e percepção espacial. O anúncio consultado é uma apresentação de visão tecnológica, não confirmação de venda no Brasil.

Para um criador que grava sozinho, a ideia de um dispositivo acompanhar a cena é fácil de imaginar. Mas o valor depende de questões práticas: enquadramento, ruído do mecanismo, consumo e comportamento quando a pessoa sai de posição. Uma apresentação não responde a tudo isso.

Nosso interesse editorial está no encontro entre câmera, software e movimento físico. É um tipo de interface que poderia mudar como mostramos um setup ou registramos um objeto, mas qualquer afirmação sobre qualidade final precisa de demonstração verificável e condições claras.

Não testamos o Robot Phone e não tratamos o conceito como recomendação de compra. Antes de embarcar no hype, separe o que foi mostrado, o que a empresa pretende desenvolver e o que chegou efetivamente às mãos de usuários. A curiosidade é ótima; manter essas etapas separadas torna a conversa muito mais interessante do que anunciar o fim dos celulares tradicionais.''',
'''At MWC on March 1, HONOR previewed Robot Phone and its first humanoid robot. The company described the phone as an exploration of embodied AI, motion and spatial awareness. The announcement examined here presents a technology vision, not confirmation of Brazilian retail availability.

For a solo creator, a device that follows a scene is easy to imagine. Its value would depend on practical questions, however: framing, mechanism noise, power consumption and behavior when someone moves out of position. A presentation cannot answer all of those.

Our editorial interest lies where camera, software and physical movement meet. This kind of interface could change how we show a setup or record an object, but claims about finished quality need verifiable demonstrations and clear conditions.

We have not tested Robot Phone and do not treat the concept as a buying recommendation. Before following the hype, separate what was shown, what the company intends to develop and what has actually reached users. Curiosity is welcome; keeping those stages distinct makes the conversation much more interesting than announcing the end of conventional smartphones.''',
'https://www.honor.com/global/news/honor-mwc2026-launch/','HONOR — MWC 2026','2026-03-01',['HONOR','Robotica','ChinaTech'],'Celular com movimento: ideia fascinante, perguntas práticas primeiro.','A phone with movement: fascinating idea, practical questions first.','Qual tarefa de gravação você gostaria de simplificar?','Which recording task would you like to simplify?','Lente abstrata em suporte articulado, claramente conceito editorial.',kind='analysis')

add('curiosidades','xiaomi-vision-gran-turismo','Xiaomi Vision Gran Turismo aproxima celulares e cultura gamer','Xiaomi Vision Gran Turismo connects phone brands and gaming culture',
'A Xiaomi apresentou um conceito de hipercarro para a franquia Gran Turismo em fevereiro. Entenda o que é projeto conceitual e o que não foi confirmado.',
'Xiaomi presented a hypercar concept for the Gran Turismo franchise in February. Understand the concept and avoid confusing it with confirmed production.',
'''A Xiaomi apresentou o Vision Gran Turismo em 28 de fevereiro, em um evento que também trouxe celulares e outros dispositivos. A empresa o descreveu como conceito de hipercarro elétrico criado para a franquia Gran Turismo. Isso não equivale a anunciar um automóvel de produção disponível para compra.

O encontro é curioso porque coloca uma marca conhecida por celulares dentro de uma linguagem familiar a jogadores: imaginar um veículo além das restrições habituais. Conceitos desse tipo podem funcionar como laboratório visual e como conversa entre design industrial e entretenimento.

Nossa leitura editorial é acompanhar o que o projeto mostra sem preencher lacunas com suposições. Render, maquete, carro funcional e conteúdo jogável são entregas diferentes. Uma imagem de apresentação não estabelece desempenho real, data de chegada a um jogo ou disponibilidade em todos os títulos da série.

Não dirigimos nem jogamos com esse conceito. O interesse da pauta está no cruzamento entre a tecnologia chinesa e a cultura automotiva dos games. Para compartilhar com qualidade, preserve a palavra conceito e a data do anúncio. Dá para curtir uma ideia ousada sem transformar expectativa em ficha técnica ou calendário que a fonte não confirmou.''',
'''Xiaomi presented Vision Gran Turismo on February 28 at an event also featuring phones and other devices. The company described it as an electric hypercar concept created for the Gran Turismo franchise. That is not an announcement of a production car available to buy.

The crossover is interesting because a brand associated with phones enters familiar gaming territory: imagining a vehicle beyond everyday constraints. Such concepts can act as visual laboratories and conversations between industrial design and entertainment.

Our editorial reading follows what the project shows without filling gaps with assumptions. A render, scale model, functional car and playable content are different deliverables. A presentation image does not establish real performance, an in-game release date or availability across every title in the series.

We have neither driven nor played with this concept. The story’s appeal is the intersection of Chinese technology and gaming’s car culture. If you share it, preserve the word concept and the announcement date. It is possible to enjoy an ambitious idea without turning expectations into specifications or a release calendar the source did not confirm.''',
'https://www.mi.com/global/discover/article?id=5972','Xiaomi — anúncio global de fevereiro','2026-02-28',['Xiaomi','GranTurismo','ChinaTech'],'Conceito de hipercarro não é anúncio de carro pronto para comprar.','A hypercar concept is not a production-car sales announcement.','Compartilhe com quem curte games de corrida.','Share with someone who loves racing games.','Curva de pista neon e silhueta geométrica inventada, sem simular o carro Xiaomi.',kind='analysis')

add('curiosidades','model-hardware-standard','Model Hardware Standard: agentes de IA saem da tela','Model Hardware Standard: AI agents move beyond the screen',
'A Anthropic abriu uma prévia de integração entre agentes e equipamentos físicos. A proposta conecta software e laboratório, com questões novas de controle.',
'Anthropic opened a preview linking agents with physical equipment. The proposal connects software and laboratories while raising practical control questions.',
'''A Anthropic anunciou em 27 de agosto uma prévia de pesquisa do Model Hardware Standard, ou MHS. A proposta padroniza a comunicação de agentes com equipamentos programáveis, como instrumentos de laboratório. Acesso inicial foi dirigido a parceiros; isso não significa adoção universal ou disponibilidade final aberta.

Para devs, a ideia lembra um problema conhecido: cada equipamento fala de um jeito e exige integração própria. Uma interface comum pode tornar a coordenação mais compreensível. Só que, quando o software movimenta algo físico, um erro deixa de ser apenas uma linha incorreta na tela.

Nossa leitura editorial é que a qualidade de uma integração depende tanto das possibilidades quanto dos limites explícitos. O sistema precisa saber o que pode observar, o que pode mudar e como interromper uma operação. Histórico e supervisão passam a fazer parte do resultado, não de um detalhe posterior.

Não operamos equipamentos com MHS nesta reportagem. O anúncio merece atenção por aproximar IA, robótica e ferramentas científicas, mas não autoriza concluir que laboratórios autônomos já são uma solução pronta para qualquer pessoa. Vale acompanhar documentação e resultados de parceiros: interoperabilidade só ganha sentido quando funciona de forma repetível no ambiente onde será usada.''',
'''Anthropic announced a research preview of the Model Hardware Standard, or MHS, on August 27. The proposal standardizes communication between agents and programmable equipment, including laboratory instruments. Initial access targeted partners; that does not mean universal adoption or a final open release.

For developers, the idea resembles a familiar problem: each device communicates differently and requires its own integration. A common interface could make coordination easier to understand. But when software moves physical equipment, a mistake becomes more than an incorrect line on a screen.

Our editorial reading is that integration quality depends as much on explicit limits as on capabilities. A system needs to know what it may observe, what it may change and how to stop an operation. History and supervision become part of the result, not details added afterward.

We did not operate equipment through MHS for this report. The announcement deserves attention for connecting AI, robotics and scientific tools, but does not establish autonomous laboratories as a ready-made solution for everyone. Follow documentation and partner results: interoperability becomes meaningful when it works repeatedly in the environment where it will be used.''',
'https://www.anthropic.com/news/model-hardware-standard-research-preview','Anthropic — prévia MHS','2026-08-27',['Robotica','Dev','IA'],'Quando a IA controla hardware, o limite também precisa fazer parte da interface.','When AI controls hardware, limits need to be part of the interface too.','Envie para quem acompanha agentes e robótica.','Send this to someone following agents and robotics.','Nós de software ligados a instrumentos abstratos e botão de parada visível.')

save()
