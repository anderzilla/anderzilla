# Revisão cruzada editorial — 10/09/2026

Revisor: agente editorial de games/consoles/gadgets. Arquivo revisado: `ia-celulares-curiosidades.json`. Leitura dos 30 corpos PT, metadados e amostras EN; conferência externa por amostragem das afirmações centrais. Não é teste de produtos nem certificação de cada especificação.

## Resultado

O lote tem 10 IA, 10 celulares e 10 curiosidades. Validação real pelo domínio CMS `validate('content', data, approved=True)`: 30/30 válidos. Slugs únicos: 30 PT e 30 EN. Resumos entre 136 e 160 caracteres. Após ajustes do autor, títulos visuais curtos e hashtags EN sem os termos PT inicialmente identificados.

Os textos distinguem especificação, anúncio, disponibilidade e teste próprio. Os critérios de uso são originais, em linguagem acessível a devs e gamers, sem rankings inventados ou preços locais inferidos. A seção curiosidades inclui novidades de desenvolvimento, maker e robótica, coerentes com o público solicitado.

## Correções encaminhadas e verificadas no arquivo

- **iPhone 18 Pro:** a fonte Apple inclui explicitamente Brasil no calendário anunciado de pré-venda (12/09) e disponibilidade (18/09). O texto foi corrigido para informar isso sem afirmar estoque nas lojas. [Anúncio Apple](https://www.apple.com/newsroom/2026/09/apple-debuts-iphone-18-pro-and-iphone-18-pro-max/).
- **Galaxy S26:** evento de 25/02 separado do comunicado publicado em 26/02. Corpo corrigido. [Samsung Business: evento](https://insights.samsung.com/2026/02/25/samsung-unpacked-february-2026-full-replay-and-highlights/).
- **Xiaomi 17 Ultra:** adicionada a fonte do anúncio global em 28/02, separada do FAQ e do lançamento chinês. [Xiaomi: anúncio global](https://www.mi.com/global/discover/article?id=5972).
- **Contexto temporal:** matérias de hardware anteriores passaram a análise/explicador quando apropriado, evitando confundir data editorial de setembro com lançamento novo.
- **Distribuição:** títulos visuais extensos e hashtags EN em português foram corrigidos pelo autor.

## Pontos finais enviados ao autor

1. Em S26, `sources[0].publishedAt` ainda precisava usar 26/02, enquanto `eventDate` permanece 25/02. A distinção já estava correta no corpo.
2. FAQ/ficha sem data de publicação visível não deve receber a data de lançamento como `publishedAt`. Omitir a data e registrar consulta em `note`; fontes datadas complementares sustentam o evento. Aplicar também a páginas de cronologia, como Unitree.
3. A matéria TypeScript 7 ganha utilidade com a limitação concreta de que a versão 7.0 não fornece API do compilador, com coexistência da 6.0 documentada. Não transformar em tutorial de migração sem testes. [Microsoft: TypeScript 7](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).
4. Resolver `{urlPT}`/`{urlEN}` antes de exportar legendas para uso real. Não publicar em redes sem ação específica autorizada.

## Amostra de evidência externa

- OpenAI Astra: anúncio e distribuição gradual sustentados pela página oficial; benchmarks tratados como avaliações do fornecedor.
- Anthropic Fable/Mythos 5.1: base compartilhada e diferença de acesso/proteções confirmadas na fonte.
- Gemini 3.8 Flash: anúncio datado de 02/09 confirmado.
- Qwen Flash-Next: página dinâmica não retornou corpo no leitor; busca oficial e README do repositório Qwen sustentam 6B ativos e lançamento26/08. É importante registrar essa limitação de leitura. [README Qwen](https://github.com/QwenLM/Qwen3.8-Flash-Next/blob/main/README.md).
- Mistral Agentic Search e Shieldstral: páginas oficiais abertas; textos não reproduzem promessas como resultado próprio.
- GitHub npm: configurações independentes com autorização por correspondência a qualquer uma, não por todas. [Changelog](https://github.blog/changelog/2026-09-03-multiple-trusted-publishing-configurations-for-npm/).
- GitHub secrets: prévia pública com requisito Secret Protection/Advanced Security confirmado. [Changelog](https://github.blog/changelog/2026-09-09-block-pull-requests-with-exposed-secrets-from-merging/).
- Godot: relatório24/08, correção4.7.2 e cenário de mouse com alta frequência confirmados. [Relatório](https://godotengine.org/article/fixing-high-polling-rate-mice-on-windows/).
- CodeQL: versão2.26.4, Go1.27 e reposicionamento de alertas Rust confirmados. [Changelog](https://github.blog/changelog/2026-09-03-codeql-2-26-4-improves-github-actions-security-detections/).
- Raspberry Pi: tutorial com dois controles e MCP3008 confirmado; matéria não reproduz ligações sem contexto. [Tutorial](https://www.raspberrypi.com/news/build-an-internet-radio/).
- Fontes oficiais de Unitree, HONOR Robot Phone e MHS abertas; textos mantêm a diferença entre demonstração, teste interno e produto comercial.

## Limite visual

Atualização após retorno do autor: S26 sources data corrigida; FAQs/fichas sem data foram ajustadas; TypeScript agora é explicador com nota sobre a API e coexistência. Os pontos editoriais acima foram atendidos, conforme confirmação do agente autor.

Revisão de conteúdo e direcionamento de cards. Não inspecionei os 60 renders finais nem o fluxo autenticado do CMS. Recorte, contraste, alt text, licença e leitura em celular ainda precisam de QA do coordenador após a geração das imagens. Não alterei o arquivo do outro agente.

## Revisão visual por amostragem

Inspeção direta dos WebP: GTA VI cover e Instagram, PlayStation Portal cover e Logitech MX Keypad Instagram. Os quatro têm texto legível, contraste adequado e nenhuma linha cortada. GTA e Portal têm motivos compatíveis. O MX Keypad recebeu desenho de headset, incompatível com o assunto: solicitado ao coordenador trocar por teclas/macropad usando o motivo individual do manifesto antes da entrega. A amostra não representa inspeção integral das 120 imagens.

## Fechamento de fontes do lote games

TGS passou a usar como fonte principal o comunicado inglês oficial acessível. Zero Company passou a apontar ao índice oficial do PlayStation Blog, que mostra resultado e data, mantendo o link individual e a limitação de reabertura registrados nas fontes. O manifesto final voltou a passar na validação CMS: 30 registros, 10 por categoria.

## Revisão integral EN do lote IA/celulares/curiosidades

Lidos todos os 30 bodyEN e todos os 180 campos sociais (Instagram, Facebook e WhatsApp em PT/EN), com comparação dos 30 leads PT. Não foram identificadas traduções contraditórias, claims novos nas legendas ou resultados de testes inventados. Datas, mercados, condições de acesso e distinção anúncio/teste permanecem coerentes entre os idiomas. A busca automatizada encontrou somente os placeholders previstos {urlPT} e {urlEN}, sem caracteres Unicode de substituição.

Correções pontuais encaminhadas ao coordenador para atualização com histórico no CMS, pois o manifesto está congelado: (1) typescript7-go: em bodyEN, trocar “Version 7.0 has no API” por “Version 7.0 does not expose a compiler API”; no correspondente bodyPT, “A versão 7.0 não expõe API” por “A versão 7.0 não expõe uma API do compilador”, tornando explícito o escopo técnico. (2) oppo-findx9ultra: no bodyEN, trocar rótulo de fonte “OPPO Japão” por “OPPO Japan”. Nenhum JSON foi alterado nesta revisão. A revisão integral de língua e consistência não equivale a nova consulta de todas as fontes; a checagem factual anterior permanece registrada nas seções acima.
