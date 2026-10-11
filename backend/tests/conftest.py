import os
import pathlib

# Must be set before any app.* module is imported -- Settings() reads the
# environment at import time, and we never want tests touching the real
# jarvis.db used by the running application.
TEST_DB_PATH = (pathlib.Path(__file__).parent / "test_jarvis.db").resolve()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["ENABLE_CLOUD_AI"] = "false"

import pytest


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    from app.models.base import Base, engine
    # Importing app.models ensures every model (including ones only
    # referenced via relationship()) is registered on Base.metadata.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def db_session():
    from app.models.base import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
