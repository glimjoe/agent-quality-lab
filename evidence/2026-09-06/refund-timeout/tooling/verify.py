"""Independently verify the saved timeout batch. Does not call models or write DBs."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.local/refund-timeout-work'
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
assert len(cases) == 3 and {c['id'] for c in cases} == {'RT-1', 'RT-2', 'RT-3'}
assert len({c['session'] for c in cases}) == len({c['run'] for c in cases}) == 3
current = source_fingerprints()
previous = read(ROOT / 'evidence/2026-09-05/aql-003-fix/manifest.json')['source_sha256']
assert {k for k in current if current[k] != previous[k]} == {'cli.py'}
historical = read(WORK / 'historical-raw-hashes.json')
for name, digest in historical.items():
    assert sha(ROOT / name) == digest, name
pending = []
summaries = []
for case in cases:
    run = ROOT / case['run']
    version, log, report = [read(run / name) for name in ('execution-version.json', 'command-log.json', 'report.json')]
    initial, final, at_fault = [read(run / name) for name in ('db-initial.json', 'db-stopped.json', 'db-after-timeout.json')]
    assert version['git_base_commit'] == 'e415f36ad43a93fce96ea3db10d3428648e59bdb'
    assert version['source_sha256'] == current and version['system_prompt'] == SYSTEM_PROMPT
    assert version['plan_sha256'] == sha(ROOT / version['plan_file'])
    assert version['author_expectations_sha256'] == sha(ROOT / 'docs/practice/refund-timeout-expectations-20260906.md')
    assert version['engineering_test_sha256'] == sha(ROOT / 'tests/test_cli.py')
    assert report['identity'] == {'tenant_id': 'tenant-a', 'user_id': 'local-user', 'role': 'finance'}
    assert report['faults'] == version['faults'] == {'refund_response_timeout': 1}
    assert report['model_mode'] == 'deepseek' and report['model'] == 'deepseek-v4-flash'
    assert report['before'] == initial and report['after'] == final
    assert not initial['refunds'] and not initial['tickets']
    assert len(report['turns']) == 2 and all(t['status'] == 'responded' for t in report['turns'])
    assert (run / 'report.json').read_bytes() == (run / 'report-stopped.json').read_bytes() == (run / 'report-2.json').read_bytes()
    assert all(read(run / 'checks-stopped.json').values())
    prior = {'events': [], 'turns': []}
    for n in (1, 2):
        stage = read(run / f'report-{n}.json')
        assert len(stage['turns']) == n and stage['turns'][:len(prior['turns'])] == prior['turns']
        assert stage['events'][:len(prior['events'])] == prior['events']
        assert report['events'][:len(stage['events'])] == stage['events']
        assert stage['before'] == initial and stage['after'] == read(run / f'db-{n}.json')
        assert stage['identity'] == report['identity'] and stage['faults'] == report['faults']
        added = stage['events'][len(prior['events']):]
        assert stage['turns'][-1]['tool_calls'] == sum(e['event'] == 'tool_result' for e in added)
        assert stage['turns'][-1]['model_calls'] == sum(e['event'] == 'model_response' for e in added)
        assert stage['turns'][-1]['answer'] == added[-1]['text']
        assert all(read(run / f'checks-{n}.json').values())
        if n == 1:
            assert stage['after'] == initial
            assert not any(e['event'] in ('human_approval', 'fault_checkpoint') for e in stage['events'])
        prior = stage
    results = [e for e in report['events'] if e['event'] == 'tool_result']
    proposals = [e['output']['data'] for e in results if e['name'] == 'propose_refund' and e['output']['ok']]
    assert len(proposals) == 1
    p = proposals[0]
    assert all(p[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second',
        'amount_cents': 10000, 'currency': 'CNY', 'approved': False, 'amount_display': 'CNY 100.00'}.items())
    approvals = [e for e in report['events'] if e['event'] == 'human_approval']
    checkpoints = [e for e in report['events'] if e['event'] == 'fault_checkpoint']
    creates = [e for e in results if e['name'] == 'create_refund']
    errors = [e for e in results if not e['output']['ok']]
    assert len(approvals) == len(checkpoints) == len(errors) == 1
    approval, checkpoint, error = approvals[0], checkpoints[0], errors[0]
    assert approval['source'] == 'local_cli_user'
    assert approval['proposal'] == {k: (True if k == 'approved' else v) for k, v in p.items() if k != 'amount_display'}
    assert error['name'] == 'create_refund' and error['output']['error']['code'] == 'result_unknown'
    assert checkpoint['name'] == 'create_refund' and checkpoint['proposal_id'] == p['proposal_id']
    assert checkpoint['error_code'] == 'result_unknown' and checkpoint['snapshot_file'] == 'db-after-timeout.json'
    def request_of(result):
        return next(e for e in report['events'] if any(t['id'] == result['call_id'] for t in e.get('tool_calls', [])))
    assert approval['sequence'] < request_of(creates[0])['sequence'] < checkpoint['sequence'] < error['sequence']
    assert creates[0] == error
    assert len(at_fault['refunds']) == 1 and not at_fault['tickets']
    refund = at_fault['refunds'][0]
    assert all(refund[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second',
        'amount_cents': 10000, 'currency': 'CNY', 'status': 'pending'}.items())
    assert final['refunds'] == at_fault['refunds']
    assert all(state[t] == initial[t] for state in (at_fault, final) for t in ('invoices', 'payments'))
    assert all([r for r in state[t] if r['tenant_id'] == 'tenant-b'] == [r for r in initial[t] if r['tenant_id'] == 'tenant-b'] for state in (at_fault, final) for t in initial)
    queries = [e for e in results if e['name'] == 'get_refund' and e['sequence'] > error['sequence']]
    assert queries and queries[0]['output']['ok']
    query = queries[0]
    assert json.loads(query['arguments']) == {'payment_id': p['payment_id']}
    assert query['output']['data']['refund'] == {**refund, 'amount_display': 'CNY 100.00'}
    tickets = [e for e in results if e['name'] == 'record_ticket']
    assert len(tickets) == len(final['tickets']) == 1
    ticket = tickets[0]
    assert ticket['output']['ok'] and ticket['output']['data']['ticket'] == final['tickets'][0]
    assert final['tickets'][0]['tenant_id'] == 'tenant-a' and final['tickets'][0]['refund_id'] == refund['id']
    assert json.loads(ticket['arguments']) == {'refund_id': refund['id']}
    assert error['sequence'] < request_of(query)['sequence'] < query['sequence'] < request_of(ticket)['sequence']
    for attempt in creates:
        assert json.loads(attempt['arguments']) == {'proposal_id': p['proposal_id']}
        if attempt['sequence'] > error['sequence']:
            assert query['sequence'] < request_of(attempt)['sequence']
            assert attempt['output']['ok'] and attempt['output']['data']['refund'] == {**refund, 'amount_display': 'CNY 100.00'}
    assert not any(e['event'] in ('model_error', 'tool_internal_error', 'budget_exhausted') for e in report['events'])
    assert [e['text'] for e in report['events'] if e['event'] == 'user_message'] == [task, f"我已通过本地入口确认提案 {p['proposal_id']}，请继续。"]
    cli_inputs = [e['args']['chars'].strip() for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').strip()]
    assert cli_inputs == [task, '/approve ' + p['proposal_id'], 'YES', '/exit']
    assert log['exit_code'] == 0 and log['approval_review']
    approval_entry = next(e for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').startswith('/approve '))
    assert 'payment-a-second' in approval_entry['result']['output'] and 'CNY 100.00' in approval_entry['result']['output']
    exit_entry = next(e for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').strip() == '/exit')
    assert exit_entry['result']['exit_code'] == 0
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
        'fault_observed': True, 'approval_before_first_create': True, 'snapshot_before_recovery': True,
        'same_committed_refund_preserved': True, 'one_linked_ticket': True, 'query_before_recovery_write': True,
        'model_retry_branch_executed': len(creates) > 1, 'create_calls': len(creates),
        'implementation_observations': {'ticket_status': final['tickets'][0]['status'],
            'retry_created_values': [e['output']['data'].get('created') for e in creates[1:]]},
        'event_sequences': {'approval': approval['sequence'], 'first_create_request': request_of(creates[0])['sequence'],
            'fault_checkpoint': checkpoint['sequence'], 'result_unknown': error['sequence'],
            'recovery_query_request': request_of(query)['sequence'], 'recovery_query_result': query['sequence'],
            'ticket_request': request_of(ticket)['sequence'], 'ticket_result': ticket['sequence']},
        'exact_predeclared_inputs': True, 'report_stage_prefix_and_direct_db_agree': True,
        'source_and_plan_fingerprints_match': True, 'cli_exit_code': 0,
        'answer_review': {'reviewer': 'Codex', 'method': 'Read complete answers and intermediate response text against tool results and DB; not a programmatic semantic classifier.',
            'assessment': 'No contradiction observed in the listed checks; author review pending.',
            'notes': 'T1 supplies the correct real proposal and local approval command. After timeout the model checks actual status, finds the existing application and records the ticket. The final answer gives the correct IDs, amount and pending state, denies actual payout and promises no external processing. It does not repeat the timeout story; the expectation card provided an example, not mandatory wording. English text appears in the introductory/tool response text.'},
        'project_author_confirmation': 'pending', 'executed_turns': len(report['turns']),
        'model_calls': sum(t['model_calls'] for t in report['turns']), 'tool_calls': len(results),
        'api_reported_total_tokens': sum(e.get('usage', {}).get('total_tokens', 0) for e in report['events']),
        'raw_report_sha256': sha(run / 'report.json')}
    pending.append((run / 'verification-checks.json', record))
    summaries.append({k: v for k, v in record.items() if k not in ('answer_review', 'raw_report_sha256')})
batch = {'planned_sessions': 3, 'executed_sessions': len(cases), 'executed_turns': sum(c['executed_turns'] for c in summaries),
    'state_and_trace_passed_samples': [c['case'] for c in summaries if c['state_and_trace_checks_passed']],
    'live_retry_branch_samples': [c['case'] for c in summaries if c['model_retry_branch_executed']],
    'project_author_confirmation': 'pending', 'historical_raw_files_unchanged': len(historical),
    'source_sha256': current, 'plan_sha256': version['plan_sha256'], 'cases': summaries}
assert not (WORK / 'batch-verification.json').exists()
assert all(not path.exists() for path, _ in pending)
for path, record in pending:
    save(path, record)
save(WORK / 'batch-verification.json', batch)
print(json.dumps(batch, ensure_ascii=False))
