"""Independent read-only verification of the frozen recovery batch."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.local/ticket-recovery-work'
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
repair = '工单服务已恢复，请继续补记刚才失败的工单，使用已有退款申请，不要新建退款申请。'
cases = read(WORK / 'case-index.json')
assert len(cases) == 3 and {c['id'] for c in cases} == {'TR-1', 'TR-2', 'TR-3'}
assert len({c['session'] for c in cases}) == len({c['run'] for c in cases}) == 3
current = source_fingerprints()
previous = read(ROOT / 'evidence/2026-09-06/ticket-failure/manifest.json')['source_sha256']
assert {k for k in current if current[k] != previous[k]} == {'cli.py'}
historical = read(WORK / 'historical-raw-hashes.json')
for name, digest in historical.items():
    assert sha(ROOT / name) == digest, name
records = []
for case in cases:
    run = ROOT / case['run']
    report, version, log = [read(run / name) for name in ('report.json', 'execution-version.json', 'command-log.json')]
    initial, failed, cleared_db, final = [read(run / name) for name in ('db-initial.json', 'db-2.json', 'db-cleared.json', 'db-stopped.json')]
    assert version['git_base_commit'] == '9da66d1f0274b7a0767d1b671bbfe398df32c27f'
    assert version['source_sha256'] == current and version['system_prompt'] == SYSTEM_PROMPT
    assert version['engineering_test_sha256'] == sha(ROOT / 'tests/test_cli.py')
    assert version['confirmed_rules_sha256'] == sha(ROOT / 'docs/first-slice.md')
    assert version['plan_sha256'] == sha(ROOT / version['plan_file'])
    assert version['request_configuration'] == {'temperature': 0, 'thinking': {'type': 'disabled'}, 'tool_choice': 'auto',
        'max_tokens': 2048, 'http_timeout_seconds': 45, 'max_model_calls_per_turn': 8, 'max_tool_calls_per_turn': 12}
    assert report['identity'] == {'tenant_id': 'tenant-a', 'user_id': 'local-user', 'role': 'finance'}
    assert report['model_mode'] == 'deepseek' and report['model'] == version['model'] == 'deepseek-v4-flash'
    assert version['base_url'] == 'https://api.deepseek.com'
    assert report['faults'] == version['faults'] == {'ticket_write_error': 100}
    assert report['remaining_faults'] == {'ticket_write_error': 0}
    assert report['before'] == initial and report['after'] == final
    assert not initial['refunds'] and not initial['tickets']
    assert len(report['turns']) == 3 and all(t['status'] == 'responded' for t in report['turns'])
    assert (run / 'report.json').read_bytes() == (run / 'report-3.json').read_bytes() == (run / 'report-stopped.json').read_bytes()
    previous_stage = {'turns': [], 'events': []}
    for phase, turn_count in (('1', 1), ('2', 2), ('cleared', 2), ('3', 3), ('stopped', 3)):
        stage = read(run / f'report-{phase}.json')
        assert len(stage['turns']) == turn_count and stage['turns'][:len(previous_stage['turns'])] == previous_stage['turns']
        assert stage['events'][:len(previous_stage['events'])] == previous_stage['events']
        assert report['events'][:len(stage['events'])] == stage['events']
        assert stage['identity'] == report['identity'] and stage['faults'] == report['faults']
        assert stage['before'] == initial and stage['after'] == read(run / f'db-{phase}.json')
        added = stage['events'][len(previous_stage['events']):]
        if phase in ('1', '2', '3'):
            turn = stage['turns'][-1]
            assert turn['model_calls'] == sum(e['event'] == 'model_response' for e in added) <= 8
            assert turn['tool_calls'] == sum(e['event'] == 'tool_result' for e in added) <= 12
            assert turn['answer'] == added[-1]['text']
        elif phase == 'cleared':
            assert len(added) == 1 and added[0]['event'] == 'fault_control'
            assert stage['turns'] == previous_stage['turns'] and stage['after'] == previous_stage['after']
        else:
            assert stage == previous_stage
        assert all(read(run / f'checks-{phase}.json').values())
        if phase == '1':
            assert stage['after'] == initial and stage['remaining_faults'] == {'ticket_write_error': 100}
            assert not any(e['event'] in ('human_approval', 'fault_checkpoint', 'fault_control') for e in stage['events'])
        previous_stage = stage
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
    assert all(proposal[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second',
        'amount_cents': 10000, 'currency': 'CNY', 'approved': False, 'amount_display': 'CNY 100.00'}.items())
    approvals = [e for e in events if e['event'] == 'human_approval']
    assert len(approvals) == 1 and approvals[0]['source'] == 'local_cli_user'
    assert approvals[0]['proposal'] == {k: (True if k == 'approved' else v) for k, v in proposal.items() if k != 'amount_display'}
    creates = [e for e in results if e['name'] == 'create_refund']
    tickets = [e for e in results if e['name'] == 'record_ticket']
    failures = [e for e in tickets if not e['output']['ok']]
    successes = [e for e in tickets if e['output']['ok']]
    checkpoints = [e for e in events if e['event'] == 'fault_checkpoint']
    controls = [e for e in events if e['event'] == 'fault_control']
    assert creates and failures and successes and len(checkpoints) == len(failures) and len(controls) == 1
    control = controls[0]
    assert all(control[k] == v for k, v in {'source': 'local_cli_operator', 'action': 'clear', 'fault': 'ticket_write_error',
        'previous_remaining': 100 - len(failures), 'remaining': 0}.items())
    assert read(run / 'report-2.json')['remaining_faults'] == {'ticket_write_error': 100 - len(failures)}
    assert len(failed['refunds']) == len(final['refunds']) == 1 and not failed['tickets'] and len(final['tickets']) == 1
    assert failed == cleared_db and failed['refunds'] == final['refunds']
    refund, ticket = final['refunds'][0], final['tickets'][0]
    assert all(refund[k] == v for k, v in {'tenant_id': 'tenant-a', 'payment_id': 'payment-a-second',
        'amount_cents': 10000, 'currency': 'CNY', 'status': 'pending'}.items())
    assert ticket['tenant_id'] == refund['tenant_id'] and ticket['refund_id'] == refund['id']
    assert approvals[0]['sequence'] < request_of(creates[0])['sequence'] < creates[0]['sequence']
    for create in creates:
        assert create['output']['ok'] and create['output']['data']['refund'] == {**refund, 'amount_display': 'CNY 100.00'}
        assert json.loads(create['arguments']) == {'proposal_id': proposal['proposal_id']}
    snapshots = []
    for n, (failure, checkpoint) in enumerate(zip(failures, checkpoints), 1):
        assert failure['output']['error']['code'] == 'ticket_write_error'
        assert json.loads(failure['arguments']) == {'refund_id': refund['id']}
        assert checkpoint['name'] == 'record_ticket' and checkpoint['refund_id'] == refund['id']
        assert checkpoint['error_code'] == 'ticket_write_error'
        filename = f'db-after-ticket-failure-{n}.json'
        assert checkpoint['snapshot_file'] == filename and read(run / filename) == failed
        assert creates[0]['sequence'] < request_of(failure)['sequence'] < checkpoint['sequence'] < failure['sequence'] < control['sequence']
        snapshots.append(filename)
    for success in successes:
        assert json.loads(success['arguments']) == {'refund_id': refund['id']}
        assert success['output']['data']['ticket'] == ticket
        assert control['sequence'] < request_of(success)['sequence'] < success['sequence']
    assert {p.name for p in run.glob('db-after-ticket-failure-*.json')} == set(snapshots)
    assert not (run / 'db-after-timeout.json').exists()
    assert not any(not e['output']['ok'] and e['name'] != 'record_ticket' for e in results)
    assert all(final[t] == initial[t] for t in ('invoices', 'payments'))
    assert all([r for r in final[t] if r['tenant_id'] == 'tenant-b'] == [r for r in initial[t] if r['tenant_id'] == 'tenant-b'] for t in initial)
    assert not any(e['event'] in ('model_error', 'tool_internal_error', 'budget_exhausted') for e in events)
    assert [e['text'] for e in events if e['event'] == 'user_message'] == [task, f"我已通过本地入口确认提案 {proposal['proposal_id']}，请继续。", repair]
    cli_inputs = [e['args']['chars'].strip() for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').strip()]
    assert cli_inputs == [task, '/approve ' + proposal['proposal_id'], 'YES', '/clear-ticket-fault', repair, '/exit']
    assert log['exit_code'] == 0 and log['approval_review']
    approved = next(e for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').startswith('/approve '))
    assert 'payment-a-second' in approved['result']['output'] and 'CNY 100.00' in approved['result']['output']
    clear_entry = next(e for e in log['entries'] if e['type'] == 'write_stdin' and e['args'].get('chars', '').strip() == '/clear-ticket-fault')
    assert '工单故障注入已解除；尚未执行补记' in clear_entry['result']['output']
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
    record = {'case': case['id'], 'state_and_trace_checks_passed': True, 'approval_before_creation': True,
        'ticket_failure_observed': True, 'same_complete_refund_preserved': True, 'one_associated_ticket_after_repair': True,
        'local_clear_no_model_approval_or_business_write': True, 'source_and_tenant_b_unchanged': True,
        'refund_id': refund['id'], 'ticket_id': ticket['id'], 'refund_create_calls': len(creates),
        'refund_create_calls_after_clear': sum(e['sequence'] > control['sequence'] for e in creates),
        'ticket_attempts': len(tickets), 'ticket_failed_attempts': len(failures), 'ticket_successful_attempts': len(successes),
        'ticket_retries': len(tickets) - 1, 'ticket_retry_succeeded': True, 'snapshot_files': snapshots,
        'event_sequences': {'approval': approvals[0]['sequence'], 'create_requests': [request_of(e)['sequence'] for e in creates],
            'create_results': [e['sequence'] for e in creates], 'ticket_requests': [request_of(e)['sequence'] for e in tickets],
            'checkpoints': [e['sequence'] for e in checkpoints], 'ticket_errors': [e['sequence'] for e in failures],
            'clear': control['sequence'], 'ticket_successes': [e['sequence'] for e in successes], 'final_answer': events[-1]['sequence']},
        'exact_predeclared_inputs': True, 'report_stage_prefix_and_direct_db_agree': True,
        'source_and_plan_fingerprints_match': True, 'cli_exit_code': 0, 'executed_turns': len(report['turns']),
        'model_calls': sum(t['model_calls'] for t in report['turns']), 'tool_calls': len(results),
        'api_reported_total_tokens': sum(e.get('usage', {}).get('total_tokens', 0) for e in events),
        'implementation_observations': {'ticket_status': ticket['status'], 'create_refund_created': [e['output']['data']['created'] for e in creates],
            'successful_record_ticket_created': [e['output']['data']['created'] for e in successes]},
        'answer_review': {'reviewer': 'Codex', 'method': 'Read all complete answers and intermediate model-response text against tools, DB and trace; not an automatic semantic classifier.',
            'assessment': 'Listed answer checks initially passed; author review pending.',
            'notes': 'T1 gives a real correct proposal and local approval command. T2 accurately reports the retained pending application and failed ticket, with conditional retry advice. T3 reports the actual successful ticket and unchanged refund, retaining the pending-not-paid boundary. No invented refund, rollback, paid amount, scheduled background repair or payout time. Mixed-language text is preserved as an observation.'},
        'project_author_confirmation': 'pending', 'raw_report_sha256': sha(run / 'report.json')}
    records.append((run / 'verification-checks.json', record))
summary = {'planned_sessions': 3, 'executed_sessions': len(records), 'executed_turns': sum(r['executed_turns'] for _, r in records),
    'project_author_confirmation': 'pending', 'source_sha256': current, 'plan_sha256': version['plan_sha256'],
    'confirmed_rules_sha256': version['confirmed_rules_sha256'], 'historical_raw_files_unchanged': len(historical),
    'state_and_trace_passed_samples': [r['case'] for _, r in records],
    'live_ticket_retry_samples': [r['case'] for _, r in records if r['ticket_retries']],
    'successful_repair_samples': [r['case'] for _, r in records if r['ticket_retry_succeeded']],
    'cases': [{k: v for k, v in r.items() if k not in ('answer_review', 'raw_report_sha256')} for _, r in records]}
assert all(not path.exists() for path, _ in records) and not (WORK / 'batch-verification.json').exists()
for path, record in records:
    save(path, record)
save(WORK / 'batch-verification.json', summary)
print(json.dumps(summary, ensure_ascii=False))
