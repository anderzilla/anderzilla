# Área do jogador autenticado — especificação de produto

Data: 05/11/2026. Estado: **planejamento para implementação; não representa funcionalidades novas publicadas**. Pedido do proprietário neste chat substitui o uso de mochila, interesses e exploração por visitantes. Documentos complementares: [fluxos e mensagens](MEMBER-AREA-UX.md), [acesso, dados e contratos](MEMBER-AREA-SECURITY-API.md), [entrega e aceite](../operations/MEMBER-AREA-DELIVERY.md). Identidade visual: [manual](BRAND-MANUAL.md). Identidade e conta: [decisões](ACCOUNTS-AND-ACCESS-PHASES.md). Pontos: [direção KP](KARACA-POINTS.md).

## 1. Decisões vigentes e limites

- **Mochila, interesses, exploração, KP, carteira e missões oficiais exigem sessão válida, e-mail confirmado e cadastro AnderZilla completo, adulto18+ e ativo.** Sessão Clerk sozinha não basta.
- Leitura de notícias, busca e categorias gerais, páginas institucionais, produtos e links públicos de canais continuam públicos conforme classificação editorial. Ler uma notícia pública não exige cadastro e não registra exploração pessoal de visitante.
- Após login comum, abrir **Painel do jogador**, com blocos úteis. Dados cadastrais ficam em **Perfil**, acessado pelo menu. Onboarding incompleto continua precedendo painel e ações de membro.
- Clicar no nome/avatar abre menu; não navega imediatamente para Perfil. O link **Seu Radar** abre notícias públicas selecionadas pelas preferências privadas do jogador, nunca a tela cadastral. Mostrar saldo KP no topo somente para membro ativo e com carteira habilitada/carregada.
- Visitante não ganha saldo/progresso, não cria mochila/interesses e não inicia missão. CTA discreto explica o benefício do login. Preferência de idioma/acessibilidade e consentimento de cookies podem continuar locais; não são interesses de conteúdo nem dados de membro.
- Quiz/passaporte que alimenta Exploração ou Missões também exige membro, sem quizDone/claims/XP de visitante misturados à conta. Material educativo público pode continuar como artigo; não usar esse caminho para criar tentativa/progresso anônimo ou distribuir gabarito de missão oficial.
- KP/carteira/missões são escopo deste **plano**, mas continuam desligados até integração, regras e aceite. Não ativar recompensas por trocar apenas uma flag. Nenhum preço, estoque, parceiro, benefício resgatável ou compra é criado por este documento.
- Assinatura do site, acesso temporário comprado e canais de live são direitos futuros independentes. Cadastro, nível, XP ou saldo KP não os concedem. Menores seguem bloqueados.

## 2. Arquitetura de navegação proposta

Manter /pt/ e /en/. Slugs de seção de conta são estáveis nos dois idiomas; rótulos são traduzidos. Páginas privadas exportadas estaticamente contêm somente estrutura genérica. Acesso aos dados é sempre pela API autorizada.

| Destino | Rota proposta em cada idioma | Conteúdo e ação principal |
|---|---|---|
| Painel do jogador / Player dashboard | /{lang}/conta/ | Visão geral; Retomar meu Radar |
| Seu Radar / Your radar | /{lang}/conta/radar/ | Lista de notícias conforme interesses; Ajustar interesses |
| Perfil / Profile | /{lang}/conta/perfil/ | Nome, avatar, idioma, consentimentos, segurança, exportação e exclusão |
| Mochila / Backpack | /{lang}/conta/mochila/ | Salvos; Abrir descoberta |
| Interesses / Interests | /{lang}/conta/interesses/ | Seleção de temas; Salvar interesses |
| Exploração / Exploration | /{lang}/conta/exploracao/ | Descobertas abertas, territórios explorados e retomada; Continuar explorando |
| Karaca Points | /{lang}/conta/kp/ | Como conquistar/usar KP, regras vigentes e resumo confirmado; Ver missões |
| Carteira / Wallet | /{lang}/conta/carteira/ | Disponível, reservado, extrato e detalhes de lançamento; Consultar extrato |
| Missões oficiais / Official missions | /{lang}/conta/missoes/ | Disponíveis, em andamento, em conferência e concluídas; Escolher missão |
| Missão individual | /{lang}/conta/missoes/{id}/ | Detalhes, tentativa, regras e confirmação; não exportar progresso pessoal |

Compatibilidade: #profile e /account apontam ao Perfil, #saved à Mochila, #points à página KP e #missions às missões; inventariar outras aliases antes de migrar. Em visitante, abrir gate e guardar apenas destino interno permitido; nunca renderizar o estado local antigo. Links públicos de categorias continuam listando notícias gerais, sem gravar interesses. Novo slug de missão pode usar página genérica + ID validado no cliente/API para manter export estático sem gerar páginas pessoais.

### Cabeçalho

- Público: logo, navegação editorial, busca, Entrar. Não mostrar nome, avatar de conta, saldo ou contadores pessoais. O Ghost da marca não se confunde com avatar do jogador.
- Autenticado: link Seu Radar, chip **{saldo} KP**, botão de menu com avatar e nome. Chip leva à Carteira e tem nome acessível “Carteira: {saldo} Karaca Points disponíveis”. Não apresentar reservado como disponível.
- Menu, nesta ordem: Painel do jogador; Seu Radar; Mochila; Interesses; Exploração; separador; Karaca Points; Carteira; Missões oficiais; separador; Perfil; Sair. Rota atual indicada. Perfil contém “Segurança e acesso”.
- KP desligado: link neutro “Karaca Points”, com explicação privada “Ainda não está liberado”, sem prazo prometido ou CTA de ganho/resgate. Indisponibilidade temporária: “KP —”; tentativa de atualizar, sem substituir por0. Zero é exibido somente após resposta válida.
- Mobile: manter logo, chip compacto e avatar; menu em painel acessível sem overflow horizontal; links editoriais recolhidos. Alvos44px. Nome longo truncado visualmente, nome acessível preservado. Menu não contém e-mail/CPF/data de nascimento.
- Suspensão, exclusão ou expiração removem todos os elementos pessoais. O estado “verificando sessão” mostra estrutura neutra, sem flash dos dados anteriores.

## 3. Dashboard em blocos

Não recriar a página de dados cadastrais. Mostrar contexto e próximos passos, sem métricas inventadas. No desktop usar grade12 colunas; no mobile uma coluna, mesma ordem de leitura. Não usar carrossel para informação essencial.

```text
Cabeçalho: AnderZilla | Seu Radar | [KP] | [Avatar Nome ▾]
Boas-vindas pelo nome + “Bora para a próxima descoberta?”
[ Seu Radar: até3 notícias ] [ KP disponível + link Carteira ]
[ Mochila: até3 salvos     ] [ Próxima missão elegível       ]
[ Exploração: retomada e territórios ] [ Seus interesses     ]
Links discretos: Perfil · Regras KP · Ajuda
```

| Bloco | Dados necessários | Vazio / indisponível | Ação |
|---|---|---|---|
| Boas-vindas | Nome de exibição | Saudação genérica durante verificação | Sem edição de cadastro aqui |
| Seu Radar | Interesses + notícias públicas elegíveis | Sem interesses: escolher temas; sem notícias: ampliar temas ou ver Radar geral | Abrir Seu Radar |
| KP | Saldo confirmado e estado do programa | Desligado: apresentação honesta; falha: não carregar valor antigo | Abrir Carteira |
| Mochila | Total +3 itens acessíveis | “Sua mochila está pronta para a primeira descoberta.” | Ver mochila / Abrir Radar |
| Missões | Uma próxima missão válida ou tentativa retomável | Sem missão: “Nenhuma missão nova por aqui. Seu Radar continua aberto.” | Continuar / Ver missões |
| Exploração | Últimas3 descobertas abertas + categorias únicas | Primeiro acesso sem pontuação fictícia | Continuar explorando |
| Interesses | Temas salvos | Sem seleção, sem interesses inferidos | Ajustar interesses |

Recomendação não deve depender da entrega de todos os blocos. Falha em carteira não bloqueia notícias. Sessão inválida/revogada ou conta suspensa/excluída limpa todo o estado pessoal; falta de direito a um conteúdo ou inelegibilidade de missão bloqueia somente a seção/ação correspondente. Não manter cards de outra sessão. Evitar múltiplas requisições iguais ao /me e à carteira por card; resumo agregado com estados por seção e leitura detalhada sob demanda.

## 4. Mochila — ciclo completo

1. Em artigo público, visitante vê “Guarde para depois” como benefício; clique abre entrada, sem salvar localmente. Após confirmação da conta, retomar intenção por ID público validado e pedir “Guardar esta descoberta?”. Não executar escrita silenciosa após login.
2. Membro salva item autorizado; botão fica pendente; servidor confirma e ícone muda. Clique repetido não cria duplicata. Pode desfazer remoção por janela curta, realizando novo comando autorizado.
3. Mochila tem busca, filtro por categoria e ordem “Mais recentes primeiro”; paginação por cursor. Pesquisa privada não vai a analytics/URL pública. Abertura de item registra exploração somente após autorização.
4. Item removido do catálogo/sem direito atual não revela título, imagem ou descrição restritos; mostrar entrada genérica “Esta descoberta não está disponível agora” e permitir removê-la. Conteúdo antes público não se torna disponível por estar salvo.
5. Salvar/remover falha: reverter estado otimista; conservar operação em memória apenas enquanto mesma sessão estiver válida. Em dúvida de confirmação, consultar estado e repetir com mesma chave, não criar outra ação.
6. Não importar automaticamente salvos do visitante legado. Após migração de política, limpar armazenamento legado e explicar uma única vez que recursos pessoais agora ficam na conta. Caso futura importação seja aprovada, exigirá consentimento, validação de IDs e nenhuma migração de KP.

## 5. Interesses e Seu Radar

- Escolher temas existentes por toggle com texto/ícone; permitir um ou mais, selecionar/desmarcar e cancelar sem gravar. Resumo “{n} temas selecionados”. Sem seleção é estado válido, não erro de cadastro.
- Salvar explicitamente; botão ativo apenas com alterações. Conflito entre abas/dispositivos pede revisar seleção, preservando a edição local da sessão válida. Não sobrescrever silenciosamente a preferência nova.
- Após salvar, atualizar painel e Radar; anunciar “Seu Radar ganhou novos rumos.”. Trocar idioma aguarda confirmação da gravação antes de navegar; em falha, deixar escolher continuar sem salvar ou tentar de novo.
- Seu Radar usa somente interesses declarados, não CPF, data de nascimento ou histórico oculto. Sem seleção: oferecer configuração e link ao Radar geral, sem fingir personalização.
- Ordenação inicial recomendada: notícias publicadas mais recentes que tenham ao menos um dos temas escolhidos; desempate por ID. Não chamar isso de IA/recomendação individual avançada. Busca e filtros temporários não alteram interesses persistentes.
- Sem correspondência: “Nenhuma novidade nesses temas por enquanto. Bora abrir o mapa?”; ações Ajustar interesses e Ver Radar geral. Não misturar conteúdo fora dos temas sem identificação explícita.
- Conteúdo comercial continua com mercado e disclosure; preferência não concede acesso pago. A lista personalizada é privada, mas a notícia pública mantém URL pública compartilhável sem identificadores da conta.

## 6. Exploração

- “Explorar” na navegação pública continua sendo navegar no acervo. **Minha Exploração** é o registro privado do membro, não uma cópia de navegação anônima.
- Registrar evento “descoberta aberta” autenticado, autorizado e deduplicado por conta+descoberta; guardar primeira/última abertura e contagem limitada quando necessária. Não afirmar “lido”, “concluído” ou “aprendido” por abrir página.
- Ao voltar: listar descobertas recentes, categoria e data própria; retomar artigo e guardar na mochila. Não inventar percentual de leitura nem tempo de vídeo sem telemetria e finalidade aprovadas.
- “Territórios explorados” conta categorias de eventos confirmados e acessíveis. Sem ranking público, streak punitiva, XP ou recompensa automática. Categorias não se tornam interesses sem escolha explícita.
- Permitir remover um registro ou limpar histórico com confirmação e resultado confirmado. Limpar exploração não apaga interesses/mochila, não revoga KP já concedido e não apaga auditoria mínima de missão. Explicar essa diferença antes da confirmação.
- A limpeza avança a geração do histórico no servidor. Eventos antigos em trânsito não podem recriar registros apagados; somente aberturas iniciadas depois da limpeza usam a geração nova. O mesmo vale para remoção de item e evento antigo que tente reinseri-lo.
- Sem registro: convite ao Seu Radar. Histórico desabilitado pelo usuário, se oferecido: não registrar novos eventos e explicar ausência de progresso; missão não pode depender secretamente de histórico desativado.

## 7. KP, carteira e missões — papéis distintos

- **Karaca Points** explica programa, regras, como conquistar e uso permitido. **Carteira** é o extrato e saldo autoritativo. **Missões** é a ação elegível que pode conceder KP. Um contador de exploração não é um quarto saldo.
- Piloto recomendado: missões educativas determinísticas e configuração voluntária de interesses. Abrir artigo, login diário, clicar anúncio, comprar produto ou repetir quiz não concedem KP automaticamente.
- KP não são comprados, não são dinheiro e não concedem assinatura de conteúdo. Não definir equivalência monetária, expiração nova, valor de missão ou estoque por este plano. Tabela de valores/regras deve ser aprovada e versionada antes de ativar, usando cobertura/benefícios reais já exigidos na estratégia KP.
- Primeira missão de interesses pode reconhecer seleção salva; missão de conhecimento usa perguntas/tentativa verificadas no servidor. Recompensa por conta/ocorrência definida na regra, não “uma vez por reload” nem simplesmente por versão técnica nova.
- Antes de iniciar: título, objetivo, passos, KP reais configurados, elegibilidade, prazo/fuso e limite de tentativas. Se recompensa/regras não estão aprovadas, missão fica draft e não aparece com valor hipotético.
- Fluxo: disponível → tentativa ativa → respostas enviadas → conferência → elegível pendente de confirmação → crédito confirmado. Alternativas: resposta incorreta com orientação; expirada; pausada; já creditada; revisão manual quando houver regra explícita. Cada estado oferece próxima ação.
- “Confirmar KP” só aparece quando servidor aprovou a evidência; fecha com crédito atômico/idempotente. Se optarmos por crédito automático numa missão futura, a versão da regra deve eliminar a confirmação redundante. Nunca executar os dois modelos para a mesma ocorrência.
- Pendência elegível reserva cobertura da campanha até o prazo de confirmação, sem somar saldo disponível. Missão sem cobertura não inicia nova promessa de crédito. Pausa de novas participações preserva confirmação de pendências válidas já cobertas. Se manutenção impedir confirmar, recuperar o status e aplicar regra de extensão/revisão publicada, nunca anunciar perda ou crédito sem consulta.
- Se janela de confirmação expirar sem crédito, liberar cobertura uma vez e informar prazo encerrado; oferecer nova tentativa somente se a regra permitir, senão consulta de status/atendimento. Não reutilizar token expirado, criar crédito duplicado ou desfazer crédito que já tinha sido confirmado.
- Resultado: mostrar KP concedidos + saldo atualizado + Ver carteira, sem tempestade de modais. Não creditar, prometer ou animar saldo antes da confirmação. Resposta perdida permite consultar status da mesma operação.
- Carteira mostra disponível, reservado e extrato paginado com motivo legível, data/fuso do usuário, identificador de suporte e status. Pendências de missão ficam em seção “Em conferência”, separadas do saldo e não utilizáveis. Sem saldo carregado: “Consultando seus KP…”; erro não significa0. KP reservados requerem motivo real, nunca placeholder de resgate.
- Resgate fica como extensão condicionada a catálogo/estoque/operação aprovados: detalhes/condições → reserva atômica pontos+estoque → acompanhamento → entrega confirmada ou devolução exatamente uma vez. Sem oferta real, não exibir vitrine falsa nem botão resgatar; manter regras de uso honestas. Pagamentos/lives ficam fora desta entrega.

## 8. Aplicação do manual visual

- Preservar Ghost original sem recolorir/redesenhar. ANDER branco, ZILLA vermelho; fundos #070B18, superfícies #10182B/#17233B, texto #F4F7FF e secundário #A9B6CE.
- Lime #C2FF36 para ação principal/foco/progresso; pink #FF58D4 para missão e acento secundário; vermelho #FF5967 em erro acompanhado de texto/ícone. Nada de KP por cor somente. Botões neon têm texto escuro.
- Oxanium em títulos e números KP; Space Grotesk na navegação e leitura. Cards18–24px, botões12–16px, escala8px, gutters20px mobile/32px desktop, largura máxima1280px.
- Um CTA principal por bloco, no máximo uma alternativa. Sem neon em todas as bordas, animação constante, confete invasivo ou vocabulário gamer que esconda uma operação financeira/de exclusão.
- Reflow320px e zoom200%, foco visível, alvo44px, contraste validado, teclado e leitor de tela. Animação120–180ms opcional e respeitando redução de movimento. KP anunciado por leitor somente quando muda por ação confirmada, não a cada render.

## 9. Separação entre decisão e sugestão

Confirmados pelo proprietário: recursos pessoais autenticados, dashboard em blocos, Perfil separado, menu no nome, Seu Radar personalizado, KP no topo e linguagem gamer humanizada com acesso protegido. Propostas deste plano: slugs, ordem dos blocos/menu, ordenação do Radar, confirmação de KP em duas etapas, política de conflito e etapas de rollout. Implementar após revisão técnica sem assumir aprovação de estoque/economia/pagamento. Critérios executáveis no documento de entrega.
