# Registro de processos de monetização — AnderZilla

Documento vivo. Atualizar em toda criação, mudança de status ou encerramento de processo.
Agente responsável: `anderzilla-commerce-trust` (+ `anderzilla-commercial` para ofertas).
Skill: `anderzilla-trust-commerce` / `anderzilla-monetization`.

Legenda de status: `ideia` · `especificado` · `em_build` · `ativo` · `pausado` · `encerrado`

| ID | Processo | Onde no site | Como monetiza | Status | CMS? | Próxima ação | Atualizado |
|----|----------|--------------|---------------|--------|------|--------------|------------|
| mon-forgekit | ForgeKit produto próprio | /forgekit + Gumroad | US$149 one-time ZIP | ativo | parcial→CMS | Trust+página CMS-driven | 2026-09-10 |
| mon-stackpick | StackPick comparações | /stackpick | Afiliado quando aprovado | especificado | sim (planejado) | Só CTAs active | 2026-09-10 |
| mon-affiliates | Loot & upgrades / parceiros | /parceiros + hub | Comissão afiliada | especificado | sim | Preencher só aprovados | 2026-09-10 |
| mon-ads | Slots publicidade | home / inventário | Ads / house | especificado | sim | Ocultar se não vendido | 2026-09-10 |
| mon-live | Lives Twitch/YT/Kick | #live / hub live | Tips, subs, sponsor in-stream | em_build | parcial | Cadência + disclosure live | 2026-09-10 |
| mon-sponsor | Patrocínios diretos | /patrocine | Pacotes fechados | especificado | sim | Kit sem métricas fake | 2026-09-10 |
| mon-newsletter | Lista email | captura hub | Sponsor / lançamentos | ideia | sim | Lead magnet real | 2026-09-10 |
| mon-karaca | Karaca Points / Store | #points #store | Retenção (não vende KP) | em_build (demo) | sim (flags) | Auth+ledger antes de resgate | 2026-09-10 |
| mon-partnerstack | Rede PartnerStack | — | SaaS affiliates | pausado | n/a | Reaplicar ≥ 2026-09-21 | 2026-09-10 |
| mon-trust | Trust / Transparência | /transparencia | Confiança (habilita o resto) | especificado | sim | Implementar com Commerce CMS | 2026-09-10 |
| mon-platform | Receita nativa YT/Twitch | canais | Ads plataforma / bits | ideia | n/a | Após cadência estável | 2026-09-10 |

## Como atualizar (obrigatório)

1. Mudou status ou surgiu processo novo → editar esta tabela no mesmo PR/commit de docs.  
2. Mudou IA de rotas/CMS → atualizar `TRUST-AND-COMMERCE-CMS.md`.  
3. Rodar skill `anderzilla-trust-commerce` no início de tarefas commerce.  
4. Nunca marcar afiliado/sponsor/`ativo` sem evidência (contrato + URL).  
5. Registrar data (America/Sao_Paulo) na coluna Atualizado.