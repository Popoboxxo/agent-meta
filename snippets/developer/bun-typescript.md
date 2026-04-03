---
snippet: developer-syntax
version: "1.0.0"
language: "TypeScript"
runtime: "Bun"
description: "Code-Patterns und Best Practices für TypeScript-Projekte mit Bun."
---

### Imports & Exports

```typescript
// ✅ Named Exports — kein default export
export function processItem(item: Item): Result { ... }
export class QueueManager { ... }

// ❌ NICHT
export default function processItem() { ... }
```

### Typisierung

```typescript
// ✅ Explizite Typen, kein any
function addVideo(item: VideoItem): void { ... }
const result: ProcessResult = process(input);

// ❌ NICHT
function addVideo(item: any) { ... }
const result = process(input); // implizites any
```

### Fehlerbehandlung

```typescript
// ✅ Benutzerfreundliche Fehlermeldung werfen
if (!item.url) {
  throw new Error("Video URL is required");
}

// ✅ Technische Details loggen
ctx.log(`Processing item ${item.id}`);
ctx.error(`Failed to parse response: ${e.message}`);
```

### Dateinamen & Struktur

```
src/
  queue-manager.ts        # kebab-case Modulname
  queue-manager.test.ts   # Test: <module>.test.ts
  utils/
    format-duration.ts
```

### Async / Await

```typescript
// ✅ async/await statt Promise-Chaining
async function fetchVideo(url: string): Promise<VideoItem> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
  return response.json() as Promise<VideoItem>;
}
```
