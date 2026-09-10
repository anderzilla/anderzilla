# Fluxo de desenvolvimento e documentação

## Separação criada
A branch órfã codex/anderzilla-docs tem histórico próprio no mesmo Git e worktree Z:/AnderZilla-docs. Ela guarda dossiê, decisões, pesquisas, roteiros e código das ferramentas de IA. A branch codex/anderzilla-foundation preserva as alterações de storefront da sessão anterior em Z:/AnderZilla. Main permanece referência anterior até revisão/merge.

Documentos antigos migram para archive/initial e ficam fora do RAG para não competir com o posicionamento atual. Arquivos mínimos AGENTS.md/CLAUDE.md/instruções de cliente no código são ponteiros operacionais, não cópias do dossiê.

Dockerfiles, Terraform e GitHub Actions permanecem na esteira de código: são artefatos executáveis de entrega e precisam evoluir com a aplicação. Ferramentas de IA editoriais e RAG têm fonte canônica na branch documental; um instalador local gera configurações dos clientes fora do Git do código.

## Esteira
1. Atualizar documentação e registrar decisão quando necessário; commit documental.
2. Fixar hash documental em .anderzilla-docs-ref na branch de implementação.
3. Desenvolver em codex/<assunto>, sem checkout destrutivo de trabalho alheio.
4. PR para develop: builds e verificações; deploy manual de homologação privada.
5. Validar visual, PT/EN, links, acessibilidade, conteúdo e orçamento em homologação.
6. Promover para main e produção pelo ambiente GitHub específico, identidade federada e artefato identificado.
7. Registrar commit, digest, revisão Cloud Run, URL, autor da validação e rollback.

Branches remotas, proteções, environments e OIDC não são presumidos pela presença do YAML. Validar plano GitHub e configurar no repositório privado quando acesso/permissões estiverem confirmados. Não publicar branch documental em hospedagem web nem usar como contexto público.

## Reconstrução
Em máquina nova: clone o repositório, crie worktree da branch documental, confira o hash de .anderzilla-docs-ref, execute ai/bootstrap.ps1 a partir da documentação e rode validações. O RAG é descartável e reconstruído; tokens não fazem parte do setup. Não fazer merge de histórias sem relação para sincronizar documentação.
