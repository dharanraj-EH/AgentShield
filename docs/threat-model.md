# Threat model

**Assets:** synthetic confidential markers, tool authority, approval integrity, isolation and useful investigation evidence. The project handles no real credentials by design.

**Adversary:** controls text in a generated document or tool response, or produces malicious/malformed tool proposals. Goals include reading a confidential fixture, sending its marker, escaping the sandbox, using an unauthorized destination, or changing/replaying an approval. The adversary cannot change trusted gateway code, administrator policy, process memory, the local operating system or fixture directories concurrently in this threat model.

**Trust boundaries:** document to agent; model proposal to gateway; gateway to filesystem/network; approval client to server-stored action; event store to dashboard. A model's instruction hierarchy is not an authorization boundary. Every supported execution passes deterministic checks even when model output appears benign.

| Attack | Enforced boundary | Evidence |
|---|---|---|
| Embedded instruction | Confidential file rule and outgoing pattern rule | Decision rule ID, warning patterns |
| Forged unknown tool | Strict tool allowlist | Schema block |
| Traversal / link escape | Resolved path containment and link checks | Isolation block |
| SSRF / arbitrary destination | Canonical literal loopback URL, fixed port/path | Isolation block |
| HTTP redirect | Redirects disabled; 3xx rejected | Execution error |
| Synthetic marker leakage | Outgoing configured patterns | DLP block |
| Approval tampering / replay | Server action, session header, atomic consumption | Approval record and fresh decision |
| Secret exposure in dashboard | Recursive marker redaction before persistence | Redacted evidence |

**Trusted computing base:** Python runtime and dependencies, gateway and policy code, local OS, local single-user admin, SQLite and the optional model runtime installation. The model itself is untrusted. Docker, if used, adds its runtime and configured network as trusted deployment infrastructure.

**Out of scope:** malicious local administrator, compromised operating system, arbitrary plugins executing Python, concurrent filesystem mutations by another process, side channels, encoded/fragmented unknown secret detection, remote multi-user access and real credential protection. A pre-check followed by a file open is not a race-resistant OS sandbox. Link defenses protect the intended static-fixture lab; stronger hostile multi-process isolation needs handle-based path opening, container/OS policies and separate privileges.

Security tests prove specific exercised behavior under this model. Finite successful tests do not establish general security.
