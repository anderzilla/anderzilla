"""Idempotent, visibly labelled demo examples. Never enables real rewards or partners."""
import argparse
import base64
import hashlib
import io
import uuid
from core import now, validate, validate_references
from storage import SQLiteStore, AzureSQLStore


def stable(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://anderzilla.com/cms-demo/' + name))


def examples():
    from PIL import Image, ImageDraw
    output = io.BytesIO()
    artwork = Image.new('RGB', (640, 360), '#142147')
    canvas = ImageDraw.Draw(artwork)
    canvas.rectangle((40, 45, 300, 75), fill='#c2ff36')
    canvas.ellipse((440, 150, 680, 390), fill='#ff58d4')
    canvas.text((50, 135), 'DEMO', fill='white', font_size=64)
    artwork.save(output, format='WEBP')
    asset = output.getvalue()
    sha = hashlib.sha256(asset).hexdigest()
    base = {'isDemo': True, 'summaryPT': 'Exemplo demonstrativo do CMS. Sem oferta ou evento real.', 'summaryEN': 'CMS demonstration example. No real offer or event.'}
    rows = [
        ('media', 'cover', {'titlePT': 'DEMO — fundo de exemplo', 'titleEN': 'DEMO — sample background', 'url': '/media/' + sha + '.webp', 'assetBase64': base64.b64encode(asset).decode(), 'assetSha256': sha, 'mimeType': 'image/webp', 'mediaType': 'image', 'width': 640, 'height': 360, 'altPT': 'Fundo azul demonstrativo, sem produto representado', 'altEN': 'Demo blue background, no product depicted', 'credit': 'AnderZilla — exemplo gerado para homologação', 'license': 'Arte demonstrativa própria AnderZilla'}),
        ('taxonomies', 'tag', {'titlePT': 'DEMO — laboratório', 'titleEN': 'DEMO — laboratory', 'slug': 'demo-laboratorio', 'kind': 'tag'}),
        ('content', 'article', {'titlePT': 'DEMO — como funciona uma pauta no AnderZilla', 'titleEN': 'DEMO — how an AnderZilla article works', 'bodyPT': '## Laboratório editorial\n\nEste texto demonstra o editor. **Não é uma notícia real.** Use título, fonte e uma imagem com crédito antes de publicar conteúdo real.', 'bodyEN': '## Editorial laboratory\n\nThis demonstrates the editor. **This is not real news.** Add a title, source and credited image before publishing real content.', 'category': 'curiosidades', 'sourceName': 'AnderZilla — demonstração interna', 'sourceUrl': 'https://anderzilla.com', 'publishedAt': '2026-09-10', 'slugPT': 'demo-pauta', 'slugEN': 'demo-article', 'author': 'AnderZilla', 'tags': stable('tag'), 'coverMediaId': stable('cover'), 'seoTitlePT': 'DEMO — laboratório editorial AnderZilla', 'seoTitleEN': 'DEMO — AnderZilla editorial laboratory', 'seoDescriptionPT': 'Exemplo demonstrativo do editor, sem notícia fictícia apresentada como real.', 'seoDescriptionEN': 'Editor demonstration, not a fictional news report presented as real.'}),
        ('pages', 'page', {'titlePT': 'DEMO — página institucional', 'titleEN': 'DEMO — information page', 'slug': 'demo-informacoes', 'bodyPT': 'Página demonstrativa para experimentar os blocos do CMS.', 'bodyEN': 'Demonstration page for trying CMS blocks.'}),
        ('events', 'event', {'titlePT': 'DEMO — encontro de teste, não agendado', 'titleEN': 'DEMO — test meetup, not scheduled', 'platform': 'twitch', 'url': 'https://www.twitch.tv/anderzillacwb', 'startsAt': '2099-01-01T20:00:00-03:00', 'endsAt': '2099-01-01T21:00:00-03:00', 'timezone': 'America/Sao_Paulo'}),
        ('offers', 'offer', {'titlePT': 'DEMO — apresentação do ForgeKit', 'titleEN': 'DEMO — ForgeKit presentation', 'url': 'https://anderzilla.gumroad.com/l/edkel', 'disclosurePT': 'Exemplo de apresentação. Produto próprio; consulte condições reais no Gumroad.', 'disclosureEN': 'Presentation example. Own product; real terms are available on Gumroad.'}),
        ('affiliates', 'affiliate', {'titlePT': 'DEMO — espaço de afiliado sem parceiro', 'titleEN': 'DEMO — affiliate slot with no partner', 'url': 'https://anderzilla.com', 'disclosurePT': 'Demonstração; não há parceiro, comissão ou oferta ativa.', 'disclosureEN': 'Demonstration; no partner, commission or active offer.', 'approvalReference': 'DEMO-NO-PARTNERSHIP'}),
        ('campaigns', 'campaign', {'titlePT': 'DEMO — campanha da própria comunidade', 'titleEN': 'DEMO — own community campaign', 'url': 'https://anderzilla.com', 'placement': 'home', 'startsAt': '2026-01-01T00:00:00Z', 'endsAt': '2099-01-01T00:00:00Z', 'disclosurePT': 'Espaço demonstrativo, sem anunciante contratado.', 'disclosureEN': 'Demo placement, no contracted advertiser.', 'approvalReference': 'DEMO-OWN-PROMOTION'}),
        ('missions', 'mission', {'titlePT': 'DEMO — missão do laboratório', 'titleEN': 'DEMO — laboratory mission', 'points': 10, 'verifier': 'demo-only', 'limit': 1, 'termsPT': 'Somente demonstração. Não concede saldo nem direito a resgate.', 'termsEN': 'Demonstration only. No balance credit or redemption rights.'}),
        ('rewards', 'reward', {'titlePT': 'DEMO — gadget ilustrativo sem estoque', 'titleEN': 'DEMO — illustrative gadget with no stock', 'points': 1000, 'category': 'gadgets', 'regions': 'BR', 'termsPT': 'Sem produto, estoque ou resgate real. Apenas demonstração da Store Points.', 'termsEN': 'No real product, stock or redemption. Store Points demonstration only.'}),
    ]
    category_names = {'games': ('games', 'games'), 'consoles': ('consoles', 'consoles'), 'celulares': ('celulares', 'phones'), 'ia': ('IA', 'AI'), 'gadgets': ('gadgets', 'gadgets')}
    for category, (pt, en) in category_names.items():
        rows.append(('content', 'article-' + category, {
            'titlePT': 'DEMO — laboratório de ' + pt,
            'titleEN': 'DEMO — ' + en + ' laboratory',
            'bodyPT': '## Exemplo editorial\n\nEsta é uma pauta demonstrativa sobre **' + pt + '** para testar o CMS. Não relata um lançamento, teste de produto ou notícia real.\n\n- Defina a pergunta do leitor.\n- Verifique fontes oficiais.\n- Separe fatos, opinião e publicidade.',
            'bodyEN': '## Editorial example\n\nThis is a **' + en + '** draft example for testing the CMS. It does not report a real launch, review or news event.\n\n- Define the reader question.\n- Verify official sources.\n- Separate facts, opinion and advertising.',
            'category': category, 'sourceName': 'AnderZilla — demonstração interna',
            'sourceUrl': 'https://anderzilla.com', 'publishedAt': '2026-09-10',
            'slugPT': 'demo-' + category, 'slugEN': 'demo-' + category + '-en',
            'author': 'AnderZilla', 'tags': stable('tag'), 'coverMediaId': stable('cover'),
            'mediaIds': stable('cover'),
            'seoTitlePT': 'DEMO — laboratório de ' + pt + ' AnderZilla',
            'seoTitleEN': 'DEMO — AnderZilla ' + en + ' laboratory',
            'seoDescriptionPT': 'Exemplo demonstrativo de conteúdo, sem alegações sobre produtos reais.',
            'seoDescriptionEN': 'Content demonstration with no claims about real products.',
        }))
    return [(collection, stable(key), {**base, **data}) for collection, key, data in rows]


def seed(store, approved=False):
    count = 0
    with store.transaction() as db:
        for collection, record_id, data in examples():
            if db.record(collection, record_id):
                continue  # Preserve every operator edit; never overwrite examples on rerun.
            validate(collection, data, approved=approved, internal=True)
            if approved:
                validate_references(db, collection, data, record_id)
            record = {'id': record_id, 'version': 1, 'status': 'approved' if approved else 'draft', 'data': data, 'updatedAt': now()}
            db.save_record(collection, record)
            db.audit('operator:demo-seed', 'seed_explicit_demo', collection, record_id, 1)
            count += 1
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--database')
    group.add_argument('--azure', action='store_true')
    parser.add_argument('--approve', action='store_true', help='Approve explicitly labelled demos for preview publication.')
    args = parser.parse_args()
    print('Seeded demo examples:', seed(AzureSQLStore() if args.azure else SQLiteStore(args.database), args.approve))
