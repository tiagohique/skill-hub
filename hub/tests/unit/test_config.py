import pytest

from hub.config import Settings


def test_settings_defaults() -> None:
    s = Settings.from_env({"DATABASE_URL": "x", "MIGRATION_DATABASE_URL": "y"})
    assert s.database_url == "x"
    assert s.migration_database_url == "y"
    assert s.max_file_bytes == 1048576
    assert s.max_bundle_bytes == 5242880
    assert s.max_files == 100
    assert s.blob_backend == "postgres"


def test_settings_overrides_limits() -> None:
    s = Settings.from_env(
        {
            "DATABASE_URL": "x",
            "MIGRATION_DATABASE_URL": "y",
            "MAX_FILE_BYTES": "10",
            "MAX_BUNDLE_BYTES": "20",
            "MAX_FILES": "3",
            "BLOB_BACKEND": "postgres",
        }
    )
    assert (s.max_file_bytes, s.max_bundle_bytes, s.max_files) == (10, 20, 3)


def test_settings_missing_database_url_raises() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings.from_env({"MIGRATION_DATABASE_URL": "y"})
