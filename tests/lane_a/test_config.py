"""Config loader: schema validation and the sandbox-refusal rule
(contracts/config.schema.json's refusal_rule)."""
from __future__ import annotations

import json

import pytest

from dispatch.common.config import (
    ConfigValidationError,
    SandboxRefusalError,
    load_config,
)
from tests.conftest import REPO_ROOT


def test_repo_sandbox_config_loads_and_passes_refusal_check():
    # config/sandbox.config.json roots point under D:\DispatchSandbox\..., not
    # under any production root, so this must succeed.
    config = load_config(REPO_ROOT / "config" / "sandbox.config.json")
    assert config["environment"] == "sandbox"


def test_sandbox_config_path_load(sandbox_config_path):
    config = load_config(sandbox_config_path)
    assert config["environment"] == "sandbox"


@pytest.mark.parametrize(
    "bad_root",
    [
        "D:\\Dispatch Operations\\Sandbox",
        "d:\\dispatch operations\\anything",
        "D:\\Memory\\Library",
        "D:\\Archive\\Evidence",
    ],
)
def test_sandbox_refusal_fires_for_production_roots(tmp_path, sandbox_config, bad_root):
    sandbox_config["roots"]["archive"] = bad_root
    path = tmp_path / "bad.config.json"
    path.write_text(json.dumps(sandbox_config), encoding="utf-8")

    with pytest.raises(SandboxRefusalError):
        load_config(path)


def test_production_environment_is_not_subject_to_refusal_check(tmp_path, sandbox_config):
    sandbox_config["environment"] = "production"
    sandbox_config["roots"]["archive"] = "D:\\Archive"
    sandbox_config["roots"]["operations"] = "D:\\Dispatch Operations"
    sandbox_config["roots"]["library"] = "D:\\Memory\\Library"
    path = tmp_path / "prod.config.json"
    path.write_text(json.dumps(sandbox_config), encoding="utf-8")

    config = load_config(path)  # must not raise
    assert config["environment"] == "production"


def test_missing_required_field_fails_schema_validation(tmp_path, sandbox_config):
    del sandbox_config["database"]
    path = tmp_path / "invalid.config.json"
    path.write_text(json.dumps(sandbox_config), encoding="utf-8")

    with pytest.raises(ConfigValidationError):
        load_config(path)


def test_unknown_root_key_fails_schema_validation(tmp_path, sandbox_config):
    sandbox_config["roots"]["extra_tier"] = "/some/path"
    path = tmp_path / "invalid_roots.config.json"
    path.write_text(json.dumps(sandbox_config), encoding="utf-8")

    with pytest.raises(ConfigValidationError):
        load_config(path)
