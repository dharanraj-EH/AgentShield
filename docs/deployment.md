# Operating AgentShield and preparing a public research pilot

AgentShield remains a research prototype. The Windows workflow supports actual local model inference. The public pilot supports synthetic simulations and public registration; it does not provide public model inference or a company production service.

## This Windows computer

1. Open PowerShell in `D:\VS Code\AgentShield`.
2. Run `scripts\start.ps1` if the services are stopped. This launches the receiver, backend, frontend and the installed Ollama runtime when available. Keep this terminal open.
3. Open `http://127.0.0.1:5173`. Create your own first local account if asked, or sign in. No default password exists. Complete the guided tour.
4. In Agent laboratory, run the legitimate summary with Offline simulation. Then use Run comparison for the embedded document attack. Inspect decisions and redacted events.
5. In Agent laboratory select Real local model, enter `Read public/report.txt and summarize its incident counts.`, and run it. Real execution is always protected. Inspect actual proposals and outcomes. A model may refuse, fail, or choose no tool; none of these automatically proves gateway enforcement.
6. Run the approval scenario and approve the exact stored action in Approval queue. A second approval is rejected. Approvals cannot change arguments.

Optional model commands:

```powershell
.\scripts\install-ollama.ps1
.\scripts\start-ollama.ps1
.\scripts\pull-model.ps1
.\.venv\Scripts\python.exe -m backend.real_evaluation --trials 2
```

The runtime archive, portable executable and model files use `D:\Softwares`. The initial model is `qwen3:0.6b`. Ollama binds only to `127.0.0.1:11434`, with cloud support disabled. Do not expose this port publicly. The model is not given shell access or unrestricted filesystem/network tools.

## Docker demonstration

```powershell
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://127.0.0.1:8780/api/health
docker compose down
```

Open `http://127.0.0.1:8780`. This is a separate workspace/database from the native development app. Its local account is created on first use. Generated files, accounts and evidence persist under `data/`. The receiving endpoint stays inside the application container. The application is on an internal network; only NGINX is connected to the ingress bridge. The native Ollama server is intentionally unavailable to this default container.

Docker Desktop was already installed in `C:\Program Files\Docker`. Its existing managed image storage has not been relocated. New portable-runtime/model downloads are under `D:\Softwares`; Docker manages its own image layers separately.

## Docker socket recovery

The observed crash concerned the stale `dockerInference` runtime socket. Closing Docker and renaming its runtime directory fixed this instance, without factory reset or removal of images. The preserved backup is under `%LOCALAPPDATA%\Docker\run.backup-*`. If the exact problem recurs, quit Docker Desktop and run `scripts\repair-docker-socket.ps1`, then reopen Docker Desktop. The script refuses to operate while Docker is running. This is a specific recovery, not a universal Docker repair.

## Free public pilot without buying a domain

Use a free Render Docker web service and a separate free Neon PostgreSQL database. Render supplies an HTTPS `onrender.com` address. Provider plans can change; choose the free plans explicitly and check the current dashboard before accepting terms. Do not add paid resources automatically. Free Render instances sleep when idle and their local filesystem is ephemeral; the external database is required for account/evidence persistence.

The remaining publishing steps require accounts owned by you. Never paste passwords, database URLs or provider tokens into this chat or commit them.

1. Create a GitHub account/repository and upload the project source. Exclude `.env`, `.venv`, `work`, `data`, `lab`, databases, `node_modules` and evaluation output. Inspect `git status` before any commit. The project does not create or publish a repository automatically.
2. Create a Neon project using its Free plan. Copy its PostgreSQL connection string with TLS (`sslmode=require`) into the hosting dashboard secret field only. Keep this database dedicated to the pilot.
3. Create a Render account. Choose **New Blueprint**, connect that repository and select `render.yaml`. Verify its web service plan says Free.
4. Supply `DATABASE_URL` as a secret environment variable. `RENDER_EXTERNAL_URL` supplies the expected HTTPS origin. On another provider, explicitly set `AGENTSHIELD_PUBLIC_ORIGIN=https://your-assigned-hostname`.
5. Public configuration must keep `AGENTSHIELD_PUBLIC=1`, `AGENTSHIELD_PUBLIC_REGISTRATION=1`, and `AGENTSHIELD_ENABLE_REAL_MODEL=0`. Startup refuses public mode without HTTPS origin and PostgreSQL, and refuses enabling public inference in this pilot.
6. After deployment, check `/api/health`. Open the assigned HTTPS address. Register two disposable accounts and verify each sees only its own runs, events, approvals and saved policy. Verify an approval URL from account A returns 404 from account B. Confirm cookies are Secure and HttpOnly in browser developer tools.
7. Restart the web service and confirm both accounts and histories persist. Run the legitimate summary, restricted read, restricted payload and approval cases. If any boundary fails, suspend public access and repair it before inviting users.
8. Delete disposable test accounts/data through an administrative database procedure before an actual pilot. This prototype does not yet offer a user deletion interface; avoid collecting personal information.

Public users receive the `operator` role and cannot claim the owner role. Each account has its own policies and evidence. Generated fixture contents are shared synthetic data. Public policies cannot add arbitrary regular expressions. Registration is capped at 500 accounts and 10 creations per ten minutes per process; these are prototype limits, not distributed abuse protection.

## Before company use

An organizational deployment needs independent security review, managed authentication/SSO, email verification and account recovery, centralized/distributed rate limiting, backups and tested restoration, monitoring, retention/deletion controls, incident response, load testing, dependency patching and a supported inference service. The current public signup has no email verification, MFA, password reset email, billing or availability guarantee. Local locks and rate limits assume one application process. Use synthetic data only in this pilot. Free hosting does not make this a production company gateway.

Official references: [Render free service limitations](https://render.com/docs/free), [Render Blueprint specification](https://render.com/docs/blueprint-spec), [Neon plans](https://neon.com/pricing), [Ollama Windows](https://docs.ollama.com/windows).
