# Roteiro — tornar real o que ainda não está (AnderZilla)

**Data:** 2026-09-16 (America/Sao_Paulo)  
**Base:** site prod conferido em https://anderzilla.com/ + `MONETIZATION-PROCESS-REGISTER.md`  
**Dono orquestração:** MoneyMaker + Trust Commerce  
**Código:** Codex local em `Z:\AnderZilla` (Cloud Agents indisponíveis no plano)

## Já é real (não reabrir)

| Item | Evidência |
|------|-----------|
| Domínio + portal Azure | https://anderzilla.com/ e www · HTTP 200 |
| Hub editorial PT/EN | Radar, lives “status não confirmado”, Karaca demo, sitemap ~132 |
| ForgeKit venda | US$149 · CTA Gumroad `anderzilla.gumroad.com/l/edkel` · sem Polar |
| ForgeKit demo | Cloud Run live |
| StackPick honestidade | Disclosure: sem comissão até afiliado ativo |
| Candidatos afiliados BR | Listados; **nenhum ativo** |
| Spec Trust BR×INT + BRIFs A/B/C | Docs canônicos em AnderZilla-docs |
| Automation worker homolog | Cloud Run privado + CMS OIDC (não = receita) |

## Princípios do roteiro

1. **Receita antes de fábrica:** Trust + 1º $ afiliado/produto > media pipeline.  
2. **Nada “ativo” sem prova:** contrato/aprovação + URL HTTPS + `market` no CMS.  
3. **Lang ≠ market:** hubs BR e INT separados; CTAs com moeda/loja.  
4. **Sem segredos no Git:** PIX/C6/Wise só no painel da plataforma.  
5. **Homolog → prod Azure** depois de build verde; não inventar métricas na Trust.  
6. Teto de custo ~R$150/mês; automation não estoura sem gate.

---

## Fase 0 — Estabilizar base (1–2 dias)

**Objetivo:** working tree limpa e docs alinhados ao prod.

| # | Ação | Quem | Done when |
|---|------|------|-----------|
| 0.1 | Commit/revisar mudanças pendentes (newsroom, hub, publisher) ou stash consciente | Codex + Anderson | `git status` limpo ou lista explícita do que fica fora |
| 0.2 | Atualizar registro: `mon-forgekit` próximo passo = Trust CMS; data 2026-09-16 | Trust Commerce | Registro versionado |
| 0.3 | Confirmar Gumroad: produto à venda, ZIP, payout PayPal ok | Anderson (painel) | Screenshot/ok verbal |

---

## Fase 1 — Trust & Commerce no site (semana 1) ← prioridade #1

**Objetivo:** acabar os 404 e dar respaldo público BR×INT.

| # | Ação | Brief / artefato | Done when |
|---|------|------------------|-----------|
| 1.1 | Rotas hub: `/[lang]/comercio/brasil`, `/internacional`, `/transparencia`, `/produtos`, `/parceiros`, `/patrocine` + redirects EN | BRIEF A | 200 em prod após deploy; empty states honestos |
| 1.2 | Copy Trust PT+EN + live/Karaca (anexo Pc Gamer) | BRIEF C + `BRIEF-trust-commerce-live-karaca.md` | Sem “ao vivo”/parceiro/ganhos inventados |
| 1.3 | CMS/Admin campo `market` br\|intl\|global + flags | BRIEF B | Admin publica placement por market sem código |
| 1.4 | ForgeKit page CMS-driven (fallback Gumroad) | BRIEF A | Mesmo CTA edkel; sem Polar |
| 1.5 | Deploy Azure (homolog visual → prod) | `infra/azure` | Rotas no sitemap; MoneyMaker re-checa URLs |
| 1.6 | Atualizar registro: `mon-trust`, `mon-hub-br`, `mon-hub-intl` → `em_build`/`ativo` conforme evidência | Trust Commerce | Datas atualizadas |

**Critério de aceite da fase:** visitante entende como AnderZilla ganha dinheiro (BR×INT) e consegue comprar ForgeKit a partir do hub Trust/Commerce.

---

## Fase 2 — Primeiro real afiliado / oferta (semana 1–2) ← prioridade #2 receita

**Objetivo:** sair de “só candidatos” para **pelo menos 1** link `ativo` com disclosure.

| # | Ação | Market | Done when |
|---|------|--------|-----------|
| 2.1 | Escolher 2–3 candidatos BR do top da lista (sugerido: Amazon Associados BR, Mercado Livre, 1 rede Awin/KaBuM) e **inscrever** | br | Conta criada; status no registro `em_build` |
| 2.2 | **PartnerStack:** reaplicar **≥ 2026-09-21** (hoje ainda cedo) | intl | Application submetida; registro atualizado |
| 2.3 | Em paralelo INT: 1P referrals (Railway / Vast / RunPod) se painel der URL | intl | URL tracking no CMS `active` |
| 2.4 | Só então: trocar placeholders StackPick / hub BR por links reais | global | Disclosure atualizado; status `ativo` no registro |
| 2.5 | Avaliar checkout BRL (Kiwify vs Hotmart vs Stripe BR) **sem lançar** até Trust no ar | br | Decisão documentada em registro (`mon-kiwify-br`) |

**Não fazer:** marcar afiliado ativo no site antes da aprovação.

---

## Fase 3 — Distribuição e prova social leve (semana 2–3)

| # | Ação | Done when |
|---|------|-----------|
| 3.1 | Cadência live mínima (1×/semana) + broadcast CMS só quando confirmado | Agenda real ou empty honesto |
| 3.2 | 1 post por canal (YT/IG/TikTok/Twitch) apontando ForgeKit + Trust | Links UTM ou equivalentes |
| 3.3 | Kit patrocínio (`/patrocine`) sem métricas fake | Página 200; outreach **só** com ok explícito de Anderson |
| 3.4 | Newsletter: só se captura+envio+opt-out reais | Senão permanece `ideia` |

---

## Fase 4 — Automation & CMS “de verdade” (semana 2–4, paralelo controlado)

**Objetivo:** fechar o que está `em_build` sem virar fábrica cara.

| # | Ação | Gate |
|---|------|------|
| 4.1 | Commit + bundle único admin/CMS automation (código local → homolog) | Testes verdes; sem publish automático |
| 4.2 | Conectar **1** fonte editorial real → rascunho → revisão humana → publish Azure | Zero auto-publish |
| 4.3 | Relatório vazio honesto (sem inventar receita) | CSV/snapshot com cobertura |
| 4.4 | Media pipeline / cortes | Só após 4.2 estável e custo/minuto conhecido |

Seguir fases 1–2 do `INTEGRATED-AUTOMATION-ROADMAP.md`; não pular para fábrica de cortes.

---

## Fase 5 — Karaca Points produção (depois de receita ou demanda clara)

| # | Ação | Done when |
|---|------|-----------|
| 5.1 | Definir verba/coorte; XP ≠ KP (plano econômico) | Decisão Anderson |
| 5.2 | Auth + ledger autoritativo; demo localStorage não migra saldo | Backend + flags |
| 5.3 | Sponsors/supply (`mon-karaca-sponsored/supply`) | Contrato + estoque; senão empty |

---

## Fase 6 — Escala (mês 2+)

- Ads só com slot vendido ou house ad explícito  
- YPP / Creator Rewards quando elegível (`mon-platform`)  
- Segundo produto digital (Gear31 / outro) só com Trust + 1º canal afiliado comprovando clique→venda  
- Homolog formal `anderzilla_reviewer` (401 anônimo) se precisar QA privada

---

## Ordem sugerida na prática (próximos 14 dias)

```
Dia 1-2   Fase 0 + começar BRIEF A (rotas Trust/Commerce)
Dia 3-5   BRIEF C copy + BRIEF B market CMS → deploy homolog → prod
Dia 6     Re-checagem URLs (MoneyMaker) + atualizar registro
Dia 7-10  Inscrições afiliados BR + preparar PartnerStack (≥21/09)
Dia 10-14 1º link ativo no site OU empty mantido; automation: 1 fonte→rascunho
```

## Donos

| Frente | Agente / pessoa |
|--------|-----------------|
| Orquestração renda | MoneyMaker |
| Trust/Commerce review | Trust Commerce |
| Afiliados BR candidatos→ativos | Caça Promo + Anderson (aprovação) |
| Live/Karaca honesty | Pc Gamer |
| Código | Codex local (Anderson cola BRIFs) |
| Workspace sync | Zilla (só se pedido) |

## Fora de escopo até gate explícito

Outreach a marcas · compra de tráfego · Polar · inventar parceiros · KP cash · publish automático sem revisão · dados bancários no repo · Cloud Agents (plano atual).

## Atualização 2026-09-17 — Contas + Karaca produção

Prioridade elevada sob pedido do proprietário: prompts multi-IA em `BRIEF-auth-karaca-accounts.md` + `LOAD-SPLIT-auth-karaca.md`. KP só com conta; popup de cadastro; Google OAuth; Instagram só se viável; privacy/terms/cookies; ledger autoritativo. Pode avançar em paralelo ao Trust Commerce se Codex tiver sessões separadas.
