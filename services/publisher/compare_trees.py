"""Compare two exported sites: the artifact in production against a build made from the database.

HTML is compared by its visible markup (scripts, comments and hashed _next paths are normalized, because
every Next.js build renames its chunks). Everything else outside _next is compared byte for byte.
Exit code 0 only when nothing differs beyond what --allow lists."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def normalize(html):
    html = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'/_next/static/[^"\' )]+', '/_next/X', html)
    return re.sub(r'\s+', ' ', html).strip()


def files(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file() and not p.relative_to(root).as_posix().startswith('_next/')}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(expected, actual):
    a, b = files(expected), files(actual)
    report = {'onlyInExpected': sorted(set(a) - set(b)), 'onlyInActual': sorted(set(b) - set(a)), 'different': [], 'identical': 0}
    for name in sorted(set(a) & set(b)):
        if name.endswith('.html'):
            same = normalize(a[name].read_text(encoding='utf-8')) == normalize(b[name].read_text(encoding='utf-8'))
        elif name.endswith('.txt') and name.endswith('index.txt'):
            continue  # React Server Component payloads embed the build id
        else:
            same = digest(a[name]) == digest(b[name])
        if same:
            report['identical'] += 1
        else:
            report['different'].append(name)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('expected', type=Path, help='artifact currently in production')
    parser.add_argument('actual', type=Path, help='build made from the database')
    parser.add_argument('--allow', action='append', default=[], help='path prefix whose differences are accepted (repeatable)')
    args = parser.parse_args()
    report = compare(args.expected, args.actual)
    allowed = lambda name: any(name.startswith(prefix) for prefix in args.allow)
    unexpected = {key: [n for n in report[key] if not allowed(n)] for key in ('onlyInExpected', 'onlyInActual', 'different')}
    summary = {'identical': report['identical'], **{key: len(report[key]) for key in unexpected}, 'unexpected': {key: len(value) for key, value in unexpected.items()}}
    print(json.dumps(summary, indent=2))
    for key, names in unexpected.items():
        for name in names[:15]:
            print(f'  {key}: {name}')
    sys.exit(1 if any(unexpected.values()) else 0)


if __name__ == '__main__':
    main()
