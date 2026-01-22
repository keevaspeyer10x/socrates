# /orchestrate - Workflow Management

Manage structured development workflows with the workflow-orchestrator.

## Usage

```
/orchestrate status        # Show current workflow state
/orchestrate start <task>  # Start a new workflow
/orchestrate advance       # Move to next phase
/orchestrate complete <id> # Complete a checklist item
```

## Instructions

When the user invokes `/orchestrate`, you should:

1. **Check if the orchestrator CLI is installed** by running:
   ```bash
   command -v orchestrator
   ```

2. **If not installed, install it** using pipx or uv:
   ```bash
   # Preferred: pipx (isolated environment)
   pipx install workflow-orchestrator

   # Alternative: uv (faster)
   uv tool install workflow-orchestrator

   # Fallback: pip with --user
   pip install --user workflow-orchestrator
   ```

   > Note: In Claude Code Web, installations don't persist across sessions.
   > This will reinstall on first use each session (takes ~5-10 seconds).

3. **Parse the subcommand** from the arguments:
   - `status` -> show current state
   - `start "<task>"` -> begin new workflow
   - `advance` -> move to next phase
   - `complete <id>` -> mark item complete
   - `skip <id>` -> skip optional item
   - `handoff` -> generate handoff prompt

4. **Run the appropriate orchestrator command**:
   ```bash
   # Check status
   orchestrator status

   # Start new workflow
   orchestrator start "Implement user authentication"

   # Complete an item
   orchestrator complete check_roadmap --notes "Reviewed ROADMAP.md"

   # Skip optional item
   orchestrator skip optional_item --reason "Not needed for this task"

   # Advance to next phase
   orchestrator advance

   # Generate handoff prompt
   orchestrator handoff
   ```

5. **Follow the workflow guidance**:
   - The orchestrator enforces a 5-phase workflow: PLAN -> EXECUTE -> REVIEW -> VERIFY -> LEARN
   - Each phase has required and optional items
   - Complete or skip all items before advancing

## Lazy Installation Pattern

Before running any orchestrator command, always check and install:

```bash
# Check if orchestrator is available
if ! command -v orchestrator &>/dev/null; then
    echo "Installing workflow-orchestrator..."
    if command -v pipx &>/dev/null; then
        pipx install workflow-orchestrator
    elif command -v uv &>/dev/null; then
        uv tool install workflow-orchestrator
    else
        pip install --user workflow-orchestrator
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

# Now run the command
orchestrator status
```

## Workflow Phases

| Phase | Purpose |
|-------|---------|
| **PLAN** | Define scope, assess risks, get approval |
| **EXECUTE** | Write tests, implement code |
| **REVIEW** | Security, architecture, code quality reviews |
| **VERIFY** | Run tests, verify functionality |
| **LEARN** | Document learnings, update roadmap |

## Examples

**User:** `/orchestrate status`

**Action:**
1. Check `command -v orchestrator` - install if missing
2. Run `orchestrator status` and present the current checklist

---

**User:** `/orchestrate start Add dark mode support`

**Action:**
1. Check `command -v orchestrator` - install if missing
2. Run `orchestrator start "Add dark mode support"` to begin a new workflow

---

**User:** `/orchestrate complete initial_plan --notes "Created plan.md with task breakdown"`

**Action:**
1. Check `command -v orchestrator` - install if missing
2. Run `orchestrator complete initial_plan --notes "Created plan.md with task breakdown"`

---

**User:** `/orchestrate advance`

**Action:**
1. Check `command -v orchestrator` - install if missing
2. Run `orchestrator advance` to move to the next phase

## Requirements

- Workflows are tracked in `.workflow_state.json`
- Use `orchestrator --help` for full command reference
- The workflow enforces best practices (TDD, reviews, documentation)
