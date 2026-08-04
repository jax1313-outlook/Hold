import pytest

from dispatch.queue.app import create_app
from dispatch.queue.store import QueueStore


@pytest.fixture
def queue_store(db_conn) -> QueueStore:
    return QueueStore(db_conn)


@pytest.fixture
def flask_app(sandbox_config):
    app = create_app(sandbox_config)
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
