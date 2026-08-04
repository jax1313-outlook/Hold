import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from init_roots import init_roots  # noqa: E402


def test_init_roots_creates_static_skeleton(sandbox_config):
    created = init_roots(sandbox_config)
    assert created  # non-empty

    operations = Path(sandbox_config["roots"]["operations"])
    library = Path(sandbox_config["roots"]["library"])
    archive = Path(sandbox_config["roots"]["archive"])

    for expected in [
        operations / "Data",
        operations / "Intake" / "Drop",
        operations / "Intake" / "Processing",
        operations / "Intake" / "Quarantine",
        operations / "PrintQueue",
        operations / "Workers" / "Librarian" / "TradeMemory",
        operations / "Testing" / "GoldenSet",
        library / "Constitutions",
        library / "Templates" / "Reports",
        library / "Vocabulary",
        library / "RateTables",
        library / "EvidenceIndex",
        archive / "Evidence",
        archive / "IFTA",
        archive / "ReportSnapshots",
        archive / "AuditRolls",
    ]:
        assert expected.is_dir(), f"missing skeleton dir: {expected}"


def test_init_roots_is_idempotent(sandbox_config):
    init_roots(sandbox_config)
    init_roots(sandbox_config)  # must not raise
