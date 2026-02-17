# HappyQuotes

Motivational quote notifications for macOS. A quote appears as a system notification every hour.

**Zero dependencies** — uses only Python 3 standard library and macOS-native tools. Fully offline.

## Quick Start

```bash
# Show a quote right now
python3 happyquotes.py

# Or via the control script
./happyquotesctl run
```

## Install as a Service (launchd)

The recommended way to run HappyQuotes — uses macOS launchd so it survives reboots and uses zero resources between quotes.

```bash
./happyquotesctl install    # Install and start (fires immediately)
./happyquotesctl status     # Check if running
./happyquotesctl stop       # Stop the service
./happyquotesctl start      # Start the service
./happyquotesctl uninstall  # Remove completely
```

## Daemon Mode (Alternative)

Run as a foreground process instead of launchd:

```bash
python3 happyquotes.py --daemon
```

Shows a quote immediately, then every hour. Stop with `Ctrl+C`.

## Files

| File | Purpose |
|---|---|
| `happyquotes.py` | Core app — picks a random quote, shows notification |
| `quotes.json` | 50 curated motivational quotes |
| `happyquotesctl` | Bash control script for managing the launchd service |
| `com.happyquotes.agent.plist` | launchd agent template |

## How It Works

- Picks a random quote from `quotes.json`
- Tracks recently shown quotes in `~/.happyquotes_history` to avoid repeats
- Once all quotes have been shown, the history resets
- Notifications are sent via `osascript` (AppleScript)
- Logs to `~/Library/Logs/happyquotes.log`
