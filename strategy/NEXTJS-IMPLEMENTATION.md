# Implementação Next.js — hub AnderZilla

Entrega de 10/09/2026. O protótipo aprovado em prototypes/editorial foi migrado para React/TypeScript em apps/web. Esta é a base de interface para o produto; carteira, estoque e autenticação reais continuam separados da demonstração local.

## Fronteiras de componentes

- Hub: composição da home, cabeçalho, navegação, footer e seleção de áreas.
- HubProvider: contexto de idioma, preferências, mochila, diálogo, progresso e pontos demonstrativos. Persistência local com validação de IDs e chave própria; não importa saldo dos protótipos anteriores.
- model: tipos, taxonomia, canais, regras demo e configuração editorial pública. Sem tokens.
- discoveries.json: acervo inicial com IDs estáveis, títulos/resumos PT/EN, datas e fontes. Não é feed automático nem CMS.
- Primitives: Ghost, ícones, links externos, cards, passaporte e diálogo de descoberta.
- Community: agenda, sala de live, plataformas, publicidade, afiliados e canais.
- Rewards: quiz, perfil/interesses, carteira, missões, extrato e Store Points.
- hub.css: estilos isolados sob .hub; fontes/tokens compartilhados. Preservar páginas ForgeKit, StackPick e institucionais existentes.

A demonstração mantém navegação interna por fragmentos (#points, #store, #agenda etc.) e idioma por ?lang=pt/en para compatibilidade com links do playtest. A próxima fase editorial deve migrar para rotas indexáveis /pt/ e /en/, com URL própria por artigo, metadata e hreflang para traduções existentes. Fragmentos não são páginas SEO distintas. Não anunciar internacionalização por rota como já entregue.

## Regras para desenvolvimento

Separar componentes de apresentação, estado visitante e adaptador API. Não substituir cliente demo por chamadas HTTP que aceitam saldo ou accountId do navegador. A interface real consumirá contratos /api/v1 e mostrará loading/erro/indisponibilidade; não retornará a saldo local quando SQL falhar. Conteúdo editorial permanece estático para reduzir custo e manter navegação disponível.

Dados comerciais entram somente com aprovação, URL e disclosure. Eventos exigem data/fuso e plataforma; indicador de live expira. Embeds só carregam após ação do visitante. Avatar Ghost original preservado; marca em Oxanium e leitura em Space Grotesk conforme manual. Links Gumroad e comparativos continuam acessíveis.

Novos módulos devem ter estados vazios e acessíveis. Usar componentes sem HTML concatenado ou scripts de protótipo injetados. Não publicar endpoints de resgate antes de testes transacionais e autenticação real. Manter controles administrativos fora do bundle público.

## Entrega e operação

npm run build em apps/web é obrigatório. Testar navegação PT/EN, persistência, quiz, duplicação de missão, mobile, teclado, diálogos e regressão de ForgeKit/StackPick. Núcleo de recompensas: python -m unittest discover -s services/rewards -v. CI inclui ambos, mas workflow versionado não comprova execução remota.

Publicação de amostra visual: infra/azure/deploy.ps1 -Environment preview. Usa slot nomeado visual no recurso homolog Free, público apenas com conteúdo demonstrativo e noindex/no-store. A homologação formal mantém papel anderzilla_reviewer. Produção/domínio principal não são atualizados por essa opção. Nunca colocar dados privados na amostra pública; noindex não é controle de acesso.

Documentação/IA na branch codex/anderzilla-docs; código, contratos executáveis e pipeline na branch de aplicação. .anderzilla-docs-ref fixa a revisão documental. Ver BRAND-MANUAL.md, BACKEND-AND-DATA.md, KARACA-POINTS.md e operations/AZURE-NEXT-PREVIEW.md para estado final de validação/publicação.
