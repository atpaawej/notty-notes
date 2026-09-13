import tempfile, shutil, pytest
from tests.e2e.harness.app_driver import get_driver

@pytest.fixture
def driver(tmp_path):
    d=get_driver(tmpdir=str(tmp_path))
    yield d
    d.close()
