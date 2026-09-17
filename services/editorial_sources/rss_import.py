"""Ferramenta pequena: RSS oficial -> rascunho CMS.

Fonte fixa inicial: https://blog.google/rss/
Nunca aprova/publica; apenas draft via CMS.save com principal autorizado.
Sem IA gerando publicação, sem duplicar notícia (dedup por sourceUrl).
"""
import argparse
import hashlib
import html
import ipaddress
import json
import re
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# Imports CMS — suporta execução como módulo ou script direto.
try:
    from core import CMS, Error  # type: ignore
    from storage import SQLiteStore, AzureSQLStore  # type: ignore
except ImportError:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cms"))
    from core import CMS, Error  # type: ignore
    from storage import SQLiteStore, AzureSQLStore  # type: ignore

SOURCE_URL = "https://blog.google/rss/"
SOURCE_NAME = "Google Blog"
SOURCE_HOST = "blog.google"
ALLOWED_HOSTS = {SOURCE_HOST}
PRINCIPAL = {"id": "operator:editorial-rss", "name": "Editorial RSS import", "roles": ["anderzilla_admin"]}

MAX_BYTES = 2 * 1024 * 1024
TIMEOUT = 10
MAX_REDIRECTS = 3
TITLE_LIMIT = 300
SUMMARY_LIMIT = 3000
BODY_LIMIT = 15000

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _is_private_host(host: str) -> bool:
    h = (host or "").lower()
    if not h:
        return True
    if h == "localhost" or h.endswith((".localhost", ".local")):
        return True
    try:
        addr = ipaddress.ip_address(h)
        return not addr.is_global
    except ValueError:
        return False


def _validate_https_url(url: str):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https":
        raise ValueError(f"HTTPS required: {url}")
    if not parts.hostname:
        raise ValueError(f"Missing host: {url}")
    if parts.username or parts.password:
        raise ValueError(f"Credentials not allowed: {url}")
    if _is_private_host(parts.hostname):
        raise ValueError(f"Private/local host not allowed: {url}")


def _strip_html(text: str, limit: int) -> str:
    if not text:
        return ""
    # Remove tags sem executar; depois unescape.
    no_tags = re.sub(r"<[^>]+>", " ", text)
    unescaped = html.unescape(no_tags)
    # Colapsar espaços
    collapsed = re.sub(r"\s+", " ", unescaped).strip()
    return collapsed[:limit]


def _rss_date_to_iso(value: str) -> str | None:
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt is None:
            raise ValueError
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        # Tenta ISO direto
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            return None


def _slug_from_url(url: str) -> str:
    h = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:12]
    slug = f"rss-google-{h}"
    # Garante padrão validado por core
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        slug = f"rss-{h}"
    return slug


def fetch_bytes(url: str, timeout: int = 10, max_bytes: int = MAX_BYTES) -> bytes:
    """Fetch com timeout, 2MB, redirects apenas mesmo domínio allowlist, HTTPS sem credenciais."""
    _validate_https_url(url)
    original_host = urllib.parse.urlsplit(url).hostname.lower()
    if original_host not in ALLOWED_HOSTS:
        raise ValueError(f"Host not in allowlist: {original_host}")
    current = url
    # Opener sem redirect automático
    opener = urllib.request.build_opener(NoRedirect())
    for _ in range(MAX_REDIRECTS + 1):
        _validate_https_url(current)
        host = urllib.parse.urlsplit(current).hostname.lower()
        if host != original_host:
            raise ValueError(f"Redirect outside allowlist: {current}")
        req = urllib.request.Request(
            current,
            headers={
                "User-Agent": "AnderZilla-RSS/1.0 (+https://anderzilla.com)",
                "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            },
            method="GET",
        )
        try:
            with opener.open(req, timeout=timeout) as resp:
                status = getattr(resp, "status", 200)
                # Alguns handlers retornam redirect como resposta normal
                if status in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("Location")
                    if not loc:
                        raise ValueError("Redirect without Location")
                    current = urllib.parse.urljoin(current, loc)
                    continue
                if status != 200:
                    raise ValueError(f"HTTP {status}")
                cl = resp.headers.get("Content-Length")
                if cl is not None:
                    try:
                        if int(cl) > max_bytes:
                            raise ValueError("Content too large")
                    except ValueError as e:
                        if "too large" in str(e).lower():
                            raise
                data = resp.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise ValueError("Content too large (2MB limit)")
                if not data:
                    raise ValueError("Empty response")
                return data
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                loc = e.headers.get("Location")
                if not loc:
                    raise ValueError("Redirect without Location")
                current = urllib.parse.urljoin(current, loc)
                continue
            raise ValueError(f"HTTP {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise ValueError(f"Fetch failed: {e}") from e
    raise ValueError("Too many redirects")


def parse_rss(xml_bytes: bytes):
    """XML seguro: rejeita DOCTYPE/ENTITY; parse títulos/link/data/resumo limitado."""
    if not xml_bytes or len(xml_bytes) > MAX_BYTES:
        raise ValueError("Invalid XML size")
    # Rejeita DOCTYPE e ENTITY (case-insensitive)
    lower = xml_bytes.replace(b'\x00', b'').lower()
    if b"<!doctype" in lower or b"<!entity" in lower:
        raise ValueError("DOCTYPE/ENTITY not allowed")
    # Também varre todo se pequeno, ou amostra maior já cobre ataque no início.
    # Para garantir, checa full se cabe.
    if len(xml_bytes) <= 20000 and (b"<!doctype" in xml_bytes.lower() or b"<!entity" in xml_bytes.lower()):
        raise ValueError("DOCTYPE/ENTITY not allowed")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise ValueError(f"XML parse failed: {e}") from e

    # RSS 2.0: channel/item ; Atom fallback
    items = []
    # RSS
    for item in root.findall(".//item"):
        title = _strip_html(item.findtext("title") or "", TITLE_LIMIT)
        link = (item.findtext("link") or "").strip()
        # content:encoded com namespace
        desc = item.findtext("description") or ""
        # tenta content:encoded
        for child in item:
            if child.tag.endswith("encoded"):
                if child.text:
                    desc = child.text
                break
        summary = _strip_html(desc or "", SUMMARY_LIMIT)
        pub = (item.findtext("pubDate") or item.findtext("published") or item.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip()
        items.append({"title": title, "link": link, "pubDate": pub, "summary": summary})
    # Se nenhum item RSS, tenta Atom
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title = _strip_html(entry.findtext("atom:title", default="", namespaces=ns) or "", TITLE_LIMIT)
            link_el = entry.find("atom:link", ns)
            link = ""
            if link_el is not None:
                link = (link_el.get("href") or "").strip()
            summary = _strip_html(entry.findtext("atom:summary", default="", namespaces=ns) or entry.findtext("atom:content", default="", namespaces=ns) or "", SUMMARY_LIMIT)
            pub = (entry.findtext("atom:published", default="", namespaces=ns) or entry.findtext("atom:updated", default="", namespaces=ns) or "").strip()
            if title or link:
                items.append({"title": title, "link": link, "pubDate": pub, "summary": summary})
    # Limita e filtra vazios
    parsed = []
    for it in items:
        if not it["link"]:
            continue
        try:
            _validate_https_url(it["link"])
        except ValueError:
            continue
        parsed.append(it)
        if len(parsed) >= 50:
            break
    return parsed


def _existing_source_urls(cms) -> set[str]:
    records = cms.list(PRINCIPAL, "content")["items"]
    urls = set()
    for r in records:
        u = (r.get("data") or {}).get("sourceUrl")
        if isinstance(u, str) and u:
            urls.add(u.strip())
        # também sources JSON
        s = (r.get("data") or {}).get("sources")
        if isinstance(s, str) and s:
            try:
                arr = json.loads(s)
                for obj in arr:
                    if isinstance(obj, dict) and isinstance(obj.get("url"), str):
                        urls.add(obj["url"].strip())
            except Exception:
                pass
    return urls


def import_feed(cms, xml_bytes: bytes | None = None, fetch_fn=None):
    """Importa RSS -> rascunhos CMS. Retorna relatório JSON."""
    source = SOURCE_URL
    fetched = 0
    imported = 0
    duplicate = 0
    rejected = 0
    errors = []
    dates = []

    # Fetch se não fornecido
    if xml_bytes is None:
        if fetch_fn is not None:
            xml_bytes = fetch_fn(source)
        else:
            xml_bytes = fetch_bytes(source)

    try:
        items = parse_rss(xml_bytes)
        fetched = len(items)
    except ValueError as e:
        return {
            "source": source,
            "fetched": 0,
            "imported": 0,
            "duplicate": 0,
            "rejected": 0,
            "coverage": {"origins": [SOURCE_HOST], "earliestPublishedAt": None, "latestPublishedAt": None},
            "error": str(e),
        }

    existing = _existing_source_urls(cms)
    # Hash determinístico para consulta (também usado para idempotência)
    existing_hashes = {hashlib.sha256(u.encode("utf-8")).hexdigest() for u in existing}

    earliest = None
    latest = None

    for it in items:
        title = it.get("title") or ""
        link = (it.get("link") or "").strip()
        summary = it.get("summary") or ""
        pub_raw = it.get("pubDate") or ""
        iso = _rss_date_to_iso(pub_raw)

        if iso:
            try:
                dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
                dates.append(dt)
                if earliest is None or dt < earliest:
                    earliest = dt
                if latest is None or dt > latest:
                    latest = dt
            except Exception:
                pass

        # Dedup determinístico por URL e por hash
        url_hash = hashlib.sha256(link.encode("utf-8")).hexdigest()
        if link in existing or url_hash in existing_hashes:
            duplicate += 1
            continue
        # Validações mínimas antes de salvar
        if not title or not link:
            rejected += 1
            errors.append({"url": link, "reason": "missing title or link"})
            continue
        try:
            _validate_https_url(link)
        except ValueError as e:
            rejected += 1
            errors.append({"url": link, "reason": str(e)})
            continue
        # Título original vai para EN; PT vazio para editor preencher
        title_en = title[:TITLE_LIMIT]
        summary_en = summary[:SUMMARY_LIMIT] if summary else title_en
        body_en = summary_en
        if len(body_en) > BODY_LIMIT:
            body_en = body_en[:BODY_LIMIT]
        slug = _slug_from_url(link)
        # publishedAt: se parse falhou, deixa vazio (draft sem data inventada)
        published_at = iso or ""
        # sources com note (campo existente suportado)
        sources_val = json.dumps(
            [{"name": SOURCE_NAME, "url": link, **({"publishedAt": iso} if iso else {}), "note": "RSS oficial — texto original em inglês; PT pendente de revisão editorial."}],
            ensure_ascii=False,
        )
        data = {
            "titlePT": "",
            "titleEN": title_en,
            "summaryPT": "",
            "summaryEN": summary_en,
            "bodyPT": "",
            "bodyEN": body_en,
            "category": "ia",
            "sourceName": SOURCE_NAME,
            "sourceUrl": link,
            "slugPT": slug,
            "slugEN": slug,
            "sources": sources_val,
        }
        if published_at:
            data["publishedAt"] = published_at
        # Usa apenas campos existentes suportados (core.FIELDS content)
        try:
            row = cms.save(PRINCIPAL, "content", data)
            # Garante que nunca aprovou
            assert row["status"] == "draft", "must remain draft"
            imported += 1
            existing.add(link)
            existing_hashes.add(url_hash)
        except Exception as e:
            # Mapeia erro de validação para rejeitado
            rejected += 1
            errors.append({"url": link, "reason": str(e)[:500]})
            continue

    coverage = {
        "origins": [SOURCE_HOST],
        "earliestPublishedAt": earliest.astimezone(timezone.utc).isoformat() if earliest else None,
        "latestPublishedAt": latest.astimezone(timezone.utc).isoformat() if latest else None,
    }
    report = {
        "source": source,
        "fetched": fetched,
        "imported": imported,
        "duplicate": duplicate,
        "rejected": rejected,
        "coverage": coverage,
    }
    if errors:
        # Sem PII: apenas url fonte e motivo técnico
        report["errors"] = errors[:20]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--database", type=Path, help="SQLite path for local test")
    g.add_argument("--azure", action="store_true", help="Use CMS_SQL_* env (explicit)")
    parser.add_argument("--report", type=Path, help="Write JSON report")
    parser.add_argument("--timeout", type=int, default=TIMEOUT)
    parser.add_argument("--limit", type=int, default=50, help="Max items (not used, capped at 50)")
    args = parser.parse_args()

    # Não lê tokens/env além do que AzureSQLStore exige quando --azure
    cms = CMS(AzureSQLStore() if args.azure else SQLiteStore(args.database))
    report = import_feed(cms)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
