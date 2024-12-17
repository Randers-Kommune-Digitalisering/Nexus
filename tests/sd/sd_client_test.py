import pytest
from unittest.mock import patch
from sd.sd_client import SDClient, SDAPIClient
from utils.config import SD_URL, SD_USERNAME, SD_PASSWORD, SD_BASIC_AUTH

sd_url = SD_URL or "https://sd-mock.com"
sd_auth = SD_BASIC_AUTH or "sd-test-basic-auth"


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
    mock_response = "<response><result>success</result></response>"
    requests_mock.post(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_api_client.post(path=path, json={"data": "value"})

    assert response == {"response": {"result": "success"}}


def test_make_request_success(sd_api_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    mock_response = "<response><key>value</key></response>"
    requests_mock.get(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_api_client.get(path)

    assert response == {"response": {"key": "value"}}


def test_make_request_failure(sd_api_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    requests_mock.get(url, status_code=404)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_api_client.get(path)

    assert response is None


def test_SDAPIClient_get_auth_headers(sd_api_client):
    headers = sd_api_client.get_auth_headers()
    assert headers == {
        "authorization": "Basic " + sd_auth,
        "content-type": "application/xml"
    }


# SDClient
@pytest.fixture
def sd_client():
    return SDClient(username=SD_USERNAME, password=SD_PASSWORD, url=sd_url)


def test_get_person(sd_client, requests_mock):
    path = "GetPerson"
    url = f"{sd_url}/{path}"
    mock_response = "<GetPerson><Person><name>John Doe</name></Person></GetPerson>"
    requests_mock.get(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        with patch.object(SDClient, 'get_request', return_value={"GetPerson": {"Person": {"name": "John Doe"}}}):
            response = sd_client.get_person(cpr="123456-7890", employement_identifier="emp_id", inst_code="inst_code")

    assert response == {"name": "John Doe"}


def test_get_employment(sd_client, requests_mock):
    path = "GetEmployment20070401"
    url = f"{sd_url}/{path}"
    mock_response = "<GetEmployment20070401><Person><Employment><position>Developer</position></Employment></Person></GetEmployment20070401>"
    requests_mock.get(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        with patch.object(SDClient, 'get_request', return_value={"GetEmployment20070401": {"Person": {"Employment": {"position": "Developer"}}}}):
            response = sd_client.get_employment(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code")

    assert response == {"position": "Developer"}


def test_get_employment_changed(sd_client, requests_mock):
    path = "GetEmploymentChanged20070401"
    url = f"{sd_url}/{path}"
    mock_response = "<GetEmploymentChanged20070401><Person><changes>some changes</changes></Person></GetEmploymentChanged20070401>"
    requests_mock.get(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        with patch.object(SDClient, 'get_request', return_value={"GetEmploymentChanged20070401": {"Person": {"changes": "some changes"}}}):
            response = sd_client.get_employment_changed(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code", activation_date="01.01.2020", deactivation_date="01.01.2021")

    assert response == {"changes": "some changes"}


def test_SDClient_post_request(sd_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    mock_response = "<response><result>success</result></response>"
    requests_mock.post(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_client.post_request(path=path, json={"data": "value"})

    assert response == {"response": {"result": "success"}}


def test_SDClient_put_request(sd_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    mock_response = "<response><result>updated</result></response>"
    requests_mock.put(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_client.put_request(path=path, json={"data": "value"})

    assert response == {"response": {"result": "updated"}}


def test_SDClient_delete_request(sd_client, requests_mock):
    path = "test"
    url = sd_url + "/" + path
    mock_response = "<response><result>deleted</result></response>"
    requests_mock.delete(url, text=mock_response)

    with patch.object(SDAPIClient, 'get_auth_headers', return_value={"Authorization": "Basic test_token"}):
        response = sd_client.delete_request(path=path)

    assert response == {"response": {"result": "deleted"}}


def test_SDClient_get_person_no_response(sd_client):
    with patch.object(SDClient, 'get_request', return_value=None):
        response = sd_client.get_person(cpr="123456-7890", employement_identifier="emp_id", inst_code="inst_code")
    assert response is False


def test_SDClient_get_person_no_person_data(sd_client):
    with patch.object(SDClient, 'get_request', return_value={"GetPerson": {}}):
        response = sd_client.get_person(cpr="123456-7890", employement_identifier="emp_id", inst_code="inst_code")
    assert response is None


def test_SDClient_get_employment_no_response(sd_client):
    with patch.object(SDClient, 'get_request', return_value=None):
        response = sd_client.get_employment(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code")
    assert response is False


def test_SDClient_get_employment_no_employment_data(sd_client):
    with patch.object(SDClient, 'get_request', return_value={"GetEmployment20070401": {"Person": {}}}):
        response = sd_client.get_employment(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code")
    assert response is None


def test_SDClient_get_employment_changed_no_response(sd_client):
    with patch.object(SDClient, 'get_request', return_value=None):
        response = sd_client.get_employment_changed(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code", activation_date="01.01.2020", deactivation_date="01.01.2021")
    assert response is False


def test_SDClient_get_employment_changed_no_person_data(sd_client):
    with patch.object(SDClient, 'get_request', return_value={"GetEmploymentChanged20070401": {}}):
        response = sd_client.get_employment_changed(cpr="123456-7890", employment_identifier="emp_id", inst_code="inst_code", activation_date="01.01.2020", deactivation_date="01.01.2021")
    assert response is None
