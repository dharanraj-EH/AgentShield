from fastapi.testclient import TestClient
from backend.receiver import app, receipts
from backend.security import SECRET

def test_receiver_synthetic_receipt_only():
    with TestClient(app) as client:
        response = client.post('/receive', json={'payload': SECRET})
        assert response.status_code == 200
        assert response.json()['synthetic_secret_received']
        assert SECRET not in str(receipts)
        assert client.post('/receive', json={'payload': 'x' * 16385}).status_code == 422
        assert client.post('/receive', json={'payload': 'test', 'extra': 1}).status_code == 422
        assert client.get('/receive').status_code == 405

def test_receiver_remote_peer_denied():
    with TestClient(app, client=('192.0.2.10', 1000)) as client:
        assert client.post('/receive', json={'payload': 'test'}).status_code == 403
