# Área do jogador — fluxos, estados e linguagem

05/11/2026. Especificação para implementação, não inventário de funções já publicadas. Ler [produto](MEMBER-AREA.md) e [segurança](MEMBER-AREA-SECURITY-API.md).

## Entrada, retorno e navegação

| Contexto | Caminho completo | Recuperação |
|---|---|---|
| Login comum | Entrar → código Clerk → cadastro completo? → Painel | Incompleto → onboarding → Painel; bloqueado → atendimento sem dados de membro |
| Ação privada em artigo público | Guardar benefício/CTA → login → onboarding se necessário → confirmar intenção do artigo → voltar ao contexto | Artigo indisponível: mensagem e Radar; cancelar login mantém página pública, sem ação efetuada |
| Link privado direto / favorito | Estrutura neutra → verificar sessão → carregar seção solicitada | Visitante: gate; token expirado: novo login; destino válido preservado, nenhum dado privado em URL |
| Seu Radar no topo | Sessão/cadastro ativo → interesses confirmados → notícias compatíveis | Sem temas: configuração; falha de preferências: tentar de novo ou abrir Radar geral claramente identificado |
| Perfil | Menu jogador → Perfil → editar → salvar → confirmação | Sair com alterações pede escolha; erro preserva formulário só na sessão atual, sem senha/CPF no storage |
| Sair | Marcar saída pendente e ocultar dados → revogar sessão → limpar caches/rascunhos privados → home pública | Falha de rede: limpar UI local imediatamente, informar que falta confirmar encerramento remoto; oferecer repetir; não anunciar revogação não confirmada |
| Expiração/troca A→B | Invalidar geração da sessão e cancelar requests → desmontar conteúdo privado → nova verificação | Respostas antigas descartadas. Sem nome/saldo/avatar/lista de A enquanto B carrega |
| Voltar do navegador / bfcache | Exibir shell neutro até revalidar identidade e estado | Não restaurar DOM antigo privado após logout, exclusão ou suspensão |
| Conta excluída/suspensa durante uso | Detectar rejeição do servidor → limpar área privada → tela neutra | Suspensão: contato/revisão; exclusão concluída: confirmação genérica. Não reiniciar onboarding automaticamente |

Destino pós-login é intenção interna explícita se houver, senão dashboard. Allowlist de rotas próprias; rejeitar URLs externas, //host, esquema arbitrário, caminhos administrativos e parâmetros que tentem representar outro usuário. Guardar só tipo de intenção+ID de conteúdo público+expiração curta; não token, CPF, saldo ou formulário pessoal. Revalidar conteúdo e permissão ao retornar.

## Estados de componente e feedback

- **Verificando identidade:** skeleton genérico, sem dados pré-carregados de outra sessão. Não mostrar ações de membro até validação.
- **Carregando seção:** skeleton com tamanho estável; resumo acessível “Carregando sua mochila…”. Bloqueio localizado, não spinner infinito em toda tela.
- **Acordando banco:** indicador calmo “Preparando seu espaço. Já vamos continuar.” Tentativas com limite/backoff e ação manual ao esgotar. Sem “SQL”, “serverless”, “token” ou contagem técnica.
- **Vazio legítimo:** explicar o próximo passo; não confundir vazio com falha. Zero KP só com consulta concluída.
- **Salvando:** feedback junto à ação; impedir repetição daquela operação. Não bloquear leitura ou menu inteiro sem necessidade.
- **Sucesso:** somente após confirmação do servidor. Toast curto + atualização no local; erro importante permanece até ação, não desaparece antes de leitura.
- **Erro recuperável:** preservar contexto de mesma conta, explicar efeito e oferecer ação concreta. Não alegar “seu progresso está salvo” sem confirmação.
- **Sem conexão:** leitura pública pode continuar quando disponível; operações pessoais/ganhos não ficam em fila persistente invisível. Não exibir dados privados offline após sessão deixar de ser verificável.
- **Conflito ou resultado incerto:** consultar operação original. Nunca “tente de novo” criando outro crédito. Não estornar automaticamente por timeout.
- **Feature desativada:** explicar status sem aparência de defeito. Flags não concedem permissão; página privada continua exigindo membro.

## Catálogo de mensagens PT/EN

IDs são para implementação; usuário não vê códigos. Traduzir por intenção, com personalidade moderada. Sempre associar erro de campo ao rótulo e anunciar resumo acessível. Não usar termos como “401”, “CPF em outra conta”, “banco caiu”, “site ficou de castigo” ou atribuir culpa ao usuário.

| ID / situação | Português | English | Ação |
|---|---|---|---|
| member_required | Entre para montar sua mochila e continuar sua jornada. | Sign in to build your backpack and continue exploring. | Entrar / Agora não |
| complete_account | Falta um passo para liberar seu espaço. Vamos concluir seu cadastro? | One step left to unlock your space. Let’s finish your account. | Concluir cadastro |
| session_expired | Sua sessão terminou. Entre de novo para continuar de onde parou. | Your session ended. Sign in again to pick up where you left off. | Entrar novamente |
| account_unavailable | Seu acesso precisa de uma revisão. Fale com a gente para conferir o próximo passo. | Your access needs a review. Contact us to check the next step. | Falar com suporte |
| warming | Preparando seu espaço. Já vamos continuar. | Getting your space ready. We’ll continue shortly. | Aguardar com limite |
| load_failed | Não conseguimos abrir este bloco agora. Vamos tentar de novo? | We couldn’t load this section just now. Try again? | Tentar novamente |
| offline | Parece que a conexão deu uma pausa. Reconecte para continuar. | Looks like your connection paused. Reconnect to continue. | Tentar novamente |
| save_failed | Ainda não conseguimos confirmar essa mudança. Vamos conferir? | We couldn’t confirm this change yet. Let’s check. | Consultar estado antes de repetir |
| saving | Guardando sua mudança… | Saving your change… | Botão pendente |
| saved | Pronto! Mudança salva. | All set! Change saved. | Sem modal obrigatório |
| backpack_empty | Sua mochila está pronta para a primeira descoberta. | Your backpack is ready for its first discovery. | Abrir meu Radar |
| bookmark_added | Foi para a mochila. Bora para a próxima? | Saved to your backpack. Ready for the next discovery? | Ver mochila |
| bookmark_removed | Descoberta removida da mochila. | Discovery removed from your backpack. | Desfazer |
| content_unavailable | Esta descoberta não está disponível agora. | This discovery isn’t available right now. | Voltar ao Radar / Remover salvo |
| interests_empty | Quais temas entram no seu Radar? | What belongs on your radar? | Escolher interesses |
| interests_saved | Seu Radar ganhou novos rumos. | Your radar has a fresh direction. | Abrir meu Radar |
| interests_conflict | Seus interesses mudaram em outro acesso. Confira a seleção antes de salvar. | Your interests changed in another session. Review your selection before saving. | Revisar seleção |
| radar_empty | Nenhuma novidade nesses temas por enquanto. Bora abrir o mapa? | No fresh stories in these topics yet. Ready to explore a little wider? | Ajustar interesses / Radar geral |
| exploration_empty | Sua próxima descoberta começa aqui. | Your next discovery starts here. | Abrir meu Radar |
| history_clear_confirm | Limpar sua exploração? Mochila, interesses e KP não mudam. | Clear your exploration history? Your backpack, interests and KP won’t change. | Limpar histórico / Cancelar |
| history_cleared | Mapa renovado. Seu histórico de exploração foi limpo. | A fresh map. Your exploration history is cleared. | Voltar à exploração |
| kp_disabled | Karaca Points ainda não está liberado. Seu Radar já tem muita coisa para explorar. | Karaca Points isn’t available yet. There’s plenty to explore on your radar. | Ver regras / Abrir Radar |
| wallet_failed | Não conseguimos consultar seus KP agora. Atualize para conferir o saldo. | We couldn’t check your KP just now. Refresh to see your balance. | Atualizar saldo |
| mission_empty | Nenhuma missão nova por aqui. Seu Radar continua aberto. | No new missions right now. Your radar is ready to explore. | Abrir meu Radar |
| mission_paused | Esta missão está em pausa. Escolha outra para continuar. | This mission is paused. Choose another to keep going. | Ver missões |
| mission_expired | O tempo desta tentativa terminou. Confira se já dá para tentar de novo. | This attempt has timed out. Check whether another attempt is available. | Ver opções |
| mission_try_again | Ainda não foi dessa vez. Revise as pistas e confira quando pode tentar de novo. | Not quite this time. Review the hints and check when you can try again. | Rever conteúdo / Ver prazo |
| mission_checking | Conferindo sua missão… | Checking your mission… | Aguardar / Consultar status |
| award_pending | Missão validada. Falta confirmar seus KP. | Mission verified. Confirm your KP to finish. | Confirmar KP |
| award_uncertain | A confirmação ainda não chegou. Vamos conferir antes de repetir. | Confirmation hasn’t arrived yet. Let’s check before trying again. | Conferir status |
| award_success | Karaca! +{kp} KP na carteira. | Karaca! +{kp} KP in your wallet. | Ver carteira |
| award_already | Esta missão já rendeu seus KP. Confira no extrato. | You’ve already earned this mission’s KP. Check your activity. | Ver lançamento |
| claim_expired | O prazo para confirmar estes KP terminou. Confira as opções desta missão. | The time to confirm these KP has ended. Check this mission’s options. | Consultar status / Nova tentativa se permitida |
| rate_limited | Vamos dar uma pausa. Tente novamente mais tarde. | Let’s take a pause. Please try again later. | Mostrar prazo real quando conhecido |
| reauth_required | Para proteger sua conta, confirme seu acesso antes de continuar. | To protect your account, confirm your access before continuing. | Confirmar acesso |
| delete_confirm | Excluir sua conta? Você perderá o acesso ao seu espaço. Confira abaixo o que será removido e o que precisa ser mantido. | Delete your account? You’ll lose access to your space. Review what will be removed and what must be retained below. | Excluir conta / Manter conta |
| deletion_pending | Seu acesso já foi encerrado. Falta concluir uma etapa da exclusão. | Your access is closed. One deletion step still needs to finish. | Conferir exclusão / Falar com suporte |
| logout_unconfirmed | Você saiu desta tela. Falta confirmar o encerramento desta sessão. | You’ve left this screen. This session still needs sign-out confirmation. | Tentar encerrar sessão |

Saída comum encerra **sessão atual**, não todas as sessões. Ação distinta “Sair de todos os dispositivos” só aparece após integração e teste desse alcance. Em revogação incerta, manter bloqueio local de reexibição e não restaurar automaticamente a sessão pelo SDK; oferecer nova entrada explícita ou repetir encerramento. Não dizer “sessão encerrada” sem confirmação.

## Detalhes de usabilidade que fecham os ciclos

- Menu: adotar disclosure de navegação com botão aria-expanded, links normais e Tab/Shift+Tab sem focus trap; Escape fecha e devolve foco ao avatar. Conteúdo fechado não recebe foco. Não usar role=menu/setas sem implementar integralmente esse padrão. Painel mobile modal, se escolhido, prende foco somente enquanto aberto e restaura ao fechar. Não abrir só por hover.
- Dashboard: heading único, ordem DOM acompanha leitura visual; atalhos não duplicam ação com rótulos contraditórios. Skeleton não anuncia repetidamente.
- Interesses: multiseleção sem depender de cor; Salvar/Cancelar próximos, aviso antes de abandonar edição, sucesso com resumo dos temas.
- Mochila: desfazer tem foco acessível e prazo claro; remoção em lote exige seleção/contagem/confirmação; sem “limpar tudo” perto de navegação.
- Missão: aviso de tempo legível sem contagem anunciada a cada segundo, preservar respostas em memória durante falha na mesma sessão, não enviar resposta automaticamente ao expirar. Reabertura consulta tentativa e não fabrica outra. Reload recupera tentativa/prazo/resultado já enviado; respostas ainda não enviadas podem precisar de novo preenchimento. Avisar antes de sair/recarregar quando tecnicamente possível, sem prometer recuperar rascunho não persistido.
- Carteira: números localizados, KP inteiro sem símbolo de moeda, disponível e reservado por extenso, extrato com filtro e paginação acessível. Consulta vazia informa “Nenhuma movimentação ainda”.
- Perfil: CPF mascarado; alteração de CPF/data de nascimento não entra em PATCH comum; suporte identifica pessoa por fluxo privado, não por formulário público com CPF. Segurança abre confirmação no Clerk sem sair antes da ação. Reautenticação retorna à confirmação de exclusão; não exclui automaticamente.
- Mensagens de falha não expõem existência de outra conta, e-mail ou CPF. Código técnico/correlationId fica em suporte interno sem tokens/dados pessoais.
- Na troca de idioma, manter seção e contexto equivalente; falha de gravação oferece continuar sem salvar. Não trocar língua silenciosamente por geolocalização.
