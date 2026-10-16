# AgentShield

**Design and Evaluation of a Policy-Enforced Security Gateway Against Prompt Injection and Data Exfiltration in Tool-Using AI Agents**

An M.Sc. research prototype. Python/FastAPI/Pydantic/SQLAlchemy/SQLite backend; React/TypeScript/Vite dashboard. The default agent is explicitly **simulated**, deterministic and offline. No external credentials, GPU, shell tool or paid service is required. A local workspace account controls access to the dashboard. A local receiver is used to observe synthetic transfers safely.

## Windows quick start

Prerequisites: Python 3.11+ and Node 22.12+ on the Node 22 line, Node 24, or Node 26+. This computer's Node 22.14.0 is compatible with the verified frontend tooling.

Open a PowerShell terminal in `D:\VS Code\AgentShield`:

```powershell
Set-Location -LiteralPath 'D:\VS Code\AgentShield'
# Needed only if your terminal refuses this project's scripts. No administrator needed.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
.\scripts\start.ps1
```

Open http://127.0.0.1:5173. On first use, create a username and a unique password (at least 12 characters). The guided tour opens automatically. Later, sign in with those credentials; no preset password is supplied. Use Getting started for complete instructions or to replay the tour. Keep the terminal open; Ctrl+C stops the services. The supplied setup uses `py -3` only when creating a new environment; it then checks for Python 3.11+. This computer was verified with Python 3.14.6. Activation is unnecessary: scripts call the environment's executable directly. Node 22.14.0, npm 11.4.1 and Git 2.47.1 were inspected. No system install was required for the default lab.

If startup fails, run these in **three separate terminals** from the project root to see diagnostic output:

```powershell
# Terminal 1: synthetic receiving service
.\.venv\Scripts\python.exe -m uvicorn backend.receiver:app --host 127.0.0.1 --port 8766
# Terminal 2: gateway/API
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
# Terminal 3: dashboard
Set-Location frontend
npm.cmd run dev
```

Use `npm.cmd` on Windows to avoid PowerShell's npm.ps1 execution-policy issues. The backend creates only generated fixtures inside `lab/` and a local SQLite database. Existing fixture files are preserved. Do not put real documents or credentials in the laboratory.

## Checks and repeatable experiments

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
Push-Location frontend
npm.cmd run build
npm.cmd test
Pop-Location
# Start the receiver first. Results are written even if a receiver error occurs;
# in that case the CLI exits unsuccessfully and the experiment is incomplete.
.\.venv\Scripts\python.exe -m backend.evaluation --trials 3 --output evaluation-output/development
.\.venv\Scripts\python.exe -m backend.evaluation --heldout --trials 3 --output evaluation-output/heldout
```

JSON includes per-run outcomes and CSV includes metric summaries. CLI trials are repeated simulator executions, not repeated LLM trials. A protected approval case stays incomplete until a human approves it; suite results do not silently auto-approve. The dashboard's JSON/CSV downloads export the most recent evaluation in that page session.

## What to demonstrate

In **Run comparison**, select injection embedded in a document and run all three modes. Unprotected and prompt-only simulations follow the hostile sequence and can deliver the synthetic marker to the local receiver. Protected execution reads the document, flags suspicious instructions, and blocks confidential-file access before sending anything. The prompt-only simulator deliberately ignores its instructions; this demonstrates the absence of an external enforcement boundary, **not** how frequently any actual model fails.

Use **Approval queue** for the legitimate sensitive action and **Security events** to inspect rule IDs and redacted evidence. Policies can be edited as JSON; edits are in memory and restart resets defaults. `policies/default.json` is an export/example of those defaults. Hard isolation cannot be relaxed by policy edits.

## Optional local model

`backend/model_adapter.py` provides a local Ollama JSON-action adapter. The supplied optional scripts install a SHA256-verified portable runtime and download a small model under `D:\Softwares`:

```powershell
.\scripts\install-ollama.ps1
.\scripts\start-ollama.ps1
.\scripts\pull-model.ps1
.\.venv\Scripts\python.exe -m backend.model_adapter --model qwen3:0.6b --task 'Read public/report.txt and summarize its incident counts.'
.\.venv\Scripts\python.exe -m backend.real_evaluation --model qwen3:0.6b --trials 2
```

The endpoint is restricted to loopback port 11434 (or the named private Ollama service in container mode); proxies and redirects are disabled. No credentials are used. Configuration is `OllamaAdapter(model, temperature=0, seed=42).run(gateway, task, max_steps=6)`. Proposals are schema-validated, step-limited, and always protected by the gateway. Model identifiers and configuration are recorded in events and run history. In Agent laboratory, select **Real local model** once the installed model is available. Real-model results are kept separate from simulated experiment metrics. A small model can produce poor summaries or invalid proposals; these are reported as failures, not successful security evaluations. See `docs/deployment.md` and the evaluation methodology.

## Optional Docker Compose

After local checks pass, a Docker Desktop Linux-container installation may run:

```powershell
docker compose up --build
# Dashboard/API: http://127.0.0.1:8780
docker compose down
```

The application serves the built frontend, API and loopback-only receiver on an internal Docker network. A separate unprivileged NGINX proxy publishes only host loopback port 8780. The application has a read-only root filesystem; generated fixtures and SQLite persist in the project `data/` directory. Back up this directory with the services stopped. Never mount personal folders into the laboratory. `docker compose down` preserves data. The default container demonstration uses simulation; the verified local-model workflow runs through the native backend at port 8765. See `docs/deployment.md` for the free public pilot configuration, registration, isolation and hosting limitations.

## Project map

`backend/security.py` contains schemas and pure policy checks; `gateway.py` is the executor boundary; `lab.py` is the scripted agent; `scenarios.py` generates safe fixtures; `store.py` persists redacted evidence; `app.py` exposes the local API; `evaluation.py` calculates metrics. The frontend uses actual API responses and contains no sample metrics. `requirements-lock.txt` records the verified Python environment; `frontend/package-lock.json` records frontend dependencies.

Read the complete [user guide](docs/user-guide.md), then [architecture](docs/architecture.md), [threat model](docs/threat-model.md), [evaluation methodology](docs/evaluation-methodology.md), [limitations](docs/limitations.md), [demo script](docs/demo-script.md), and [viva guide](docs/viva-guide.md). Build status and evidence are in `PLAN.md` and `docs/verification.md`.

This is a research laboratory, not a production security product. No novelty claim is made without a literature review and broader independent evaluation.
