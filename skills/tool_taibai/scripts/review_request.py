"""Review request tool for Taibai.

Submits documents for review by writing an A2A envelope to the review pool.
The scheduler resolves which agent actually performs the review.
"""

import os
import uuid
from datetime import datetime, timezone

A2A_INBOX_DIR = "a2a_inbox"

VALID_REVIEW_TYPES = {"format", "quality", "assertion", "architecture"}


def request_review(
    document_path: str,
    review_type: str = "format",
    context_notes: str = "",
) -> dict:
    """Submit a document for review.

    Args:
        document_path: Path to the document to review.
        review_type: Category of review requested. One of: format, quality, assertion, architecture.
        context_notes: Additional context for the reviewer.

    Returns:
        dict with ticket_id, status, review_type, document_path.

    Raises:
        FileNotFoundError: If the document does not exist.
        ValueError: If review_type is not recognized.
    """
    if not os.path.exists(document_path):
        raise FileNotFoundError(f"Document not found: {document_path}")

    if review_type not in VALID_REVIEW_TYPES:
        raise ValueError(f"Invalid review_type: {review_type}. Must be one of {VALID_REVIEW_TYPES}")

    ticket_id = f"REV-{uuid.uuid4().hex[:8].upper()}"

    # Write A2A envelope to review pool
    envelope = {
        "message_type": "request",
        "from": "taibai",
        "to": "review-pool",
        "priority": "normal",
        "document_ref": document_path,
        "payload": {
            "review_type": review_type,
            "ticket_id": ticket_id,
            "context_notes": context_notes,
            "submitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
    }

    # Import here to avoid circular dependencies at module level
    from skills.a2a_utils import write_envelope
    write_envelope(envelope, inbox_dir=A2A_INBOX_DIR)

    return {
        "ticket_id": ticket_id,
        "status": "submitted",
        "review_type": review_type,
        "document_path": document_path,
    }
