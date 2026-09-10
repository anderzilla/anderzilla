# Playtest 03 — neon, monetização e lives

## Ajustes aprovados

O proprietário confirmou a direção gamer do Playtest 02 e solicitou refinamentos: trocar o amarelo de ZILLA por vermelho, usar “caraca!” no português, verde-limão neon nas ações principais e pink neon em áreas secundárias. A imagem Ghost permanece original. Tokens atuais: vermelho #ff5967, verde-limão #c2ff36 e pink #ff58d4. Home usa verde; desafio e chamada de live usam pink.

Protótipo local: http://127.0.0.1:4175/?lang=pt&v=3#home. Sem publicação Azure nesta revisão. apps/web e apps/forgekit não foram alterados.

## Publicidade e afiliados

A home tem espaço publicitário após o conteúdo, identificado como demonstrativo, com acesso a formatos comerciais. Nenhum anúncio foi vendido, campanha ativada ou script de ad network instalado. O placeholder pertence ao playtest; em produção, espaço não contratado deve ser ocultado ou usado para campanha própria claramente identificada, sem simular anunciante.

“Loot & upgrades” prepara a área de afiliação. Sem links ativos confirmados, mostra fontes oficiais de produtos já presentes na curadoria e informa que não geram comissão. Não inventa desconto, preço, aprovação ou selo de parceiro. A configuração affiliates está vazia. Apenas registros com status active e URL HTTPS entram no bloco remunerado, com identificação e rel sponsored noopener noreferrer. Aprovação contratual e URL precisam ser verificadas antes de preencher o registro; um status no código não comprova aprovação externa.

## Sala de live

A rota #live reúne Twitch, YouTube e Kick com links diretos dos canais confirmados. Twitch carrega um iframe somente após clique, com parent correspondente ao hostname atual e autoplay=false. O player foi inspecionado no Chrome: carregou o canal AnderZillaCWB e mostrou offline. Isso é observação da plataforma naquele momento, não monitoramento contínuo.

Twitch exige janela de pelo menos 400×300. Em telas estreitas, o protótipo oferece acesso direto ou orientação para uma janela maior em vez de encolher o player abaixo do mínimo. Trocar plataforma remove o iframe anterior. YouTube suporta incorporação quando houver um ID de vídeo/transmissão confirmado; ainda não foi informado. Kick usa link direto nesta versão; incorporação não implementada. A reprodução pode depender das condições da plataforma e do navegador.

O badge de transmissão atual não é inferido da abertura do canal. A configuração broadcast aceita plataforma, título, checkedAt e expiresAt; só exibe AO VIVO com confirmação válida e não expirada ao renderizar. Atualmente é null, portanto o status aparece não confirmado. Atualização automática e revalidação contínua dependem de integração de status ainda não implementada. Nenhuma credencial deve ficar nos arquivos públicos.

O iframe exibiu também uma agenda cadastrada na própria Twitch. Como o proprietário informou que ainda não há próxima live marcada, essa agenda externa não foi importada nem tratada como compromisso vigente do AnderZilla. O conteúdo do player é controlado pela plataforma.

## Agenda

O proprietário solicitou um espaço próprio para eventos, sem datas atuais. A rota #agenda mostra um estado vazio adequado e está ligada à home e à sala de live. Eventos confirmados poderão informar tema PT/EN, plataforma e início ISO com fuso; aparecem em ordem cronológica e são exibidos no horário de Brasília. A primeira data futura também abastece a faixa de próxima live. Eventos passados não ficam anunciados como próximos.

Configuração pública em prototypes/editorial/hub-settings.js: live.events, live.next, live.broadcast, live.youtubeVideoId e affiliates. Código de apresentação e players em features.js; identidade e layout em hub.css e hub.js. Isso é cadastro por arquivo, não painel administrativo ou sincronização automática com calendários.

## Verificação

Verificados PT/EN e larguras 320, 390, 768 e 1440px nas páginas Home, Live, Agenda e Parcerias, sem overflow horizontal ou duplicação de h1. JavaScript passou em node --check. Confirmados os valores CSS vermelho e verde-limão e a chamada “caraca!”.

Testados carregamento sob demanda do iframe Twitch, canal/parent/autoplay, remoção ao mudar plataforma e fallback em largura inferior a 400px. O player real carregou; emitiu uma exceção interna de getLayoutMap relacionada à política do iframe, sem impedir a tela offline observada. Não apresentar isso como ausência absoluta de mensagens de terceiro ou como reprodução de uma live validada.

Fixtures temporárias, sem gravação nos arquivos públicos, verificaram rejeição de status ao vivo expirado, aceitação de confirmação vigente, exibição de evento futuro e separação entre afiliado candidato e ativo. Não foram criados eventos ou parceiros fictícios na configuração entregue.

Fontes oficiais consultadas em 10/09/2026: [Twitch — incorporação de vídeo, parent e dimensões](https://dev.twitch.tv/docs/embed/video-and-clips/); [YouTube — parâmetros do player](https://developers.google.com/youtube/player_parameters). Nenhum pacote pago, API ou serviço de nuvem adicional foi contratado.
