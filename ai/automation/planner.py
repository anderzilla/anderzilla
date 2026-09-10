"""Local workflow planner: no network, credentials or cloud execution."""
import argparse
import json
import re
from datetime import date
from decimal import Decimal

WORKFLOWS = {
    'editorial-package': 2, 'offer-check': 2, 'live-overlay': 2,
    'media-cuts': 10, 'seo-audit': 2, 'report-weekly': 2,
    'report-monthly': 2, 'report-custom': 2,
}

def plan(workflow, start=None, end=None, media_id=None, estimated_brl='0'):
    if workflow not in WORKFLOWS:
        raise ValueError('Unknown workflow')
    amount = Decimal(estimated_brl)
    if not amount.is_finite() or amount < 0 or amount > WORKFLOWS[workflow]:
        raise ValueError('Estimate outside planning envelope')
    if workflow.startswith('report-') and (not start or not end):
        raise ValueError('Reports require explicit start and exclusive end')
    if bool(start) != bool(end):
        raise ValueError('Provide both dates')
    if start and date.fromisoformat(start) >= date.fromisoformat(end):
        raise ValueError('End must follow start')
    if workflow == 'media-cuts' and not media_id:
        raise ValueError('Media object ID required')
    if media_id and not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', media_id):
        raise ValueError('Paths and URLs are not media IDs')
    return dict(schema_version=1, workflow=workflow, mode='dry-run', dispatch=False,
                estimated_brl=str(amount), start=start, end_exclusive=end,
                timezone='America/Sao_Paulo', media_id=media_id,
                prerequisites=['CMS authorization', 'idempotency key',
                               'budget reservation', 'configured worker'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workflow', choices=WORKFLOWS)
    for argument in ['start', 'end', 'media-id', 'estimated-brl']:
        parser.add_argument('--' + argument, default='0' if argument == 'estimated-brl' else None)
    try:
        print(json.dumps(plan(**vars(parser.parse_args())), indent=2))
    except (ValueError, ArithmeticError) as error:
        parser.error(str(error))
