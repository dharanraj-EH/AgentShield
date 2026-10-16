import json
import os
from pathlib import Path
import httpx
import pytest
from backend.security import Action, Policy, SECRET, decide, safe_path, safe_url, screen, redact
from backend.scenarios import generate, act, URL
from backend.store import Store, Approval
from backend.gateway import Gateway
from backend.lab import run_scenario
from backend.evaluation import metrics

@pytest.fixture
def gateway(tmp_path):
    root = tmp_path / 'lab'; generate(root)
    return Gateway(root, Store('sqlite:///' + str(tmp_path / 'test.db')))

@pytest.mark.parametrize('mode', [True, False])
@pytest.mark.parametrize('path', ['../outside.txt', '/etc/passwd', 'C:/Windows/win.ini', '..\\outside.txt', 'public/../../outside.txt'])
def test_paths_never_leave_lab(gateway, mode, path):
    assert decide(gateway.root, act('read_file', path=path), gateway.policy, mode)[0] == 'block'

def test_symlink_escape(gateway, tmp_path):
    outside = tmp_path / 'outside.txt'; outside.write_text('outside')
    link = gateway.root / 'public/link.txt'
    try: link.symlink_to(outside)
    except OSError: pytest.skip('Windows account lacks symlink privilege; junction boundary tested separately')
    with pytest.raises(ValueError): safe_path(gateway.root, 'public/link.txt')

@pytest.mark.skipif(os.name != 'nt', reason='Windows junction test')
def test_windows_junction_escape(gateway, tmp_path):
    import subprocess
    outside = tmp_path / 'outside'; outside.mkdir(); (outside / 'x.txt').write_text('outside')
    junction = gateway.root / 'public/junction'
    result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)], capture_output=True)
    if result.returncode: pytest.skip('Junction creation unavailable')
    try:
        with pytest.raises(ValueError): safe_path(gateway.root, 'public/junction/x.txt')
    finally: os.rmdir(junction)  # Remove the link, never recurse into its target.

@pytest.mark.parametrize('url', ['https://127.0.0.1:8766/receive', 'http://localhost:8766/receive', 'http://127.0.0.1:80/receive', 'http://127.0.0.1:8766/receive?x=1', 'http://127.0.0.1:8766/receive#x', 'http://user@127.0.0.1:8766/receive', 'http://2130706433:8766/receive', 'file:///etc/passwd', 'http://example.com/receive', 'http://127.0.0.1:8766/receive/'])
def test_url_isolation(url):
    with pytest.raises(ValueError): safe_url(url)

def test_canonical_url(): assert safe_url(URL) == URL

def test_default_deny_and_strict_arguments(gateway):
    for action in [act('shell', command='whoami'), act('read_file'), act('read_file', path=3), act('read_file', path='public/report.txt', approved=True)]:
        assert gateway.request('test', action)['decision'] == 'block'

def test_policy_tools_files_classification_and_dlp(gateway):
    assert gateway.request('a', act('read_file', path='confidential/secret.txt'))['rule_id'] == 'classification.confidential'
    assert gateway.request('a', act('send_http_request', url=URL, payload='prefix '+SECRET))['rule_id'] == 'dlp.restricted'
    gateway.policy.allowed_tools = []
    assert gateway.request('a', act('read_file', path='public/report.txt'))['rule_id'] == 'policy.tool'
    gateway.policy = Policy(allowed_files=['review'])
    assert gateway.request('a', act('read_file', path='public/report.txt'))['rule_id'] == 'policy.file'
    gateway.policy = Policy(allowed_http_destinations=[])
    assert gateway.request('a', act('send_http_request', url=URL, payload='public'))['rule_id'] == 'policy.destination'

def test_approval_exact_action_and_replay(gateway):
    proposal = act('read_file', path='review/budget.txt')
    pending = gateway.request('a', proposal)
    proposal.arguments['path'] = 'confidential/secret.txt'
    result = gateway.approve(pending['approval_id'], True)
    assert result['status'] == 'success'
    assert '5000' in result['output']
    with pytest.raises(ValueError): gateway.approve(pending['approval_id'], True)

def test_fresh_policy_after_approval(gateway):
    pending = gateway.request('a', act('read_file', path='review/budget.txt'))
    gateway.policy.allowed_files = ['public']
    assert gateway.approve(pending['approval_id'], True)['decision'] == 'block'

def test_reject_and_replay(gateway):
    pending = gateway.request('a', act('read_file', path='review/budget.txt'))
    assert gateway.approve(pending['approval_id'], False)['status'] == 'rejected'
    with pytest.raises(ValueError): gateway.approve(pending['approval_id'], True)

def test_redirect_rejected_and_proxy_disabled(gateway, monkeypatch):
    real_client = httpx.Client
    def client(**kwargs):
        assert kwargs['trust_env'] is False and kwargs['follow_redirects'] is False
        return real_client(transport=httpx.MockTransport(lambda req: httpx.Response(302, headers={'location': 'https://example.com'})), **kwargs)
    monkeypatch.setattr('backend.gateway.httpx.Client', client)
    result = gateway.request('a', act('send_http_request', url=URL, payload='public'))
    assert result['status'] == 'error' and 'Redirect' in result['reason']

def test_log_redaction_unprotected(gateway):
    run = run_scenario(gateway, 'direct', 'unprotected')
    assert run['attack_success']
    assert SECRET not in json.dumps(gateway.store.events())
    assert SECRET not in json.dumps(gateway.store.runs())
    assert SECRET not in json.dumps(run)

def test_screening_does_not_block_quotes(gateway):
    result = run_scenario(gateway, 'quoted', 'protected')
    assert result['legitimate_complete'] and not result['blocked']
    assert any(e['kind'] == 'screening' for e in gateway.store.events())

def test_protected_injection_stops_before_secret(gateway):
    run = run_scenario(gateway, 'embedded', 'protected')
    assert run['blocked'] and not run['attack_success']
    assert not any(e.get('tool') == 'send_http_request' for e in gateway.store.events())

def test_metrics_denominators():
    rows = [dict(scenario='a', mode='protected', malicious=True, attack_success=True, legitimate_complete=False, blocked=False, duration_ms=4, decision_latencies_ms=[1, 3]),
      dict(scenario='b', mode='protected', malicious=True, attack_success=False, legitimate_complete=False, blocked=True, duration_ms=6, decision_latencies_ms=[2]),
      dict(scenario='c', mode='protected', malicious=False, attack_success=False, legitimate_complete=True, blocked=False, duration_ms=2, decision_latencies_ms=[2])]
    m = metrics(rows)[2]
    assert m['attack_success_rate'] == .5 and m['legitimate_completion_rate'] == 1
    assert m['false_block_rate'] == 0 and m['mean_decision_latency_ms'] == 2
    assert metrics([])[0]['attack_success_rate'] is None
