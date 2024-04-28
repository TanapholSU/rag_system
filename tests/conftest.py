import pytest
import os

from vector_db_task import app
from config import app_config

@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "redis://127.0.0.1/0",
        "result_backend": "redis://127.0.0.1/0",
    }


#
def pytest_configure():
    # set debug to false
    app_config.debug = False
