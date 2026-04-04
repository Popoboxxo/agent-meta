# Versioning Strategy

> [← Back to Architecture Overview](../../ARCHITECTURE.md)

```mermaid
graph TD
    RV["Repo Version\nVERSION file\nz.B. 0.12.0"]
    AV["Agent Version\nFrontmatter jeder .md\nunabhängig pro Datei"]
    SV["Snippet Version\nFrontmatter jeder .md\nunabhängig pro Datei"]
    PL["2-platform Agent\nbased-on: 1-generic@x.y.z"]

    RV -->|"Major: Breaking\nMinor: Features\nPatch: Fixes"| RV
    AV -->|"Major: Verhalten\nMinor: Sektion\nPatch: Text"| AV
    SV -->|"bei inhaltlichen\nÄnderungen"| SV
    AV --> PL
```
