import time
import pytest
from fastapi.testclient import TestClient
from backend import app as module
from backend.auth import Auth, User, LoginSession, COOKIE, digest, password_matches
from backend.store import Store, now
from backend.gateway import Gateway
from backend.scenarios import generate

CREDS = {'username': 'Researcher', 'password': 'Only-for-tests-7291-phrase'}

@pytest.fixture
def client(tmp_path, monkeypatch):
    root = tmp_path / 'lab'; generate(root)
    store = Store('sqlite:///' + str(tmp_path / 'auth.db'))
    auth = Auth(store)
    monkeypatch.setattr(module, 'store', store)
    monkeypatch.setattr(module, 'auth', auth)
    monkeypatch.setattr(module, 'gateway', Gateway(root, store))
    with TestClient(module.app) as c: yield c

def setup(client):
    response = client.post('/api/auth/setup', json=CREDS)
    assert response.status_code == 200
    return {'x-agentshield-session': response.json()['token']}

def test_login_required_for_data_and_old_bootstrap(client):
    assert client.get('/api/session').status_code == 401
    for path in ['runs','events','approvals','policy','scenarios']:
        assert client.get('/api/'+path).status_code == 401
    assert client.get('/api/runs', headers={'x-agentshield-session':'forged'}).status_code == 401

def test_first_account_hash_cookie_and_setup_locked(client):
    assert client.get('/api/auth/status').json()['setup_required']
    short = {**CREDS, 'password':'short'}
    assert client.post('/api/auth/setup', json=short).status_code == 422
    response = client.post('/api/auth/setup', json=CREDS)
    assert response.status_code == 200
    cookie = response.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=strict' in cookie and 'path=/api' in cookie
    assert not client.get('/api/auth/status').json()['setup_required']
    assert client.post('/api/auth/setup', json={**CREDS,'username':'other'}).status_code == 409
    with module.store.session() as db:
        user = db.query(User).one()
        assert user.password_hash != CREDS['password'] and password_matches(CREDS['password'], user.password_hash)
        assert CREDS['password'] not in str(module.store.events())
        assert client.cookies.get(COOKIE) != db.query(LoginSession).one().token_hash

def test_csrf_tour_persistence_and_logout(client):
    headers = setup(client)
    assert client.get('/api/session').json()['user']['tour_completed'] is False
    assert client.post('/api/auth/tour', json={}).status_code == 403
    assert client.post('/api/auth/tour', headers=headers, json={}).json()['tour_completed'] is True
    assert client.post('/api/auth/logout', headers=headers, json={}).status_code == 200
    assert client.get('/api/session').status_code == 401
    response = client.post('/api/auth/login', json=CREDS)
    assert response.status_code == 200 and response.json()['user']['tour_completed'] is True
    assert response.json()['token'] != headers['x-agentshield-session']

def test_cookie_alone_or_header_alone_cannot_authorize_mutation(client):
    headers = setup(client)
    assert client.post('/api/runs', json={'scenario':'summary'}).status_code == 403
    client.cookies.clear()
    assert client.post('/api/runs', headers=headers, json={'scenario':'summary'}).status_code == 401

def test_expiry_and_revocation(client):
    headers=setup(client); old_cookie=client.cookies.get(COOKIE)
    client.post('/api/auth/login', json=CREDS)
    assert module.store.session
    with module.store.session() as db: assert db.get(LoginSession,digest(old_cookie)) is None
    with module.store.session.begin() as db:
        db.query(LoginSession).update({'expires_at':'2000-01-01T00:00:00+00:00'})
    assert client.get('/api/session').status_code == 401
    assert client.get('/api/runs', headers=headers).status_code == 401

def test_wrong_credentials_and_throttling(client):
    setup(client)
    for attempt in range(5):
        response=client.post('/api/auth/login', json={'username':'missing','password':'wrong'})
        assert response.status_code == 401 and response.json()['detail']=='Username or password is incorrect'
    assert client.post('/api/auth/login', json=CREDS).status_code == 429
    module.auth.failures=[time.monotonic()-61]
    assert client.post('/api/auth/login', json=CREDS).status_code == 200

def test_cross_origin_setup_and_login_rejected(client):
    for path in ['setup','login']:
        assert client.post('/api/auth/'+path, json=CREDS, headers={'origin':'https://evil.invalid'}).status_code == 403

def test_authenticated_session_survives_auth_object_restart(client, monkeypatch):
    setup(client)
    monkeypatch.setattr(module,'auth',Auth(module.store))
    assert client.get('/api/session').status_code == 200
