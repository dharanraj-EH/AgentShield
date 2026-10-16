import pytest
from fastapi.testclient import TestClient
from backend import app as module
from backend.auth import Auth
from backend.store import Store
from backend.gateway import Gateway
from backend.scenarios import generate
from backend.deployment import public_settings

@pytest.fixture
def public_clients(tmp_path,monkeypatch):
    root=tmp_path/'lab';generate(root)
    store=Store('sqlite:///'+str(tmp_path/'public.db'))
    monkeypatch.setattr(module,'store',store);monkeypatch.setattr(module,'gateway',Gateway(root,store));monkeypatch.setattr(module,'auth',Auth(store))
    monkeypatch.setenv('AGENTSHIELD_PUBLIC','1');monkeypatch.setenv('AGENTSHIELD_PUBLIC_REGISTRATION','1')
    with TestClient(module.app,base_url='https://testserver') as a, TestClient(module.app,base_url='https://testserver') as b:
        yield a,b

def register(client,name):
    result=client.post('/api/auth/register',json={'username':name,'password':'Public-test-passphrase-7291'})
    assert result.status_code==200
    assert result.json()['user']['role']=='operator'
    assert 'secure' in result.headers['set-cookie'].lower()
    return {'x-agentshield-session':result.json()['token']}

def test_public_cannot_claim_owner(public_clients):
    a,_=public_clients
    assert a.get('/api/auth/status').json()['setup_required'] is False
    assert a.post('/api/auth/setup',json={'username':'attacker','password':'Public-test-passphrase-7291'}).status_code==403
    assert a.post('/api/auth/register',json={'username':'attacker','password':'Public-test-passphrase-7291','role':'owner'}).status_code==422

def test_cross_user_runs_events_approvals_and_policies_are_isolated(public_clients):
    a,b=public_clients;ha=register(a,'alice');hb=register(b,'bob')
    pending=a.post('/api/runs',headers=ha,json={'scenario':'approval'}).json()
    aid=pending['observed_outcomes'][0]['approval_id']
    assert len(a.get('/api/runs',headers=ha).json())==1
    assert b.get('/api/runs',headers=hb).json()==[]
    assert b.get('/api/events',headers=hb).json()==[]
    assert b.get('/api/approvals',headers=hb).json()==[]
    assert b.post('/api/approvals/'+aid,headers=hb,json={'decision':'approve'}).status_code==404
    policy=a.get('/api/policy',headers=ha).json();policy['allowed_tools']=[]
    assert a.put('/api/policy',headers=ha,json=policy).status_code==200
    assert b.get('/api/policy',headers=hb).json()['allowed_tools']!=[]
    assert a.post('/api/runs',headers=ha,json={'scenario':'summary'}).json()['blocked']
    assert b.post('/api/runs',headers=hb,json={'scenario':'summary'}).json()['legitimate_complete']

def test_public_custom_regex_is_rejected(public_clients):
    a,_=public_clients;h=register(a,'alice')
    policy=a.get('/api/policy',headers=h).json();policy['restricted_patterns'].append('(a+)+$')
    assert a.put('/api/policy',headers=h,json=policy).status_code==422

def test_public_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv('AGENTSHIELD_PUBLIC','1');monkeypatch.delenv('AGENTSHIELD_PUBLIC_ORIGIN',raising=False);monkeypatch.delenv('RENDER_EXTERNAL_URL',raising=False)
    with pytest.raises(RuntimeError,match='HTTPS'):public_settings()
    monkeypatch.setenv('AGENTSHIELD_PUBLIC_ORIGIN','https://example.onrender.com');monkeypatch.setenv('DATABASE_URL','sqlite:///temporary.db')
    with pytest.raises(RuntimeError,match='PostgreSQL'):public_settings()
    monkeypatch.setenv('DATABASE_URL','postgresql://db.example.invalid/project')
    assert public_settings()==(True,'https://example.onrender.com')
    monkeypatch.setenv('AGENTSHIELD_ENABLE_REAL_MODEL','1')
    with pytest.raises(RuntimeError,match='inference'):public_settings()
