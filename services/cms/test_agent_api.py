import base64
import io
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from agent_api import AgentGateway, fetch_image, handle
from core import CMS, Error
from storage import SQLiteStore

ADMIN = {'id': 'human-admin', 'name': 'Anderson', 'roles': ['anderzilla_admin']}


def png_b64(color=(200, 30, 30), size=(64, 48)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


def article(**extra):
    data = {'titlePT': 'Título', 'titleEN': 'Title', 'summaryPT': 'Resumo', 'summaryEN': 'Summary', 'bodyPT': 'Corpo em **Markdown**.', 'bodyEN': 'Body in **Markdown**.',
            'category': 'games', 'sourceName': 'Fonte Oficial', 'sourceUrl': 'https://example.com/noticia', 'publishedAt': '2026-10-29',
            'slugPT': 'titulo', 'slugEN': 'title'}
    data.update(extra)
    return data


class AgentApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cms = CMS(SQLiteStore(Path(self.temp.name) / 'cms.db'))
        self.fetched = []
        self.gateway = AgentGateway(self.cms, media_hosts=['images.example.com'], fetcher=lambda url, hosts: (self.fetched.append(url), base64.b64decode(png_b64()))[1])
        self.key = self.gateway.create_key(ADMIN, 'claude-test')['key']
        self.auth = 'Bearer ' + self.key

    def tearDown(self):
        self.temp.cleanup()

    def call(self, method, path, body=None, idem=None, human=None, auth='default'):
        return handle(self.gateway, method, path, body, self.auth if auth == 'default' else auth, human, idem)

    def media(self, idem='media-key-0001', **extra):
        body = {'contentBase64': png_b64(), 'filename': 'capa.png', 'altPT': 'Descrição', 'altEN': 'Description', 'credit': 'Autor', 'license': 'Autorizada', 'sourceUrl': 'https://example.com/foto'}
        body.update(extra)
        return self.call('POST', '/v1/media', body, idem)

    def package(self):
        status, media = self.media()
        self.assertEqual(status, 201, media)
        status, art = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': article(coverMediaId=media['id'])}, 'article-key-0001')
        self.assertEqual(status, 201, art)
        status, submission = self.call('POST', '/v1/submissions', {'note': 'Teste', 'records': [{'collection': 'media', 'id': media['id'], 'version': media['version']}, {'collection': 'content', 'id': art['id'], 'version': art['version']}]}, 'submit-key-0001')
        self.assertEqual(status, 201, submission)
        return media, art, submission

    # ---- keys and identity ----
    def test_keys_are_hashed_scoped_revocable_and_human_made(self):
        with self.assertRaises(Error):
            self.gateway.create_key({'id': 'x', 'roles': ['anderzilla_editor']}, 'nope')
        with self.store_db() as db:
            stored = db.agent_key(self.key.split('_')[1])
        self.assertNotIn(self.key.split('_', 2)[2], str(stored))
        self.assertEqual(self.call('GET', '/v1/schema')[0], 200)
        for bad in (None, 'Bearer', 'Bearer azk_bad_secret', 'Bearer ' + self.key[:-2] + 'xx'):
            self.assertEqual(self.call('GET', '/v1/schema', auth=bad)[0], 401)
        self.gateway.revoke_key(ADMIN, self.key.split('_')[1])
        self.assertEqual(self.call('GET', '/v1/schema')[0], 401)

    def store_db(self):
        return self.cms.store.transaction()

    def test_agent_cannot_use_human_routes_or_forge_identity(self):
        _, _, submission = self.package()
        sid = submission['id']
        agent_as_human = {'id': 'agent:x', 'roles': ['anderzilla_agent']}
        for human in (None, agent_as_human, {'id': 'e', 'roles': ['anderzilla_editor']}):
            for path in ('approve', 'request-changes'):
                self.assertIn(self.call('POST', f'/v1/submissions/{sid}/{path}', {}, human=human)[0], (401, 403))
            self.assertIn(self.call('POST', f'/v1/submissions/{sid}/comments', {'collection': 'content', 'recordId': 'x', 'text': 'oi'}, human=human)[0], (401, 403))
        self.assertEqual(self.call('POST', '/v1/releases/abc/promote', human=agent_as_human)[0], 403)
        self.assertEqual(self.call('POST', '/v1/releases/abc/promote', human=ADMIN)[0], 501)

    # ---- validation and drafts ----
    def test_validate_does_not_save_and_reports_errors(self):
        status, result = self.call('POST', '/v1/articles:validate', article())
        self.assertEqual((status, result['valid']), (200, True))
        status, result = self.call('POST', '/v1/articles:validate', article(sourceUrl='http://insecure.example.com'))
        self.assertFalse(result['valid'])
        self.assertEqual(result['errors'][0]['field'], 'sourceUrl')
        status, result = self.call('POST', '/v1/articles:validate', {'titlePT': 'só isso'})
        self.assertFalse(result['valid'])
        self.assertEqual(self.cms.list(ADMIN, 'content')['items'], [])

    def test_upsert_is_idempotent_and_updates_by_key(self):
        first = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': article()}, 'idem-key-00001')
        again = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': article()}, 'idem-key-00001')
        self.assertEqual(first, again)
        self.assertEqual(len(self.cms.list(ADMIN, 'content')['items']), 1)
        self.assertEqual(self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': article(titlePT='Outro')}, 'idem-key-00001')[0], 409)
        updated = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'version': 1, 'data': article(titlePT='Outro')}, 'idem-key-00002')
        self.assertEqual((updated[0], updated[1]['version'], updated[1]['id']), (201, 2, first[1]['id']))
        self.assertEqual(self.call('POST', '/v1/articles', {'key': 'noticia-um', 'version': 1, 'data': article()}, 'idem-key-00003')[0], 409)
        self.assertEqual(self.call('POST', '/v1/articles', {'key': 'noticia-dois', 'data': article()}, 'short')[0], 422)

    def test_agent_cannot_smuggle_protected_or_unknown_fields(self):
        for data in (article(assetBase64='AAAA'), article(roles='anderzilla_admin'), article(sourceUrl='https://user:pw@example.com')):
            self.assertEqual(self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': data}, 'smuggle-key-1')[0], 422)
        self.assertEqual(self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': article(), 'status': 'approved'}, 'smuggle-key-2')[0], 422)
        self.assertEqual(self.call('POST', '/v1/offers', {'x': 1}, 'smuggle-key-3')[0], 404)

    def test_published_record_is_protected_from_silent_edit(self):
        media, art, submission = self.package()
        self.assertEqual(self.call('POST', f"/v1/submissions/{submission['id']}/approve", human=ADMIN)[0], 202)
        approved = self.cms.list(ADMIN, 'content')['items'][0]
        self.assertEqual(approved['status'], 'approved')
        blocked = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'version': approved['version'], 'data': article(titlePT='Mudou')}, 'edit-key-0001')
        self.assertEqual((blocked[0], blocked[1]['error']['code']), (409, 'published_record'))

    # ---- banners ----
    def test_banner_requires_internal_or_https_links_and_approved_image(self):
        status, media = self.media()
        banner = {'key': 'banner-um', 'imageMediaId': media['id'], 'titlePT': 'T', 'titleEN': 'T', 'linkPT': '/pt/produtos/', 'linkEN': '/en/produtos/', 'startsAt': '2026-10-30T00:00:00+00:00', 'order': 1}
        status, saved = self.call('POST', '/v1/banners', banner, 'banner-key-0001')
        self.assertEqual((status, saved['status']), (201, 'draft'))
        for link in ('javascript:alert(1)', '//evil.example.com', 'http://example.com', 'https://localhost/x'):
            self.assertEqual(self.call('POST', '/v1/banners', {**banner, 'key': 'banner-dois', 'linkPT': link}, 'banner-bad-' + str(len(link)) + 'zz')[0], 422, link)
        # draft image cannot back an approved banner
        with self.assertRaises(Error):
            self.cms.save(ADMIN, 'banners', None, saved['id'], 1, 'approve')

    # ---- media ----
    def test_media_by_base64_and_by_url(self):
        status, media = self.media()
        self.assertEqual((status, media['data']['mimeType'], media['data']['sourceUrl']), (201, 'image/webp', 'https://example.com/foto'))
        status, remote = self.call('POST', '/v1/media', {'sourceImageUrl': 'https://images.example.com/a/capa.png', 'altPT': 'a', 'altEN': 'b', 'credit': 'c', 'license': 'd', 'sourceUrl': 'https://example.com/p'}, 'media-key-0002')
        self.assertEqual(status, 201, remote)
        self.assertEqual(self.fetched, ['https://images.example.com/a/capa.png'])
        self.assertEqual(self.media(idem='media-key-0001')[1]['id'], media['id'])  # replay, no second upload
        for body in ({'contentBase64': png_b64()}, {'altPT': 'a', 'altEN': 'b', 'credit': 'c', 'license': 'd', 'sourceUrl': 'https://example.com/p'}):
            self.assertEqual(self.call('POST', '/v1/media', body, 'media-bad-key1')[0], 422)
        self.assertEqual(self.media(idem='media-bad-key2', contentBase64=base64.b64encode(b'not an image').decode())[0], 422)

    def test_fetcher_blocks_ssrf_and_unsafe_urls(self):
        public = lambda host, port, type=0: [(2, 1, 6, '', ('93.184.216.34', 443))]
        private = lambda host, port, type=0: [(2, 1, 6, '', ('10.0.0.5', 443))]
        metadata = lambda host, port, type=0: [(2, 1, 6, '', ('169.254.169.254', 443))]
        for url, resolver, code in (('http://images.example.com/a.png', public, 'invalid_url'), ('https://user:pw@images.example.com/a.png', public, 'invalid_url'),
                                    ('https://evil.example.org/a.png', public, 'host_not_allowed'), ('https://images.example.com.evil.org/a.png', public, 'host_not_allowed'),
                                    ('https://images.example.com/a.png', private, 'invalid_url'), ('https://images.example.com/a.png', metadata, 'invalid_url'),
                                    ('https://images.example.com:8443/a.png', public, 'invalid_url')):
            with self.assertRaises(Error) as caught:
                fetch_image(url, ['images.example.com'], resolver=resolver)
            self.assertEqual(caught.exception.code, code, url)
        with self.assertRaises(Error) as caught:
            fetch_image('https://images.example.com/a.png', [], resolver=public)
        self.assertEqual(caught.exception.code, 'host_not_allowed')

    # ---- submissions: review loop ----
    def test_review_loop_comment_resubmit_approve_and_release(self):
        media, art, submission = self.package()
        sid = submission['id']
        self.assertEqual((submission['status'], submission['round']), ('pending', 1))
        self.assertIn(f'/submissions/{sid}', submission['reviewUrl'])
        # the human needs a comment before sending changes back
        self.assertEqual(self.call('POST', f'/v1/submissions/{sid}/request-changes', human=ADMIN)[0], 422)
        status, comment = self.call('POST', f'/v1/submissions/{sid}/comments', {'collection': 'content', 'recordId': art['id'], 'field': 'titlePT', 'text': 'Deixe o título mais curto.'}, human=ADMIN)
        self.assertEqual(status, 201, comment)
        self.assertEqual(self.call('POST', f'/v1/submissions/{sid}/comments', {'collection': 'content', 'recordId': 'other', 'text': 'x'}, human=ADMIN)[0], 422)
        self.assertEqual(self.call('POST', f'/v1/submissions/{sid}/request-changes', human=ADMIN)[1]['status'], 'changes_requested')
        # the agent reads the corrections and resubmits the fixed draft
        status, listed = self.call('GET', f'/v1/submissions/{sid}/comments')
        self.assertEqual([c['text'] for c in listed['items']], ['Deixe o título mais curto.'])
        fixed = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'version': art['version'], 'data': article(titlePT='Título curto', coverMediaId=media['id'])}, 'article-key-0002')[1]
        status, again = self.call('POST', f'/v1/submissions/{sid}/resubmit', {'answeredCommentIds': [comment['id']], 'records': [{'collection': 'media', 'id': media['id'], 'version': media['version']}, {'collection': 'content', 'id': fixed['id'], 'version': fixed['version']}]}, 'resubmit-key-01')
        self.assertEqual((status, again['status'], again['round']), (200, 'pending', 2), again)
        self.assertTrue(self.call('GET', f'/v1/submissions/{sid}/comments')[1]['items'][0]['resolved'])
        # nothing is live before human approval
        self.assertEqual({row['status'] for row in self.cms.list(ADMIN, 'content')['items']}, {'draft'})
        status, release = self.call('POST', f'/v1/submissions/{sid}/approve', human=ADMIN)
        self.assertEqual((status, release['status']), (202, 'queued'), release)
        self.assertEqual({row['status'] for row in self.cms.list(ADMIN, 'content')['items']}, {'approved'})
        self.assertEqual(self.call('GET', f"/v1/releases/{release['id']}")[1]['status'], 'queued')
        self.assertEqual(self.call('GET', f'/v1/submissions/{sid}')[1]['status'], 'approved')
        snapshot = self.cms.releases(ADMIN, release['id'], True)
        self.assertEqual(len(snapshot['collections']['content']), 1)

    def test_approval_is_atomic_and_detects_stale_drafts(self):
        media, art, submission = self.package()
        sid = submission['id']
        # a draft edited after submission makes the package stale; nothing gets approved
        self.call('POST', '/v1/articles', {'key': 'noticia-um', 'version': art['version'], 'data': article(titlePT='Mudou depois', coverMediaId=media['id'])}, 'article-key-0009')
        status, error = self.call('POST', f'/v1/submissions/{sid}/approve', human=ADMIN)
        self.assertEqual((status, error['error']['code']), (409, 'stale_submission'))
        self.assertEqual({row['status'] for row in self.cms.list(ADMIN, 'content')['items'] + self.cms.list(ADMIN, 'media')['items']}, {'draft'})

    def test_failed_approval_reverts_everything(self):
        # an article missing required fields approves nothing, including the media approved before it
        status, media = self.media()
        status, art = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': {'titlePT': 'Incompleta'}}, 'article-key-0003')
        status, submission = self.call('POST', '/v1/submissions', {'records': [{'collection': 'media', 'id': media['id'], 'version': media['version']}, {'collection': 'content', 'id': art['id'], 'version': art['version']}]}, 'submit-key-0003')
        self.assertEqual(status, 201, submission)
        status, error = self.call('POST', f"/v1/submissions/{submission['id']}/approve", human=ADMIN)
        self.assertEqual((status, error['error']['code']), (422, 'incomplete_record'))
        self.assertEqual({row['status'] for row in self.cms.list(ADMIN, 'media')['items']}, {'draft'})
        self.assertEqual(self.call('GET', f"/v1/submissions/{submission['id']}")[1]['status'], 'pending')
        self.assertEqual(self.cms.releases(ADMIN)['items'], [])

    def test_agents_see_only_their_own_submissions(self):
        _, _, submission = self.package()
        other = 'Bearer ' + self.gateway.create_key(ADMIN, 'gemini-test')['key']
        self.assertEqual(self.call('GET', f"/v1/submissions/{submission['id']}", auth=other)[0], 404)
        self.assertEqual(self.call('GET', f"/v1/submissions/{submission['id']}/comments", auth=other)[0], 404)
        self.assertEqual(self.call('GET', f"/v1/submissions/{submission['id']}", human=ADMIN)[0], 200)

    def test_only_drafts_with_current_version_enter_a_package(self):
        media, art, submission = self.package()
        body = {'records': [{'collection': 'content', 'id': art['id'], 'version': art['version'] + 5}]}
        self.assertEqual(self.call('POST', '/v1/submissions', body, 'submit-key-0007')[0], 409)
        self.assertEqual(self.call('POST', '/v1/submissions', {'records': [{'collection': 'pages', 'id': 'x', 'version': 1}]}, 'submit-key-0008')[0], 403)

    def test_scope_limits_what_a_key_can_touch(self):
        narrow = 'Bearer ' + self.gateway.create_key(ADMIN, 'media-only', collections=['media'])['key']
        self.assertEqual(self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': article()}, 'scope-key-0001', auth=narrow)[0], 403)
        self.assertEqual(self.call('POST', '/v1/media', {'contentBase64': png_b64(), 'altPT': 'a', 'altEN': 'b', 'credit': 'c', 'license': 'd', 'sourceUrl': 'https://example.com/p'}, 'scope-key-0002', auth=narrow)[0], 201)


if __name__ == '__main__':
    unittest.main()
