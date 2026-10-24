import os

import pytest

# Las pruebas usan la base de datos en memoria: no tocan Supabase.
os.environ["USE_MEMORY_DB"] = "1"
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret")
os.environ.setdefault("FERNET_KEY", "x3sJ3B2O2iZ0eQm3Vn6W8bS7mVq3F3bC1cP0QnqXy1E=")


@pytest.fixture(autouse=True, scope="session")
def prefect_harness():
    """Servidor Prefect temporal y aislado para que los flows corran sin `prefect server start`."""
    from prefect.testing.utilities import prefect_test_harness

    with prefect_test_harness():
        yield
