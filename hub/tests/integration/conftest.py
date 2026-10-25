import pytest


@pytest.fixture(autouse=True)
def _clean(clean_db: None) -> None:
    """Todo teste de integração começa com o esquema migrado e as tabelas vazias."""
