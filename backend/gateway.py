import json
import time
from pathlib import Path
import httpx
from .security import Action, Policy, SCHEMAS, decide, safe_path, safe_url, screen
from .store import Approval, Run, uid, now, current_owner

class Gateway:
    def __init__(self, root, store, policy=None):
        self.root = Path(root).resolve()
        self.store = store
        self.policy = policy or Policy()

    def execute(self, action):
        args = SCHEMAS[action.tool].model_validate(action.arguments).model_dump()
        if action.tool == 'send_http_request':
            url = safe_url(args['url'])
            # Fixed literal loopback destination; environment proxies and redirects disabled.
            with httpx.Client(trust_env=False, follow_redirects=False, timeout=3) as client:
                response = client.post(url, json={'payload': args['payload']})
                if 300 <= response.status_code < 400: raise ValueError('Redirects are forbidden')
                response.raise_for_status()
                return response.json()
        path = safe_path(self.root, args['path'])
        if action.tool == 'list_files':
            if not path.is_dir(): raise ValueError('Expected a directory')
            return sorted(p.name for p in path.iterdir() if p.is_file() and not p.is_symlink())
        if not path.is_file(): raise ValueError('Expected a regular file')
        if path.stat().st_size > 65536: raise ValueError('File exceeds laboratory size limit')
        return path.read_text(encoding='utf-8')

    def request(self, run_id, action, protected=True, approved=False):
        self.store.event(run_id, 'tool_request', {'tool': action.tool, 'arguments': action.arguments})
        start = time.perf_counter()
        decision, rule, reason = decide(self.root, action, self.policy, protected, approved)
        elapsed = (time.perf_counter() - start) * 1000
        result = dict(decision_id=uid(), run_id=run_id, tool=action.tool, decision=decision,
                      rule_id=rule, reason=reason, timestamp=now(), decision_latency_ms=elapsed)
        self.store.event(run_id, 'decision', result)
        if decision == 'require_approval':
            approval_id = uid()
            with self.store.session.begin() as db:
                db.add(Approval(id=approval_id, run_id=run_id, action=action.model_dump_json(), status='pending', timestamp=now()))
            self.store.event(run_id, 'approval_requested', {'approval_id': approval_id})
            return {**result, 'approval_id': approval_id}
        if decision == 'block': return result
        try:
            output = self.execute(action)
            warnings = screen(output if isinstance(output, str) else json.dumps(output))
            if warnings: self.store.event(run_id, 'screening', {'patterns': warnings, 'interpretation': 'Risk signal only', 'source': 'tool_response'})
            self.store.event(run_id, 'execution', {'tool': action.tool, 'status': 'success', 'output': output})
            # Raw output only stays inside the agent loop, never in the API response or event store.
            return {**result, 'output': output, 'status': 'success'}
        except (ValueError, OSError, httpx.HTTPError) as error:
            self.store.event(run_id, 'execution', {'tool': action.tool, 'status': 'error', 'reason': str(error)})
            return {**result, 'status': 'error', 'reason': str(error)}

    def approve(self, approval_id, approve):
        # Serialize consumption in this single-process laboratory. Database compare-and-set
        # additionally prevents duplicate consumption across processes.
        with self.store.lock:
            with self.store.session.begin() as db:
                approval = db.get(Approval, approval_id)
                if not approval: raise LookupError('Approval does not exist')
                if current_owner.get() and approval.owner_id not in (None,current_owner.get()): raise LookupError('Approval does not exist')
                import os
                if os.getenv('AGENTSHIELD_PUBLIC')=='1' and approval.owner_id!=current_owner.get(): raise LookupError('Approval does not exist')
                if approval.status != 'pending': raise ValueError('Approval has already been consumed')
                action = Action.model_validate_json(approval.action)
                run_id = approval.run_id
                updated = db.query(Approval).filter(Approval.id == approval_id, Approval.status == 'pending').update({'status': 'approved' if approve else 'rejected'})
                if updated != 1: raise ValueError('Approval has already been consumed')
            self.store.event(run_id, 'approval', {'approval_id': approval_id, 'approved': approve, 'actor': 'local-human-session'})
            if not approve:
                with self.store.session.begin() as db:
                    run = db.get(Run, run_id)
                    if run:
                        data = json.loads(run.result)
                        data.update(approval_resolved=True, pending_approval=False, legitimate_complete=False)
                        run.result = json.dumps(data)
                return {'status': 'rejected'}
            # Fresh policy and filesystem checks; approval bypasses only the approval gate.
            result = self.request(run_id, action, protected=True, approved=True)
            with self.store.session.begin() as db:
                run = db.get(Run, run_id)
                if run:
                    data = json.loads(run.result)
                    data['approval_resolved'] = True
                    data['pending_approval'] = False
                    data['legitimate_complete'] = result.get('status') == 'success'
                    run.result = json.dumps(data)
            from .security import redact
            return redact(result)
