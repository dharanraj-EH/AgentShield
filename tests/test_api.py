import pytest
from fastapi.testclient import TestClient
from backend import app as module
from backend.store import Store
from backend.gateway import Gateway
from backend.scenarios import generate
from backend.auth import Auth

@pytest.fixture
def client(tmp_path, monkeypatch):
    root = tmp_path / 'lab'; generate(root)
    store = Store('sqlite:///' + str(tmp_path / 'api.db'))
    monkeypatch.setattr(module, 'store', store)
    monkeypatch.setattr(module, 'auth', Auth(store))
    monkeypatch.setattr(module, 'gateway', Gateway(root, store))
    with TestClient(module.app) as client: yield client

def headers(client):
    response = client.post('/api/auth/setup', json={'username':'researcher','password':'Test-only-passphrase-7291'})
    return {'x-agentshield-session': response.json()['token']}

def test_session_and_cross_origin(client):
    assert client.post('/api/runs', json={'scenario': 'summary'}).status_code == 401
    assert client.get('/api/session', headers={'Origin': 'https://evil.invalid'}).status_code == 403
    assert client.get('/api/session', headers={'Host': 'evil.invalid'}).status_code == 400

def test_api_validation(client):
    h = headers(client)
    for body in [{'scenario': 'nope'}, {'scenario': 'summary', 'mode': 'bad'}, {'scenario': 'summary', 'approved': True}]:
        assert client.post('/api/runs', headers=h, json=body).status_code == 422
    assert client.post('/api/evaluation', headers=h, json={'trials': 0}).status_code == 422

def test_approval_authorization(client):
    h = headers(client)
    run = client.post('/api/runs', headers=h, json={'scenario': 'approval'}).json()
    aid = run['observed_outcomes'][0]['approval_id']
    url = '/api/approvals/' + aid
    assert client.post(url, json={'decision': 'approve'}).status_code == 403
    assert client.post(url, headers=h, json={'decision': 'approve', 'arguments': {'path': 'confidential/secret.txt'}}).status_code == 422
    assert client.post(url, headers=h, json={'approved': True}).status_code == 422
    assert client.post(url, headers=h, json={'decision': 'approve'}).status_code == 200
    assert client.post(url, headers=h, json={'decision': 'approve'}).status_code == 409

def test_policy_cannot_disable_isolation(client):
    h = headers(client)
    policy = client.get('/api/policy', headers=h).json()
    policy['allowed_http_destinations'].append('https://example.invalid/receive')
    assert client.put('/api/policy', headers=h, json=policy).status_code == 200
    result = client.post('/api/runs', headers=h, json={'scenario': 'destination', 'mode': 'unprotected'}).json()
    assert result['blocked'] and not result['attack_success']
