"""Authorized operational snapshots; disconnected financial sources remain unavailable."""
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from core import Error, require, now

LIMIT = 10000


def period(query):
    try:
        zone = ZoneInfo(query.get('timezone', 'America/Sao_Paulo'))
        start_day, end_day = date.fromisoformat(query['start']), date.fromisoformat(query['end'])
        if not 0 < (end_day - start_day).days <= 366:
            raise ValueError()
        start = datetime.combine(start_day, time.min, zone).astimezone(timezone.utc)
        end = datetime.combine(end_day, time.min, zone).astimezone(timezone.utc)
        return start.isoformat(), end.isoformat(), zone.key
    except (KeyError, ValueError, ZoneInfoNotFoundError):
        raise Error(422, 'invalid_period', 'Informe início e fim exclusivo (YYYY-MM-DD), até 366 dias, e fuso IANA válido.')


def csv_cell(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else text


def operations(cms, principal, query, environment):
    require(principal)
    if not {'anderzilla_admin', 'anderzilla_commercial'}.intersection(principal.get('roles', [])):
        raise Error(403, 'forbidden', 'Relatório disponível para administração e operação comercial.')
    start, end, zone = period(query)
    with cms.store.transaction() as db:
        prefix = f'SELECT TOP {LIMIT + 1}' if db.sql_server else 'SELECT'
        suffix = '' if db.sql_server else f' LIMIT {LIMIT + 1}'
        rows = db.execute(prefix + ' document FROM automation_runs WHERE environment=? AND created_at>=? AND created_at<? ORDER BY created_at,id' + suffix, (environment, start, end)).fetchall()
    seen, items = set(), []
    for raw in rows[:LIMIT]:
        row = json.loads(raw[0])
        if row['id'] in seen:
            continue
        seen.add(row['id'])
        items.append({key: row.get(key, '') for key in ('id', 'processId', 'status', 'createdAt', 'updatedAt')})
    complete = len(rows) <= LIMIT
    snapshot = {
        'generatedAt': now(), 'environment': environment,
        'period': {'start': query['start'], 'endExclusive': query['end'], 'timezone': zone, 'startUTC': start, 'endUTC': end},
        'source': 'CMS automation_runs', 'coverage': {'complete': complete, 'maximumRows': LIMIT, 'observedRuns': len(items), 'note': 'Execuções registradas no CMS; não mede audiência, cliques, conversões ou receita.'},
        'statusCounts': dict(Counter(row['status'] for row in items)),
        'financial': {'available': False, 'currencies': [], 'reason': 'Nenhuma fonte financeira conciliada conectada.'},
        'audience': {'available': False}, 'items': items,
    }
    snapshot['sha256'] = hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(['source', snapshot['source'], 'timezone', zone, 'startUTC', start, 'endExclusiveUTC', end])
    writer.writerow(['coverage', 'complete' if complete else 'truncated', 'financial', 'unavailable'])
    fields = ('id', 'processId', 'status', 'createdAt', 'updatedAt')
    writer.writerow(fields)
    for row in items:
        writer.writerow([csv_cell(row[key]) for key in fields])
    return {'snapshot': snapshot, 'csv': stream.getvalue()}
