# Planejador local de automações

Ferramenta IA de planejamento, sem rede, execução cloud, agendamento ou alteração no CMS. Catálogo de oito workflows em planner.py; valores BRL são envelopes propostos por execução, não preços nem saldo real.

```powershell
python ai/automation/planner.py media-cuts --media-id owned_1 --estimated-brl 3.50
python ai/automation/planner.py report-custom --start 2026-09-01 --end 2026-10-01
python -m unittest discover -s ai/automation -v
```

Todos os resultados são dry-run com dispatch=false. Datas locais, fim exclusivo. Semanas e meses recebem datas explícitas para replay determinístico. IDs não comprovam existência nem direitos da mídia: a futura API deve validar ambos, identidade, permissões, orçamento e idempotência.

Não expor esta CLI como serviço público nem tratá-la como autorização. Implementação runtime no repositório de código seguirá ../../strategy/INTEGRATED-AUTOMATION-ROADMAP.md e ../../strategy/AUTOMATION-CMS-CONTROL.md.
