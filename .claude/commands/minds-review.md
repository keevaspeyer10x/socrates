# /minds-review - Multi-Model Code Review

Get code review feedback from multiple AI models with synthesized recommendations.

## Usage

```
/minds-review                    # Review all changes vs main branch
/minds-review --uncommitted      # Review only uncommitted changes
/minds-review --fast             # Use faster/cheaper models
/minds-review <file>             # Review specific file
```

## Instructions

When the user invokes `/minds-review`, you should:

1. **Check if the minds CLI is installed** by running:
   ```bash
   command -v minds
   ```

2. **If not installed, install it** using pipx or uv:
   ```bash
   # Preferred: pipx (isolated environment)
   pipx install multiminds

   # Alternative: uv (faster)
   uv tool install multiminds

   # Fallback: pip with --user
   pip install --user multiminds
   ```

   > Note: In Claude Code Web, installations don't persist across sessions.
   > This will reinstall on first use each session (takes ~5-10 seconds).

3. **Determine the scope** of the review:
   - No arguments -> review all changes vs main branch
   - `--uncommitted` -> only uncommitted changes
   - `<file>` -> specific file

4. **Check for flags**:
   - `--fast` -> use faster/cheaper model versions
   - `--base <branch>` -> diff against specific branch

5. **Run the minds review CLI**:
   ```bash
   # Default: all changes vs main
   minds review --verbose

   # Only uncommitted changes
   minds review --uncommitted --verbose

   # Fast mode
   minds review --fast --verbose

   # Specific file
   minds review path/to/file.py --verbose

   # Different base branch
   minds review --base develop --verbose
   ```

6. **Present the results** to the user, including:
   - Which models provided feedback
   - Consensus issues (found by multiple models)
   - Unique insights from individual models
   - Severity categorization (critical, high, medium, low)
   - Suggested fixes

## Lazy Installation Pattern

Before running any minds review command, always check and install:

```bash
# Check if minds is available
if ! command -v minds &>/dev/null; then
    echo "Installing multiminds..."
    if command -v pipx &>/dev/null; then
        pipx install multiminds
    elif command -v uv &>/dev/null; then
        uv tool install multiminds
    else
        pip install --user multiminds
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

# Now run the command
minds review --verbose
```

## Examples

**User:** `/minds-review`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds review --verbose` to get multi-model review of all changes

---

**User:** `/review --uncommitted`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds review --uncommitted --verbose` to review working changes

---

**User:** `/review src/auth.py --fast`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds review src/auth.py --fast --verbose`

---

**User:** `/review --base develop`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds review --base develop --verbose`

## Requirements

- API keys must be configured for external models
- Reviews are synthesized from multiple AI perspectives
- Use `--fast` for quicker turnaround during development
- Critical security issues are highlighted prominently
