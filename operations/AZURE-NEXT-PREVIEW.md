# Azure — prévia Next.js componentizada

Entrega em 10/09/2026. URL verificada: https://salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net/?lang=pt#home

Publicação concluída no ambiente nomeado **visual**, dentro do recurso **anderzilla-web-homolog**, grupo anderzilla-web, SKU Free. Conta CLI anderzilla@ymail.com, tenant 3fdcb773-0842-4fb9-925e-bea17d681f83 e assinatura 44b76346-26bd-4cd3-a529-627e47e99e5a revalidados antes do deploy. Nenhum recurso pago ou banco criado.

A amostra visual é pública, com X-Robots-Tag noindex/nofollow/noarchive e Cache-Control no-store, sem dados privados, conta ativa ou resgates reais. Noindex não é autenticação. A homologação formal no hostname sem -visual continua com papel anderzilla_reviewer, respondendo401 anônimo. O recurso de produção e o domínio principal não foram publicados nesta entrega.

## Validação

- npm run build em apps/web passou:18 páginas exportadas, homepage16,8kB e120kB de JavaScript inicial segundo Next. apps/forgekit não foi tocada.
- Playwright/Chrome: oito áreas × dois idiomas × quatro larguras (320,390,768,1440), um h1, sem overflow horizontal e sem erros de página.
- Fluxos locais: diálogo/Escape, salvar/recarregar mochila, selecionar interesses, receber25KP demo, completar quiz e chegar a125KP, impedir nova concessão, embed opt-in/parent correto e remoção ao mudar plataforma.
- Azure: HTTP200 com noindex/no-store; home React hidratada, Store em inglês, ForgeKit, StackPick, comparativo, privacidade e termos200; sem erros de página.
- Avatar Ghost no public/hub tem SHA256 original D250940D7F8D8BF44875B5B5071D6983BEB79D2D73AB6590580E5664AF6256B6.
- Núcleo rewards:11 testes aprovados. RAG:9 aprovados,1 ignorado porque Windows não permitiu symlink; teste real de junction passou, incluindo lifecycle stdio somente leitura.

Manifesto dos78 arquivos de export antes da configuração de preview: AZURE-NEXT-ARTIFACT.json, digest a1cf7f562fd6f09e62e78849138ab86faf018c64a29091e982f42af40f4dbe34. Configuração do slot acrescenta noindex/no-store e robots Disallow. Screenshots de QA ficam em .cache, não versionadas.

## Reproduzir e reverter

Executar build em apps/web e infra/azure/deploy.ps1 -Environment preview usando AzureCli portátil e AZURE_CONFIG_DIR exclusivos do projeto. O script verifica conta/SKU e usa --env visual. Nunca trocar por production para revisar o novo visual. Para rollback do slot, reconstruir a revisão anterior validada da branch em checkout isolado e republicar no mesmo visual. Para remover a amostra, excluir somente ambiente visual do recurso homolog; não excluir o recurso ou alterar DNS.

.github/workflows/preview-azure-web.yml prepara o mesmo ambiente por dispatch manual. Pipeline remoto ainda não foi executado/configurado com secrets nesta entrega; não apresentar como CI ativo. CI de código inclui build das apps e testes do núcleo rewards. Publicação CLI atual foi real e verificada.

## Limites deliberados

Áreas internas ainda usam hash e idioma por query; URLs editoriais /pt/en e artigos indexáveis entram na próxima fase. Pontos locais são demonstração descartável. Banco Azure SQL e Functions são arquitetura proposta, não implantados. Catálogo, campanhas e agenda não inventam itens/eventos. O OG gerado existente ainda usa visual anterior; revisar junto da migração editorial de URLs, antes de promover o redesign ao domínio principal.
