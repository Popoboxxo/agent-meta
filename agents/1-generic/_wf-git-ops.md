# Git — Erweiterte Workflows & Plattform-Hinweise

## Workflow-Referenz

**W1 Commit + Push:**
```bash
git status && git add <files> && git diff --staged
git commit -m "<type>: <beschreibung>"
git push origin {{GIT_MAIN_BRANCH}}
```

**W2 Feature-Branch:**
```bash
git checkout -b feat/REQ-042-kurzbeschreibung
# ... commits ...
git checkout {{GIT_MAIN_BRANCH}} && git pull
git merge --no-ff feat/REQ-042-kurzbeschreibung
git push origin {{GIT_MAIN_BRANCH}}
git branch -d feat/REQ-042-kurzbeschreibung
```

**W3 Release-Tag:**
```bash
git tag -a vX.Y.Z -m "vX.Y.Z — <Titel>"
git push origin vX.Y.Z
```

**W4 Rebase (saubere History):**
```bash
git fetch origin && git rebase origin/{{GIT_MAIN_BRANCH}}
```

**W5 Letzten Commit korrigieren (vor Push):**
```bash
git commit --amend -m "fix: korrigierte message"
git add vergessene-datei && git commit --amend --no-edit
```

**W6 Stash:**
```bash
git stash push -m "WIP: beschreibung"
git stash list && git stash pop
```

**W7 Issue schließen:**
```bash
gh issue close <id> --comment "Fixed in <commit>: <summary>"
```

## Destruktive Operationen — immer bestätigen

| Kommando | Risiko | Alternative |
|----------|--------|-------------|
| `git reset --hard` | Verliert changes | `git stash` |
| `git push --force` | Überschreibt Remote | `--force-with-lease` |
| `git branch -D` | Löscht ungemergte Commits | `git branch -d` |
| `git clean -fd` | Löscht untracked files | erst `git clean -nd` |

## Plattform-Hinweise

**GitHub:**
```bash
gh auth status
gh issue list [--label bug]
gh issue view <id> [--comments]
gh pr create --title "..." --body "Closes #<id>"
```

**GitLab:**
```bash
git remote set-url origin https://oauth2:<TOKEN>@gitlab.com/owner/repo.git
glab mr create --title "..."
```

**Gitea:** Analog GitHub, eigene URL + Access Token in `.netrc`.

## Submodule (agent-meta)

```bash
git submodule update --init --recursive
cd .agent-meta && git checkout v<version> && cd ..
git add .agent-meta && git commit -m "chore: upgrade agent-meta to v<version>"
```
