"""Loads and validates dispatch.config.json against contracts/config.schema.json.

Enforces the refusal rule from that contract: a component MUST refuse to
start if environment is "sandbox" but any root resolves under a
production path (D:\\Dispatch Operations, D:\\Memory, D:\\Archive). No
component ever hardcodes a root — every path a caller needs comes out of
the dict this module returns.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SCHEMA_PATH = _REPO_ROOT / "contracts" / "config.schema.json"

# Production roots, per contracts/config.schema.json's refusal_rule and
# DISPATCH_BASE_CONSTITUTION_v1 #1 (storage mapping). Compared
# case-insensitively against a forward-slash-normalized form of each
# configured root, so this check is correct regardless of the host OS this
# loader happens to run on.
_PRODUCTION_ROOT_PREFIXES = (
    "d:/dispatch operations",
    "d:/memory",
    "d:/archive",
)


class ConfigError(Exception):
    """Base class for config loading/validation failures."""


class ConfigValidationError(ConfigError):
    """The config file does not conform to contracts/config.schema.json."""


class SandboxRefusalError(ConfigError):
    """environment is 'sandbox' but a root resolves under a production path."""


def _normalize(path_str: str) -> str:
    return path_str.replace("\\", "/").strip().lower()


def _is_production_path(path_str: str) -> bool:
    normalized = _normalize(path_str)
    return any(normalized.startswith(prefix) for prefix in _PRODUCTION_ROOT_PREFIXES)


def load_schema(schema_path: Path | str = _DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(
    config_path: Path | str, schema_path: Path | str = _DEFAULT_SCHEMA_PATH
) -> dict[str, Any]:
    """Load, schema-validate, and sandbox-refusal-check a dispatch config
    file. Returns the parsed config dict on success."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    schema = load_schema(schema_path)
    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as exc:
        raise ConfigValidationError(
            f"{config_path} does not conform to {schema_path}: {exc.message}"
        ) from exc

    if config["environment"] == "sandbox":
        for tier, root in config["roots"].items():
            if _is_production_path(root):
                raise SandboxRefusalError(
                    f"Refusing to start: environment is 'sandbox' but "
                    f"roots.{tier} ({root!r}) resolves under a production path."
                )

    return config
