# Cadastro editorial em lote

O CMS é a fonte dos registros e das revisões. `services/cms/import_content.py` é um importador legado e não deve ser usado para este fluxo.

No painel, abra **Conteúdo → Importar lote editorial com histórico**. Carregue um JSON ou cole o manifesto. A importação usa a sessão Microsoft existente, envia as capas para a biblioteca e cria rascunhos pelas rotas da API. Revise os registros e aprove cada matéria. O kit social copia texto, URL e hashtags; não publica nas redes.

Formato do manifesto:

```json
{"items":[{"key":"identificador-estavel","data":{"slugPT":"slug-pt","slugEN":"slug-en","sourceUrl":"https://fonte.oficial/noticia"},"cover":{"filename":"identificador-estavel.webp","contentBase64":"BASE64_DO_ARQUIVO","altPT":"Descrição objetiva","altEN":"Objective description","credit":"Autor da imagem","license":"Autorização ou licença verificada"}}]}
```

O exemplo demonstra a estrutura; `data` precisa conter os campos editoriais obrigatórios reais antes da aprovação. Use nomes de arquivo únicos por capa. Campos disponíveis: título, resumo/introduction, corpo Markdown, slugs e SEO PT/EN, categoria, fonte principal, autoria, capa/galeria, tags de taxonomia, `sources`, `verifiedAt`, `eventDate`, `editorialType`, `hashtagsPT/EN` e `socialInstagramPT/EN`, `socialFacebookPT/EN`, `socialWhatsappPT/EN`. O campo opcional `instagramUrl` guarda o HTTPS de um post ou reel em instagram.com (caminhos `/p/`, `/reel/`, `/reels/` ou `/tv/`). Quando a notícia publicada traz esse link, o carrossel da home pode priorizá-la e a página da notícia mostra “Veja no Instagram”. `sources` é uma string JSON com 1–20 objetos `{name,url,publishedAt?,note?}`; no dataset público vira uma lista. Fontes usam HTTPS público. Datas aceitam ISO `YYYY-MM-DD` ou timestamp com fuso. Data do fato não é data de publicação do artigo.

Importação preserva registros existentes por slug e fonte. Uma fonte divergente para um slug existente interrompe o lote; não sobrescreve uma revisão. Uma falha preserva operações anteriores e pode ser retomada com o mesmo manifesto. A interface cria rascunhos, limita o lote a 100 itens e o arquivo a 15 MB. Capas usam o upload normalizado existente (2 MB por arquivo, 32 MB totais da biblioteca — amplia de 10 MB para suportar 60 notícias com fotos/galerias, mantendo 1600 px, validação hash/WEBP e teto consistente entre CMS e publisher). O lote não publica o site.

O checkbox **Aprovar matérias após importar** vem desligado. Quando marcado por um operador após a revisão editorial, cada notícia nova recebe a transição de aprovação pela mesma API, com histórico separado. Registros existentes continuam preservados. O campo opcional `socialImage` de cada item aceita a mesma estrutura de upload de `cover`: cadastra uma imagem vertical aprovada na biblioteca e referencia `socialMediaId`, separado da galeria do site. No editor, o kit social mostra a imagem enviada e permite baixá-la para distribuição.

Para o operador, o mesmo domínio CMS está disponível por `python services/cms/import_newsroom.py manifesto.json --azure --report relatorio.json`. A opção `--approve` aprova apenas notícias recém-criadas; matérias já existentes continuam intocadas, inclusive rascunhos. Configure `CMS_SQL_SERVER`, `CMS_SQL_DATABASE`, `CMS_SQL_USER`, `CMS_SQL_PASSWORD` exclusivamente no ambiente privado e use a identidade SQL de runtime com permissões restritas. Esse CLI usa `CMS.upload_media`/`CMS.save`, grava revisões e registra o ator explícito `operator:editorial-launch`, como o publicador operador existente. Não é um endpoint de autenticação, não personifica usuário e não escreve tabelas diretamente.

Após revisão, a publicação mantém o fluxo snapshot → build → homologação → validação. Cadastros aprovados não comprovam uma implantação. Textos sociais e hashtags são metadados editáveis e versionados junto à matéria. Links canônicos do kit pressupõem a futura publicação no domínio AnderZilla; confira o artigo publicado antes de distribuir.

## Imagens das fontes

Priorize fotografias, capturas e materiais oficiais diretamente relacionados à pauta. Use arte editorial própria como alternativa quando não houver imagem adequada verificável. Diferencie fotografia, render de produto, captura de jogo e arte promocional nas descrições; não apresente uma ilustração como fotografia ou prova de uso real.

Cadastre cada arquivo na biblioteca com descrições PT/EN, crédito, direitos e `sourceUrl` apontando para a página de origem. A disponibilidade pública não implica licença aberta. Inspecione cada imagem: exclua avatares, QR codes, anúncios, produtos de notícias relacionadas e duplicatas. Quando a fonte oferecer mais imagens relevantes, selecione uma capa e vincule as demais em `mediaIds`. Preserve os arquivos anteriores e o histórico.

O site mostra a fonte nas legendas e permite ampliar capas e imagens da galeria, mantendo seu enquadramento. O publicador inclui `sourceUrl` no registro público e gera JPEG para as prévias sociais. Depois de publicar, confira carregamento, enquadramento, fontes e compartilhamento nas versões PT/EN e em tela pequena.
