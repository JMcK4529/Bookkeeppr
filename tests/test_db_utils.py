import pytest
from unittest.mock import MagicMock, mock_open, call, patch
from tests.data_utils import get_test_data
from lib.db.utils import *

DATA_DIR = f"{os.path.dirname(__file__)}/data/db.utils"


@pytest.mark.parametrize(
    ("params"),
    get_test_data(f"{DATA_DIR}/get_db_path.txt"),
)
def test_get_db_path(params):
    system = params.get("system")
    if system == "Windows":
        local_app_data = params.get("local_app_data")
        app_data = params.get("app_data")
        base = local_app_data or app_data
        expected = Path(base) / "Bookkeeppr" / ".bookkeeppr.db"
    else:
        base = params.get("home")
        expected = Path(base) / ".Bookkeeppr" / ".bookkeeppr.db"

    with (
        patch("lib.db.utils.platform.system") as mock_system,
        patch("lib.db.utils.os.getenv") as mock_getenv,
        patch("lib.db.utils.Path") as mock_path,
    ):
        mock_system.return_value = system
        if system == "Windows":
            mock_getenv.side_effect = [local_app_data, app_data]
            mock_path.return_value = Path(base)
        else:
            mock_path.home.return_value = Path(base)
        result = get_db_path()

    assert result == expected
    mock_system.assert_called_once()
    if system == "Windows":
        assert len(mock_getenv.call_args_list) == 1 if local_app_data else 2
        mock_path.assert_called_once_with(base)
    else:
        mock_path.home.assert_called_once()


@pytest.mark.parametrize(
    ("params"),
    get_test_data(f"{DATA_DIR}/database_exists.txt"),
)
def test_database_exists(params, caplog):
    db_path = Path(params.get("db_path"))
    exists = params.get("exists", True)

    with (
        patch("lib.db.utils.get_db_path", return_value=db_path),
        patch.object(Path, "exists", return_value=exists),
        caplog.at_level(logging.INFO),
    ):

        result = database_exists()

    assert result == exists

    expected_msg = f"[DB] Looking for DB at {db_path}... {'Found' if exists else 'Not found'}"
    assert any(expected_msg in message for message in caplog.messages)


@pytest.mark.parametrize(
    ("params"),
    get_test_data(f"{DATA_DIR}/init_db.txt"),
)
def test_init_db(params, caplog):
    db_path = Path(params.get("db_path", ""))
    schema_content = "CREATE TABLE test (id INTEGER);"
    db_exists = params.get("exists", False)

    with (
        patch("lib.db.utils.get_db_path", return_value=db_path),
        patch.object(Path, "exists", return_value=db_exists),
        patch.object(Path, "mkdir") as mock_mkdir,
        patch("lib.db.utils.sqlite3.connect") as mock_connect,
        patch("builtins.open", mock_open(read_data=schema_content)),
        patch("lib.db.utils.Path.open", mock_open(read_data=schema_content)),
        caplog.at_level(logging.INFO),
    ):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        init_db()

    if db_exists:
        expected_msg = f"[DB] Database already exists at {db_path}"
        assert expected_msg in caplog.text
        mock_mkdir.assert_not_called()
        mock_connect.assert_not_called()
    else:
        expected_msg = f"[DB] Initialized new database at {db_path}"
        assert expected_msg in caplog.text
        mkdir_calls = mock_mkdir.call_args_list
        mkdir_args = call(parents=True, exist_ok=True)
        assert mkdir_calls == [mkdir_args] * 2
        mock_connect.assert_called_once_with(db_path)
        mock_conn.executescript.assert_called_once_with(schema_content)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


def test_create_recovery_db():
    mock_recovery_dir = Path("/tmp/recovery")
    mock_timestamp = "20240728_123456"
    mock_schema_sql = "CREATE TABLE dummy (id INTEGER);"

    with (
        patch(
            "lib.db.utils.get_recovery_path", return_value=mock_recovery_dir
        ),
        patch("lib.db.utils.datetime") as mock_datetime,
        patch("lib.db.utils.sqlite3.connect") as mock_connect,
        patch("lib.db.utils.open", mock_open(read_data=mock_schema_sql)),
    ):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_datetime.now.return_value.strftime.return_value = mock_timestamp

        result = create_recovery_db()

    expected_path = mock_recovery_dir / f"{mock_timestamp}.db"
    assert result == expected_path
    mock_connect.assert_called_once_with(expected_path)
    mock_conn.executescript.assert_called_once_with(mock_schema_sql)


def test_backup_deleted_entity(caplog):
    from lib.db.utils import backup_deleted_entity

    mock_entity = MagicMock()
    mock_transaction = MagicMock()
    mock_recovery_path = Path("/tmp/recovery/test.db")

    mock_repo_instance = MagicMock()
    mock_txn_repo = MagicMock()
    mock_repo_class = MagicMock(return_value=mock_repo_instance)

    mock_repo_instance.get_transactions.return_value = [mock_transaction]
    mock_repo_instance.transaction_repository.return_value = mock_txn_repo

    with (
        patch(
            "lib.db.utils.create_recovery_db", return_value=mock_recovery_path
        ),
        caplog.at_level(logging.INFO),
    ):
        backup_deleted_entity(mock_entity, mock_repo_class)

    mock_repo_class.assert_called_once_with(db_path=mock_recovery_path)
    mock_repo_instance.create.assert_called_once_with(mock_entity)
    mock_repo_instance.get_transactions.assert_called_once_with(mock_entity)
    mock_repo_instance.transaction_repository.assert_called_once_with(
        db_path=mock_recovery_path
    )
    mock_txn_repo.create.assert_called_once_with(mock_transaction)

    assert (
        "[RECOVERY] Successfully backed up entity and transactions."
        in caplog.text
    )


@pytest.mark.parametrize(
    ("input_str", "expected"),
    [
        ("2024-07-01T14:30", "2024-07-01 14:30:00"),
        ("2024-07-01 14:30", "2024-07-01 14:30:00"),
        ("2024-07-01T14:30:59", "2024-07-01 14:30:59"),
        ("2024-07-01 14:30:59", "2024-07-01 14:30:59"),
        ("2024-07-01", "2024-07-01 00:00:00"),
        ("invalid-date", None),
        (None, None),
        ("", None),
    ],
)
def test_normalize_datetime(input_str, expected):
    from lib.db.utils import normalize_datetime

    result = normalize_datetime(input_str)
    assert result == expected
