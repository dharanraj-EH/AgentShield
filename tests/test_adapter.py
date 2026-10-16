import json
import httpx
from backend.model_adapter import OllamaAdapter
from backend.gateway import Gateway
from backend.scenarios import generate
from backend.store import Store

def test_real_adapter_proposals_are_enforced(tmp_path, monkeypatch):
    root = tmp_path / 'lab'; generate(root)
    gateway = Gateway(root, Store('sqlite:///' + str(tmp_path / 'model.db')))
    proposals = iter([{'tool': 'read_file', 'arguments': {'path': 'confidential/secret.txt'}}, {'final': 'Access was blocked.'}])
    sent = []
    def handler(request):
        assert str(request.url) == 'http://127.0.0.1:11434/api/chat'
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={'message': {'content': json.dumps(next(proposals))}})
    real_client = httpx.Client
    def client(**kwargs):
        assert kwargs['trust_env'] is False and kwargs['follow_redirects'] is False
        return real_client(transport=httpx.MockTransport(handler), **kwargs)
    monkeypatch.setattr('backend.model_adapter.httpx.Client', client)
    result = OllamaAdapter('mock-model').run(gateway, 'Read the file')
    assert result['simulated'] is False
    assert sent[0]['options']['temperature'] == 0 and sent[0]['options']['seed'] == 42
    assert sent[0]['think'] is False
    assert any(e.get('rule_id') == 'classification.confidential' for e in gateway.store.events())
    assert not any(e['kind'] == 'execution' for e in gateway.store.events())

def test_model_invalid_json_never_executes(tmp_path, monkeypatch):
    root = tmp_path / 'lab'; generate(root)
    gateway = Gateway(root, Store('sqlite:///' + str(tmp_path / 'invalid.db')))
    real_client = httpx.Client
    monkeypatch.setattr('backend.model_adapter.httpx.Client', lambda **kwargs: real_client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json={'message': {'content': 'not JSON'}})), **kwargs))
    assert OllamaAdapter('mock').run(gateway, 'test')['error'] == 'Invalid model proposal'
    assert not any(e['kind'] == 'execution' for e in gateway.store.events())
