# Manual da marca AnderZilla

Versão 1 — 10/09/2026. Direção aplicada ao hub Next.js e materiais futuros; o avatar Ghost original permanece intacto. Fonte de decisão: pedidos do proprietário e protótipo aprovado, não pesquisa de reconhecimento de marca.

## Ideia e personalidade

AnderZilla é um ponto de encontro pessoal para descobrir games, consoles, celulares, IA, gadgets e curiosidades. O visitante deve encontrar algo interessante, aprender, guardar e voltar. A marca é curiosa, bem-humorada e tecnicamente honesta. CodeMatrix continua sendo a atuação profissional separada.

Promessa editorial: “Tecnologia para explorar, jogar e se divertir.” / “Tech to explore, play, and enjoy.” Karaca! é a expressão de descoberta e o nome do universo de recompensas. A grafia permanece **Karaca!**, **Karaca Points** e **Store Points** em ambos os idiomas. KP abrevia pontos quando o contexto já estiver claro.

## Assinatura e avatar

Escrever AnderZilla em texto corrido. Na assinatura visual usar ANDER em branco suave e ZILLA em vermelho, sem espaço entre as partes, em Oxanium 800. Tracking entre -0.04em e -0.02em, sem distorcer as letras. A versão compacta usa o Ghost sozinho; não criar outro mascote ou monograma para substituir a identidade reconhecida.

Preservar o arquivo AnderZilla-Ghost.png: boné vermelho, caveira amarela e parede azul. Não recolorir, redesenhar, gerar variantes por IA, trocar rosto, remover elementos ou aplicar filtros sobre a imagem. Recortes de apresentação quadrados/circulares são permitidos por CSS, mantendo rosto e boné visíveis e arquivo original intacto. Alt: “Avatar Ghost da AnderZilla” / “AnderZilla Ghost avatar”.

Respiro mínimo da assinatura: metade da altura de uma letra em todos os lados; avatar separado do texto por 12–16px. Avatar mínimo recomendado 40px; wordmark mínimo recomendado 140px. Em aplicações monocromáticas usar assinatura inteira branca sobre escuro ou navy sobre claro, mantendo a imagem original colorida quando presente. Nunca colocar assinatura sobre detalhes que prejudiquem leitura. Não usar o nome civil completo como marca de marketing.

Arquivo original: C:/Users/ander/OneDrive/Imagens/AnderZilla-Ghost.png. SHA256: D250940D7F8D8BF44875B5B5071D6983BEB79D2D73AB6590580E5664AF6256B6. A cópia de aplicação deve conservar esse hash.

## Paleta e funções

| Token | Cor | Uso |
|---|---|---|
| background | #070B18 | Fundo principal, atmosfera noturna |
| surface | #10182B | Cards e painéis |
| surface-raised | #17233B | Áreas de interação e diálogos |
| cobalt | #315EFF | Luz ambiente, detalhes de descoberta; não texto pequeno sobre navy |
| text | #F4F7FF | Títulos e leitura principal |
| muted | #A9B6CE | Metadados e texto secundário sobre superfícies escuras |
| brand-red | #FF5967 | ZILLA e assinatura; erros precisam também de ícone/texto |
| neon-lime | #C2FF36 | Ação principal da home, progresso, descoberta |
| neon-pink | #FF58D4 | Desafios, live, área secundária |
| focus | #C2FF36 | Contorno de foco de teclado |
| border | #334563 | Divisórias decorativas; controles exigem contraste validado |

Amarelo continua no Ghost; não é cor principal de botões. Botões lime/pink usam texto background escuro, nunca branco. Cor de categoria pode orientar, mas sempre acompanhada do nome/ícone. Aproximadamente 80% da tela deve permanecer em tons escuros, 15% em conteúdo e 5% em acentos; é uma orientação de composição, não uma métrica de produto.

## Tipografia

**Oxanium**: marca, hero, títulos de seção, KP e números de destaque, pesos 600–800. Geometria com referência a interfaces de jogos sem transformar toda a leitura em painel futurista. **Space Grotesk**: parágrafos, navegação, botões, rótulos e metadados, pesos 400–700. Fallback: Arial, sans-serif. Código de artigos usa ui-monospace, Consolas, monospace; não exige uma terceira fonte externa.

Escala recomendada: hero clamp(2.5rem, 5vw, 4.5rem), seção 28–36px, card 20–24px, texto 16–18px com line-height 1.55–1.7, metadados 13–14px. Parágrafos até 65–75 caracteres de largura. Não usar caixa alta em texto longo. Validar acentos PT, cedilha, números e pontuação EN. Na aplicação usar next/font ou arquivos locais com licença preservada; a configuração escolhida deve funcionar no build e não depender do navegador buscar fontes de terceiros.

Fontes primárias: [Oxanium no Google Fonts](https://fonts.google.com/specimen/Oxanium), [repositório Google Fonts](https://github.com/google/fonts/tree/main/ofl/oxanium), [Space Grotesk e licença OFL](https://github.com/floriankarsten/space-grotesk). Verificadas em 10/09/2026. Incluir licença ao distribuir arquivos de fonte; não presumir que isso concede direitos sobre marcas de terceiros.

## Componentes e estilo

Cards com raio 18–24px, botões 12–16px e chips arredondados. Espaçamento em múltiplos de 4px, base 8px; gutters 20px mobile e 32px desktop. Conteúdo com largura máxima aproximada de 1280px. Um CTA principal por bloco, com no máximo uma alternativa. Cards de notícia mostram categoria, data, contexto/fonte e ação; imagem não substitui título.

Fundo pode usar gradiente navy/cobalt, luz neon suave e textura discreta. Brilho pertence a acentos e foco, nunca a todo texto. Evitar bordas luminosas em cada elemento, glitch contínuo, scanlines sobre leitura e excesso de fontes gamer. Hero pode usar ilustração original identificada como arte; imagens de produtos devem representar o produto e ter fonte/direitos apropriados.

## Ícones e movimento

Adotar uma única família de SVG de traço, grade 24px e traço próximo a 2px. Opção recomendada: Lucide, mantendo a licença correspondente se instalado. Ícones semânticos: gamepad para games, CPU para IA, smartphone para celulares, headphones para gadgets, bookmark para mochila, calendar para agenda, radio para live e gift para Store Points. Não depender de emoji para estrutura principal: aparência varia por sistema. Logos de plataformas são ativos distintos, não endossos.

Ícones decorativos têm aria-hidden; ações apenas com ícone recebem nome acessível e tooltip não substitui esse nome. Não usar apenas cor para estados. Hover/foco: transição de 120–180ms e deslocamento máximo 2px. Conquistas: feedback breve e discreto, sem tela bloqueante ou confete constante. Respeitar prefers-reduced-motion, desabilitando deslocamento/animação não essencial. Nunca piscar repetidamente.

## Acessibilidade e estados

Meta: WCAG 2.2 AA. Validar contraste real em cada combinação, foco visível, navegação por teclado, 200% zoom, 320px de largura e mensagens por leitores de tela. Cor decorativa não comprova contraste de controle. Alvos de interação preferencialmente 44px. Formulários têm rótulos persistentes, erros específicos e ação de recuperação. Botões desabilitados explicam o motivo em texto próximo. Não comunicar sucesso sem operação confirmada.

Prever loading, vazio, erro, offline, conteúdo desatualizado, acesso negado e ação concluída. Agenda vazia é honesta e útil; não inventar eventos. Live só recebe indicador confirmado quando há fonte atual de status. Embeds carregam por ação do visitante e preservam link externo. Store sem estoque confirmado mostra disponibilidade real e não cria urgência artificial.

## Voz PT/EN e conteúdo

PT: direto, brasileiro, curioso. Exemplos: “Karaca! Olha o que chegou no radar”, “Guarda na mochila”, “Bora testar seu conhecimento?”. EN adapta sentido: “Fresh on the radar”, “Save to your backpack”, “Ready for a quick challenge?”. Evitar tradução literal de gírias. Karaca! é expressão da marca, não título obrigatório em cada card. Humor não diminui precisão; dizer o que foi testado, o que é anúncio e o que é hipótese.

Mostrar fontes e datas em notícias; separar fato, rumor, opinião e publicidade. Não fingir testes próprios, testemunhos, usuários simultâneos, prêmios ou resultados. Posts de nostalgia/arquivo recebem data e contexto. Notícias atraem por utilidade e surpresa, não por título enganoso.

## Comércio e Karaca Points

Anúncios e patrocínios identificados antes do clique. Recomendações de afiliados têm disclosure junto ao link; termos comerciais não mudam a avaliação. Produtos próprios mostram responsável, entrega, preço atual e condições. Catálogo vazio não exibe marcas como parceiros. Slot demonstrativo fica restrito ao preview; produção usa campanha confirmada ou conteúdo próprio.

KP é conquistado por atividades elegíveis, não vendido. Saldo demonstrativo deve estar claramente identificado e separado de saldo real. Mostrar extrato, regras, prazo e disponibilidade do resgate. Nunca premiar cliques em anúncios ou criar obrigação de compra para participar. Nenhum item aparece resgatável sem estoque, elegibilidade e operação aprovados. Estratégia econômica e antifraude fica interna; o visitante vê regras claras e benefícios reais, sem promessa de enriquecimento.

## Aplicação e manutenção

Componentes compartilhados devem consumir tokens de cor/tipografia, sem valores neon divergentes por página. Conferir header, hero, cards, pontuação, agenda, diálogos e footer em PT/EN e mobile/desktop. Manter esta direção alinhada ao código; registrar desvios por necessidade de legibilidade e não alterar o Ghost. A marca pode evoluir em assinatura, layout e iconografia sem perder o anfitrião reconhecido.
