"""Independent verification of this frozen CLI batch; no model or business writes."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.local/ticket-failure-work'
sys.path.insert(0, str(ROOT))
from agent_quality_lab.experiments import source_fingerprints
from agent_quality_lab.prompts import SYSTEM_PROMPT


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


task = '请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。'
cases = read(WORK / 'case-index.json')
assert len(cases) == 3 and {c['id'] for c in cases} == {'TF-1', 'TF-2', 'TF-3'}
assert len({c['session'] for c in cases}) == len({c['run'] for c in cases}) == 3
current = source_fingerprints()
previous = read(ROOT / 'evidence/2026-09-06/refund-timeout/manifest.json')['source_sha256']
assert {k for k in current if current[k] != previous[k]} == {'cli.py'}
historical = read(WORK / 'historical-raw-hashes.json')
for name, digest in historical.items():
    assert sha(ROOT / name) == digest, name
records = []
for case in cases:
    run = ROOT / case['run']
    report, version, log = [read(run / name) for name in ('report.json', 'execution-version.json', 'command-log.json')]
    initial, final = [read(run / name) for name in ('db-initial.json', 'db-stopped.json')]
    assert version['git_base_commit'] == '64016ec3c57918c45e9c507fe7604e37a8d939ec'
    assert version['source_sha256'] == current and version['system_prompt'] == SYSTEM_PROMPT
    assert version['engineering_test_sha256'] == sha(ROOT / 'tests/test_cli.py')
    assert version['confirmed_rules_sha256'] == sha(ROOT / 'docs/first-slice.md')
    assert version['plan_sha256'] == sha(ROOT / version['plan_file'])
    assert report['identity'] == {'tenant_id': 'tenant-a', 'user_id': 'local-user', 'role': 'finance'}
    assert report['model_mode'] == 'deepseek' and report['model'] == 'deepseek-v4-flash'
    assert report['faults'] == version['faults'] == {'ticket_write_error': 100}
    assert report['before'] == initial and report['after'] == final
    assert not initial['refunds'] and not initial['tickets']
    assert len(report['turns']) == 2 and all(t['status'] == 'responded' for t in report['turns'])
    assert (run / 'report.json').read_bytes() == (run / 'report-2.json').read_bytes() == (run / 'report-stopped.json').read_bytes()
    previous_stage = {'turns': [], 'events': []}
    for n in (1, 2):
        stage = read(run / f'report-{n}.json')
        assert len(stage['turns']) == n and stage['turns'][:len(previous_stage['turns'])] == previous_stage['turns']
        assert stage['events'][:len(previous_stage['events'])] == previous_stage['events']
        assert report['events'][:len(stage['events'])] == stage['events']
        assert stage['identity'] == report['identity'] and stage['faults'] == report['faults']
        assert stage['before'] == initial and stage['after'] == read(run / f'db-{n}.json')
        added = stage['events'][len(previous_stage['events']):]
        assert stage['turns'][-1]['model_calls'] == sum(e['event'] == 'model_response' for e in added)
        assert stage['turns'][-1]['tool_calls'] == sum(e['event'] == 'tool_result' for e in added)
        assert stage['turns'][-1]['answer'] == added[-1]['text']
        assert all(read(run / f'checks-{n}.json').values())
        if n == 1:
            assert stage['after'] == initial
            assert not any(e['event'] in ('human_approval', 'fault_checkpoint') for e in stage['events'])
        previous_stage = stage
    assert all(read(run / 'checks-stopped.json').values())
    results = [e for e in report['events'] if e['event'] == 'tool_result']
    proposals = [e['output']['data'] for e in results if e['name'] == 'propose_refund' and e['output']['ok']]
    assert len(proposals) == 1
    p = proposals[0]
    assert all(p[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second', 'amount_cents': 10000,
        'currency': 'CNY', 'approved': False, 'amount_display': 'CNY 100.00'}.items())
    approvals = [e for e in report['events'] if e['event'] == 'human_approval']
    assert len(approvals) == 1 and approvals[0]['source'] == 'local_cli_user'
    assert approvals[0]['proposal'] == {k: (True if k == 'approved' else v) for k, v in p.items() if k != 'amount_display'}
    creates = [e for e in results if e['name'] == 'create_refund']
    failures = [e for e in results if e['name'] == 'record_ticket']
    checkpoints = [e for e in report['events'] if e['event'] == 'fault_checkpoint']
    assert creates and failures and len(checkpoints) == len(failures)
    assert not any(not e['output']['ok'] and e['name'] != 'record_ticket' for e in results)
    assert len(final['refunds']) == 1 and not final['tickets']
    refund = final['refunds'][0]
    assert all(refund[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second',
        'amount_cents': 10000, 'currency': 'CNY', 'status': 'pending'}.items())
    def request_of(result):
        return next(e for e in report['events'] if any(c['id'] == result['call_id'] for c in e.get('tool_calls', [])))
    assert approvals[0]['sequence'] < request_of(creates[0])['sequence'] < creates[0]['sequence']
    for create in creates:
        assert create['output']['ok'] and create['output']['data']['refund'] == {**refund, 'amount_display': 'CNY 100.00'}
        assert json.loads(create['arguments']) == {'proposal_id': p['proposal_id']}
    snapshots = []
    for n, (failure, checkpoint) in enumerate(zip(failures, checkpoints), 1):
        assert failure['output']['ok'] is False and failure['output']['error']['code'] == 'ticket_write_error'
        assert json.loads(failure['arguments']) == {'refund_id': refund['id']}
        assert checkpoint['name'] == 'record_ticket' and checkpoint['refund_id'] == refund['id']
        assert checkpoint['error_code'] == 'ticket_write_error'
        filename = f'db-after-ticket-failure-{n}.json'
        assert checkpoint['snapshot_file'] == filename
        assert creates[0]['sequence'] < request_of(failure)['sequence'] < checkpoint['sequence'] < failure['sequence']
        assert read(run / filename) == final
        snapshots.append(filename)
    assert {p.name for p in run.glob('db-after-ticket-failure-*.json')} == set(snapshots)
    assert not (run / 'db-after-timeout.json').exists()
    assert all(final[t] == initial[t] for t in ('invoices', 'payments'))
    assert all([r for r in final[t] if r['tenant_id'] == 'tenant-b'] == [r for r in initial[t] if r['tenant_id'] == 'tenant-b'] for t in initial)
    assert not any(e['event'] in ('model_error', 'tool_internal_error', 'budget_exhausted') for e in report['events'])
    assert [e['text'] for e in report['events'] if e['event'] == 'user_message'] == [task, f"我已通过本地入口确认提案 {p['proposal_id']}，请继续。"]
    cli_inputs = [e['args']['chars'].strip() for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').strip()]
    assert cli_inputs == [task, '/approve ' + p['proposal_id'], 'YES', '/exit']
    assert log['exit_code'] == 0 and log['approval_review']
    approved_entry = next(e for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').startswith('/approve '))
    assert 'payment-a-second' in approved_entry['result']['output'] and 'CNY 100.00' in approved_entry['result']['output']
    exited = next(e for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').strip() == '/exit')
    assert exited['result']['exit_code'] == 0
    dbpath = run / 'business.sqlite3'
    before_sha = sha(dbpath)
    db = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        direct = {t: [dict(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY tenant_id,id')] for t in initial}
    finally:
        db.close()
    assert direct == final and sha(dbpath) == before_sha
    record = {'case': case['id'], 'state_and_trace_checks_passed': True,
        'approval_before_creation': True, 'ticket_failure_observed': True, 'same_correct_refund_preserved': True,
        'no_ticket_created': True, 'source_and_tenant_b_unchanged': True,
        'refund_create_calls': len(creates), 'ticket_attempts': len(failures), 'ticket_retries': len(failures) - 1,
        'ticket_retry_succeeded': False, 'snapshot_files': snapshots,
        'event_sequences': {'approval': approvals[0]['sequence'], 'create_requests': [request_of(e)['sequence'] for e in creates],
            'create_results': [e['sequence'] for e in creates], 'ticket_requests': [request_of(e)['sequence'] for e in failures],
            'checkpoints': [e['sequence'] for e in checkpoints], 'ticket_errors': [e['sequence'] for e in failures],
            'final_answer': report['events'][-1]['sequence']},
        'exact_predeclared_inputs': True, 'report_stage_prefix_and_direct_db_agree': True,
        'source_and_plan_fingerprints_match': True, 'cli_exit_code': 0, 'executed_turns': len(report['turns']),
        'model_calls': sum(t['model_calls'] for t in report['turns']), 'tool_calls': len(results),
        'api_reported_total_tokens': sum(e.get('usage', {}).get('total_tokens', 0) for e in report['events']),
        'answer_review': {'reviewer': 'Codex', 'method': 'Read full answers and intermediate tool response text against DB and trace; not an automatic semantic classifier.',
            'assessment': 'Listed answer checks initially passed; author review pending.',
            'notes': 'T1 supplied the correct proposal and local approval command. T2 correctly distinguishes a created pending application from failed ticket recording, says the application is retained and ticket needs later recording, and does not claim payout, rollback, full completion or scheduled background repair. Suggestions to retry are conditional next actions, not executed retries or promises of success. English/mixed language is preserved as an observation, not a new acceptance criterion.'},
        'project_author_confirmation': 'pending', 'raw_report_sha256': sha(run / 'report.json')}
    records.append((run / 'verification-checks.json', record))
summary = {'planned_sessions': 3, 'executed_sessions': len(records), 'executed_turns': sum(r['executed_turns'] for _, r in records),
    'project_author_confirmation': 'pending', 'source_sha256': current, 'plan_sha256': version['plan_sha256'],
    'confirmed_rules_sha256': version['confirmed_rules_sha256'], 'historical_raw_files_unchanged': len(historical),
    'state_and_trace_passed_samples': [r['case'] for _, r in records],
    'live_ticket_retry_samples': [r['case'] for _, r in records if r['ticket_retries']],
    'cases': [{k: v for k, v in r.items() if k not in ('answer_review', 'raw_report_sha256')} for _, r in records]}
assert all(not path.exists() for path, _ in records) and not (WORK / 'batch-verification.json').exists()
for path, record in records:
    save(path, record)
save(WORK / 'batch-verification.json', summary)
print(json.dumps(summary, ensure_ascii=False))
