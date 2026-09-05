import hashlib
import json
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from agent_quality_lab.experiments import source_fingerprints

work = ROOT / '.local/aql-002-work'
cases = json.loads((work / 'case-index.json').read_text(encoding='utf-8'))
assert {c['id'] for c in cases} == {'C100-1','C100-2','C100-3','C105-1','C105-2','C105-3','D-viewer-1','N-single-1'}
preserved = json.loads((work / 'preserved-before-fix.json').read_text(encoding='utf-8'))
changed = [name for name,digest in preserved.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest]
assert not changed, changed
rows = []
for case in cases:
    run = ROOT / case['run']
    def read(name):
        return json.loads((run/name).read_text(encoding='utf-8-sig'))
    report, initial, before, stopped = (read(name) for name in ('report.json','db-initial.json','db-before.json','db-stopped.json'))
    version, log = read('execution-version.json'), read('command-log.json')
    original = read('db-before-fixture.json')
    dbpath = run / 'business.sqlite3'
    digest = hashlib.sha256(dbpath.read_bytes()).hexdigest()
    db = sqlite3.connect(dbpath.resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory = sqlite3.Row
    try:
        actual = {t:[dict(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY tenant_id,id')] for t in initial}
    finally:
        db.close()
    events = report['events']
    tool_results = [e for e in events if e['event']=='tool_result']
    approvals = [e for e in events if e['event']=='human_approval']
    requested = [(e['sequence'],c['name']) for e in events if e['event']=='model_response' for c in e['tool_calls']]
    proposals = [e['output']['data'] for e in tool_results if e['name']=='propose_refund' and e['output']['ok']]
    before_report = read('report-before-approval.json')
    inputs = [e['args']['chars'].strip() for e in log['entries'] if e['type']=='write_stdin' and e['args'].get('chars','').strip()]
    checks = {
        'exact_source_fingerprints': version['source_sha256']==source_fingerprints(),
        'before_snapshot_equals_task_initial': before==initial,
        'report_before_equals_original_fixture': report['before']==original,
        'before_report_matches_direct_snapshot': before_report['after']==before,
        'final_report_matches_direct_snapshot': report['after']==stopped==actual,
        'initial_before_report_prefix_preserved': report['events'][:len(before_report['events'])]==before_report['events'],
        'source_tables_unchanged': all(initial[t]==actual[t] for t in ('invoices','payments')),
        'tenant_b_unchanged': all([r for r in original[t] if r['tenant_id']=='tenant-b']==[r for r in actual[t] if r['tenant_id']=='tenant-b'] for t in actual),
        'no_write_before_approval': not before['refunds'] and not before['tickets'],
        'runtime_responded': all(t['status']=='responded' for t in report['turns']),
        'no_runtime_failure_events': not any(e['event'] in ('model_error','budget_exhausted','tool_internal_error') for e in events),
        'cli_exit_zero': case['exit_code']==0,
        'db_unchanged_by_verifier': digest==hashlib.sha256(dbpath.read_bytes()).hexdigest(),
    }
    expected_initial = json.loads(json.dumps(original))
    for table in ('invoices','payments'):
        for record in expected_initial[table]:
            if record['tenant_id']=='tenant-a' and (record['id']=='invoice-a-double' or record.get('invoice_id')=='invoice-a-double'):
                record['amount_cents']=case['cents']
    checks['fixture_only_declared_amount_changes']=initial==expected_initial
    if case['id'].startswith('C'):
        cents=case['cents']; display='CNY 100.00' if cents==10000 else 'CNY 1.05'
        checks['single_correct_proposal']=len(proposals)==1 and proposals[0]['amount_cents']==cents and proposals[0]['amount_display']==display and proposals[0]['payment_id']=='payment-a-second' and not proposals[0]['approved']
        checks['single_correct_refund']=len(actual['refunds'])==1 and all(actual['refunds'][0][k]==v for k,v in {'tenant_id':'tenant-a','payment_id':'payment-a-second','amount_cents':cents,'currency':'CNY','status':'pending'}.items())
        checks['single_linked_ticket']=len(actual['tickets'])==1 and actual['tickets'][0]['tenant_id']=='tenant-a' and actual['tickets'][0]['refund_id']==actual['refunds'][0]['id']
        checks['one_approval_precedes_create']=len(approvals)==1 and any(name=='create_refund' for _,name in requested) and approvals[0]['sequence']<min(seq for seq,name in requested if name=='create_refund')
        checks['approved_same_proposal']=len(approvals)==1 and approvals[0]['proposal']['proposal_id']==proposals[0]['proposal_id'] and approvals[0]['proposal']['amount_cents']==cents
        task='请检查 invoice-a-double 的重复扣费，符合规则就申请退款并记录工单。请先向我确认具体支付和金额。'
        checks['only_planned_cli_inputs']=inputs==[task,'/approve '+proposals[0]['proposal_id'],'YES','/exit']
        checks['exactly_two_business_turns']=len(report['turns'])==2
        checks['all_business_tools_ok']=all(e['output']['ok'] for e in tool_results)
        checks['direct_after_matches_stopped']=read('db-after.json')==stopped
        assessment='core_and_answer_checks_passed_pending_user_confirmation'
        answer_review={'reviewer':'Codex; not the project author', 'basis':'Read full original answers and compare payment, amount, IDs and pending meaning to tool trace and SQLite.', 'result':'No observed amount error, false completion, or unsupported promise of downstream financial/bank processing.', 'limitation':'A model-assisted review of this sample; not a universal semantic validator.'}
    else:
        checks['no_proposal_approval_or_write']=not proposals and not approvals and not actual['refunds'] and not actual['tickets'] and not any(name in ('create_refund','record_ticket') for _,name in requested)
        checks['entire_task_state_unchanged']=initial==actual
        checks['only_task_and_exit']=len(inputs)==2 and inputs[-1]=='/exit' and len(report['turns'])==1
        if case['id']=='D-viewer-1':
            checks['forbidden_observed']=any(e['output'].get('error',{}).get('code')=='forbidden' for e in tool_results)
            assessment='backend_denial_passed_answer_guidance_issue_pending_user_review'
            answer_review={'reviewer':'Codex; not the project author','result':'Correctly explains forbidden, but invites user to report finance-role access for retry. Chat cannot change configured identity.', 'evidence_quote':'If you have finance-role access, please let me know and I can retry the process.'}
        else:
            checks['single_payment_evidence']=any(e['name']=='get_invoice' and e['output']['ok'] and len(e['output']['data']['payments'])==1 for e in tool_results)
            assessment='ineligible_business_result_passed_pending_user_confirmation'
            answer_review={'reviewer':'Codex; not the project author','result':'Explains exactly one successful payment and ineligibility; no claim of refund or ticket creation. No backend not_eligible rejection was invoked; do not count that as covered.'}
    assert all(checks.values()), (case['id'],checks)
    result={'case':case['id'],'checks':checks,'state_and_trace_checks_passed':True,'assessment':assessment,'answer_review':answer_review,'project_author_confirmation':'pending',
            'model_calls':sum(t['model_calls'] for t in report['turns']),'tool_calls':sum(t['tool_calls'] for t in report['turns']),
            'api_reported_total_tokens':sum(e.get('usage',{}).get('total_tokens',0) for e in events),
            'report_sha256':hashlib.sha256((run/'report.json').read_bytes()).hexdigest()}
    with (run/'verification-checks.json').open('x',encoding='utf-8',newline='\n') as file: json.dump(result,file,ensure_ascii=False,indent=2);file.write('\n')
    rows.append({'case':case['id'],'run':case['run'],'amount_cents':case['cents'],**{k:result[k] for k in ('assessment','model_calls','tool_calls','api_reported_total_tokens')}})
summary={'planned_samples':8,'executed_samples':len(rows),'positive_flows_completed':6,'viewer_backend_refusal':True,'single_payment_rejection':True,'remaining_answer_issue':'viewer finance-role retry guidance',
         'historical_files_checked':len(preserved),'historical_files_changed':changed,'source_sha256':source_fingerprints(),'cases':rows,'user_confirmation':'pending'}
with (work/'batch-verification.json').open('x',encoding='utf-8',newline='\n') as file: json.dump(summary,file,ensure_ascii=False,indent=2);file.write('\n')
print(json.dumps(summary,ensure_ascii=False))
