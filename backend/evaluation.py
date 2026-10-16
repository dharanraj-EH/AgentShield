"""Repeatable control evaluation. No simulated result is an LLM robustness claim."""
import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from .lab import MODES, run_scenario
from .scenarios import SCENARIOS, generate
from .gateway import Gateway
from .store import Store, now

def metrics(rows):
    output = []
    baseline = {(r['scenario'], r.get('trial', 0)): r['duration_ms'] for r in rows if r['mode'] == 'unprotected'}
    for mode in MODES:
        group = [r for r in rows if r['mode'] == mode]
        attacks = [r for r in group if r['malicious']]
        legitimate = [r for r in group if not r['malicious']]
        latencies = [v for r in group for v in r['decision_latencies_ms']]
        overhead = [r['duration_ms'] - baseline[(r['scenario'], r.get('trial', 0))] for r in group if (r['scenario'], r.get('trial', 0)) in baseline]
        output.append(dict(mode=mode, provider='deterministic-simulator-v1', simulated=True,
          attack_trials=len(attacks), legitimate_trials=len(legitimate),
          attack_success_rate=sum(r['attack_success'] for r in attacks) / len(attacks) if attacks else None,
          legitimate_completion_rate=sum(r['legitimate_complete'] for r in legitimate) / len(legitimate) if legitimate else None,
          false_block_rate=sum(r['blocked'] for r in legitimate) / len(legitimate) if legitimate else None,
          pending_approvals=sum(r.get('pending_approval', False) and not r.get('approval_resolved', False) for r in group),
          execution_errors=sum(r.get('execution_error', False) for r in group),
          mean_decision_latency_ms=mean(latencies) if latencies else None,
          mean_end_to_end_ms=mean(r['duration_ms'] for r in group) if group else None,
          mean_overhead_vs_unprotected_ms=mean(overhead) if overhead else None))
    return output

def experiment(gateway, heldout=False, trials=1):
    rows = []
    for trial in range(trials):
        for name, case in SCENARIOS.items():
            if case.get('heldout', False) != heldout: continue
            for mode in MODES:
                rows.append({**run_scenario(gateway, name, mode), 'trial': trial})
    return {'dataset': 'heldout-v1' if heldout else 'development-v1', 'trials': trials,
        'timestamp': now(), 'provider': 'deterministic-simulator-v1', 'simulated': True,
        'policy_snapshot': gateway.policy.model_dump(),
        'interpretation': 'Simulated control enforcement only; approval cases remain pending until a human acts.',
        'metrics': metrics(rows), 'runs': rows}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--heldout', action='store_true')
    parser.add_argument('--trials', type=int, default=1)
    parser.add_argument('--output', default='evaluation-output')
    args = parser.parse_args()
    if not 1 <= args.trials <= 100: parser.error('trials must be 1..100')
    root = Path('lab').resolve(); generate(root)
    result = experiment(Gateway(root, Store()), args.heldout, args.trials)
    out = Path(args.output); out.mkdir(exist_ok=True, parents=True)
    (out / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    with (out / 'metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(result['metrics'][0])); writer.writeheader(); writer.writerows(result['metrics'])
    print(json.dumps(result['metrics'], indent=2))
    if any(r.get('execution_error') for r in result['runs']):
        raise SystemExit('Evaluation incomplete: execution errors occurred. Is the receiver running?')
if __name__ == '__main__': main()
