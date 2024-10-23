import os
import time
import pytest
from unittest.mock import patch
from nexus.nexus_client import NexusClient, NexusAPIClient, NexusRequest
from utils.config import NEXUS_TOKEN_ROUTE

nexus_url = "https://nexus-mock.com"


# NexusAPIClient

@pytest.fixture
def nexus_api_client():
    return NexusAPIClient(client_id="test_id", client_secret="test_secret", url=nexus_url)


def test_classmethod_get_client():
    client1 = NexusClient(client_id="test_id", client_secret="test_secret", url=nexus_url).api_client

    assert client1.client_id == "test_id"
    assert client1.client_secret == "test_secret"
    assert client1.base_url == nexus_url

    client2 = NexusAPIClient.get_client(
        client_id="test_id",
        client_secret="test_secret",
        url=nexus_url
    )

    assert client1 == client2


def test_post_request(nexus_api_client, requests_mock):
    path = "test"
    url = nexus_url + "/" + path
    mock_response = {"result": "success"}
    requests_mock.post(url, json=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_api_client.post(path=path, json={"data": "value"})

    assert response == mock_response


def test_make_request_success(nexus_api_client, requests_mock):
    path = "test"
    url = nexus_url + "/" + path
    mock_response = {"key": "value"}
    requests_mock.get(url, json=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_api_client.get(path)

    assert response == mock_response


def test_make_request_failure(nexus_api_client, requests_mock):
    path = "test"
    url = nexus_url + "/" + path
    requests_mock.get(url, status_code=404)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_api_client.get(path)

    assert response is None


def test_put_request(nexus_api_client, requests_mock):
    path = "test"
    url = nexus_url + "/" + path
    mock_response = {"result": "updated"}
    requests_mock.put(url, json=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_api_client.put(path, json={"data": "value"})

    assert response == mock_response


def test_delete_request(nexus_api_client, requests_mock):
    path = "test"
    url = f"{nexus_api_client.base_url}/{path}"
    mock_response = b"success"  # Use bytes for mock response
    requests_mock.delete(url, content=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_api_client.delete(path)

    assert response == mock_response


def test_request_access_token_success(nexus_api_client, requests_mock):
    url = nexus_url + '/' + os.environ["NEXUS_TOKEN_ROUTE"]
    mock_response = {
        "access_token": "test_access_token",
        "expires_in": 3600,
        "refresh_token": "test_refresh_token",
        "refresh_expires_in": 7200
    }
    requests_mock.post(url, json=mock_response)

    response = nexus_api_client.request_access_token()
    assert response == mock_response["access_token"]
    assert nexus_api_client.access_token == mock_response["access_token"]
    assert nexus_api_client.refresh_token == mock_response["refresh_token"]


def test_refresh_access_token_success(nexus_api_client, requests_mock):
    url = nexus_url + '/' + os.environ["NEXUS_TOKEN_ROUTE"]
    mock_response = {
        "access_token": "new_test_access_token",
        "expires_in": 3600,
        "refresh_token": "new_test_refresh_token",
        "refresh_expires_in": 7200
    }
    nexus_api_client.refresh_token = "old_test_refresh_token"
    requests_mock.post(url, json=mock_response)

    response = nexus_api_client.refresh_access_token()
    assert response == mock_response["access_token"]
    assert nexus_api_client.access_token == mock_response["access_token"]
    assert nexus_api_client.refresh_token == mock_response["refresh_token"]


def test_request_access_token_failure(nexus_api_client, requests_mock):
    requests_mock.post(f'{nexus_url}/{NEXUS_TOKEN_ROUTE}', status_code=400)

    response = nexus_api_client.get_auth_headers()

    assert response is None
    assert nexus_api_client.access_token is None


def test_refresh_access_token_failure(nexus_api_client, requests_mock):
    requests_mock.post(f'{nexus_url}/{NEXUS_TOKEN_ROUTE}', status_code=400)

    nexus_api_client.access_token = "existing_token"
    nexus_api_client.access_token_expiry = time.time() - 60

    response = nexus_api_client.get_auth_headers()

    assert response is None


def test_get_auth_headers_returns_headers_self_token_if_not_expired(nexus_api_client):
    nexus_api_client.access_token = "existing_token"
    nexus_api_client.access_token_expiry = time.time() + 60

    expected_headers = {"Authorization": "Bearer existing_token"}

    headers = nexus_api_client.get_auth_headers()

    assert headers == expected_headers


# NexusClient

@pytest.fixture
def nexus_client():
    return NexusClient(client_id="test_id", client_secret="test_secret", url=nexus_url)


def test_home_resource(nexus_client, requests_mock):
    path = "api/core/mobile/randers/v2/"
    url = f"{nexus_url}/{path}"
    mock_response = {"key": "value"}
    requests_mock.get(url, json=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.home_resource()

    assert response == mock_response


def test_find_professional_by_query(nexus_client, requests_mock):
    home_path = "api/core/mobile/randers/v2/"
    home_url = f"{nexus_url}/{home_path}"
    home_response = {
        "_links": {
            "professionals": {
                "href": f"{nexus_url}/professionals"
            }
        }
    }
    professionals_response = {"professionals": ["prof1", "prof2"]}
    requests_mock.get(home_url, json=home_response)
    requests_mock.get(f"{nexus_url}/professionals", json=professionals_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.find_professional_by_query("test_query")

    assert response == professionals_response


def test_find_external_professional_by_query(nexus_client, requests_mock):
    home_path = "api/core/mobile/randers/v2/"
    home_url = f"{nexus_url}/{home_path}"
    home_response = {
        "_links": {
            "importProfessionalFromSts": {
                "href": f"{nexus_url}/importProfessionalFromSts"
            }
        }
    }
    external_professionals_response = {"external_professionals": ["ext_prof1", "ext_prof2"]}
    requests_mock.get(home_url, json=home_response)
    requests_mock.get(f"{nexus_url}/importProfessionalFromSts", json=external_professionals_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.find_external_professional_by_query("test_query")

    assert response == external_professionals_response


def test_find_patient_by_query(nexus_client, requests_mock):
    home_path = "api/core/mobile/randers/v2/"
    home_url = f"{nexus_url}/{home_path}"
    home_response = {
        "_links": {
            "patients": {
                "href": f"{nexus_url}/patients"
            }
        }
    }
    patients_response = {"patients": ["patient1", "patient2"]}
    requests_mock.get(home_url, json=home_response)
    requests_mock.get(f"{nexus_url}/patients", json=patients_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.find_patient_by_query("test_query")

    assert response == patients_response


def test_fetch_patient_by_query(nexus_client, requests_mock):
    home_path = "api/core/mobile/randers/v2/"
    home_url = f"{nexus_url}/{home_path}"
    home_response = {
        "_links": {
            "patients": {
                "href": f"{nexus_url}/patients"
            }
        }
    }
    patient_search_response = {
        "pages": [
            {
                "_links": {
                    "patientData": {
                        "href": f"{nexus_url}/patientData"
                    }
                }
            }
        ]
    }
    patient_data_response = [
        {
            "_links": {
                "self": {
                    "href": f"{nexus_url}/self"
                }
            }
        }
    ]
    patient_self_response = {"patient": "details"}
    requests_mock.get(home_url, json=home_response)
    requests_mock.get(f"{nexus_url}/patients", json=patient_search_response)
    requests_mock.get(f"{nexus_url}/patientData", json=patient_data_response)
    requests_mock.get(f"{nexus_url}/self", json=patient_self_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.fetch_patient_by_query("test_query")

    assert response == patient_self_response


def test_fetch_patient_by_query_response_structure_fail(nexus_client, requests_mock):
    home_path = "api/core/mobile/randers/v2/"
    home_url = f"{nexus_url}/{home_path}"
    home_response = {
        "_links": {
            "patients": {
                "href": f"{nexus_url}/patients"
            }
        }
    }
    patient_search_response = {"pages": {}}
    requests_mock.get(home_url, json=home_response)
    requests_mock.get(f"{nexus_url}/patients", json=patient_search_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.fetch_patient_by_query("test_query")

    assert response is None


# forces a key exception
def test_fetch_patient_by_query_exception_fail(nexus_client, requests_mock):
    home_path = "api/core/mobile/randers/v2/"
    home_url = f"{nexus_url}/{home_path}"
    home_response = {
        "_links": {
            "patients": {
                "href": f"{nexus_url}/patients"
            }
        }
    }
    patient_search_response = {"mock": {}}  # forces a key exception, "pages" key is missing
    requests_mock.get(home_url, json=home_response)
    requests_mock.get(f"{nexus_url}/patients", json=patient_search_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.fetch_patient_by_query("test_query")

    assert response is None


def test_fetch_borgerkalender(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    patient_preferences_response = {"CITIZEN_CALENDAR": [{"name": "Borgerkalender", "_links": {"self": {"href": f"{nexus_url}/borgerkalender"}}}]}
    borgerkalender_response = {"calendar": "details"}
    requests_mock.get(f"{nexus_url}/patientPreferences", json=patient_preferences_response)
    requests_mock.get(f"{nexus_url}/borgerkalender", json=borgerkalender_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.fetch_borgerkalender(patient)

    assert response == borgerkalender_response


def test_fetch_dashboard(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    dashboard_id = "dashboard1"
    patient_preferences_response = {"CITIZEN_DASHBOARD": [{"id": dashboard_id, "_links": {"self": {"href": f"{nexus_url}/dashboard"}}}]}
    dashboard_response = {"dashboard": "details"}
    requests_mock.get(f"{nexus_url}/patientPreferences", json=patient_preferences_response)
    requests_mock.get(f"{nexus_url}/dashboard", json=dashboard_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.fetch_dashboard(patient, dashboard_id)

    assert response == dashboard_response


def test_fetch_dashboard_no_dashboard(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    dashboard_id = "dashboard1"
    patient_preferences_response = {"CITIZEN_DASHBOARD": [{"id": 'mock', "_links": {"self": {"href": f"{nexus_url}/dashboard"}}}]}
    dashboard_response = {"dashboard": "details"}
    requests_mock.get(f"{nexus_url}/patientPreferences", json=patient_preferences_response)
    requests_mock.get(f"{nexus_url}/dashboard", json=dashboard_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.fetch_dashboard(patient, dashboard_id)

    assert response is False


def test_fetch_dashboard_exception(nexus_client):
    with patch('nexus.nexus_client.NexusRequest.__init__', raise_exception=Exception("Test exception")):
        patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
        response = nexus_client.fetch_dashboard(patient, 'mock_dashboard_id')

        assert response is None


def test_client_get_request(nexus_client, requests_mock):
    path = "test"
    url = f"{nexus_url}/{path}"
    mock_response = {"result": "success"}
    requests_mock.get(url, json=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.get_request(path)

    assert response == mock_response


def test_client_post_request(nexus_client, requests_mock):
    path = "test"
    url = f"{nexus_url}/{path}"
    mock_response = {"result": "success"}
    requests_mock.post(url, json=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.post_request(path, json={"data": "value"})

    assert response == mock_response


def test_client_put_request(nexus_client, requests_mock):
    path = "test"
    url = f"{nexus_url}/{path}"
    mock_response = {"result": "updated"}
    requests_mock.put(url, json=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.put_request(path, json={"data": "value"})

    assert response == mock_response


def test_client_delete_request(nexus_client, requests_mock):
    path = "test"
    url = f"{nexus_url}/{path}"
    mock_response = b"success"  # Use bytes for mock response
    requests_mock.delete(url, content=mock_response)

    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = nexus_client.delete_request(path)

    assert response == mock_response


# NexusRequest

def test_nexus_request_get(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    patient_preferences_response = {"preferences": "details"}
    requests_mock.get(f"{nexus_url}/patientPreferences", json=patient_preferences_response)

    request = NexusRequest(method="GET", link_href="patientPreferences", input_response=patient)
    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = request.execute(None)

    assert response == patient_preferences_response


def test_nexus_request_post(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    post_response = {"result": "success"}
    requests_mock.post(f"{nexus_url}/patientPreferences", json=post_response)

    request = NexusRequest(method="POST", link_href="patientPreferences", input_response=patient, payload={"data": "value"})
    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = request.execute(None)

    assert response == post_response


def test_nexus_request_put(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    put_response = {"result": "updated"}
    requests_mock.put(f"{nexus_url}/patientPreferences", json=put_response)

    request = NexusRequest(method="PUT", link_href="patientPreferences", input_response=patient, payload={"data": "value"})
    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = request.execute(None)

    assert response == put_response


def test_nexus_request_delete(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    delete_response = b"success"
    requests_mock.delete(f"{nexus_url}/patientPreferences", content=delete_response)

    request = NexusRequest(method="DELETE", link_href="patientPreferences", input_response=patient)
    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = request.execute(None)

    assert response == delete_response


def test_nexus_request_get_with_params(nexus_client, requests_mock):
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}
    patient_preferences_response = {"preferences": "details"}
    requests_mock.get(f"{nexus_url}/patientPreferences?param1=value1", json=patient_preferences_response)

    request = NexusRequest(method="GET", link_href="patientPreferences", input_response=patient, params={"param1": "value1"})
    with patch.object(NexusAPIClient, 'get_auth_headers', return_value={"Authorization": "Bearer test_token"}):
        response = request.execute(None)

    assert response == patient_preferences_response


def test_nexus_request_invalid_method():
    patient = {"_links": {"patientPreferences": {"href": f"{nexus_url}/patientPreferences"}}}

    request = NexusRequest(method="INVALID", link_href="patientPreferences", input_response=patient)
    with pytest.raises(ValueError, match="Unsupported method: INVALID"):
        request.execute(None)


def test_nexus_request_link_not_found():
    patient = {"_links": {}}

    request = NexusRequest(method="GET", link_href="patientPreferences", input_response=patient)
    with pytest.raises(ValueError, match="Link 'patientPreferences' not found in the response"):
        request.execute(None)


def test_get_nested_value_success():
    data = {
        "level1": {
            "level2": {
                "level3": "value"
            }
        }
    }
    keys = ["level1", "level2", "level3"]
    request = NexusRequest(method="GET")
    result = request._get_nested_value(data, keys)
    assert result == "value"


def test_get_nested_value_missing_key():
    data = {
        "level1": {
            "level2": {
                "level3": "value"
            }
        }
    }
    keys = ["level1", "missing_level", "level3"]
    request = NexusRequest(method="GET")
    result = request._get_nested_value(data, keys)
    assert result is None


def test_get_nested_value_non_dict():
    data = {
        "level1": ["not_a_dict"]
    }
    keys = ["level1", "level2"]
    request = NexusRequest(method="GET")
    result = request._get_nested_value(data, keys)
    assert result is None


def test_get_nested_value_empty_keys():
    data = {
        "level1": {
            "level2": {
                "level3": "value"
            }
        }
    }
    keys = []
    request = NexusRequest(method="GET")
    result = request._get_nested_value(data, keys)
    assert result == data
