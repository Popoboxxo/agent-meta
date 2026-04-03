---
snippet: tester-syntax
version: "1.0.0"
language: "TypeScript"
runtime: "Bun"
description: "Test-Syntax und Beispiele für TypeScript-Projekte mit Bun-Test-Runner."
---

### Test-Syntax

```typescript
import { describe, it, expect, beforeEach, afterEach, mock } from "bun:test";

describe("ModuleName", () => {
  it("[REQ-xxx] should do something specific", () => {
    // Arrange
    const input = /* realistischer Wert */;
    // Act
    const result = functionUnderTest(input);
    // Assert
    expect(result).toBe(expectedValue);
  });
});
```

### Test-Benennung

```typescript
describe("QueueManager", () => {
  it("[REQ-004] should add a video to the queue", () => { ... });
  it("[REQ-007] should remove a video by position", () => { ... });
});
```

### Echte Assertions

```typescript
// ❌ FALSCH — prüft nichts Sinnvolles
it("[REQ-004] should add video", () => {
  expect(true).toBe(true);
});

// ✅ RICHTIG — prüft das tatsächliche Ergebnis
it("[REQ-004] should add a video to the queue", () => {
  addVideo(item);
  expect(queue.length).toBe(1);
  expect(queue[0].id).toBe(item.id);
});
```

### Realitätsnahe Testdaten

```typescript
// ❌ FALSCH — bedeutungslose Dummy-Daten
const video = { id: "abc", title: "test", url: "foo" };

// ✅ RICHTIG — realistische Daten die dem echten Use-Case entsprechen
const video = {
  id: "yt-dQw4w9WgXcQ",
  title: "Rick Astley - Never Gonna Give You Up",
  url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  duration: 213,
};
```
