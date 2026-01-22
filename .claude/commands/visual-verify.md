# /visual-verify - Visual Regression Testing

Run visual verification tests against web pages and UI components using multiple AI vision models.

## Usage

```
/visual-verify <url> "<assertion>"
/visual-verify start                    # Start the service
/visual-verify stop                     # Stop the service
/visual-verify status                   # Check service status
```

## Instructions

When the user invokes `/visual-verify`, you should:

1. **Check if the visual-verify CLI is installed** by running:
   ```bash
   command -v visual-verify
   ```

2. **If not installed, install it** from GitHub:
   ```bash
   npm install -g github:keevaspeyer10x/visual-verification-service
   ```

   > Note: In Claude Code Web, installations don't persist across sessions.
   > This will reinstall on first use each session.

3. **Determine the command type**:
   - `start` -> Start the background service
   - `stop` -> Stop the running service
   - `status` -> Check if service is running
   - `<url> "<assertion>"` -> Run a visual verification test

4. **For service management** (start/stop/status):
   Use the devtools CLI for lifecycle management:
   ```bash
   # Start the service
   devtools start visual-verification-service

   # Start on custom port
   devtools start visual-verification-service --port 3001

   # Check status
   devtools service-status visual-verification-service

   # Stop the service
   devtools stop visual-verification-service
   ```

5. **For visual verification tests**:
   ```bash
   # Run a verification test
   visual-verify "<url>" "<assertion>"

   # Examples:
   visual-verify "https://example.com/login" "Login button is visible and centered"
   visual-verify "http://localhost:3000/dashboard" "Chart shows sales data with blue bars"
   ```

## Lazy Installation Pattern

Before running any visual-verify command, always check and install:

```bash
# Check if visual-verify is available
if ! command -v visual-verify &>/dev/null; then
    echo "Installing visual-verification-service..."
    npm install -g github:keevaspeyer10x/visual-verification-service
fi

# For service start, use devtools
if ! command -v devtools &>/dev/null; then
    # Run from keeva-devtools repo
    /path/to/keeva-devtools/scripts/devtools start visual-verification-service
else
    devtools start visual-verification-service
fi
```

## Service Lifecycle

The visual-verification-service runs as a background HTTP service. It must be started before running verification tests.

### Start Service
```bash
devtools start visual-verification-service           # Default port 3000
devtools start visual-verification-service --port 3001  # Custom port
```

### Check Status
```bash
devtools service-status visual-verification-service
```

Output:
```
Service: visual-verification-service
=========================================
Status:  running
PID:     12345
Port:    3000
Logs:    ~/.cache/keeva-devtools/logs/visual-verification-service.log

Recent logs:
  [2026-01-14 10:30:00] Server started on port 3000
  [2026-01-14 10:30:01] Ready to accept verification requests
```

### Stop Service
```bash
devtools stop visual-verification-service
```

## Examples

**User:** `/visual-verify start`

**Action:**
1. Check `command -v visual-verify` - install if missing
2. Run `devtools start visual-verification-service`

---

**User:** `/visual-verify https://myapp.com/signup "Email field is visible with placeholder text"`

**Action:**
1. Check `command -v visual-verify` - install if missing
2. Ensure service is running (start if needed)
3. Run `visual-verify "https://myapp.com/signup" "Email field is visible with placeholder text"`

---

**User:** `/visual-verify status`

**Action:**
1. Run `devtools service-status visual-verification-service`

---

**User:** `/visual-verify stop`

**Action:**
1. Run `devtools stop visual-verification-service`

---

**User:** `/visual-verify http://localhost:8080 "Navigation menu has 5 items" --screenshot`

**Action:**
1. Check `command -v visual-verify` - install if missing
2. Ensure service is running
3. Run `visual-verify "http://localhost:8080" "Navigation menu has 5 items" --screenshot`

## Troubleshooting

### Service won't start
- Check if port is in use: `lsof -i :3000`
- Try a different port: `devtools start visual-verification-service --port 3001`
- Check logs: `~/.cache/keeva-devtools/logs/visual-verification-service.log`

### Verification fails
- Ensure the URL is accessible
- Check if the page requires authentication
- Try simpler assertions first

## Requirements

- Node.js 18+ installed
- npm available
- API keys for vision models (configured via environment variables)

## Files

- Logs: `~/.cache/keeva-devtools/logs/visual-verification-service.log`
- PID: `~/.cache/keeva-devtools/pids/visual-verification-service.pid`
