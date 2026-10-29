"""The SQLite schema (tests, local) and the Azure SQL schema (production) must describe the same tables, and the
runtime user must be granted exactly what each table needs. Catches drift that would only fail after deployment."""
import re
import unittest
from pathlib import Path

HERE = Path(__file__).parent
RUNTIME_USER = 'anderzilla_cms_runtime'


def read(name):
    return (HERE / name).read_text(encoding='utf-8')


def split_top(body):
    parts, depth, current = [], 0, ''
    for char in body:
        depth += (char == '(') - (char == ')')
        if char == ',' and depth == 0:
            parts.append(current.strip())
            current = ''
        else:
            current += char
    parts.append(current.strip())
    return [part for part in parts if part]


def tables(sql, pattern):
    result = {}
    for match in re.finditer(pattern, sql, flags=re.S | re.I):
        name, body = match.group(1), match.group(2)
        columns = set()
        for part in split_top(body):
            if re.match(r'(CONSTRAINT|PRIMARY|UNIQUE)\b', part, flags=re.I):
                continue
            columns.add(part.split()[0].lower())
        result[name.lower()] = columns
    return result


def sqlite_tables():
    return tables(read('schema.sql'), r'CREATE TABLE IF NOT EXISTS (\w+)\((.*?)\);')


def azure_tables():
    return tables(read('schema.azure.sql'), r"IF OBJECT_ID\('(\w+)'\) IS NULL CREATE TABLE \1\((.*?)\);")


class SchemaParityTest(unittest.TestCase):
    def test_same_tables_and_columns(self):
        local, azure = sqlite_tables(), azure_tables()
        self.assertTrue(local, 'no SQLite tables parsed')
        self.assertEqual(set(local), set(azure))
        for name in local:
            self.assertEqual(local[name], azure[name], name)

    def test_same_indexes(self):
        local = set(re.findall(r'CREATE INDEX IF NOT EXISTS (\w+) ON', read('schema.sql')))
        azure = set(re.findall(r"IF NOT EXISTS \(SELECT 1 FROM sys\.indexes WHERE name='(\w+)'", read('schema.azure.sql')))
        self.assertEqual(local, azure)

    def test_schema_is_additive_and_idempotent(self):
        text = read('schema.azure.sql')
        for statement in [line for line in text.splitlines() if line.strip()]:
            self.assertRegex(statement, r'^IF (OBJECT_ID|NOT EXISTS)', statement[:60])
        self.assertNotRegex(text, r'(?i)\b(DROP|TRUNCATE|DELETE\s+FROM|ALTER\s+TABLE)\b')

    def test_runtime_grants_cover_every_table_and_forbid_destruction(self):
        grants = read('runtime-permissions.azure.sql')
        statements = [line.strip() for line in grants.splitlines() if line.strip() and not line.startswith('--')]
        for statement in statements:
            self.assertRegex(statement, rf'^(GRANT|DENY) .* TO {RUNTIME_USER};$', statement)
            self.assertNotRegex(statement, r'(?i)\b(db_owner|db_datawriter|CONTROL|ALTER|EXECUTE)\b')
        for table in azure_tables():
            self.assertTrue(any(s.startswith('GRANT SELECT') and f'dbo.{table}' in s for s in statements), f'{table}: no SELECT grant')
            self.assertTrue(any(s.startswith('DENY') and 'DELETE' in s and f'dbo.{table} ' in s + ' ' for s in statements), f'{table}: DELETE is not denied')
        # the append-only audit trail and revisions must never be updatable
        for table in ('cms_revisions', 'cms_audit', 'agent_requests', 'automation_commands'):
            self.assertTrue(any(s.startswith('DENY UPDATE, DELETE') and f'dbo.{table} ' in s + ' ' for s in statements), f'{table}: UPDATE is not denied')
        # API keys: only the document may change (revocation), never the stored hash
        self.assertTrue(any('UPDATE ON OBJECT::dbo.agent_keys(document)' in s for s in statements))
        self.assertFalse(any('UPDATE ON OBJECT::dbo.agent_keys ' in s + ' ' and s.startswith('GRANT') for s in statements))


if __name__ == '__main__':
    unittest.main()
