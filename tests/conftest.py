import pytest
import os


from vector_db_task import app


@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "redis://127.0.0.1/0",
        "result_backend": "redis://127.0.0.1/0",
    }


#
def pytest_configure():
    # os.system('curl -s -L -o tektome_files.tar.gz "https://drive.google.com/uc?export=download&id=1lFs8qpOEzXqYP9OB47Cjp0aPx7HkHdtW"')
    # os.system('mkdir test_files && tar -xzvf tektome_files.tar.gz -C test_files/')
    pass
