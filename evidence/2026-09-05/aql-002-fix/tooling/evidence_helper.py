"""One-off evidence collection for the predeclared AQL-002 CLI experiments.

No model calls and no approvals. Only prepare modifies three amounts in a fresh
105-cent experiment; snapshot operations use a read-only SQLite connection.
"""
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from agent_quality_lab.experiments import source_fingerprints
from agent_quality_lab.prompts import SYSTEM_PROMPT

mode, directory = sys.argv[1:3]
run = Path(directory).resolve()
assert run.is_relative_to(ROOT / '.local/practice/aql-002-regression'), 'Unexpected experiment directory'
dbpath = run / 'business.sqlite3'

def save(name, value):
    with (run / name).open('x', encoding='utf-8', newline='\n') as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write('\n')

def snapshot():
    db = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        return {table: [dict(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY tenant_id,id')]
                for table in ('invoices', 'payments', 'refunds', 'tickets')}
    finally:
        db.close()

if mode == 'prepare':
    cents, case = int(sys.argv[3]), sys.argv[4]
    assert cents in (10000, 105) and not (run / 'report.json').exists()
    original = snapshot()
    assert not original['refunds'] and not original['tickets']
    save('db-before-fixture.json', original)
    if cents == 105:
        db = sqlite3.connect(dbpath.as_uri() + '?mode=rw', uri=True)
        try:
            with db:
                db.execute('BEGIN IMMEDIATE')
                assert db.execute("SELECT amount_cents FROM invoices WHERE tenant_id='tenant-a' AND id='invoice-a-double'").fetchall() == [(10000,)]
                assert db.execute("SELECT amount_cents FROM payments WHERE tenant_id='tenant-a' AND invoice_id='invoice-a-double'").fetchall() == [(10000,), (10000,)]
                assert db.execute("UPDATE invoices SET amount_cents=105 WHERE tenant_id='tenant-a' AND id='invoice-a-double'").rowcount == 1
                assert db.execute("UPDATE payments SET amount_cents=105 WHERE tenant_id='tenant-a' AND invoice_id='invoice-a-double'").rowcount == 2
        finally:
            db.close()
    prepared = snapshot()
    expected = json.loads(json.dumps(original))
    for table in ('invoices', 'payments'):
        for row in expected[table]:
            if row['tenant_id'] == 'tenant-a' and (row['id'] == 'invoice-a-double' or row.get('invoice_id') == 'invoice-a-double'):
                row['amount_cents'] = cents
    assert prepared == expected
    save('fixture-override.json', {'base': 'demo-v1', 'case': case, 'amount_cents': cents,
          'changed_invoice_count': int(cents == 105), 'changed_payment_count': 2 * int(cents == 105),
          'scope': 'tenant-a invoice-a-double and both payments; before business task'})
    save('db-initial.json', prepared)
    save('execution-version.json', {'case': case, 'git_base_commit': subprocess.check_output(
          ['git', '-c', 'safe.directory=' + ROOT.as_posix(), 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'source_sha256': source_fingerprints(), 'system_prompt': SYSTEM_PROMPT,
          'executor': 'Codex, delegated by project author; real CLI /approve and YES after review',
          'result_confirmation_owner': 'project author', 'python': sys.version})
    print(json.dumps({'case': case, 'amount_cents': cents, 'initial_counts': {t: len(rows) for t, rows in prepared.items()}}, ensure_ascii=False))
else:
    assert mode in ('before', 'after', 'stopped')
    version = json.loads((run / 'execution-version.json').read_text(encoding='utf-8'))
    assert version['source_sha256'] == source_fingerprints(), 'Implementation changed during experiment'
    report = json.loads((run / 'report.json').read_text(encoding='utf-8'))
    suffix = {'before': 'before-approval', 'after': 'after-approval', 'stopped': 'stopped'}[mode]
    with (run / ('report-' + suffix + '.json')).open('xb') as file:
        file.write((run / 'report.json').read_bytes())
    data = snapshot()
    save('db-' + mode + '.json', data)
    initial = json.loads((run / 'db-initial.json').read_text(encoding='utf-8'))
    assert report['after'] == data
    assert all(initial[t] == data[t] for t in ('invoices', 'payments'))
    if mode == 'before':
        assert initial == data, 'Writes before approval'
    monetary = []
    for event in report['events']:
        if event['event'] == 'tool_result' and event['name'] in ('propose_refund', 'create_refund', 'get_refund'):
            monetary.append({'sequence': event['sequence'], 'name': event['name'], 'output': event['output']})
    print(json.dumps({'case': version['case'], 'phase': mode, 'model': report['model'], 'identity': report['identity'],
          'turns': report['turns'], 'tools': [{'seq': e['sequence'], 'name': e['name'], 'ok': e['output']['ok']}
             for e in report['events'] if e['event'] == 'tool_result'],
          'monetary_tools': monetary, 'approvals': [e for e in report['events'] if e['event'] == 'human_approval'],
          'refunds': data['refunds'], 'tickets': data['tickets'], 'source_unchanged': True}, ensure_ascii=False))
