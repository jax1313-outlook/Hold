import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from seed_library import seed_library  # noqa: E402


def test_seed_library_installs_expected_files(sandbox_config):
    written, skipped = seed_library(sandbox_config)
    assert not skipped
    assert written

    library_root = Path(sandbox_config["roots"]["library"])
    assert (library_root / "Constitutions" / "LIBRARIAN_CONSTITUTION_v1.md").is_file()
    assert (library_root / "Vocabulary" / "expense_vocabulary.v1.json").is_file()
    assert (library_root / "RateTables" / "README.md").is_file()

    # .gitkeep placeholders are not part of the seed content.
    assert not any(library_root.rglob(".gitkeep"))


def test_seed_library_is_idempotent_by_default(sandbox_config):
    library_root = Path(sandbox_config["roots"]["library"])
    seed_library(sandbox_config)

    target = library_root / "Vocabulary" / "expense_vocabulary.v1.json"
    target.write_text('{"tampered": true}', encoding="utf-8")

    written, skipped = seed_library(sandbox_config)
    assert target in skipped
    assert target not in written
    assert target.read_text(encoding="utf-8") == '{"tampered": true}'


def test_seed_library_force_overwrites(sandbox_config):
    library_root = Path(sandbox_config["roots"]["library"])
    seed_library(sandbox_config)

    target = library_root / "Vocabulary" / "expense_vocabulary.v1.json"
    target.write_text('{"tampered": true}', encoding="utf-8")

    written, skipped = seed_library(sandbox_config, force=True)
    assert target in written
    assert target.read_text(encoding="utf-8") != '{"tampered": true}'
