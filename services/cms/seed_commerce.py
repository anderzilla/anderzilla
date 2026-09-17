"""Create the documented ForgeKit as an idempotent draft; never approve or deploy."""
import argparse
from pathlib import Path
from core import CMS
from storage import SQLiteStore

FORGEKIT = {
    'titlePT': 'ForgeKit', 'titleEN': 'ForgeKit', 'slug': 'forgekit',
    'summaryPT': 'Produto digital próprio AnderZilla, entregue pela Gumroad.',
    'summaryEN': 'An AnderZilla digital product, delivered through Gumroad.',
    'bodyPT': 'Compra única: ZIP e GETTING_STARTED. Consulte condições, conteúdo e suporte na loja antes da compra.',
    'bodyEN': 'One-time purchase: ZIP and GETTING_STARTED. Check contents, terms and support in the store before purchasing.',
    'market': 'intl', 'currency': 'USD', 'status': 'active', 'priceMinor': 14900,
    'store': 'Gumroad', 'ctaUrl': 'https://anderzilla.gumroad.com/l/edkel',
    'demoUrl': 'https://forgekit-kwzn5potra-rj.a.run.app', 'disclosureKey': 'own-product',
    'disclosurePT': 'Produto próprio AnderZilla. O checkout e as condições finais são da Gumroad.',
    'disclosureEN': 'An AnderZilla product. Gumroad provides checkout and final purchase terms.',
}


def seed(cms, principal):
    existing = cms.list(principal, 'products')['items']
    if any(row['data'].get('slug') == 'forgekit' for row in existing):
        return None
    return cms.save(principal, 'products', FORGEKIT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    args = parser.parse_args()
    record = seed(CMS(SQLiteStore(args.database)), {'id': 'local-commerce-import', 'roles': ['anderzilla_admin']})
    print('ForgeKit draft created; review, approve and publish separately.' if record else 'ForgeKit exists; unchanged.')
