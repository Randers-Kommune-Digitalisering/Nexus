import pytest
import requests
from unittest.mock import patch, MagicMock
from auth_header_api_client import APIClientWithAuthHeaders


@pytest.fixture
def client():
    with patch.multiple(APIClientWithAuthHeaders, __abstractmethods__=set()):
        base_url = "http://example.com"
        client = APIClientWithAuthHeaders(base_url)
        yield client


@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.get')
def test_get(mock_get, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.get("test-path")

    mock_get.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'}, params=None)
    assert response == {"key": "value"}


@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.post')
def test_post(mock_post, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    response = client.post("test-path", json={"data": "value"})

    mock_post.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'}, data=None, json={"data": "value"})
    assert response == {"key": "value"}


@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.put')
def test_put(mock_put, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status.return_value = None
    mock_put.return_value = mock_response

    response = client.put("test-path", json={"data": "value"})

    mock_put.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'}, data=None, json={"data": "value"})
    assert response == {"key": "value"}


@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.delete')
def test_delete(mock_delete, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status.return_value = None
    mock_delete.return_value = mock_response

    response = client.delete("test-path")

    mock_delete.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'})
    assert response == {"key": "value"}


@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.post')
def test_post_upload(mock_post, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    response = client.post_upload("test-path", data={"key": "value"}, files={"file": "file_content"})

    mock_post.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'}, data={"key": "value"}, files={"file": "file_content"})
    assert response == {"key": "value"}


# Test cases for the get and post methods with full url (starting with http:// or https://)
@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.get')
def test_get_full_url(mock_get, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    full_url = "http://another-example.com/test-path"
    response = client.get(full_url)

    mock_get.assert_called_once_with(full_url, headers={'Authorization': 'Bearer token'}, params=None)
    assert response == {"key": "value"}


@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.post')
def test_post_full_url(mock_post, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    full_url = "https://another-example.com/test-path"
    response = client.post(full_url, json={"data": "value"})

    mock_post.assert_called_once_with(full_url, headers={'Authorization': 'Bearer token'}, data=None, json={"data": "value"})
    assert response == {"key": "value"}


# Test case for handling JSONDecodeError
@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.get')
def test_get_json_decode_error(mock_get, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "", 0)
    mock_response.content = b'Invalid JSON'
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.get("test-path")

    mock_get.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'}, params=None)
    assert response == b'Invalid JSON'


# Test case for handling empty response content
@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.get')
def test_get_empty_content(mock_get, mock_auth_headers, client):
    mock_response = MagicMock()
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "", 0)
    mock_response.content = b''
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.get("test-path")

    mock_get.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'}, params=None)
    assert response == ' '


# Test case for handling RequestException
@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value={'Authorization': 'Bearer token'})
@patch('requests.get')
def test_get_request_exception(mock_get, mock_auth_headers, client):
    mock_get.side_effect = requests.exceptions.RequestException("Request failed")

    response = client.get("test-path")

    mock_get.assert_called_once_with(f"{client.base_url}/test-path", headers={'Authorization': 'Bearer token'}, params=None)
    assert response is None


# Test case for request is not made if no auth headers
@patch.object(APIClientWithAuthHeaders, 'get_auth_headers', return_value=None)
@patch('requests.get')
def test_make_request_no_auth_headers(mock_get, mock_auth_headers, client):
    response = client.get("test-path")

    mock_get.assert_not_called()
    assert response is None
