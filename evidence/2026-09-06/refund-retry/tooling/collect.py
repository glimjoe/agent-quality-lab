"""Read-only stage collector for the frozen same-proposal refund retry batch."""
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
assert run.is_relative_to(ROOT / '.local/practice/refund-retry')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(name, value):
    with (run / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def test_fingerprints():
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted((ROOT / 'tests').rglob('*.py'))}


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
        'source_sha256': source_fingerprints(), 'test_sha256': test_fingerprints(), 'system_prompt': SYSTEM_PROMPT,
        'plan_file': 'tests/refund-retry-test-cases.md', 'plan_sha256': sha(ROOT / 'tests/refund-retry-test-cases.md'),
        'confirmed_rules_sha256': sha(ROOT / 'docs/first-slice.md'), 'python': sys.version,
        'model': settings.model, 'base_url': settings.base_url, 'fixture': 'demo-v1; no data modifications', 'faults': {},
        'request_configuration': {'temperature': 0, 'thinking': {'type': 'disabled'}, 'tool_choice': 'auto',
            'max_tokens': 2048, 'http_timeout_seconds': 45, 'max_model_calls_per_turn': 8, 'max_tool_calls_per_turn': 12}})
    print(json.dumps({'initialized': sys.argv[3], 'plan_sha256': sha(ROOT / 'tests/refund-retry-test-cases.md')}))
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
        'test_fingerprints_unchanged': version['test_sha256'] == test_fingerprints(),
        'plan_unchanged': version['plan_sha256'] == sha(ROOT / version['plan_file']),
        'identity_unchanged': report['identity'] == {'tenant_id': 'tenant-a', 'user_id': 'local-user', 'role': 'finance'},
        'no_injected_faults': report['faults'] == report['remaining_faults'] == {},
        'no_fault_control_or_checkpoint': not any(e['event'] in ('fault_control', 'fault_checkpoint') for e in report['events']),
        'report_matches_direct_db': report['after'] == data, 'initial_matches_report': report['before'] == initial,
        'all_turns_responded': all(t['status'] == 'responded' for t in report['turns']),
        'source_records_unchanged': all(data[t] == initial[t] for t in ('invoices', 'payments')),
        'one_correct_proposal': len(proposals) == 1 and all(proposals[0][k] == v for k, v in {
            'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second', 'amount_cents': 10000,
            'currency': 'CNY', 'amount_display': 'CNY 100.00', 'approved': False}.items())}
    observations = {}
    if len(report['turns']) == 1:
        checks['no_write_or_approval'] = data == initial and not approvals
    else:
        checks['one_approval'] = len(approvals) == 1
        checks['one_correct_refund'] = len(data['refunds']) == 1 and all(data['refunds'][0][k] == v for k, v in {
            'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second', 'amount_cents': 10000, 'currency': 'CNY', 'status': 'pending'}.items())
        checks['one_associated_ticket'] = len(data['tickets']) == len(data['refunds']) == 1 and data['tickets'][0]['tenant_id'] == 'tenant-a' and data['tickets'][0]['refund_id'] == data['refunds'][0]['id']
        if len(report['turns']) == 3:
            before_retry = read(run / 'report-2.json')
            checks['all_business_records_unchanged_after_repeat'] = data == read(run / 'db-2.json')
            extra = report['events'][len(before_retry['events']):]
            retried = [e for e in extra if e['event'] == 'tool_result' and e['name'] == 'create_refund']
            observations = {'create_retry_observed': bool(retried), 'create_retry_calls': len(retried),
                'retry_used_original_proposal': bool(retried) and len(proposals) == 1 and all(json.loads(e['arguments']) == {'proposal_id': proposals[0]['proposal_id']} for e in retried),
                'all_retry_results_same_refund': bool(retried) and len(before_retry['after']['refunds']) == 1 and all(e['output'].get('data', {}).get('refund') == {**before_retry['after']['refunds'][0], 'amount_display': 'CNY 100.00'} and e['output']['ok'] for e in retried),
                'create_retry_result_sequences': [e['sequence'] for e in retried]}
    save('checks-' + phase + '.json', {'state_checks': checks, 'call_coverage_observations': observations})
    print(json.dumps({'case': version['case'], 'turn_count': len(report['turns']), 'state_checks': checks,
        'call_coverage_observations': observations, 'proposal': proposals, 'latest_turn': report['turns'][-1],
        'tool_results': [{'seq': e['sequence'], 'name': e['name'], 'arguments': e['arguments'], 'output': e['output']} for e in results],
        'refunds': data['refunds'], 'tickets': data['tickets']}, ensure_ascii=False))
