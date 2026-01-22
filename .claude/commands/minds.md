# /minds - Get Multi-Model AI Perspectives

Query multiple AI models and get a synthesized response.

## Usage

```
/minds <question>
/minds <question> --fast
/minds <question> --models gemini,gpt,grok
/minds <question> --file path/to/file.py
```

## Instructions

When the user invokes `/minds`, you should:

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

3. **Extract the question** from the user's input after `/minds`

4. **Check for flags** in the arguments:
   - `--fast` -> use faster/cheaper model versions
   - `--models <list>` -> query specific models only
   - `--file <path>` -> include file contents as context

5. **Run the minds CLI** to get external model perspectives:
   ```bash
   # Default (all models, full quality)
   minds ask "<question>" --verbose

   # Fast mode (cheaper/faster models)
   minds ask "<question>" --fast --verbose

   # Specific models
   minds ask "<question>" --models gemini,gpt --verbose

   # With file context
   minds ask "<question>" --file <path> --verbose
   ```

6. **Present the results** to the user, including:
   - Which models responded
   - The synthesized consensus
   - Any notable disagreements
   - Your own perspective if relevant

## Lazy Installation Pattern

Before running any minds command, always check and install:

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
minds ask "..." --verbose
```

## Examples

**User:** `/minds Should I use Redis or PostgreSQL for a job queue?`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds ask "Should I use Redis or PostgreSQL for a job queue?" --verbose`

---

**User:** `/minds What's the meaning of life? --fast`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds ask "What's the meaning of life?" --fast --verbose`

---

**User:** `/minds Review this authentication code --file src/auth.py`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds ask "Review this authentication code" --file src/auth.py --verbose`

---

**User:** `/minds What's the best error handling pattern? --models gemini,gpt`

**Action:**
1. Check `command -v minds` - install if missing
2. Run `minds ask "What's the best error handling pattern?" --models gemini,gpt --verbose`

## Requirements

- API keys must be configured (ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, XAI_API_KEY, etc.)
- Use `minds status` to check available models
- Default behavior queries all available models (including Claude) with synthesis
- For code reviews with repo context, use `/minds-review` instead (runs `minds review`)
