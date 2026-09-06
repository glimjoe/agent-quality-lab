"""Read-only CLI evidence collector for the frozen ticket failure exercise."""
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from agent_quality_lab.experiments import source_fingerprints
from agent_quality_lab.models import Settings
from agent_quality_lab.prompts import SYSTEM_PROMPT

mode, directory = sys.argv[1:3]
run = Path(directory).resolve()
assert run.is_relative_to(ROOT / '.local/practice/ticket-failure')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(name, value):
    with (run / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def snapshot():
    path = run / 'business.sqlite3'
    before_sha = sha(path)
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        data = {t: [dict(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY tenant_id,id')]
                for t in ('invoices', 'payments', 'refunds', 'tickets')}
    finally:
        db.close()
    assert sha(path) == before_sha
    return data


if mode == 'init':
    assert not (run / 'report.json').exists()
    settings = Settings.load()
    assert settings.model == 'deepseek-v4-flash' and settings.base_url == 'https://api.deepseek.com'
    save('db-initial.json', snapshot())
    save('execution-version.json', {'case': sys.argv[3], 'executor': 'Codex; delegated by project author',
        'project_author_confirmation': 'pending',
        'git_base_commit': subprocess.check_output(['git', '-c', 'safe.directory=' + ROOT.as_posix(), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': source_fingerprints(), 'system_prompt': SYSTEM_PROMPT,
        'plan_file': 'tests/ticket-failure-test-cases.md', 'plan_sha256': sha(ROOT / 'tests/ticket-failure-test-cases.md'),
        'confirmed_rules_sha256': sha(ROOT / 'docs/first-slice.md'),
        'engineering_test_sha256': sha(ROOT / 'tests/test_cli.py'), 'python': sys.version,
        'model': settings.model, 'base_url': settings.base_url,
        'fixture': 'demo-v1; no data modifications', 'faults': {'ticket_write_error': 100}})
    print(json.dumps({'initialized': sys.argv[3], 'source_sha256': source_fingerprints()}))
else:
    assert mode in ('turn', 'stop')
    phase = sys.argv[3] if mode == 'turn' else 'stopped'
    original = (run / 'report.json').read_bytes()
    with (run / ('report-' + phase + '.json')).open('xb') as stream:
        stream.write(original)
    report = json.loads(original)
    data, initial, version = snapshot(), read(run / 'db-initial.json'), read(run / 'execution-version.json')
    save('db-' + phase + '.json', data)
    results = [e for e in report['events'] if e['event'] == 'tool_result']
    proposals = [e['output']['data'] for e in results if e['name'] == 'propose_refund' and e['output']['ok']]
    approvals = [e for e in report['events'] if e['event'] == 'human_approval']
    checks = {'source_fingerprints_unchanged': version['source_sha256'] == source_fingerprints(),
        'plan_unchanged': version['plan_sha256'] == sha(ROOT / version['plan_file']),
        'identity_unchanged': report['identity'] == {'tenant_id': 'tenant-a', 'user_id': 'local-user', 'role': 'finance'},
        'fault_configuration_matches': report['faults'] == version['faults'],
        'report_matches_direct_db': report['after'] == data,
        'initial_matches_report': report['before'] == initial,
        'all_turns_responded': all(t['status'] == 'responded' for t in report['turns']),
        'source_records_unchanged': all(data[t] == initial[t] for t in ('invoices', 'payments'))}
    if len(report['turns']) == 1:
        checks.update({'no_write_or_approval': data == initial and not approvals,
            'one_correct_unapproved_proposal': len(proposals) == 1 and all(proposals[0][k] == v for k, v in {
                'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second', 'amount_cents': 10000,
                'currency': 'CNY', 'amount_display': 'CNY 100.00', 'approved': False}.items())})
    else:
        failures = [e for e in results if e['name'] == 'record_ticket' and e['output'].get('error', {}).get('code') == 'ticket_write_error']
        snapshots = [read(path) for path in sorted(run.glob('db-after-ticket-failure-*.json'))]
        checks['ticket_failure_observed'] = bool(failures)
        checks['one_snapshot_per_failure'] = bool(snapshots) and len(snapshots) == len(failures)
        checks['one_approval'] = len(approvals) == 1
        checks['one_correct_refund'] = len(data['refunds']) == 1 and all(data['refunds'][0][k] == v for k, v in {
            'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second', 'amount_cents': 10000, 'currency': 'CNY', 'status': 'pending'}.items())
        checks['no_tickets'] = not data['tickets']
        checks['no_successful_ticket_result'] = not any(e['name'] == 'record_ticket' and e['output']['ok'] for e in results)
        checks['failed_attempts_preserve_final_state'] = bool(snapshots) and all(s == data for s in snapshots)
    save('checks-' + phase + '.json', checks)
    print(json.dumps({'case': version['case'], 'turn_count': len(report['turns']), 'checks': checks,
        'proposal': proposals, 'latest_turn': report['turns'][-1],
        'tool_results': [{'seq': e['sequence'], 'name': e['name'], 'arguments': e['arguments'], 'output': e['output']} for e in results],
        'refunds': data['refunds'], 'tickets': data['tickets']}, ensure_ascii=False))
