#!/usr/bin/env python3
"""A2A Inbox Notification Daemon.

A lightweight observer that polls the A2A inbox and prints notifications
for new envelopes.  It does NOT execute agent logic, route messages, or
invoke tools — it is purely a notifier.
"""

import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
POLL_INTERVAL = 2  # seconds
INBOX_DIR = Path("a2a_inbox") / "pending"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_envelope_filename(filename: str) -> tuple[str, str] | None:
    """Extract sender and recipient from an envelope filename.

    Expected format: {timestamp}_{from}_to_{to}_{uuid}.md
    Example: 20250518_120000_nezha_to_taibai_a1b2c3.md
    """
    if not filename.endswith(".md"):
        return None

    # Remove .md extension
    name = filename[:-3]

    # Split by '_to_'
    if "_to_" not in name:
        return None

    parts_before_to, parts_after_to = name.split("_to_", 1)

    # sender is the last segment before _to_
    sender = parts_before_to.split("_")[-1]

    # recipient is the first segment after _to_
    recipient = parts_after_to.split("_")[0]

    if not sender or not recipient:
        return None

    return sender, recipient


def get_current_envelopes() -> set[str]:
    """Return the set of envelope filenames currently in the inbox."""
    if not INBOX_DIR.exists():
        return set()
    return {
        entry.name
        for entry in INBOX_DIR.iterdir()
        if entry.is_file() and entry.name.endswith(".md")
    }


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"[A2A] Daemon started — watching {INBOX_DIR}")
    print("[A2A] Press Ctrl+C to stop\n")

    known: set[str] = get_current_envelopes()

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            current = get_current_envelopes()
            new = current - known

            for filename in new:
                parsed = parse_envelope_filename(filename)
                if parsed is None:
                    continue
                sender, recipient = parsed
                print(f"[A2A] New envelope for {recipient} from {sender}")

            known = current

    except KeyboardInterrupt:
        print("\n[A2A] Daemon stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
