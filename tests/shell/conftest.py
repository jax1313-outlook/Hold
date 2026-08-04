"""Shell fixtures. sandbox_config/db_conn come from tests/conftest.py --
the same throwaway-sandbox pattern every other lane's tests use."""
from __future__ import annotations

import pytest

from dispatch.shell.app import create_app


@pytest.fixture
def client(sandbox_config):
    app = create_app(sandbox_config)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
