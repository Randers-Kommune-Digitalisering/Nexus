import pytest
import requests
import requests_mock
from unittest.mock import MagicMock
from kp.kp_client import KPAPIClient, KPClient
from utils.config import BROWSERLESS_URL, KP_URL

kp_url = KP_URL


@pytest.fixture
def kp_api_client():
    return KPAPIClient(username="test_user", password="test_password")


@pytest.fixture
def kp_client(kp_api_client):
    kp_client = KPClient(username="test_user", password="test_password")
    kp_api_client.request_session_token = MagicMock(return_value="test_session_cookie")
    kp_client.api_client = kp_api_client
    return kp_client


@pytest.fixture
def mock_multiple_requests():
    with requests_mock.Mocker() as m:
        yield m


# KPAPIClient
def test_classmethod_get_client():
    client1 = KPClient(username="test_username", password="test_password").api_client

    assert client1.username == "test_username"
    assert client1.password == "test_password"

    client2 = KPAPIClient.get_client(
        username="test_username",
        password="test_password"
    )

    assert client1 == client2


def test_request_session_token_success(kp_api_client, requests_mock):
    mock_response = {
        "cookies": [
            {"name": "JSESSIONID", "value": "test_session_cookie"}
        ]
    }

    requests_mock.post(f'{BROWSERLESS_URL}/function', json=mock_response)

    session_cookie = kp_api_client.request_session_token()

    assert session_cookie == "test_session_cookie"
    assert kp_api_client.session_cookie == "test_session_cookie"


def test_request_session_token_failed_not_json(kp_api_client, requests_mock):
    requests_mock.post(f'{BROWSERLESS_URL}/function', text="mock_response")

    session_cookie = kp_api_client.request_session_token()

    assert session_cookie is None
    assert kp_api_client.session_cookie is None


def test_request_session_token_failed_incorrect_json(kp_api_client, requests_mock):
    mock_response = {"mock": []}

    requests_mock.post(f'{BROWSERLESS_URL}/function', json=mock_response)

    session_cookie = kp_api_client.request_session_token()

    assert session_cookie is None
    assert kp_api_client.session_cookie is None


def test_request_session_token_failed_connection_issue(kp_api_client, requests_mock):
    requests_mock.post(f'{BROWSERLESS_URL}/function', exc=requests.exceptions.RequestException)

    session_cookie = kp_api_client.request_session_token()

    assert session_cookie is None
    assert kp_api_client.session_cookie is None


def test_make_request_success(kp_api_client, requests_mock):
    kp_api_client.session_cookie = "test_session_cookie"

    mock_response = {"mock": "response"}

    requests_mock.get(f'{kp_url}/test', json=mock_response)

    response = kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert response == mock_response


def test_make_request_failed_html_response_reauthenticate_called(kp_api_client, mock_multiple_requests):
    kp_api_client.session_cookie = "test_session_cookie"

    kp_api_client.reauthenticate = MagicMock(wraps=kp_api_client.reauthenticate)
    mock_multiple_requests.get(f'{kp_url}/test', [{"text": '<html>mock</html>', 'headers': {"content-type": "text/html"}}, {"json": {"mock": "response"}}])

    kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert kp_api_client.reauthenticate.call_count == 1


def test_make_request_failed_500_AccessDeniedException_reauthenticate_called(kp_api_client, requests_mock):
    kp_api_client.session_cookie = "test_session_cookie"

    kp_api_client.reauthenticate = MagicMock(wraps=kp_api_client.reauthenticate)
    requests_mock.get(f'{kp_url}/test', text="AccessDeniedException", status_code=500)

    kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert kp_api_client.reauthenticate.call_count == 2


def test_make_request_failed_401_reauthenticate_called(kp_api_client, requests_mock):
    kp_api_client.session_cookie = "test_session_cookie"

    kp_api_client.reauthenticate = MagicMock(wraps=kp_api_client.reauthenticate)
    requests_mock.get(f'{kp_url}/test', text="Unauthorized", status_code=401)

    kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert kp_api_client.reauthenticate.call_count == 2


def test_fetch_token_timeout(kp_api_client, mock_multiple_requests):
    kp_api_client.session_cookie = "test_session_cookie"
    kp_api_client.timeout = 0.1

    kp_api_client.authenticate = MagicMock(wraps=kp_api_client.authenticate)
    kp_api_client.reauthenticate = MagicMock(wraps=kp_api_client.reauthenticate)

    mock_response_success = {"json": {"mock": "response"}}
    mock_response_failed = {"text": '<html>mock</html>', 'headers': {"content-type": "text/html"}}
    mock_multiple_requests.get(f'{kp_url}/test', [mock_response_failed, mock_response_success])

    kp_api_client.is_fetching_token = True
    res = kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert kp_api_client.authenticate.call_count == 3
    assert kp_api_client.reauthenticate.call_count == 1
    assert res == mock_response_success.get("json", {})


def test_authenticate_retry_twice_only(kp_api_client, requests_mock):
    kp_api_client.session_cookie = "test_session_cookie"
    kp_api_client.timeout = 0.1

    kp_api_client.authenticate = MagicMock(wraps=kp_api_client.authenticate)
    kp_api_client.reauthenticate = MagicMock(wraps=kp_api_client.reauthenticate)

    requests_mock.get(f'{kp_url}/test', text='<html>mock</html>', headers={"content-type": "text/html"})

    kp_api_client.is_fetching_token = True
    res = kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert kp_api_client.authenticate.call_count == 3
    assert kp_api_client.reauthenticate.call_count == 2
    assert res is None


def test_make_request_return_is_text(kp_api_client, requests_mock):
    kp_api_client.session_cookie = "test_session_cookie"

    mock_response = "mock_ response"

    requests_mock.get(f'{kp_url}/test', text=mock_response)

    res = kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert res == mock_response.encode("utf-8")


def test_make_request_return_is_text_and_empty(kp_api_client, requests_mock):
    kp_api_client.session_cookie = "test_session_cookie"

    mock_response = ""

    requests_mock.get(f'{kp_url}/test', text=mock_response)

    res = kp_api_client._make_request(requests.get, f'{kp_url}/test')

    assert res == " "


# KPClient
def test_kpclient_fetch_token(kp_api_client, requests_mock):
    mock_response = {
        "cookies": [
            {"name": "JSESSIONID", "value": "test_session_cookie"}
        ]
    }

    kp_client = KPClient(username="test_user", password="test_password")
    kp_client.api_client = kp_api_client

    requests_mock.post(f'{BROWSERLESS_URL}/function', json=mock_response)

    session_cookie = kp_client.fetch_token()

    assert session_cookie == "test_session_cookie"
    assert kp_client.api_client.session_cookie == "test_session_cookie"


def test_kpclient_search_person(kp_client, requests_mock):
    mock_response = {"results": ["person1", "person2"]}
    cpr = "1234567890"

    requests_mock.post(f'{kp_url}/rest/api/search/person', json=mock_response)

    response = kp_client.search_person(cpr)

    assert response == mock_response


def test_kpclient_get_person(kp_client, requests_mock):
    mock_response = {"id": "123", "name": "John Doe"}
    person_id = "123"

    requests_mock.get(f'{kp_url}/rest/api/person/overview/{person_id}', json=mock_response)

    response = kp_client.get_person(person_id)

    assert response == mock_response


def test_kpclient_get_pension(kp_client, requests_mock):
    mock_response = {"pension": "details"}
    person_id = "123"

    requests_mock.get(f'{kp_url}/rest/api/person/overview/{person_id}/pensionsoplysninger', json=mock_response)

    response = kp_client.get_pension(person_id)

    assert response == mock_response


def test_kpclient_get_cases(kp_client, requests_mock):
    mock_response = {"cases": ["case1", "case2"]}
    person_id = "123"

    requests_mock.get(f'{kp_url}/rest/api/person/overview/{person_id}/sager?types=aktiv', json=mock_response)

    response = kp_client.get_cases(person_id)

    assert response == mock_response


def test_kpclient_get_personal_supplement(kp_client, requests_mock):
    mock_response = {"supplement": "details"}
    person_id = "123"

    requests_mock.get(f'{kp_url}/rest/api/person/history/{person_id}/personligTillaegsprocent', json=mock_response)

    response = kp_client.get_personal_supplement(person_id)

    assert response == mock_response


def test_kpclient_get_health_supplement(kp_client, requests_mock):
    mock_response = {"health_supplement": "details"}
    person_id = "123"

    requests_mock.get(f'{kp_url}/rest/api/person/history/{person_id}/helbredstillaegsprocent', json=mock_response)

    response = kp_client.get_health_supplement(person_id)

    assert response == mock_response


def test_kpclient_get_special_information(kp_client, requests_mock):
    mock_response = {"special_info": "details"}
    person_id = "123"

    requests_mock.get(f'{kp_url}/rest/api/warning/person/{person_id}', json=mock_response)

    response = kp_client.get_special_information(person_id)

    assert response == mock_response
