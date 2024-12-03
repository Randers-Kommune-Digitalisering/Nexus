import pytest
from unittest.mock import patch
from sd.sd_client import SDClient, SDAPIClient
from utils.config import SD_USERNAME, SD_PASSWORD


sd_url = "https://sd-mock.com"


# SDAPIClient
@pytest.fixture
def sd_api_client():
    return SDAPIClient(username=SD_USERNAME, password=SD_PASSWORD, url=sd_url)


def test_get_client(sd_api_client):
    assert sd_api_client.username == SD_USERNAME
    assert sd_api_client.password == SD_PASSWORD
    assert sd_api_client.base_url == sd_url


def test_classmethod_get_client():
    client1 = SDClient(username=SD_USERNAME, password=SD_PASSWORD, url=sd_url).api_client

    assert client1.username == SD_USERNAME
    assert client1.password == SD_PASSWORD
    assert client1.base_url == sd_url

    client2 = SDAPIClient.get_client(
        username=SD_USERNAME,
        password=SD_PASSWORD,
        url=sd_url
    )

    assert client1 == client2


def test_SDAPIClient_post_request(sd_api_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    mock_response = {"result": "success"}
    requests_mock.post(url, json=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_api_client.post(path=path, json={"data": "value"})

    assert response == mock_response


def test_make_request_success(sd_api_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    mock_response = {"key": "value"}
    requests_mock.get(url, json=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_api_client.get(path)

    assert response == mock_response


def test_make_request_failure(sd_api_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    requests_mock.get(url, status_code=404)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_api_client.get(path)

    assert response is None


# SDClient
@pytest.fixture
def sd_client():
    return SDClient(username=SD_USERNAME, password=SD_PASSWORD, url=sd_url)


def test_get_person(sd_client, requests_mock):
    path = "GetPerson"
    url = f"{sd_url}/{path}"
    mock_response = {"GetPerson": {"Person": {"name": "John Doe"}}}
    requests_mock.get(url, json=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_client.get_person(cpr="123456-7890", employement_identifier="emp_id", inst_code="inst_code")

    assert response == mock_response["GetPerson"]["Person"]


def test_get_employment(sd_client, requests_mock):
    path = "GetEmployment20070401"
    url = f"{sd_url}/{path}"
    mock_response = {"GetEmployment20070401": {"Person": {"Employment": {"position": "Developer"}}}}
    requests_mock.get(url, json=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_client.get_employment(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code")

    assert response == mock_response["GetEmployment20070401"]["Person"]["Employment"]


def test_get_employment_changed(sd_client, requests_mock):
    path = "GetEmploymentChanged20070401"
    url = f"{sd_url}/{path}"
    mock_response = {"GetEmploymentChanged20070401": {"Person": {"changes": "some changes"}}}
    requests_mock.get(url, json=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_client.get_employment_changed(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code", activation_date="01.01.2020", deactivation_date="01.01.2021")

    assert response == mock_response["GetEmploymentChanged20070401"]["Person"]
