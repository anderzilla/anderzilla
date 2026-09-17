# Conta do hub — integração UI e QA

Implementado localmente em 2026-09-17. Sem deploy ou declaração de autenticação operacional em produção. Contrato definitivo: `services/identity/CONTRACT.md` (prevalece).

## Configuração

`NEXT_PUBLIC_ACCOUNT_API_BASE` precisa apontar ao backend identity separado e é aplicada no build estático. HTTPS obrigatório, exceto localhost em desenvolvimento. Sem base/serviço/capabilities a UI informa indisponibilidade e mantém visitante navegando. Cookies enviados com `credentials: include`; toda mutação usa CSRF obtido do bootstrap e `Content-Type: application/json`; nenhuma credencial entra no bundle. Origin/CORS e SameSite precisam funcionar para os domínios realmente utilizados.

- Google redirect no portal: `/account/callback` (ou `/?account=google`), com `code/state` trocados via POST na API. Query sensível removida imediatamente.
- E-mail: `/verify?token=...`, remove token da URL e pede confirmação explícita. Token não vai para localStorage.
- Caps: registration, emailPassword, google, meta, passwordReset, emailResend, rewards, minimumAge, termsVersion, privacyVersion, csrfToken. Google/Meta só aparecem se habilitados. Reset fica oculto enquanto não suportado.
- Me/profile: envelope account; lang pt-BR/en normalizado para pt/en no hub; wallet/ledger permanecem exclusivamente da API.
- Missão oficial: missions → challenge → evidence → pending/claim com Idempotency-Key estável. API fornece perguntas/condições/recompensa; cliente não decide direito ou crédito. Preview pendente fica em sessionStorage com expiração, atrelado ao browser pelo backend; não é token de sessão e não basta para autorizar crédito.

## Separação dos dados

Guest localStorage preserva somente a experiência visitante; nunca importa claims, saldo ou quizDone como prova oficial. Conta usa interesses, mochila e opened da API; mutações são serializadas e falhas não simulam salvamento. Sair volta às preferências locais anteriores. Quiz local dá selo/progresso e popup de convite sem somar KP. Carteira não calcula saldo a partir do localStorage e não mostra zero inventado em erro.

Cadastro e Google exigem 18+ e aceite de versões dos termos/privacidade; marketing separado e desmarcado. Política provisória, sem avaliação jurídica concluída.

## Checklist de validação integrada

- [ ] 320, 390, 768 e 1440px; PT e EN; sem overflow horizontal.
- [ ] Entrar abre dialog, foco contido nativo, Escape fecha, foco volta ao acionador; rádio/checkbox navegáveis por teclado.
- [ ] Sem API: perfil/entrar indisponíveis com texto honesto; visitante salva mochila e joga.
- [ ] Quiz local correto abre convite; Agora não conserva selo; nenhum KP oficial é criado ou importado.
- [ ] capabilities Google=false/Meta=false: sem botão social; reset=false: sem fluxo de reset anunciado.
- [ ] Cadastro exige idade/aceites; opt-in desmarcado; rejeição de SMTP não aparece como conta criada com sucesso.
- [ ] Link /verify preenche token, remove query e exige confirmar; erro/expiração são honestos; login/verificação sucedida consultam /me.
- [ ] Login carrega preferências da API; alternar idioma/interesses/mochila salva no servidor; falha mostra erro e não simula persistência.
- [ ] Wallet/ledger usam available/reserved/items; erro exibe indisponível; load-more usa cursor da API.
- [ ] Missão oficial anônima guarda preview curto, signup/verify e claim revalidam; replay conserva chave; valor nunca enviado para crédito.
- [ ] Google callback valida no servidor, erros/account_link_required não auto-vinculam conta local.
- [ ] Export gera arquivo apenas após sucesso; delete exige confirmação e senha ou reautenticação social recente; logout não deixa preferências privadas no guest storage.

TypeScript `tsc --noEmit` passou durante implementação. Build integrado e UI browser são executados pelo orquestrador após integração legal/backend.
