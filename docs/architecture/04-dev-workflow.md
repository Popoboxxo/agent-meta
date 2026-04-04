# Development Workflow

> [Back to Architecture Overview](../../ARCHITECTURE.md) &nbsp;|&nbsp; [Open in Mermaid Live Editor](https://mermaid.live/edit#base64:eyJjb2RlIjogInNlcXVlbmNlRGlhZ3JhbVxuICAgIGFjdG9yIFVzZXJcbiAgICBwYXJ0aWNpcGFudCBPUkMgYXMgb3JjaGVzdHJhdG9yXG4gICAgcGFydGljaXBhbnQgUkVRIGFzIHJlcXVpcmVtZW50c1xuICAgIHBhcnRpY2lwYW50IFRTVCBhcyB0ZXN0ZXJcbiAgICBwYXJ0aWNpcGFudCBERVYgYXMgZGV2ZWxvcGVyXG4gICAgcGFydGljaXBhbnQgVkFMIGFzIHZhbGlkYXRvclxuICAgIHBhcnRpY2lwYW50IERPQyBhcyBkb2N1bWVudGVyXG4gICAgcGFydGljaXBhbnQgR0lUIGFzIGdpdFxuICAgIFVzZXItPj5PUkM6IG5ldyBmZWF0dXJlIHJlcXVlc3RcbiAgICBPUkMtPj5SRVE6IGFzc2lnbiBSRVEtSURcbiAgICBSRVEtLT4-T1JDOiBSRVEtMDQyIGRvbmVcbiAgICBPUkMtPj5UU1Q6IHdyaXRlIHRlc3RzIFRERCByZWRcbiAgICBUU1QtLT4-T1JDOiB0ZXN0cyB3cml0dGVuXG4gICAgT1JDLT4-REVWOiBpbXBsZW1lbnRcbiAgICBERVYtLT4-T1JDOiBjb2RlIGRvbmVcbiAgICBPUkMtPj5UU1Q6IHJ1biB0ZXN0c1xuICAgIFRTVC0tPj5PUkM6IHRlc3RzIGdyZWVuXG4gICAgT1JDLT4-VkFMOiBEb0QgY2hlY2tcbiAgICBWQUwtLT4-T1JDOiBEb0QgcGFzc2VkXG4gICAgT1JDLT4-RE9DOiB1cGRhdGUgZG9jc1xuICAgIERPQy0tPj5PUkM6IGRvY3MgdXBkYXRlZFxuICAgIE9SQy0-PkdJVDogY29tbWl0IGFuZCBwdXNoXG4gICAgR0lULS0-Pk9SQzogY29tbWl0dGVkXG4gICAgT1JDLS0-PlVzZXI6IGZlYXR1cmUgY29tcGxldGUiLCAibWVybWFpZCI6IHsidGhlbWUiOiAiZGVmYXVsdCJ9fQ)

## Workflow A: Neues Feature (via orchestrator)

```mermaid
sequenceDiagram
    actor User
    participant ORC as orchestrator
    participant REQ as requirements
    participant TST as tester
    participant DEV as developer
    participant VAL as validator
    participant DOC as documenter
    participant GIT as git

    User->>ORC: new feature request
    ORC->>REQ: assign REQ-ID
    REQ-->>ORC: REQ-042 done
    ORC->>TST: write tests TDD red
    TST-->>ORC: tests written
    ORC->>DEV: implement
    DEV-->>ORC: code done
    ORC->>TST: run tests
    TST-->>ORC: tests green
    ORC->>VAL: DoD check
    VAL-->>ORC: DoD passed
    ORC->>DOC: update docs
    DOC-->>ORC: docs updated
    ORC->>GIT: commit and push
    GIT-->>ORC: committed
    ORC-->>User: feature complete
```

## Workflow B: Neues Feature (via feature-Agent)

Der `feature`-Agent ist ein **Shortcut** — er führt denselben Lifecycle wie Workflow A durch,
aber als eigenständiger Workflow-Agent mit festem 8-Schritt-Prozess inkl. Branch + PR.

```mermaid
sequenceDiagram
    actor User
    participant FEA as feature
    participant GIT as git
    participant REQ as requirements
    participant TST as tester
    participant DEV as developer
    participant VAL as validator
    participant DOC as documenter

    User->>FEA: "ich will Feature X bauen"
    FEA->>GIT: create branch feat/X
    GIT-->>FEA: branch created
    FEA->>REQ: assign REQ-ID
    REQ-->>FEA: REQ-042
    FEA->>TST: write tests TDD red
    TST-->>FEA: tests written
    FEA->>DEV: implement TDD green
    DEV-->>FEA: code done
    FEA->>TST: run tests verify
    TST-->>FEA: tests green
    FEA->>VAL: DoD check
    VAL-->>FEA: DoD passed
    FEA->>DOC: update docs (optional)
    DOC-->>FEA: docs updated
    FEA->>GIT: commit + push + PR
    GIT-->>FEA: PR created
    FEA-->>User: REQ-042 done, PR link
```

## Wann feature, wann orchestrator?

| Situation | Agent |
|-----------|-------|
| Neues Feature von Null, mit Branch + PR | `feature` |
| Bugfix, Refactoring, Ad-hoc-Aufgaben | `orchestrator` |
| Mehrere unabhängige Tasks in einer Session | `orchestrator` |
| Strukturierter TDD-Lifecycle erzwungen | `feature` |
