---
name: anderzilla-trust-commerce
description: Use when implementing or updating AnderZilla Trust & Commerce, Brasil vs Internacional market hubs, CMS commerce types, monetization process register, ForgeKit storefront trust, affiliates/ads/sponsor empty-vs-active rules.
---

# anderzilla-trust-commerce

Canonical docs: `Z:/AnderZilla-docs` branch `codex/anderzilla-docs`.

## Before changes
1. Read strategy/TRUST-AND-COMMERCE-CMS.md and strategy/MONETIZATION-PROCESS-REGISTER.md
2. Confirm real status per process; never promote candidate → active without evidence
3. Use strategy/TRUST-AND-COMMERCE-CMS-PROMPT.md as implementation checklist
4. Keep **Área Brasil** and **Área Internacional** visually and in data model

## Rules
- Every commercial entity has `market`: br | intl | global
- Trust center explains BR×INT money paths (no bank secrets in repo)
- ForgeKit: Gumroad https://anderzilla.gumroad.com/l/edkel + demo Cloud Run; no Polar stub language; market=intl
- Affiliates/ads/sponsor: honest empty states; feature flags per market
- Karaca Points: not a cash checkout
- Update process register in the same change set
- No brand outreach without explicit authorization

## After
Build touched apps; list routes + CMS fields; document how admin publishes per market.