# AnderZilla — hub de descobertas e exploração

## Direção vigente

O objetivo principal é dar vontade de explorar novidades e voltar: games, consoles, celulares, gadgets, IA e curiosidades tecnológicas. A proposta de revista clara e séria foi rejeitada pelo proprietário por parecer um portal genérico. O hub deve comunicar diversão e personalidade imediatamente. Cursos, assinaturas e produtos são ofertas complementares, encontradas quando o interesse do visitante cria contexto.

AnderZilla Ghost permanece a identidade reconhecível. Azul elétrico, fundo noturno, amarelo do personagem e acentos vermelhos orientam a interface. O personagem acompanha a exploração como anfitrião. A imagem original foi preservada; não foi substituída por outro avatar ou mascote.

## Playtest 02 implementado

Código no worktree Z:/AnderZilla, diretório prototypes/editorial. O endereço local continua http://127.0.0.1:4175/?lang=pt#home. Não foi publicado no Azure nesta etapa.

- index.html: carregamento do hub e diálogo acessível.
- hub.css: interface noturna, capa, categorias, feed, passaporte e mobile.
- hub.js: PT/EN, mochila, interesses, exploração, quiz e navegação.
- discoveries.js: seis resumos de curadoria com fonte primária e data.
- assets/anderzilla-ghost.png: imagem original do proprietário, preservada byte a byte.
- assets/discovery-room.png: arte conceitual gerada para o esconderijo gamer, sem representar equipamento real. Não foi usada como fotografia de produto ou prova de review.

As seis telas são Radar, Mochila, Desafio, Seu Radar, Canais e Parcerias. Detalhes das descobertas abrem em diálogo com resumo, curiosidade, data e fonte original. Não há catálogo de cursos acima do conteúdo; ForgeKit fica em link contextual no rodapé e na rota comercial.

## Retenção que pode ser testada

| Interação implementada | Valor para o visitante | Estado real |
|---|---|---|
| Radar por interesses | Temas preferidos aparecem primeiro em Tudo junto | Preferências salvas no localStorage deste navegador |
| Mochila | Guardar achados para revisitar sem procurar de novo | Favoritos persistem após recarregar; podem ser removidos |
| Me surpreenda | Encontrar assunto fora do caminho habitual | Sorteia uma descoberta ainda não aberta; evita repetir a atual quando todas já foram abertas |
| Passaporte | Visualizar os seis territórios explorados | Marca categoria após abrir o resumo; não alega medir leitura completa |
| Desafio | Aprender uma curiosidade e testar entendimento | Três perguntas com explicação e fonte; nova tentativa sem punição; selo local após acerto das três |

Esses mecanismos são hipóteses de retenção, não comprovação de que alguém voltará. Não há contadores de usuários, ranking, urgência, sequência diária punitiva, prêmio financeiro ou atividade comunitária fictícia. Preferências e progresso não são enviados a servidor; sem sincronização entre dispositivos. Se o armazenamento estiver indisponível, o estado fica só na sessão e a interface informa isso.

## Conteúdo é o motor

A curadoria inicial tem seis itens, não é um feed automatizado ou uma operação editorial diária. Cada item mostra data original; peças de 2025 estão identificadas como arquivo. Claims de fabricantes são resumos de fontes, sem fingir teste pelo criador. A base de fontes fica em research/hub-discoveries.json e em discoveries.js; deve haver revisão antes de mudar uma chamada ou informar disponibilidade.

Para uma versão operada, separar o radar em novidades datadas, curiosidades duradouras, experiências próprias, vídeos e listas salvas. Uma atualização precisa acrescentar uma descoberta útil, não somente trocar a capa. IA pode ajudar a triar e rascunhar; publicação deve verificar fonte, data, rumor versus confirmação, região e direitos das imagens.

O próximo investimento deve ser conteúdo e experiência, não fórum vazio ou sistema de pontos complexo. Selecionar duas ou três pautas principais por ciclo conforme tempo disponível, com recortes para os canais existentes. Não assumir frequência diária sem confirmar capacidade. A lógica de quiz deve receber novas perguntas a partir de conteúdos revisados; repetir o mesmo desafio para sempre elimina sua utilidade.

## Monetização por interesse

Descoberta → curiosidade satisfeita → retorno/salvamento → decisão de aprofundar ou comprar. Essa é a hipótese de funil escolhida, a ser medida. Afiliação aparece em escolha de produto pertinente e somente com aprovação e URL ativa. Curso pode aprofundar um experimento procurado pelo leitor. Assinatura precisa oferecer um benefício recorrente real. Produto próprio aparece quando ajuda a executar algo relacionado ao conteúdo. Patrocínio integra uma experiência identificada, sem comprar a conclusão.

Não bloquear o entretenimento inicial atrás de compra ou exigir cadastro para salvar no playtest. Antes de paywall, testar demanda e capacidade de entrega. As regras comerciais de evidência e separação da CodeMatrix continuam vigentes; o tom divertido não autoriza parceria, depoimento ou promessa inventados.

## Validação e próximos critérios

JavaScript passou em node --check. Foram exercitadas seis telas em PT/EN nas larguras 320, 390, 768 e 1440px, sem overflow horizontal da página e com um h1 por tela. Testes de interação verificaram seis filtros, favorito após recarregar, passaporte persistente, ordenação por interesse, resposta incorreta/repetição e conclusão persistente do quiz. Nenhum erro de página foi registrado. Home desktop e mobile foram inspecionadas visualmente.

Isso não equivale a auditoria completa de acessibilidade ou desempenho. A capa usa PNG original grande no protótipo; otimização de imagem e variantes responsivas fazem parte da implementação de produção. apps/web e apps/forgekit não foram alterados nesta revisão; nenhum novo deploy ou recurso pago de nuvem foi criado.

Antes de portar para Next.js: avaliar visual e uso com o proprietário; revisar o acervo e as fontes; decidir a cadência; implementar URLs indexáveis PT/EN, páginas de conteúdo e atualização editorial; testar segurança/privacidade de qualquer recurso que passe a usar servidor. Preservar compra ForgeKit e rotas existentes.

Métricas propostas para piloto: retorno em sete dias, descobertas abertas por visita, salvamentos por visita, reabertura de salvos, uso de interesses, conclusão do desafio e cliques comerciais contextualizados. Não foram instaladas ferramentas de analytics nem produzidos números fictícios. Comparar coortes e esforço editorial; cliques extras, isoladamente, não comprovam satisfação ou receita.
