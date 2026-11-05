# Cadastro AnderZilla — fase 1

A fonte canônica das decisões está na branch documental `codex/anderzilla-docs`:

- `G:/AnderZilla-docs/strategy/ACCOUNTS-AND-ACCESS-PHASES.md`: escopo, quatro fases, CPF e responsabilidade parental.
- `G:/AnderZilla-docs/operations/REGISTRATION-PHASE1-20261104.md`: execução, verificações e continuidade.

Branch de implementação: `codex/registration-phase1-20261104`.

Clerk foi escolhido pelo proprietário. Esta entrega não inclui pagamentos, planos ou streaming. Estado inicial: em implementação, **não publicado**. Não confundir autenticação Clerk, conclusão do cadastro privado e autorização de acesso futuro.

O backend deve rejeitar identidades sem e-mail confirmado, CPF inválido/repetido, cadastro incompleto, conta banida e vínculo parental ausente. Informar CPF do responsável não autoriza o cadastro de um menor. Menores precisam de autorização prévia autenticada e procedimento do fornecedor confirmado.

Não incluir chaves, CPF real, tokens, dados de menores ou credenciais em exemplos, testes, commits ou relatórios. Instalação/configuração e validação real serão registradas nos documentos canônicos.

Atualização do proprietário: **menores de 18 anos bloqueados nesta fase**. Vínculo parental está adiado. Operador: Anderson Henrique Gonçalves; atendimento: player.one@anderzilla.com.
