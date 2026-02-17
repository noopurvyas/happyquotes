#!/usr/bin/env python3
"""HappyQuotes — Motivational quote notifications for macOS."""

import json
import logging
import os
import random
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
QUOTES_FILE = SCRIPT_DIR / "quotes.json"
HISTORY_FILE = Path.home() / ".happyquotes_history"
LOG_FILE = Path.home() / "Library" / "Logs" / "happyquotes.log"
MAX_QUOTE_LEN = 200
INTERVAL = 3600  # 1 hour


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_quotes():
    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f)


def pick_quote(quotes):
    history = load_history()
    available = [q for q in quotes if q["q"] not in history]
    if not available:
        # Pool exhausted — reset history
        history = []
        available = quotes
    quote = random.choice(available)
    history.append(quote["q"])
    save_history(history)
    return quote


def _applescript_escape(s):
    """Escape a string for use inside AppleScript double quotes."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def show_notification(title, message):
    """Show a macOS notification safely using a temp AppleScript file."""
    # Truncate to fit notification limits
    if len(message) > MAX_QUOTE_LEN:
        message = message[: MAX_QUOTE_LEN - 1] + "\u2026"

    escaped_message = _applescript_escape(message)
    escaped_title = _applescript_escape(title)
    applescript = (
        f'display notification "{escaped_message}" '
        f'with title "{escaped_title}"'
    )

    fd, path = tempfile.mkstemp(suffix=".applescript")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(applescript)
        result = subprocess.run(
            ["osascript", path], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Notification failed: {result.stderr.strip()}"
            )
    finally:
        os.unlink(path)


def run_once():
    quotes = load_quotes()
    quote = pick_quote(quotes)
    text = f'"{quote["q"]}" — {quote["a"]}'
    logging.info("Showing quote: %s", text)
    show_notification("HappyQuotes \u2728", text)


def daemon_loop():
    """Run in daemon mode — show a quote every hour."""
    shutdown = False

    def handle_signal(signum, _frame):
        nonlocal shutdown
        logging.info("Received signal %s, shutting down.", signum)
        shutdown = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    logging.info("Daemon started (interval=%ds)", INTERVAL)
    while not shutdown:
        try:
            run_once()
        except Exception:
            logging.exception("Error showing quote")
        # Sleep in small increments so we can respond to signals promptly
        for _ in range(INTERVAL):
            if shutdown:
                break
            time.sleep(1)
    logging.info("Daemon stopped.")


def main():
    setup_logging()
    if "--daemon" in sys.argv:
        daemon_loop()
    else:
        try:
            run_once()
        except Exception:
            logging.exception("Error showing quote")
            sys.exit(1)


if __name__ == "__main__":
    main()
