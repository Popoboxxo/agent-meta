---
snippet: parse-input
version: "1.0.0"
language: markdown
runtime: "agent-meta Modern Mode"
---

## 1. Parse input
A2A envelope present → parse `payload.{t,ctx,con,refs,pri,dep}`. Otherwise: plain directive from `main_chat`.
