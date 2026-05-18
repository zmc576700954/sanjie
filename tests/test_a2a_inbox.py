import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_a2a_directory_structure():
    inbox_dir = os.path.join(project_root, "a2a_inbox")
    assert os.path.exists(inbox_dir)
    assert os.path.exists(os.path.join(inbox_dir, "pending"))
    assert os.path.exists(os.path.join(inbox_dir, "claimed"))
    assert os.path.exists(os.path.join(inbox_dir, "completed"))


from skills.a2a_utils import write_envelope, read_envelope_for_agent


def test_write_and_read_envelope(tmp_path):
    inbox = str(tmp_path)
    os.makedirs(os.path.join(inbox, "pending"), exist_ok=True)
    os.makedirs(os.path.join(inbox, "claimed"), exist_ok=True)

    envelope = {
        "message_id": "test-uuid",
        "from": "yangjian",
        "to": "nezha",
        "handoff_payload": {"recommended_skill": "yindan"}
    }

    write_envelope(envelope, inbox_dir=inbox)

    pending = os.listdir(os.path.join(inbox, "pending"))
    assert len(pending) == 1

    result = read_envelope_for_agent("nezha", inbox_dir=inbox)
    assert result["from"] == "yangjian"
    assert result["handoff_payload"]["recommended_skill"] == "yindan"

    # After reading, file should move to claimed
    pending = os.listdir(os.path.join(inbox, "pending"))
    claimed = os.listdir(os.path.join(inbox, "claimed"))
    assert len(pending) == 0
    assert len(claimed) == 1
