# A2A Anti-Re-Delegation Gates

1. Limit depth to {{A2A_MAX_DEPTH}}, no self-handoff.
2. Short payload: `payload.t` max {{A2A_T_SIZE_LIMIT}} Zeichen.
3. No Re-Delegation (payload starts with "Du bist...").
4. Singleton Orchestrator: NUR der `main_chat` darf den `orchestrator` spawnen.
5. Execution-Trace-Isolation: Worker-Output muss strukturiert sein (STATUS, RESULT, ARTIFACTS). Keine rohen Logs propagieren.
