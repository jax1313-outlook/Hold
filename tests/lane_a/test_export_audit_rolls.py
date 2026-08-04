import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from export_audit_rolls import export_audit_rolls  # noqa: E402


def test_export_writes_one_jsonl_per_month(spine, sample_file, sample_metadata, sandbox_config):
    spine.register(sample_file, "pump_receipt", sample_metadata)

    written = export_audit_rolls(sandbox_config)
    assert len(written) == 1
    (month, path) = next(iter(written.items()))
    assert path.name == f"{month}.jsonl"
    assert path.parent.name == "AuditRolls"

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["action"] == "evidence.register"
    assert entry["outcome"] == "completed"


def test_export_is_idempotent_and_reflects_current_state(spine, sample_file, sample_metadata, sandbox_config):
    spine.register(sample_file, "pump_receipt", sample_metadata)
    export_audit_rolls(sandbox_config)

    other_file = sample_file.parent / "second.txt"
    other_file.write_text("a second document", encoding="utf-8")
    spine.register(other_file, "invoice", sample_metadata)

    written = export_audit_rolls(sandbox_config)
    (path,) = written.values()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2  # rewritten from current DB state, not appended


def test_export_month_filter(spine, sample_file, sample_metadata, sandbox_config):
    spine.register(sample_file, "pump_receipt", sample_metadata)
    written = export_audit_rolls(sandbox_config, month="1999-01")
    assert written == {}
