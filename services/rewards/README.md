# Rewards domain reference

Local Python standard-library implementation. No HTTP listener, Azure deployment or real reward catalog.

```powershell
python -m unittest discover -s services/rewards -v
python -m json.tool services/rewards/openapi.json > $null
```

- `core.py`: domain operations and trusted-principal boundary.
- `schema.sql`: SQLite reference schema, append-only ledger and audit.
- `test_rewards.py`: test-only accounts, verifier and inventory; never production seeds.
- `openapi.json`: planned OpenAPI 3.1 HTTP contract, with no deployment server URL.

Integrate through a session-validating adapter. Never deserialize browser input into `Principal` or accept client-supplied awards. The default mission verifier rejects completion. The HTTP adapter, TLS SQL driver, Azure SQL migrations, pagination and reward terms acceptance remain to implement. Map reference-core fields to the contract explicitly; this is not a generated HTTP service.

SQLite files are local only. Port transactions and constraints to durable Azure SQL before cloud use; do not put SQLite on Functions' ephemeral disk. Architecture and rollout are canonical in the sibling documentation worktree, `strategy/BACKEND-AND-DATA.md`.
