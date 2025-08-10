import pytest
from unittest.mock import MagicMock, patch
import app


@pytest.fixture
def client():
    app.app.testing = True
    with app.app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200


def test_main_starts_webview(monkeypatch):
    mock_thread = MagicMock()
    mock_webview = MagicMock()
    mock_exit = MagicMock()

    monkeypatch.setattr(
        app.threading, "Thread", lambda target, daemon: mock_thread
    )
    monkeypatch.setattr(app, "webview", mock_webview)
    monkeypatch.setattr(app.sys, "exit", mock_exit)

    app.main()

    mock_thread.start.assert_called_once()
    mock_webview.create_window.assert_called_once_with(
        "Bookkeeppr", "http://localhost:1304", width=1000, height=700
    )
    mock_webview.start.assert_called_once()
    mock_exit.assert_called_once_with(0)
