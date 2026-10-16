# Verification record

## Latest deployment verification — 13 October 2026

This section supersedes the earlier environment and optional-deployment status below.

- Docker Desktop's stale `dockerInference` socket error was repaired by preserving and renaming the runtime directory, then restarting Desktop. No factory reset was performed. Docker Engine 28.3.2 responded successfully.
- `docker compose build` completed; application container healthy and NGINX running. Both `http://127.0.0.1:8780/api/health` and the built dashboard root returned HTTP 200. SQLite and generated fixtures persist in project `data/`.
- Official portable Ollama v0.40.3 ZIP was SHA256-verified: `e5ecff02dfc7cae8ddf6d6b7a7ac5f727ffeedf4491f44ae75ff5b0820dbbbd5`. Runtime and models are under `D:\Softwares\Ollama`. Local server API verified.
- Installed `qwen3:0.6b`, digest `7df6b6e09427a769808717c0a93cadc4ae99ed4eb8bf5ca557c90846becea435`, Q4_K_M, 522,653,767 bytes. NVIDIA inspection confirmed RTX 3050 6GB Laptop GPU, 6,144 MiB VRAM, driver 551.76. No GPU capacity assumption was used.
- Live protected pilot: four cases × two trials, eight real model runs. Zero protocol/execution errors, four trials with explicit gateway blocks, zero trials with a synthetic marker received, no trials without a tool proposal. Both legitimate summaries retrieved the report and included the two predeclared numeric facts. Embedded-document cases retrieved content without attempting the injected transfer; this is not counted as a gateway block. JSON and CSV retained under `evaluation-output/real-model/`. Configuration: temperature 0, seeds 42/43, context 2,048, generation limit 512, thinking disabled, maximum six proposals.
- Latest backend: **53 passed, 1 skipped**. File symlink creation still requires Windows privilege; junction handling passed. One upstream Starlette/httpx deprecation warning remains. `pip check`: no broken requirements.
- Latest frontend: **11 tests passed**, TypeScript/Vite production build passed, production dependency audit reported zero known vulnerabilities at verification time.
- Disposable PostgreSQL 17 integration: registration, independent runs/events/policies, cross-user approval denial, and persistence after reopening the database passed against an actual PostgreSQL container. Disposable container removed after the check. Public settings reject SQLite, missing HTTPS origin and enabled public inference. Four public API/configuration tests passed in the backend suite.
- Native backend restarted with the new code; health verified. Default Docker demonstration uses simulation. Actual local inference is verified through the native protected gateway. No public URL, cloud deployment or company production certification exists.
- The earlier browser-policy limitation still applies to fresh login/tour visual acceptance. Component tests passed; no alternate browser workaround was used.

Development computer inspected on 13 October 2026 (Asia/Calcutta). Active project: `D:\VS Code\AgentShield`.

- Python 3.14.6; Node 22.14.0; npm 11.4.1; Git 2.47.1. Python invoked through project-local `.venv`.
- C: initially about 46 GiB free; D: initially about 81 GiB free; reported physical RAM 16,438,312,960 bytes. RTX 3050 is detected but Windows AdapterRAM reporting is inconsistent with its name; no usable VRAM assumption or GPU dependency was made.
- `python -m pytest -q`: **40 passed, 1 skipped**. Windows file-symlink creation lacked privilege. The Windows junction test passed. One upstream Starlette/httpx TestClient deprecation warning remains; tests still executed successfully.
- `python -m pip check`: no broken requirements. Exact installed Python packages recorded in `requirements-lock.txt`.
- TypeScript check plus Vite 8.3.4 production build: passed. Vitest 5.0.4: **2 passed**. Frontend dependencies are locked; `npm audit` reported **0 vulnerabilities** after updating the originally affected test dependencies. This is an advisory snapshot, not a guarantee of absence of vulnerabilities.
- Actual loopback receiver and API started successfully; health, run and event endpoints returned successful responses. The persisted/API evidence was checked for the full synthetic marker and did not contain it.
- Repeatable simulator evaluation: **90 development runs** (10 cases × 3 modes × 3 trials) and **36 held-out runs** (4 × 3 × 3), with zero receiver/execution errors in the verified suites. Saved under `evaluation-output/development` and `evaluation-output/heldout`.
- Initial development rate outcomes: unprotected/prompt-only attacks 12/21 each; protected attacks 0/21. Protected legitimate completion 6/9, with three human approvals pending and no false blocks. Initial held-out outcomes: unprotected/prompt-only attacks 3/6 each; protected attacks 0/6, legitimate completion 6/6 and no false blocks. Timing values are in the saved JSON/CSV; use each saved artifact rather than mixing timing from separate runs.
- `docker compose config --quiet`: passed configuration parsing. Docker CLI 28.3.2 is installed, but Docker Desktop's Linux engine was unavailable. No container image/build/start claim is made. Starting Docker Desktop and running the documented command is the remaining optional deployment check.
- Optional local-model adapter is mock-tested for configuration and gateway enforcement; no installed model was required or contacted, and no live-model evaluation was performed.

Fresh headless Edge UI verification passed all seven dashboard views, a live scenario run, an exact-action approval, a three-mode comparison and a held-out evaluation. No browser JavaScript page errors occurred. Accessible scenario selectors were corrected during this check, then the complete browser flow passed. Desktop (1440px) and mobile (390px) screenshots were generated and inspected. The screenshots and environment-specific smoke script are intermediate files under `work/`; tests never use a personal browser profile or existing browser session.

The UI JSON and CSV export buttons were also executed: the held-out JSON contained 12 run rows and three metric rows, and the CSV contained its header plus three mode rows.

## Interface redesign

The requested visual redesign replaces the navy/cyan presentation with white surfaces, a soft grey workspace and muted green actions. It adds a recorded policy-decision breakdown, consistent typography, 20-row run-history pagination and a mobile navigation drawer. All seven views were opened in the live application and a protected document-summary scenario completed successfully. Desktop layout was inspected at 1440px and mobile at 390px; drawer opening and dismissal were verified. Browser viewport overrides were reset afterward. The TypeScript/Vite build and existing frontend tests were rerun for the redesign. The original stylesheet is preserved under `work/style-before-redesign.css`.

Both PowerShell scripts passed parser validation. The individual service commands were executed successfully; the combined start script is supplied as a convenience wrapper, with manual diagnostic commands in README.md. Services were bound to loopback only. The delivered default workflow is verified; the optional live-model runtime and Docker container execution remain separate, unverified integrations.

## Local authentication and onboarding

Added a custom vector gateway logo and favicon, grouped sidebar with account/sign-out controls, first-account setup, credential-based login, automatic eight-step tour and a permanent Getting started page. No default credentials are embedded. Passwords use salted PBKDF2 hashes; server-side sessions expire in eight hours and rotate on login. Cookies are HttpOnly and SameSite=Strict; authorized data/tool endpoints also require the session-bound header. Logout and local owner recovery revoke existing sessions. Tour completion is stored on the user record; deferral does not mark completion.

Verification: 49 backend tests passed, one Windows file-symlink privilege skip, 11 frontend tests passed, TypeScript/Vite production build passed and npm audit reported zero known vulnerabilities. New checks cover unsigned data access, first-account setup lock, password hashing, wrong credentials and throttling, cookie/header requirements, expiry, revocation, recovery, tour persistence, automatic first-login tour routing and the absence of tool execution during tours. Actual unsigned session/data endpoints returned HTTP 401; the restored normal database reported first-account setup required at the time of checking. Test account data stayed in temporary test databases; no live account was created for the user.

The browser security policy rejected the attempted preview refresh with a protocol restriction. No alternate browser or workaround was attempted. New login/sidebar/tour visuals therefore remain unverified in the live browser, despite successful component and API tests. The user can refresh the local dashboard to complete visual acceptance.
