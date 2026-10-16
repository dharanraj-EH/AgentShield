"""Explicit integration check against a disposable agentshield_test database only."""
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
url = os.environ.get('AGENTSHIELD_TEST_DATABASE_URL', '')
if urlsplit(url).path != '/agentshield_test':
    raise SystemExit('Supply AGENTSHIELD_TEST_DATABASE_URL for disposable agentshield_test only.')

from fastapi.testclient import TestClient
from backend import app as module
from backend.auth import Auth
from backend.store import Store, current_owner
from backend.gateway import Gateway
from backend.scenarios import generate
from secrets import token_hex

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder) / 'lab'; generate(root)
    module.store = Store(url)
    module.gateway = Gateway(root, module.store)
    module.auth = Auth(module.store)
    os.environ['AGENTSHIELD_PUBLIC'] = '1'
    os.environ['AGENTSHIELD_PUBLIC_REGISTRATION'] = '1'
    suffix = token_hex(4)
    with TestClient(module.app, base_url='https://testserver') as a, TestClient(module.app, base_url='https://testserver') as b:
        users=[]
        for client, name in [(a,'alice'), (b,'bob')]:
            response=client.post('/api/auth/register',json={'username':name+suffix,'password':token_hex(16)})
            assert response.status_code==200, response.status_code
            users.append(response.json())
        ha={'x-agentshield-session':users[0]['token']}
        hb={'x-agentshield-session':users[1]['token']}
        pending=a.post('/api/runs',headers=ha,json={'scenario':'approval'}).json()
        aid=pending['observed_outcomes'][0]['approval_id']
        assert b.get('/api/runs',headers=hb).json()==[]
        assert b.get('/api/events',headers=hb).json()==[]
        assert b.post('/api/approvals/'+aid,headers=hb,json={'decision':'approve'}).status_code==404
        policy=a.get('/api/policy',headers=ha).json(); policy['allowed_tools']=[]
        assert a.put('/api/policy',headers=ha,json=policy).status_code==200
        assert b.get('/api/policy',headers=hb).json()['allowed_tools']!=[]
        restarted=Store(url)
        token=current_owner.set(users[0]['user']['id'])
        try:
            assert any(run['id']==pending['id'] for run in restarted.runs())
            assert restarted.policy_for_owner().allowed_tools==[]
        finally: current_owner.reset(token)
        restarted.engine.dispose()
    module.store.engine.dispose()
print('PostgreSQL registration, run/event/approval/policy isolation and reconnect persistence passed.')
