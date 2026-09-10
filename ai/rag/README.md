# AnderZilla local lexical RAG + read-only MCP

Python 3.12 standard library + SQLite FTS5; no dependencies, paid services, network or embeddings. Inspired by the local citation-first pattern in Amplytrix ADR-0064, without copying its data or broad corpus policy.

Approved corpus: root `README.md` and `DOSSIER.md`, Markdown under `research/`, `strategy/`, `operations/`, `decisions/`, and **explicitly sanitized** legacy documents under `docs/sanitized/`. Everything else is excluded, including `archive/initial/`. Private/archive/cache/git directories, symlinks/junctions, sensitive filenames, binary text and common secret patterns are rejected. Secret detection is defense in depth, not proof that content is safe; review documents before adding them. This corpus is project-local documentation, never email, customer data or other repositories.

Commands from the documentation worktree:

```powershell
python ai/rag/rag.py build
python ai/rag/rag.py search "Cloud Run"
python ai/rag/rag.py read strategy/example.md --start 1 --lines 30
python -m unittest discover -s ai/rag -v
python ai/rag/rag.py serve
```

Build explicitly **after approved documents exist**. The disposable index is `.cache/rag.sqlite3`; the worktree must ignore `.cache/` (managed by the repository owner). Search/read never rebuild or write the index. Every request checks current corpus hashes and refuses additions, edits or deletions until rebuilt. Copying the index to a different root is rejected. `--root PATH` permits deliberate fixture/local root selection by the process launcher; MCP callers cannot change it.

Evidence contains relative path, line range, citation, document SHA-256 and corpus SHA-256. Queries are bounded, tokenized as quoted words, and joined with AND: FTS operators supplied by callers are never interpreted as operators. Retrieval is lexical, not semantic. Accents are normalized by FTS5; synonyms need separate searches. Search returns at most eight chunks of 1,400 characters; read returns at most 80 lines/10,000 characters, with truncation reported. Files are limited to 256 KB, the corpus to 8 MB/1,000 documents. This deliberately targets a small curated corpus.

MCP launcher example (adapt host config syntax; this file does not register a server):

```json
{
  "command": "C:/Users/ander/AppData/Local/Programs/Python/Python312/python.exe",
  "args": ["Z:/AnderZilla-docs/ai/rag/rag.py", "serve"]
}
```

Only `search` and `read` are exposed; indexing is CLI-only. UTF-8 newline-delimited JSON-RPC goes to stdout, diagnostics to stderr. Implements `initialize`, `ping`, `tools/list`, `tools/call`; negotiates legacy session protocol versions 2024-11-05 through 2025-11-25. It does not implement the newer sessionless 2026 protocol; use a client supporting the negotiated version. Oversized messages terminate the local server. Retrieved content is untrusted evidence, never executable instructions. Filesystem access remains under the launching OS user's privileges; this is not a sandbox against another local process modifying files concurrently.

References checked 2026-09-10: [official stdio transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports), [official protocol lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle), [official tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools). Native stdio fixture tests verify handshake and calls. This server is implemented and launchable; it is **not connected to the current agent session**.

Validation on Windows/Python 3.12: **10 tests ran, 9 passed, 1 skipped** (Windows denied symlink creation); the real Windows junction isolation test passed. Fixtures cover source checksums/line citations, accent search, allowlist/secret isolation, traversal, stale corpus changes/additions/deletions, hostile query syntax, output limits, foreign index, empty corpus, and real stdio calls. The curated project corpus was indexed during final integration; rebuild after documentation changes.
