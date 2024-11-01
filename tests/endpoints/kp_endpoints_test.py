import pytest
from unittest.mock import patch
from flask import Flask
from endpoints.kp_endpoints import api_kp_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(api_kp_bp)
    yield app.test_client()


@pytest.fixture
def success_mock_kp_client():
    with patch('endpoints.kp_endpoints.kp_client') as mock_kp_client:
        mock_kp_client.fetch_token.return_value = {'token': 'mock_token'}
        mock_kp_client.search_person.return_value = {'personSearches': [{'id': 'mock_id'}]}
        mock_kp_client.get_person.return_value = {'id': 'mock_id', 'name': 'mock_name'}
        mock_kp_client.get_cases.return_value = [{'case_id': 'mock_case_id'}]
        mock_kp_client.get_pension.return_value = {'pension': 'mock_pension'}
        mock_kp_client.get_personal_supplement.return_value = {'personal_supplement': 'mock_personal_supplement'}
        mock_kp_client.get_health_supplement.return_value = {'heath_supplement': 'mock_heath_supplement'}
        mock_kp_client.get_special_information.return_value = {'special_information': 'mock_special_information'}
        yield mock_kp_client


@pytest.fixture
def failed_mock_kp_client():
    with patch('endpoints.kp_endpoints.kp_client') as mock_kp_client:
        mock_kp_client.fetch_token.return_value = None
        mock_kp_client.search_person.return_value = None
        mock_kp_client.get_person.return_value = None
        mock_kp_client.get_cases.return_value = None
        mock_kp_client.get_pension.return_value = None
        mock_kp_client.get_personal_supplement.return_value = None
        mock_kp_client.get_health_supplement.return_value = None
        mock_kp_client.get_special_information.return_value = None
        yield mock_kp_client


@pytest.fixture
def failed_mock_kp_client_with_exception():
    with patch('endpoints.kp_endpoints.kp_client') as mock_kp_client:
        mock_kp_client.fetch_token.side_effect = Exception('mock_exception')
        mock_kp_client.search_person.side_effect = Exception('mock_exception')
        mock_kp_client.get_person.side_effect = Exception('mock_exception')
        mock_kp_client.get_cases.side_effect = Exception('mock_exception')
        mock_kp_client.get_pension.side_effect = Exception('mock_exception')
        mock_kp_client.get_personal_supplement.side_effect = Exception('mock_exception')
        mock_kp_client.get_health_supplement.side_effect = Exception('mock_exception')
        mock_kp_client.get_special_information.side_effect = Exception('mock_exception')
        yield mock_kp_client


def test_fetch_kp_token(client, success_mock_kp_client):
    response = client.get('/api/kp/token')

    assert response.status_code == 200
    assert response.get_json() == {'token': 'mock_token'}
    success_mock_kp_client.fetch_token.assert_called_once()


def test_search_person(client, success_mock_kp_client):
    response = client.post('/api/kp/search/person', json={'cpr': 'mock_cpr'})

    assert response.status_code == 200
    assert response.get_json() == {'personSearches': [{'id': 'mock_id'}]}
    success_mock_kp_client.search_person.assert_called_once_with('mock_cpr')


def test_search_person_no_cpr(client, success_mock_kp_client):
    response = client.post('/api/kp/search/person', json={'test': 'mock_cpr'})

    assert response.status_code == 400
    assert response.get_json() == {'error': 'cpr is required'}


def test_search_person_kp_client_failed(client, failed_mock_kp_client):
    response = client.post('/api/kp/search/person', json={'cpr': 'mock_cpr'})

    assert response.status_code == 400
    assert response.get_json() == {'cpr': 'mock_cpr', 'error': 'No response'}


def test_search_person_kp_client_exception(client, failed_mock_kp_client_with_exception):
    response = client.post('/api/kp/search/person', json={'cpr': 'mock_cpr'})

    assert response.status_code == 500
    assert response.get_json() == {'error': 'mock_exception'}


def test_get_person_with_id(client, success_mock_kp_client):
    response = client.get('/api/kp/person', query_string={'id': 'mock_id'})

    assert response.status_code == 200

    keys_to_check = ['id', 'sager', 'pension', 'personligTillaegsprocent', 'helbredstillaegsprocent', 'saerligeOplysninger']
    assert all(key in response.get_json() for key in keys_to_check)
    success_mock_kp_client.get_person.assert_called_once_with('mock_id')


def test_get_person_with_cpr(client, success_mock_kp_client):
    response = client.get('/api/kp/person', query_string={'cpr': 'mock_cpr'})

    assert response.status_code == 200

    keys_to_check = ['id', 'sager', 'pension', 'personligTillaegsprocent', 'helbredstillaegsprocent', 'saerligeOplysninger']
    assert all(key in response.get_json() for key in keys_to_check)
    success_mock_kp_client.search_person.assert_called_once_with('mock_cpr')


def test_get_person_no_id_no_cpr(client, success_mock_kp_client):
    response = client.get('/api/kp/person')

    assert response.status_code == 400
    assert response.get_json() == {'error': 'id or cpr is required'}


def test_get_person_kp_client_failed(client, failed_mock_kp_client):
    response = client.get('/api/kp/person', query_string={'id': 'mock_id'})

    assert response.status_code == 500
    assert response.get_json() == {'cpr': None, 'id': 'mock_id', 'error': 'No response'}


def test_get_person_kp_client_exception(client, failed_mock_kp_client_with_exception):
    response = client.get('/api/kp/person', query_string={'id': 'mock_id'})

    assert response.status_code == 500
    assert response.get_json() == {'error': 'mock_exception'}
