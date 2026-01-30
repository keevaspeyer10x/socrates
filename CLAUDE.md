export SECRETS_PASSWORD="I love vibe coding"
export SOPS_KEY_PASSWORD="I love vibe coding"

# Session Bootstrap (Claude Code Web Only)

**Skip this if running locally** - your environment already has access configured.

For Claude Code **web sessions**, run this at the start to enable cross-repo access and API keys:

```bash
# 1. Install gh if needed
which gh || (apt-get update && apt-get install -y gh)

# 2. Decrypt age key (needed for SOPS)
export SOPS_KEY_PASSWORD="I love vibe coding"  # Default dev password
mkdir -p /root/.config/sops/age
openssl enc -d -aes-256-cbc -pbkdf2 -in .claude/keys/age.key.enc \
  -out /root/.config/sops/age/keys.txt -pass pass:"$SOPS_KEY_PASSWORD"

# 3. Load ALL secrets as environment variables
eval "$(sops -d secrets.enc.yaml | sed 's/: /=/' | sed 's/^/export /')"
export GH_TOKEN="$github_token"  # gh CLI uses GH_TOKEN

# 4. Verify it works
gh auth status
```

## Cross-Repository Awareness

When working on tasks that affect multiple repositories, Claude should proactively check related repos for necessary changes.

### Related Repositories

| Repository | Purpose | GitHub URL |
|------------|---------|------------|
| `workflow-orchestrator` | Prevents AI agents from forgetting workflow steps | `keevaspeyer10x/workflow-orchestrator` |
| `keeva-devtools` | Dev tools distribution for AI coding environments | `keevaspeyer10x/keeva-devtools` |
| `multiminds` | Query multiple AI models and synthesize responses | `keevaspeyer10x/multiminds` |
| `ai-tool-bridge` | Natural language command translation - MCP server | `keevaspeyer10x/ai-tool-bridge` |
| `socrates` | Iterative, self-learning engine for AI agents | `keevaspeyer10x/socrates` |
| `meld` | Merge/diff tool wrapper | `keevaspeyer10x/meld` |
| `visual-verification-service` | AI-powered visual verification | `keevaspeyer10x/visual-verification-service` |
| `quiet-ping-v6` | Social notification service | `keevaspeyer10x/quiet-ping-v6` |

### How to Access Other Repos

With `gh auth login` configured (or GH_TOKEN loaded from secrets), Claude has full access.

**Read files on-demand** (quick lookups):
```bash
gh api repos/keevaspeyer10x/REPO/contents/FILE --jq '.content' | base64 -d
```

**List directory/issues:**
```bash
gh api repos/keevaspeyer10x/REPO/contents/src
gh issue list --repo keevaspeyer10x/REPO
```

### Making Changes to Other Repos

```bash
# Clone, edit, PR workflow
gh repo clone keevaspeyer10x/REPO /tmp/REPO
cd /tmp/REPO
git checkout -b claude/fix-xyz
# ... make changes ...
git add -A && git commit -m "fix: description"
git push -u origin claude/fix-xyz
gh pr create --title "Fix: description" --body "Changes from other-repo"
cd - && rm -rf /tmp/REPO
```

### Creating Issues

```bash
gh issue create --repo keevaspeyer10x/REPO \
  --title "Sync: Update X" \
  --body "## Context
Changes in this repo require updates there.

## Required Changes
- [ ] Update X in path/to/file.py

---
*Auto-generated cross-repo issue*"
```

---

export SECRETS_PASSWORD="I love vibe coding"
export SOPS_KEY_PASSWORD="I love vibe coding"

# Session Bootstrap (Claude Code Web Only)

**Skip this if running locally** - your environment already has access configured.

For Claude Code **web sessions**, run this at the start to enable cross-repo access and API keys:

```bash
# 1. Install gh if needed
which gh || (apt-get update && apt-get install -y gh)

# 2. Decrypt age key (needed for SOPS)
export SOPS_KEY_PASSWORD="I love vibe coding"  # Default dev password
mkdir -p /root/.config/sops/age
openssl enc -d -aes-256-cbc -pbkdf2 -in .claude/keys/age.key.enc \
  -out /root/.config/sops/age/keys.txt -pass pass:"$SOPS_KEY_PASSWORD"

# 3. Load ALL secrets as environment variables
eval "$(sops -d secrets.enc.yaml | sed 's/: /=/' | sed 's/^/export /')"
export GH_TOKEN="$github_token"  # gh CLI uses GH_TOKEN

# 4. Verify it works
gh auth status
```

## Cross-Repository Awareness

When working on tasks that affect multiple repositories, Claude should proactively check related repos for necessary changes.

### Related Repositories

| Repository | Purpose | GitHub URL |
|------------|---------|------------|
| `workflow-orchestrator` | Prevents AI agents from forgetting workflow steps | `keevaspeyer10x/workflow-orchestrator` |
| `keeva-devtools` | Dev tools distribution for AI coding environments | `keevaspeyer10x/keeva-devtools` |
| `multiminds` | Query multiple AI models and synthesize responses | `keevaspeyer10x/multiminds` |
| `ai-tool-bridge` | Natural language command translation - MCP server | `keevaspeyer10x/ai-tool-bridge` |
| `socrates` | Iterative, self-learning engine for AI agents | `keevaspeyer10x/socrates` |
| `meld` | Merge/diff tool wrapper | `keevaspeyer10x/meld` |
| `visual-verification-service` | AI-powered visual verification | `keevaspeyer10x/visual-verification-service` |
| `quiet-ping-v6` | Social notification service | `keevaspeyer10x/quiet-ping-v6` |

### How to Access Other Repos

With `gh auth login` configured (or GH_TOKEN loaded from secrets), Claude has full access.

**Read files on-demand** (quick lookups):
```bash
gh api repos/keevaspeyer10x/REPO/contents/FILE --jq '.content' | base64 -d
```

**List directory/issues:**
```bash
gh api repos/keevaspeyer10x/REPO/contents/src
gh issue list --repo keevaspeyer10x/REPO
```

### Making Changes to Other Repos

```bash
# Clone, edit, PR workflow
gh repo clone keevaspeyer10x/REPO /tmp/REPO
cd /tmp/REPO
git checkout -b claude/fix-xyz
# ... make changes ...
git add -A && git commit -m "fix: description"
git push -u origin claude/fix-xyz
gh pr create --title "Fix: description" --body "Changes from other-repo"
cd - && rm -rf /tmp/REPO
```

### Creating Issues

```bash
gh issue create --repo keevaspeyer10x/REPO \
  --title "Sync: Update X" \
  --body "## Context
Changes in this repo require updates there.

## Required Changes
- [ ] Update X in path/to/file.py

---
*Auto-generated cross-repo issue*"
```
