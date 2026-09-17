# BRIEF MESTRE — Contas de usuário, segurança, termos e Karaca Points (produção)

**Cole no Codex** · workspace `Z:\AnderZilla` · branch `codex/anderzilla-foundation`  
Docs: `Z:\AnderZilla-docs` · ler também `strategy/KARACA-POINTS.md`, `KARACA-ECONOMY-AND-PARTNERSHIPS.md`, `ROTEIRO-TORNAR-REAL.md`, `LOAD-SPLIT-auth-karaca.md`.

## Objetivo

Tirar o hub do modo **localStorage demo** e entregar:

1. Conta de leitor/jogador AnderZilla (não confundir com login Microsoft do **admin/CMS**).
2. Verificação de identidade por **e-mail**.
3. Login/cadastro facilitados: **Google** obrigatório no MVP; **Instagram** só se existir caminho OAuth/Meta suportado e estável — senão documentar bloqueio e oferecer “continuar com Meta/Facebook” ou adiar (não inventar provedor).
4. **Karaca Points só creditados em conta autenticada** (ledger no servidor). Visitante anônimo pode jogar/desafiar, mas ao ganhar KP → **popup** convidando a criar login e salvar pontos na conta.
5. Perfil: atualizar dados, preferências e personalização alinhada ao que o site já oferece.
6. Segurança + páginas burocráticas: Privacy, Terms, Cookies/Consent (PT-BR + EN), sem dados bancários no Git.

## Estado atual (verificado)

- Hub público: progresso em `localStorage` chave `anderzilla-hub-demo-v1` (`PlayerState`: saved, opened, interests, quizDone, claims). Missões demo: interests=25 KP, quiz=100 KP — **adulteráveis**, sem direito real.
- Admin: Entra/AAD separado — **não reutilizar** como login de visitante.
- ForgeKit Cloud Run: auth demo do produto — **não** é a conta do hub.
- KP não se vende, não saca, não vira dinheiro; Store Points só com estoque/auth reais depois.

## Personalização já existente (deve continuar e migrar para conta)

| Superfície | Hoje | Com conta |
|------------|------|-----------|
| Idioma PT/EN | query `lang` | preferência salva no perfil |
| Interesses (6 categorias) | local | perfil + ranking do feed |
| Mochila (saved) | local | sync servidor |
| Opened / progresso | local | sync |
| Quiz + claims de missão | local | só credita KP se autenticado + API |
| Perfil / Points / Store UI | demo | saldo/extrato da API |
| Filtro categoria, live, agenda | público | sem mudança de auth |

## Regra de ouro KP

- Cliente **nunca** define saldo, prêmio ou elegibilidade final.
- Sem conta: UI pode mostrar “você desbloqueou uma recompensa — crie conta para salvar X KP” (valor só como preview; crédito só após signup+verify+claim server-side idempotente).
- Não premiar clique em ad/afiliado; missões com evidência verificável.
- Demo localStorage **não migra saldo automaticamente** como direito; opcional: oferecer “importar progresso local” como sugestão de missões já feitas, revalidando no servidor.

## Ordem de build (incremental)

A) Gap analysis (BRIEF-auth-gap-analysis)  
B) Legal stubs + consent banner (BRIEF-auth-legal-security) — textos claros; flag “revisão jurídica pendente”  
C) Backend auth + ledger (BRIEF-auth-backend-ledger)  
D) UI/UX (BRIEF-auth-ui-ux)  
E) Homolog Azure; prod só com ok de Anderson  

## Fora de escopo

Resgates reais Store sem estoque; venda de KP; admin Entra; Polar; outreach; segredos no Git; auto-publish.

## Done when

- Conta email+verify + Google login funcionando em homolog  
- Popup em missão/desafio sem conta  
- KP só no ledger; perfil editável; privacy/terms/cookies PT+EN  
- Matriz gap analysis documentada  
- Builds verdes; registro `mon-karaca` / novo `mon-auth-accounts` atualizado  