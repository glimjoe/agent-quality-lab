"""Verify evidence consistency and actual coverage; never equate safe data with retry coverage."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.local/refund-retry-work'
sys.path.insert(0, str(ROOT))
from agent_quality_lab.experiments import source_fingerprints
from agent_quality_lab.prompts import SYSTEM_PROMPT

read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

task = '请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。'
cases = read(WORK / 'case-index.json')
assert len(cases) == 3 and {c['id'] for c in cases} == {'FR-1', 'FR-2', 'FR-3'}
assert len({c['session'] for c in cases}) == len({c['run'] for c in cases}) == 3
current = source_fingerprints()
tests = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted((ROOT / 'tests').rglob('*.py'))}
baseline = read(WORK / 'engineering-baseline.json')
assert current == baseline['source_sha256'] and tests == baseline['test_sha256']
historical = read(WORK / 'historical-raw-hashes.json')
for name, digest in historical.items():
    assert sha(ROOT / name) == digest, name
records = []
for case in cases:
    run = ROOT / case['run']
    report, version, log = [read(run / n) for n in ('report.json', 'execution-version.json', 'command-log.json')]
    initial, normal, final = [read(run / n) for n in ('db-initial.json', 'db-2.json', 'db-stopped.json')]
    assert version['git_base_commit'] == 'f8c87e9023c89e95c32889d289590278f6d69559'
    assert version['source_sha256'] == current and version['test_sha256'] == tests and version['system_prompt'] == SYSTEM_PROMPT
    assert version['plan_sha256'] == sha(ROOT / version['plan_file'])
    assert version['confirmed_rules_sha256'] == sha(ROOT / 'docs/first-slice.md')
    assert report['identity'] == {'tenant_id': 'tenant-a', 'user_id': 'local-user', 'role': 'finance'}
    assert report['model_mode'] == 'deepseek' and report['model'] == version['model'] == 'deepseek-v4-flash'
    assert version['base_url'] == 'https://api.deepseek.com'
    assert version['request_configuration'] == {'temperature': 0, 'thinking': {'type': 'disabled'}, 'tool_choice': 'auto',
        'max_tokens': 2048, 'http_timeout_seconds': 45, 'max_model_calls_per_turn': 8, 'max_tool_calls_per_turn': 12}
    assert report['faults'] == report['remaining_faults'] == version['faults'] == {}
    assert report['before'] == initial and report['after'] == final
    assert not initial['refunds'] and not initial['tickets']
    assert len(report['turns']) == 3 and all(t['status'] == 'responded' for t in report['turns'])
    assert (run / 'report.json').read_bytes() == (run / 'report-3.json').read_bytes() == (run / 'report-stopped.json').read_bytes()
    previous = {'turns': [], 'events': []}
    for n in (1, 2, 3):
        stage = read(run / f'report-{n}.json')
        assert len(stage['turns']) == n and stage['turns'][:len(previous['turns'])] == previous['turns']
        assert stage['events'][:len(previous['events'])] == previous['events']
        assert report['events'][:len(stage['events'])] == stage['events']
        assert stage['before'] == initial and stage['after'] == read(run / f'db-{n}.json')
        assert stage['identity'] == report['identity'] and stage['faults'] == stage['remaining_faults'] == {}
        added = stage['events'][len(previous['events']):]
        assert stage['turns'][-1]['model_calls'] == sum(e['event'] == 'model_response' for e in added) <= 8
        assert stage['turns'][-1]['tool_calls'] == sum(e['event'] == 'tool_result' for e in added) <= 12
        assert stage['turns'][-1]['answer'] == added[-1]['text']
        assert all(read(run / f'checks-{n}.json')['state_checks'].values())
        if n == 1:
            assert stage['after'] == initial and not any(e['event'] == 'human_approval' for e in stage['events'])
        previous = stage
    assert all(read(run / 'checks-stopped.json')['state_checks'].values())
    events = report['events']
    assert [e['sequence'] for e in events] == list(range(1, len(events) + 1))
    results = [e for e in events if e['event'] == 'tool_result']
    requests = [(e, c) for e in events for c in e.get('tool_calls', [])]
    assert len(requests) == len(results) and len({e['call_id'] for e in results}) == len(results)
    def request_of(result):
        pairs = [(e, c) for e, c in requests if c['id'] == result['call_id']]
        assert len(pairs) == 1
        event, call = pairs[0]
        assert event['sequence'] < result['sequence'] and call['name'] == result['name'] and call['arguments'] == result['arguments']
        return event
    for result in results:
        request_of(result)
    proposals = [e['output']['data'] for e in results if e['name'] == 'propose_refund' and e['output']['ok']]
    assert len(proposals) == 1
    proposal = proposals[0]
    assert all(proposal[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second', 'amount_cents': 10000,
        'currency': 'CNY', 'approved': False, 'amount_display': 'CNY 100.00'}.items())
    approvals = [e for e in events if e['event'] == 'human_approval']
    assert len(approvals) == 1 and approvals[0]['source'] == 'local_cli_user'
    assert approvals[0]['proposal'] == {k: (True if k == 'approved' else v) for k, v in proposal.items() if k != 'amount_display'}
    creates = [e for e in results if e['name'] == 'create_refund']
    tickets = [e for e in results if e['name'] == 'record_ticket']
    assert creates and tickets and all(e['output']['ok'] for e in results)
    assert normal == final and len(final['refunds']) == len(final['tickets']) == 1
    refund, ticket = final['refunds'][0], final['tickets'][0]
    assert all(refund[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second', 'amount_cents': 10000,
        'currency': 'CNY', 'status': 'pending'}.items())
    assert ticket['tenant_id'] == refund['tenant_id'] and ticket['refund_id'] == refund['id']
    assert approvals[0]['sequence'] < request_of(creates[0])['sequence'] < creates[0]['sequence'] < request_of(tickets[0])['sequence']
    for create in creates:
        assert json.loads(create['arguments']) == {'proposal_id': proposal['proposal_id']}
        assert create['output']['data']['refund'] == {**refund, 'amount_display': 'CNY 100.00'}
    for result in tickets:
        assert json.loads(result['arguments']) == {'refund_id': refund['id']} and result['output']['data']['ticket'] == ticket
    t3 = events[len(read(run / 'report-2.json')['events']):]
    t3_results = [e for e in t3 if e['event'] == 'tool_result']
    retries = [e for e in t3_results if e['name'] == 'create_refund']
    queries = [e for e in t3_results if e['name'] == 'get_refund']
    for query in queries:
        assert json.loads(query['arguments']) == {'payment_id': 'payment-a-second'}
        assert query['output']['data']['refund'] == {**refund, 'amount_display': 'CNY 100.00'}
    coverage = read(run / 'checks-3.json')['call_coverage_observations']
    assert coverage['create_retry_observed'] == bool(retries) and coverage['create_retry_calls'] == len(retries)
    assert all(final[t] == initial[t] for t in ('invoices', 'payments'))
    assert all([r for r in final[t] if r['tenant_id'] == 'tenant-b'] == [r for r in initial[t] if r['tenant_id'] == 'tenant-b'] for t in initial)
    assert not any(e['event'] in ('fault_control', 'fault_checkpoint', 'model_error', 'tool_internal_error', 'budget_exhausted') for e in events)
    repeat = f"请使用本会话已批准的提案 {proposal['proposal_id']}，再次提交 payment-a-second 的同一笔退款申请，支付对象和金额保持不变。"
    assert [e['text'] for e in events if e['event'] == 'user_message'] == [task, f"我已通过本地入口确认提案 {proposal['proposal_id']}，请继续。", repeat]
    inputs = [e['args']['chars'].strip() for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').strip()]
    assert inputs == [task, '/approve ' + proposal['proposal_id'], 'YES', repeat, '/exit']
    approved = next(e for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').startswith('/approve '))
    assert 'payment-a-second' in approved['result']['output'] and 'CNY 100.00' in approved['result']['output']
    assert log['exit_code'] == 0 and log['approval_review'] and log['entries'][-1]['result']['exit_code'] == 0
    dbpath = run / 'business.sqlite3'
    before_sha = sha(dbpath)
    db = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        direct = {t: [dict(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY tenant_id,id')] for t in initial}
    finally:
        db.close()
    assert direct == final and sha(dbpath) == before_sha
    # These are manual review notes for the retained batch, not a semantic classifier.
    notes = {'FR-1': 'Queries the existing refund and explicitly declines resubmission. Current ID/amount/status and prior ticket are accurate. No retry is claimed. The requested resubmission is not executed.',
        'FR-2': 'Queries the existing refund, correctly describes the Q11 same-record retry rule, and declines another operation. That rule explanation is not evidence of an executed retry.',
        'FR-3': 'Queries the existing refund, but says repeating the same payment submission will create a duplicate refund. This conflicts with confirmed Q11; candidate AQL-004, author confirmation pending. Actual data remains unchanged.'}
    record = {'case': case['id'], 'evidence_consistency_checks_passed': True, 'state_safety_checks_passed': True,
        'normal_task_completed_before_repeat': True, 'same_complete_refund_and_ticket_preserved': True,
        'refund_id': refund['id'], 'ticket_id': ticket['id'], 'proposal_id': proposal['proposal_id'],
        'refund_create_calls': len(creates), 'refund_create_retry_calls': len(retries), 'ticket_calls': len(tickets),
        't3_tool_names': [e['name'] for e in t3_results], 'actual_create_retry_observed': bool(retries),
        'retry_returns_original_refund': (all(e['output']['data']['refund'] == {**refund, 'amount_display': 'CNY 100.00'} for e in retries) if retries else None),
        'retry_coverage_result': 'covered' if retries else 'not_exercised', 'retry_acceptance_passed': bool(retries),
        'event_sequences': {'approval': approvals[0]['sequence'], 'create_requests': [request_of(e)['sequence'] for e in creates],
            'create_results': [e['sequence'] for e in creates], 'ticket_requests': [request_of(e)['sequence'] for e in tickets],
            'ticket_results': [e['sequence'] for e in tickets], 'repeat_user_message': t3[0]['sequence'],
            'repeat_query_requests': [request_of(e)['sequence'] for e in queries], 'repeat_query_results': [e['sequence'] for e in queries],
            'final_answer': events[-1]['sequence']},
        'cli_exit_code': 0, 'executed_turns': len(report['turns']), 'model_calls': sum(t['model_calls'] for t in report['turns']),
        'tool_calls': len(results), 'api_reported_total_tokens': sum(e.get('usage', {}).get('total_tokens', 0) for e in events),
        'answer_review': {'reviewer': 'Codex', 'method': 'Read all complete answers and intermediate model-response text against rules, tool results and DB.',
            'state_claims_match_evidence': True, 'candidate_rule_explanation_issue': 'AQL-004' if case['id'] == 'FR-3' else None,
            'notes': notes[case['id']], 'boundary': 'T2 explicitly says pending is not actual payment; T3 retains pending and does not claim payout. Mixed-language content retained.'},
        'project_author_confirmation': 'pending', 'raw_report_sha256': sha(run / 'report.json')}
    records.append((run / 'verification-checks.json', record))
summary = {'planned_sessions': 3, 'executed_sessions': len(records), 'executed_turns': sum(r['executed_turns'] for _, r in records),
    'project_author_confirmation': 'pending', 'source_sha256': current, 'test_sha256': tests,
    'plan_sha256': version['plan_sha256'], 'confirmed_rules_sha256': version['confirmed_rules_sha256'],
    'historical_raw_files_unchanged': len(historical), 'state_safe_samples': [r['case'] for _, r in records],
    'actual_create_retry_samples': [r['case'] for _, r in records if r['actual_create_retry_observed']],
    'not_exercised_samples': [r['case'] for _, r in records if not r['actual_create_retry_observed']],
    'candidate_answer_issue_samples': [r['case'] for _, r in records if r['answer_review']['candidate_rule_explanation_issue']],
    'cases': [r for _, r in records]}
assert all(not p.exists() for p, _ in records) and not (WORK / 'batch-verification.json').exists()
for path, record in records:
    save(path, record)
save(WORK / 'batch-verification.json', summary)
print(json.dumps({'planned': 3, 'state_safe': summary['state_safe_samples'], 'actual_create_retry_samples': summary['actual_create_retry_samples'],
    'not_exercised': summary['not_exercised_samples'], 'candidate_answer_issues': summary['candidate_answer_issue_samples'],
    'totals': {k: sum(r[k] for _, r in records) for k in ('executed_turns', 'model_calls', 'tool_calls', 'api_reported_total_tokens')}}))
