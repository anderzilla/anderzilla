# IA AnderZilla

## O que está disponível
Codex é o coordenador desta sessão. Foram executados três pesquisadores/revisores Codex com tarefas separadas; posteriormente esses papéis implementaram calendário, RAG e infraestrutura. Claude Code estava autenticado por OAuth e respondeu a uma consulta independente de estratégia. Não houve consulta comprovada ao Gemini ou GitHub Copilot; não contabilizar esses provedores como participantes.

Seis papéis portáveis em ai/agents: researcher, editor, commercial, platform, reviewer e analyst. São perfis para acionamento por tarefa, não seis processos pagos permanentes. Os arquivos têm frontmatter Claude Code e ferramentas somente leitura por padrão; a coordenação Codex usa os mesmos papéis como instruções de subtarefas. A implementação fica com o agente principal ou com delegação explícita delimitada.

Quatro skills canônicas em ai/skills: editorial, monetization, release e knowledge, todas restritas a AnderZilla. O bootstrap cria junctions para descoberta local por Codex/Claude e pode instalar junctions no catálogo pessoal de skills. A fonte continua na branch documental. Não sobrescreve configuração preexistente diferente.

## Conhecimento e MCP
RAG local Python/SQLite FTS5 em ai/rag, sem embeddings e sem custo por consulta. Indexa somente documentos aprovados AnderZilla, com caminho/linha/hash e detecção de atualização. Não indexa emails, dados de clientes, tokens, arquivo privado, Git ou conteúdo de outros projetos. Reaproveita o padrão conceitual de ADR0064 do Amplytrix; não copia sua base de conhecimento nem código de produto.

MCP de conhecimento: implementação local stdio somente leitura. Microsoft Learn MCP: documentação pública, sem login e sem custo do servidor, não controla assinatura Azure. O bootstrap prepara os dois clientes. Configuração local não prova carregamento na sessão atual: testar handshake/consulta e reiniciar cliente quando necessário. Fonte oficial: https://learn.microsoft.com/en-us/training/support/mcp.

Google Developer Knowledge MCP é candidato após selecionar projeto/conta e autenticação, não instalado com chave emprestada da CodeMatrix. O endpoint exige credencial/projeto conforme https://developers.google.com/knowledge/mcp. Gmail/Drive/GitHub e demais conectores existentes devem confirmar identidade antes de cada operação relevante; não duplicar conector com MCP artesanal sem necessidade.

## Cadência e contexto
1. Consultar a versão documental fixada por .anderzilla-docs-ref.
2. Recuperar somente o conhecimento relevante; atualizar corpus e registrar fontes.
3. Separar pesquisa, rascunho e revisão independente quando a tarefa justificar.
4. Resolver divergências com evidência e decisão humana, não por votação de modelos.
5. Fazer uma rodada pequena por experimento. Registrar quando um provedor não estava disponível.

Nenhuma automação recorrente de geração ou publicação foi criada: volume não substitui conteúdo próprio. Sugerir/agendar recorrência somente com objetivo, frequência, conta e orçamento definidos. Não usar saída de uma IA como comprovação de recurso de conta, política vigente ou propriedade de perfil.

## Comandos
Executar `./ai/bootstrap.ps1 -CodeRoot Z:/AnderZilla -InstallUserSkills` na branch documental. Executar `python ai/rag/rag.py build` depois de editar o corpus. Ver comandos search/read/serve e testes em ai/rag/README.md.

Fontes de configuração: documentação oficial Codex https://developers.openai.com/codex/mcp e https://developers.openai.com/codex/skills; CLI `claude --help` inspecionada localmente. Os clientes podem exigir reinício para descobrir as novas configurações.
