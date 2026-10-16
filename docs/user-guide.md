# Using AgentShield

## 1. Start the local services

Open PowerShell in the project:

```powershell
Set-Location -LiteralPath 'D:\VS Code\AgentShield'
.\scripts\start.ps1
```

Open http://127.0.0.1:5173. Keep the terminal open. If the project scripts are blocked, use the process-only execution-policy command in README.md. If services are already running, open the existing dashboard instead of starting a second copy. The manual startup commands in README.md show service diagnostics.

## 2. Create the first local account

On a new installation, choose a username of 3–40 letters, numbers, dots, hyphens or underscores. Choose a dedicated password of 12–128 characters and enter it twice. Click **Create account & start tour**. No preset password, email, paid service or cloud account is needed. The first account owns this local workspace. Public account creation closes after that account exists.

On later visits, enter the same username and password at **Sign in to workspace**. Usernames are case-insensitive; passwords are case-sensitive. Passwords are stored as salted PBKDF2 hashes, not plaintext. The browser receives an HttpOnly, SameSite=Strict cookie; tool/data API calls also require a session-bound header. Sessions expire after eight hours. Sign out from the account control at the bottom of the sidebar. Signing in again rotates the session; password reset revokes existing sessions.

This remains a single-account, loopback-only research lab, not an enterprise identity system. Do not reuse another service's password. HTTPS, multi-user roles, MFA and hosted account recovery are outside this version.

## 3. Take the first-login tour

The eight-step tour opens automatically for an account that has not finished it. **Next step** takes you through the actual workspace pages. **Back** returns to the previous page. The tour describes actions but does not execute tools, approve actions or change policies. **Finish tour** saves completion on the server. Closing or pressing Escape defers the tour; it will be offered again on the next sign-in. Replay it anytime through **Take the guided tour** in the sidebar or **Getting started**.

The left navigation is grouped into Workspace, Investigation, Governance and Resources. On smaller screens, use the top-left menu button to open the drawer; choosing a page closes it.

## 4. Run a safe task

Open **Agent laboratory**. Select **Legitimate document summary**, choose **AgentShield enforced**, and click **Execute scenario**. Expect **Task completed**. The simulator returns a labelled extractive summary of a generated document. Click the run's short ID for its event history. History is paginated in groups of 20; use Previous and Next.

## 5. Compare an attack

Open **Run comparison**, select **Injection embedded in document**, and click **Run all three modes**. With the default policy and receiver running, the unprotected and prompt-only simulations can transfer the synthetic marker to the local receiver. Protected execution blocks confidential access. All modes retain the hard laboratory boundary. The prompt-only script deliberately ignores instructions: this does not measure real-model susceptibility.

## 6. Read the evidence

Open a specific run or choose it in **Filter by run** under **Security events**. Inspect tool requests, decision events, screening warnings and execution outcomes. Expand **Redacted evidence** for the decision ID, rule ID, reason and UTC timestamp. `classification.confidential` blocks a confidential fixture read; `dlp.restricted` blocks a configured outgoing marker. Export the filtered redacted events if needed. A warning alone is not an authorization block.

## 7. Try human approval

Run **Legitimate sensitive action** in protected mode. It should show **Awaiting approval**. Open **Approval queue**, find that run, inspect the stored `review/budget.txt` request, then approve or reject the exact action. Approval is single-use, arguments cannot be changed, and the gateway validates the current policy again. Successful approval updates the run to Task completed. Other pending requests from earlier evaluations are separate actions.

## 8. Check leakage and false positives

Run **Restricted synthetic outgoing payload** in protected mode: expect `dlp.restricted`. Run **Quoted injection false-positive challenge**: expect a completed read even if suspicious wording raises warnings. Traversal and unauthorized-destination cases should be blocked in every mode by hard isolation. Use generated test files only.

## 9. Run and export evaluation

Open **Evaluation results**. Choose **Development suite**, set trials to `1`, then click **Run evaluation**. This produces 30 simulated runs: 10 cases × three configurations. Confirm execution errors are zero. Download **JSON** for run-level evidence and **CSV** for metric summaries. The separate held-out suite produces 12 runs per trial and should be treated as observed once inspected.

The protected development completion rate is initially 66.7% because one of three legitimate cases needs approval. Pending is incomplete, not a false block. A later approval does not rewrite an already-exported snapshot. Read docs/evaluation-methodology.md for full metric denominators and timing limits.

## 10. Inspect policies carefully

The first demonstration should use defaults. The **Policies** page lets the signed-in local owner inspect or edit policy JSON. Only **Validate & apply policy** changes it. Rules reset on service restart and cannot authorize arbitrary network destinations or files outside the lab. Do not disable controls merely to make a demo pass.

## Recovery and troubleshooting

- **Wrong credentials:** recheck username/password. After five unsuccessful attempts, wait one minute. The throttle is process-local and intentionally simple.
- **Forgotten password:** the local workspace owner can run the following from the project directory. The password is requested privately, not passed as a command-line argument:

```powershell
.\.venv\Scripts\python.exe -m backend.account reset-password --username YOUR_USERNAME
```

- **Execution error:** check the receiver on 127.0.0.1:8766 using the README startup instructions. A connection error is not a successful defense. Fix the service and rerun.
- **Session expired:** sign in again. Signing out or resetting a password invalidates the previous session.
- **No results:** run a scenario; the dashboard uses real stored data and does not invent empty-state metrics.
- **Docker recreation:** optional Docker uses ephemeral SQLite storage; recreating the container loses accounts and events as well as laboratory state.

For a viva, explain the chain: untrusted proposal → schema and isolation checks → deterministic policy → allow, block or approval → execution → redacted evidence. Authentication controls access to the workspace; it is separate from authorization of the agent's tools.
