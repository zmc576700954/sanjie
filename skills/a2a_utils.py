import os
import json
import uuid
from datetime import datetime, timezone


def write_envelope(envelope: dict, inbox_dir: str = "a2a_inbox") -> str:
    """Write an A2A envelope to the pending directory.

    Args:
        envelope: The envelope dictionary to write.
        inbox_dir: The root inbox directory.

    Returns:
        The filepath of the written envelope.
    """
    # Auto-populate message_id and timestamp if missing
    if "message_id" not in envelope:
        envelope["message_id"] = str(uuid.uuid4())
    if "timestamp" not in envelope:
        envelope["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    from_agent = envelope.get("from", "unknown")
    to_agent = envelope.get("to", "unknown")

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]

    filename = f"{timestamp_str}_{from_agent}_to_{to_agent}_{short_uuid}.md"

    pending_dir = os.path.join(inbox_dir, "pending")
    os.makedirs(pending_dir, exist_ok=True)

    filepath = os.path.join(pending_dir, filename)

    json_content = json.dumps(envelope, indent=2, ensure_ascii=False)
    content = f"```json A2A_ENVELOPE\n{json_content}\n```\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def read_envelope_for_agent(agent_name: str, inbox_dir: str = "a2a_inbox") -> dict:
    """Read the most recent pending envelope for a given agent.

    Args:
        agent_name: The name of the agent to read envelopes for.
        inbox_dir: The root inbox directory.

    Returns:
        The parsed envelope dictionary, or None if no pending envelopes.
    """
    pending_dir = os.path.join(inbox_dir, "pending")
    if not os.path.exists(pending_dir):
        return None

    # Find files matching *_to_{agent_name}_*.md
    matching_files = []
    for filename in os.listdir(pending_dir):
        if filename.endswith(".md") and f"_to_{agent_name}_" in filename:
            matching_files.append(filename)

    if not matching_files:
        return None

    # Sort by filename to get the most recent one
    matching_files.sort()
    most_recent = matching_files[-1]

    pending_path = os.path.join(pending_dir, most_recent)

    with open(pending_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract JSON from markdown fence
    lines = content.splitlines()
    json_lines = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```json A2A_ENVELOPE"):
            in_fence = True
            continue
        if in_fence and line.strip() == "```":
            break
        if in_fence:
            json_lines.append(line)

    envelope = json.loads("\n".join(json_lines))

    # Move file to claimed directory
    claimed_dir = os.path.join(inbox_dir, "claimed")
    os.makedirs(claimed_dir, exist_ok=True)
    claimed_path = os.path.join(claimed_dir, most_recent)
    os.rename(pending_path, claimed_path)

    return envelope
