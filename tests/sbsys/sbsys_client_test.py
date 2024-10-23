import pytest
import time
from unittest.mock import patch
from sbsys.sbsys_client import SbsysClient, SbsysAPIClient
from utils.config import SBSIP_URL


sbsys_url = "https://sbsys-mock.com"


# SbsysAPIClient

@pytest.fixture
def sbsys_api_client():
    return SbsysAPIClient(client_id="test_id", client_secret="test_secret", username="test_user", password="test_password", url=sbsys_url)


def test_get_client(sbsys_api_client):
    assert sbsys_api_client.client_id == "test_id"
    assert sbsys_api_client.client_secret == "test_secret"
    assert sbsys_api_client.username == "test_user"
    assert sbsys_api_client.password == "test_password"
    assert sbsys_api_client.base_url == sbsys_url


def test_classmethod_get_client():
    client1 = SbsysClient(client_id="test_id", client_secret="test_secret", username="test_user", password="test_password", url=sbsys_url).api_client

    assert client1.client_id == "test_id"
    assert client1.client_secret == "test_secret"
    assert client1.username == "test_user"
    assert client1.password == "test_password"
    assert client1.base_url == sbsys_url

    client2 = SbsysAPIClient.get_client(
        client_id="test_id",
        client_secret="test_secret",
        username="test_user",
        password="test_password",
        url=sbsys_url
    )

    assert client1 == client2


def test_SbsysAPIClient_post_request(sbsys_api_client, requests_mock):
    path = "test"
    url = sbsys_url + "/" + path
    mock_response = {"result": "success"}
    requests_mock.post(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_api_client.post(path=path, json={"data": "value"})

    assert response == mock_response


def test_make_request_success(sbsys_api_client, requests_mock):
    path = "test"
    url = sbsys_url + "/" + path
    mock_response = {"key": "value"}
    requests_mock.get(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_api_client.get(path)

    assert response == mock_response


def test_make_request_failure(sbsys_api_client, requests_mock):
    path = "test"
    url = sbsys_url + "/" + path
    requests_mock.get(url, status_code=404)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_api_client.get(path)

    assert response is None


def test_SbsysAPIClient_put_request(sbsys_api_client, requests_mock):
    path = "test"
    url = sbsys_url + "/" + path
    mock_response = {"result": "updated"}
    requests_mock.put(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_api_client.put(path, json={"data": "value"})

    assert response == mock_response


def test_SbsysAPIClient_delete_request(sbsys_api_client, requests_mock):
    path = "test"
    url = f"{sbsys_api_client.base_url}/{path}"
    mock_response = b"success"  # Use bytes for mock response
    requests_mock.delete(url, content=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_api_client.delete(path)

    assert response == mock_response


def test_request_access_token_success(sbsys_api_client, requests_mock):
    url = SBSIP_URL + "/auth/realms/sbsip/protocol/openid-connect/token"
    mock_response = {
        "access_token": "test_access_token",
        "expires_in": 3600
    }
    requests_mock.post(url, json=mock_response)

    response = sbsys_api_client.request_access_token()
    assert response == mock_response["access_token"]
    assert sbsys_api_client.access_token == mock_response["access_token"]


def test_request_access_token_failure(sbsys_api_client, requests_mock):
    url = SBSIP_URL + "/auth/realms/sbsip/protocol/openid-connect/token"
    requests_mock.post(url, status_code=400)

    response = sbsys_api_client.get(sbsys_url)

    assert response is None
    assert sbsys_api_client.access_token is None


def test_get_auth_headers_returns_headers_self_token_if_not_expired(sbsys_api_client):
    sbsys_api_client.access_token = "existing_token"
    sbsys_api_client.access_token_expiry = time.time() + 60

    expected_headers = {"Authorization": "Bearer existing_token"}

    headers = sbsys_api_client.get_auth_headers()

    assert headers == expected_headers


# SbsysClient
@pytest.fixture
def sbsys_client():
    return SbsysClient(client_id="test_id", client_secret="test_secret", username="test_user", password="test_password", url=sbsys_url)


def test_sag_search(sbsys_client, requests_mock):
    path = "api/sag/search"
    url = f"{sbsys_url}/{path}"
    mock_response = {"result": "success"}
    requests_mock.post(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_client.sag_search(payload={"data": "value"})

    assert response == mock_response


def test_fetch_documents(sbsys_client, requests_mock):
    sag_id = "123"
    path = f"api/sag/{sag_id}/dokumenter"
    url = f"{sbsys_url}/{path}"
    mock_response = {"documents": ["doc1", "doc2"]}
    requests_mock.get(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_client.fetch_documents(sag_id)

    assert response == mock_response


def test_fetch_file(sbsys_client, requests_mock):
    file_id = "456"
    path = f"/api/fil/{file_id}"
    url = f"{sbsys_url}/{path}"
    mock_response = b"file_content"
    requests_mock.get(url, content=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_client.fetch_file(file_id)

    assert response == mock_response


def test_SbsysClient_get_request(sbsys_client, requests_mock):
    path = "test"
    url = f"{sbsys_url}/{path}"
    mock_response = {"key": "value"}
    requests_mock.get(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_client.get_request(path)

    assert response == mock_response


def test_SbsysClient_post_request(sbsys_client, requests_mock):
    path = "test"
    url = f"{sbsys_url}/{path}"
    mock_response = {"result": "success"}
    requests_mock.post(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_client.post_request(path=path, json={"data": "value"})

    assert response == mock_response


def test_SbsysClient_put_request(sbsys_client, requests_mock):
    path = "test"
    url = f"{sbsys_url}/{path}"
    mock_response = {"result": "updated"}
    requests_mock.put(url, json=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_client.put_request(path=path, json={"data": "value"})

    assert response == mock_response


def test_SbsysClient_delete_request(sbsys_client, requests_mock):
    path = "test"
    url = f"{sbsys_url}/{path}"
    mock_response = b"success"
    requests_mock.delete(url, content=mock_response)

    with patch.object(SbsysAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = sbsys_client.delete_request(path)

    assert response == mock_response
