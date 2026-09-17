"""Testes mock fetch/parser/idempotência/draft preserved — sem rede, sem PII."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

# Imports flexíveis como nos testes CMS existentes
try:
    from rss_import import fetch_bytes, parse_rss, import_feed, SOURCE_URL, SOURCE_HOST, PRINCIPAL, _validate_https_url, _strip_html, _slug_from_url, _rss_date_to_iso
    from core import CMS, Error
    from storage import SQLiteStore
except ImportError:
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "cms"))
    _sys.path.insert(0, str(_P(__file__).resolve().parent))
    from rss_import import fetch_bytes, parse_rss, import_feed, SOURCE_URL, SOURCE_HOST, PRINCIPAL, _validate_https_url, _strip_html, _slug_from_url, _rss_date_to_iso
    from core import CMS, Error
    from storage import SQLiteStore

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Google Blog</title>
<item><title>Gemini 2.0 launches</title><link>https://blog.google/products/gemini-2-launch/</link><pubDate>Wed, 17 Sep 2026 10:00:00 GMT</pubDate><description><![CDATA[<p>New <b>Gemini</b> features &amp; more.</p>]]></description></item>
<item><title>AI Studio update</title><link>https://blog.google/ai-studio/update/</link><pubDate>Wed, 17 Sep 2026 09:00:00 GMT</pubDate><description>Plain summary</description></item>
</channel></rss>"""

BAD_DOCTYPE = b'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss></rss>'
BAD_ENTITY = b'<?xml version="1.0"?><rss><!ENTITY x "evil"></rss>'

class FetchSecurityTests(unittest.TestCase):
    def test_late_and_utf16_doctype_rejected(self):
        for payload in (b' '*21000 + BAD_DOCTYPE, BAD_DOCTYPE.decode().encode('utf-16')):
            with self.assertRaisesRegex(ValueError, 'DOCTYPE'):
                parse_rss(payload)

    def test_real_opener_disables_automatic_redirect(self):
        from rss_import import NoRedirect
        import urllib.request
        opener = urllib.request.build_opener(NoRedirect())
        redirect = next(h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler))
        self.assertIsNone(redirect.redirect_request(None, None, 302, '', {}, 'https://evil.invalid'))

    def test_rejects_doctype(self):
        with self.assertRaises(ValueError):
            parse_rss(BAD_DOCTYPE)

    def test_rejects_entity(self):
        with self.assertRaises(ValueError):
            parse_rss(BAD_ENTITY)

    def test_strip_html_no_execution(self):
        out = _strip_html('<script>alert(1)</script><p>Hello <b>world</b></p>', 100)
        self.assertNotIn("<", out)
        self.assertNotIn("script", out.lower())
        self.assertIn("Hello", out)
        self.assertIn("world", out)

    def test_strip_html_limit(self):
        out = _strip_html("<p>" + "a"*5000 + "</p>", 10)
        self.assertEqual(len(out), 10)

    def test_validate_https_only(self):
        with self.assertRaises(ValueError):
            _validate_https_url("http://blog.google/rss/")
        with self.assertRaises(ValueError):
            _validate_https_url("https://user:pass@blog.google/rss/")
        with self.assertRaises(ValueError):
            _validate_https_url("https://192.168.1.1/rss")
        with self.assertRaises(ValueError):
            _validate_https_url("https://localhost/rss")
        _validate_https_url("https://blog.google/rss/")

    def test_parse_limits_and_https_filter(self):
        rss = b"""<?xml version="1.0"?><rss><channel>
        <item><title>ok</title><link>https://blog.google/a</link><description>hi</description></item>
        <item><title>bad</title><link>http://blog.google/b</link><description>hi</description></item>
        <item><title>bad2</title><link>https://192.168.0.1/c</link><description>hi</description></item>
        </channel></rss>"""
        items = parse_rss(rss)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["link"], "https://blog.google/a")

    def test_rss_date_to_iso(self):
        iso = _rss_date_to_iso("Wed, 17 Sep 2026 10:00:00 GMT")
        self.assertIn("2026-09-17", iso)
        self.assertIsNone(_rss_date_to_iso("not a date"))

    def test_slug_deterministic(self):
        url = "https://blog.google/products/gemini-2-launch/"
        s1 = _slug_from_url(url)
        s2 = _slug_from_url(url)
        self.assertEqual(s1, s2)
        self.assertRegex(s1, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    @patch("rss_import.urllib.request.build_opener")
    def test_fetch_rejects_too_large(self, mock_opener):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers = {"Content-Length": str(3*1024*1024)}
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: False
        mock_opener.return_value.open.return_value = mock_resp
        with self.assertRaises(ValueError):
            fetch_bytes(SOURCE_URL)

    @patch("rss_import.urllib.request.build_opener")
    def test_fetch_rejects_redirect_outside_allowlist(self, mock_opener):
        # Primeira resposta é redirect para outro host
        mock_resp = MagicMock()
        mock_resp.status = 301
        mock_resp.headers = {"Location": "https://evil.com/rss"}
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda *a: False
        mock_opener.return_value.open.return_value = mock_resp
        with self.assertRaises(ValueError):
            fetch_bytes(SOURCE_URL)

    @patch("rss_import.urllib.request.build_opener")
    def test_fetch_timeout_propagates(self, mock_opener):
        mock_opener.return_value.open.side_effect = urllib.error.URLError("timeout")
        with self.assertRaises(ValueError):
            fetch_bytes(SOURCE_URL)


class ImportIdempotenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cms = CMS(SQLiteStore(Path(self.tmp.name) / "cms.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_creates_draft_only(self):
        report = import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        self.assertEqual(report["imported"], 2)
        self.assertEqual(report["duplicate"], 0)
        self.assertEqual(report["rejected"], 0)
        items = self.cms.list(PRINCIPAL, "content")["items"]
        self.assertEqual(len(items), 2)
        for row in items:
            self.assertEqual(row["status"], "draft")
            data = row["data"]
            # Título original em EN, PT vazio
            self.assertTrue(data["titleEN"])
            self.assertEqual(data["titlePT"], "")
            self.assertEqual(data["summaryPT"], "")
            self.assertEqual(data["bodyPT"], "")
            self.assertEqual(data["sourceName"], "Google Blog")
            self.assertTrue(data["sourceUrl"].startswith("https://blog.google/"))
            # Campos via existentes apenas
            self.assertIn("sources", data)
            sources = json.loads(data["sources"])
            self.assertEqual(sources[0]["name"], "Google Blog")
            self.assertEqual(sources[0]["url"], data["sourceUrl"])

    def test_idempotent_duplicate(self):
        r1 = import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        self.assertEqual(r1["imported"], 2)
        r2 = import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        self.assertEqual(r2["imported"], 0)
        self.assertEqual(r2["duplicate"], 2)
        self.assertEqual(r2["rejected"], 0)
        items = self.cms.list(PRINCIPAL, "content")["items"]
        self.assertEqual(len(items), 2)
        # Hash determinístico — mesmos slugs
        slugs = {r["data"]["slugEN"] for r in items}
        self.assertEqual(len(slugs), 2)

    def test_failed_inventory_aborts_without_writes(self):
        with patch.object(self.cms, 'list', side_effect=RuntimeError('unavailable')), patch.object(self.cms, 'save') as save:
            with self.assertRaises(RuntimeError):
                import_feed(self.cms, xml_bytes=SAMPLE_RSS)
            save.assert_not_called()

    def test_draft_preserved_on_retry(self):
        import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        items = self.cms.list(PRINCIPAL, "content")["items"]
        first_id = items[0]["id"]
        first_version = items[0]["version"]
        # Editor altera título PT
        self.cms.save(PRINCIPAL, "content", {**items[0]["data"], "titlePT": "Título editado"}, first_id, first_version)
        # Reimport não deve sobrescrever
        report = import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        self.assertEqual(report["duplicate"], 2)
        updated = self.cms.list(PRINCIPAL, "content")["items"]
        edited = next(r for r in updated if r["id"] == first_id)
        self.assertEqual(edited["data"]["titlePT"], "Título editado")
        self.assertEqual(edited["version"], first_version + 1)

    def test_dedup_consults_existing_collections(self):
        # Cria conteúdo existente com sourceUrl manualmente (simula published)
        existing_data = {
            "titlePT": "", "titleEN": "Existing", "summaryPT": "", "summaryEN": "x", "bodyPT": "", "bodyEN": "x",
            "category": "ia", "sourceName": "Google Blog", "sourceUrl": "https://blog.google/products/gemini-2-launch/",
            "slugPT": "existing", "slugEN": "existing", "sources": json.dumps([{"name":"Google Blog","url":"https://blog.google/products/gemini-2-launch/"}])
        }
        self.cms.save(PRINCIPAL, "content", existing_data)
        report = import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        # Um já existe, um novo
        self.assertEqual(report["imported"], 1)
        self.assertEqual(report["duplicate"], 1)

    def test_report_coverage_without_pii(self):
        report = import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        self.assertEqual(report["source"], SOURCE_URL)
        self.assertIn("fetched", report)
        self.assertIn("imported", report)
        self.assertIn("coverage", report)
        self.assertEqual(report["coverage"]["origins"], [SOURCE_HOST])
        self.assertIsNotNone(report["coverage"]["earliestPublishedAt"])
        self.assertIsNotNone(report["coverage"]["latestPublishedAt"])
        # Sem PII: não há actor/email/token
        dumped = json.dumps(report)
        self.assertNotIn("@", dumped)
        self.assertNotIn("token", dumped.lower())

    def test_mock_fetch_injection(self):
        def fake_fetch(url):
            self.assertEqual(url, SOURCE_URL)
            return SAMPLE_RSS
        report = import_feed(self.cms, fetch_fn=fake_fetch)
        self.assertEqual(report["imported"], 2)

    def test_rejected_counts(self):
        bad_rss = b"""<?xml version="1.0"?><rss><channel>
        <item><title></title><link>https://blog.google/ok</link><description>no title</description></item>
        <item><title>good</title><link>https://blog.google/good</link><description>ok</description></item>
        </channel></rss>"""
        report = import_feed(self.cms, xml_bytes=bad_rss)
        self.assertEqual(report["rejected"], 1)
        self.assertEqual(report["imported"], 1)

    def test_never_approves_or_releases(self):
        import_feed(self.cms, xml_bytes=SAMPLE_RSS)
        items = self.cms.list(PRINCIPAL, "content")["items"]
        for row in items:
            self.assertNotEqual(row["status"], "approved")
            self.assertNotEqual(row["status"], "archived")
        # Tentar aprovar via import não existe
        with self.assertRaises(Error):
            self.cms.save(PRINCIPAL, "content", None, items[0]["id"], items[0]["version"], "approve")
            # O teste acima mostra que approve exigiria campos completos; mas o ponto é que import não chamou approve
        # Verifica que import não deixa rastro de approve
        self.assertEqual(items[0]["status"], "draft")


if __name__ == "__main__":
    unittest.main()
