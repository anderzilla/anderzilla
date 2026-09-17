# Produção republicada — 17/09/2026 (correção de UX de contas)

Publicado por volta de 2026-09-17T16:20Z (verificado às 16:31Z) em https://anderzilla.com e https://www.anderzilla.com, a pedido explícito do proprietário ("pode publicar em produção"), direto — sem passar por homolog desta vez. Mesmo recurso `anderzilla-web-production`, mesma conta/tenant/assinatura já conferidos pelo script em publicações anteriores.

- Código-base: commit `9d7340392c9a03cefb37e4518ae805d8cf0fa2b1`.
- Conteúdo desta leva: correção do bug de especificidade CSS que fazia o diálogo de contas (login/cadastro/verificação) herdar estilo de outro diálogo do hub — o proprietário havia reportado a tela como "bem feia" com um print real de produção. Também: seletor de avatar (8 presets + upload de foto com redimensionamento no cliente), e os demais ajustes de UX/acessibilidade da revisão do agente de marca (ver commit `9d73403` no repositório de código).
- `npm run build`: 171 arquivos, sem erros.

## Verificação pós-publicação

- HTTP 200 em `anderzilla.com`, `www.anderzilla.com` e no hostname Azure.
- Rotas novas/relevantes com 200: `/pt/comercio/brasil`, `/pt/privacidade`, `/pt/termos`, `/hub/avatars/preset-1.svg`. Caminho inexistente segue 404.
- **Inspeção visual real do problema relatado**: abri "Entrar" na home pública e o diálogo "Entre no seu radar" agora renderiza com padding, largura e sombra corretos — o mesmo estado que aparecia quebrado no print original do proprietário. Sem erros no console do navegador.
- Backend de contas (`services/identity`) continua não implantado no Azure; o diálogo mostra "Contas estão fora do ar por aqui" como projetado — não é regressão, é o estado esperado até essa implantação separada acontecer.

## Rollback

Reconstruir o build a partir do commit anterior (`00bdaf9`, publicado nesta mesma sessão mais cedo) e republicar com `infra/azure/deploy.ps1 -Environment production`. Export estático, sem migração de dados envolvida.
