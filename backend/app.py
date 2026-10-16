import os
import re
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import Field
from .security import Strict, Policy, redact, PATTERNS
from .store import Store, current_owner
from .gateway import Gateway
from .scenarios import SCENARIOS, generate
from .lab import run_scenario
from .evaluation import experiment

from .deployment import public_settings
PUBLIC_MODE, PUBLIC_ORIGIN = public_settings()
ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = Path(os.getenv('AGENTSHIELD_LAB_ROOT','/tmp/lab' if os.getenv('AGENTSHIELD_CONTAINER')=='1' else str(ROOT/'lab')))
generate(LAB_ROOT)
store = Store()
gateway = Gateway(LAB_ROOT, store)
from .auth import Auth, Credentials
auth = Auth(store)
app = FastAPI(title='AgentShield', version='0.2.0')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'] + ([__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(PUBLIC_ORIGIN).hostname] if PUBLIC_ORIGIN else []))

@app.middleware('http')
async def local_boundary(request: Request, call_next):
    from starlette.responses import JSONResponse
    # Bind to loopback as well. This is a local demonstration, not remote authentication.
    if not PUBLIC_MODE and os.getenv('AGENTSHIELD_CONTAINER') != '1' and request.client and request.client.host not in ('127.0.0.1', '::1', 'testclient'):
        return JSONResponse({'detail': 'Local access only'}, status_code=403)
    origin = request.headers.get('origin')
    if origin and origin not in ('http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:8765', 'http://localhost:8765','http://127.0.0.1:8780','http://localhost:8780',PUBLIC_ORIGIN):
        return JSONResponse({'detail': 'Origin forbidden'}, status_code=403)
    owner_token=None
    if request.cookies.get('agentshield_session'):
        try: owner_token=current_owner.set(auth.session(request)['user']['id'])
        except HTTPException: pass
    try: response = await call_next(request)
    finally:
        if owner_token is not None: current_owner.reset(owner_token)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    if PUBLIC_MODE:
        response.headers['Strict-Transport-Security']='max-age=31536000'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
    return response

def authorized(request: Request):
    session=auth.session(request, require_csrf=True)
    if request.method in ('POST','PUT','DELETE') and request.url.path not in ('/api/auth/logout','/api/auth/tour') and session['user']['role']=='viewer': raise HTTPException(403,'Viewer accounts cannot execute or change policy')
    return session

@app.get('/api/health')
def health(): return {'status': 'ok', 'version': '0.2.0', 'simulated_default': True}

@app.get('/api/auth/status')
def auth_status(): return {'setup_required': auth.setup_required(),'public_registration':os.getenv('AGENTSHIELD_PUBLIC_REGISTRATION')=='1','public_mode':os.getenv('AGENTSHIELD_PUBLIC')=='1'}

@app.post('/api/auth/setup')
def setup(body: Credentials, response: Response):
    auth.create(body)
    return auth.login(body, response)

@app.post('/api/auth/register')
def register(body: Credentials, response: Response):
    auth.create(body,registration=True)
    return auth.login(body,response)

@app.post('/api/auth/login')
def login(body: Credentials, response: Response):
    return auth.login(body, response)

@app.get('/api/session')
def session(request: Request): return auth.session(request)

@app.post('/api/auth/logout', dependencies=[Depends(authorized)])
def logout(request: Request, response: Response):
    auth.logout(request, response)
    return {'status': 'signed_out'}

@app.post('/api/auth/tour', dependencies=[Depends(authorized)])
def complete_tour(request: Request): return auth.complete_tour(request)

@app.get('/api/scenarios', dependencies=[Depends(authorized)])
def scenarios():
    return [dict(id=k, label=v['label'], malicious=v['malicious'], heldout=v.get('heldout', False)) for k, v in SCENARIOS.items()]

class RunRequest(Strict):
    scenario: str
    mode: Literal['unprotected', 'prompt_only', 'protected'] = 'protected'

@app.post('/api/runs', dependencies=[Depends(authorized)])
def start_run(body: RunRequest):
    if body.scenario not in SCENARIOS: raise HTTPException(422, 'Unknown scenario')
    with store.lock: return run_scenario(active_gateway(), body.scenario, body.mode)

@app.get('/api/runs', dependencies=[Depends(authorized)])
def runs(): return store.runs()

@app.get('/api/events', dependencies=[Depends(authorized)])
def events(): return store.events()

@app.get('/api/policy', dependencies=[Depends(authorized)])
def policy(): return active_gateway().policy.model_dump()

@app.put('/api/policy', dependencies=[Depends(authorized)])
def set_policy(body: Policy):
    # An editable policy cannot relax the hard laboratory network/filesystem boundary.
    if any(p not in body.restricted_patterns for p in PATTERNS):
        raise HTTPException(422, 'Baseline synthetic redaction pattern must remain configured')
    if len(body.restricted_patterns) > 12 or any(len(p) > 128 for p in body.restricted_patterns):
        raise HTTPException(422, 'Pattern limits exceeded')
    try:
        for pattern in body.restricted_patterns: re.compile(pattern)
    except re.error: raise HTTPException(422, 'Invalid regular expression')
    if os.getenv('AGENTSHIELD_PUBLIC')=='1' and body.restricted_patterns!=['SYNTHETIC_SECRET_[A-Z0-9_]+']: raise HTTPException(422,'Public workspaces use the fixed synthetic redaction pattern')
    with store.lock:
        if os.getenv('AGENTSHIELD_PUBLIC')=='1': store.save_policy(body)
        else: gateway.policy = body
        if os.getenv('AGENTSHIELD_PUBLIC')!='1': PATTERNS[:] = list(body.restricted_patterns)
        store.event('policy', 'policy_updated', {'policy': body.model_dump()})
    return body

@app.get('/api/approvals', dependencies=[Depends(authorized)])
def approvals(): return store.approvals()

class ApprovalRequest(Strict):
    decision: Literal['approve', 'reject']

@app.post('/api/approvals/{approval_id}', dependencies=[Depends(authorized)])
def approval(approval_id: str, body: ApprovalRequest):
    try: return active_gateway().approve(approval_id, body.decision == 'approve')
    except LookupError as error: raise HTTPException(404, str(error))
    except ValueError as error: raise HTTPException(409, str(error))

class EvaluationRequest(Strict):
    heldout: bool = False
    trials: int = Field(default=1, ge=1, le=10)

@app.post('/api/evaluation', dependencies=[Depends(authorized)])
def evaluation(body: EvaluationRequest):
    if os.getenv('AGENTSHIELD_PUBLIC')=='1' and body.trials>2:raise HTTPException(422,'Public pilot permits at most two trials per evaluation')
    with store.lock: return experiment(active_gateway(), body.heldout, body.trials)

def active_gateway():
    return Gateway(LAB_ROOT,store,store.policy_for_owner()) if os.getenv('AGENTSHIELD_PUBLIC')=='1' else gateway

@app.get('/api/model',dependencies=[Depends(authorized)])
def model_status():
    import httpx
    enabled=os.getenv('AGENTSHIELD_ENABLE_REAL_MODEL','1' if not PUBLIC_MODE else '0')=='1'
    model=os.getenv('AGENTSHIELD_MODEL','qwen3:0.6b')
    result={'enabled':enabled,'model':model,'provider':'ollama-local','available':False}
    if enabled:
        from .model_adapter import model_endpoint
        try:
            with httpx.Client(trust_env=False,follow_redirects=False,timeout=2) as client:
                response=client.get(model_endpoint().replace('/api/chat','/api/tags'))
                result['available']=response.status_code==200 and any(m.get('name')==model for m in response.json().get('models',[]))
        except (httpx.HTTPError,ValueError): pass
    return result

class RealModelRequest(Strict):
    task: str=Field(min_length=1,max_length=2000)

@app.post('/api/real-runs',dependencies=[Depends(authorized)])
def real_run(body:RealModelRequest):
    status=model_status()
    if not status['enabled'] or not status['available']: raise HTTPException(503,'Configured local model is unavailable; use simulation or start the local model service')
    from .model_adapter import OllamaAdapter
    with store.lock:return OllamaAdapter(status['model']).run(active_gateway(),body.task)

# Optional built dashboard, served on the API's origin in the container.
if (ROOT / 'static').is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount('/', StaticFiles(directory=ROOT / 'static', html=True), name='dashboard')
