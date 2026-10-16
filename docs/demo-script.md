# Five-minute demonstration

1. Start all three services with `scripts/start.ps1`. Open the dashboard, create the first local account or sign in, and finish or defer the guided tour. The Getting started page contains the full beginner workflow. Explain the simulation badge and that all secrets are generated synthetic markers.
2. Open Run comparison. Select **Injection embedded in document** and run all three modes. Explain that the scripted agent reads hostile text, tries a confidential read and proposes a transfer. Even unprotected mode cannot leave the lab.
3. Show the unprotected and prompt-only receipt outcomes in Security events: the receiver reports a marker transfer, but the marker itself is redacted. Explain that prompt-only ignores instructions by design in this simulator; it is not a real-model experiment.
4. Show the protected run. The document triggers named warning patterns, then confidential access gets `classification.confidential`. No send is executed. Explain why the external policy is the decisive control rather than the warning.
5. Run **Restricted synthetic outgoing payload** in protected mode. Show `dlp.restricted` independently of the read restriction.
6. Run **Quoted injection false-positive challenge**. It produces a screening warning while the authorized read completes. This separates suspicious language from malicious behavior.
7. Run **Legitimate sensitive action**. Open Approval queue, approve the exact stored action, inspect the fresh allow decision. An API replay is covered by automated tests and returns conflict. No editable arguments or approved flag are accepted.
8. Run the evaluation suite, show malicious and legitimate denominators, pending approvals, execution errors and simulation labels. Download CSV/JSON. The untouched held-out suite can be run for final reporting after development decisions are frozen; once viewed, acknowledge it has been observed.

If the receiver is stopped, transfers show execution errors. Fix the service and rerun rather than calling the absence of a receipt successful prevention. If a port is occupied, stop your own AgentShield services or use the three manual terminals to identify the issue. Never kill an unknown process just to free a port.
