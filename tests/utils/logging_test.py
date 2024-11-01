import pytest
from unittest.mock import patch, MagicMock
from werkzeug import serving
from utils.logging import disable_endpoint_logs


@pytest.fixture
def mock_log_request():
    with patch('utils.logging.serving.WSGIRequestHandler.log_request') as mock:
        yield mock


def test_disable_endpoint_logs_for_disabled_endpoints(mock_log_request):
    disabled_endpoints = ('/metrics', '/healthz')
    disable_endpoint_logs(disabled_endpoints)

    # Create a mock request handler
    mock_handler = MagicMock()
    mock_handler.path = '/metrics'

    # Call the log_request method
    serving.WSGIRequestHandler.log_request(mock_handler)

    # Ensure the original log_request is not called for disabled endpoints
    mock_log_request.assert_not_called()


def test_disable_endpoint_logs_for_non_disabled_endpoints(mock_log_request):
    disabled_endpoints = ('/metrics', '/healthz')
    disable_endpoint_logs(disabled_endpoints)

    # Create a mock request handler
    mock_handler = MagicMock()
    mock_handler.path = '/other'

    # Call the log_request method
    serving.WSGIRequestHandler.log_request(mock_handler)

    # Ensure the original log_request is called for other endpoints
    mock_log_request.assert_called_once()


def test_disable_endpoint_logs_partial_match(mock_log_request):
    disabled_endpoints = ('/metrics', '/healthz')
    disable_endpoint_logs(disabled_endpoints)

    # Create a mock request handler
    mock_handler = MagicMock()
    mock_handler.path = '/metrics/extra'

    # Call the log_request method
    serving.WSGIRequestHandler.log_request(mock_handler)

    # Ensure the original log_request is called for partial matches
    mock_log_request.assert_called_once()


def test_disable_endpoint_logs_no_disabled_endpoints(mock_log_request):
    disabled_endpoints = ()
    disable_endpoint_logs(disabled_endpoints)

    # Create a mock request handler
    mock_handler = MagicMock()
    mock_handler.path = '/metrics'

    # Call the log_request method
    serving.WSGIRequestHandler.log_request(mock_handler)

    # Ensure the original log_request is called when no endpoints are disabled
    mock_log_request.assert_called_once()
