import pytest
from flask import Flask
from unittest.mock import patch
from endpoints.nexus_endpoints import api_nexus_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(api_nexus_bp)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_nexus_client():
    with patch('endpoints.nexus_endpoints.nexus_client') as mock_nexus_client:
        mock_nexus_client.fetch_patient_by_query.return_value = {'_links': {'lendings': {'href': '/mock_url'}}}
        mock_nexus_client.get_request.return_value = [{'item': {'product': {'categoryName': 'Category1'}}}, {'item': {'product': {'categoryName': 'Category2'}}}]
        yield mock_nexus_client


def test_fetch_lendings(client, mock_nexus_client):
    mock_cpr = '1234567890'

    response = client.post('/api/nexus/fetch-lendings', json={'cpr': mock_cpr})
    assert response.status_code == 200
    assert response.get_json() == ['Category1', 'Category2']


def test_fetch_lendings_nexus_client_empty_response(client):
    # fetch_patient_by_query is empty
    with patch('endpoints.nexus_endpoints.nexus_client') as mock_nexus_client:
        mock_nexus_client.fetch_patient_by_query.return_value = {}
        mock_cpr = '1234567890'

        response = client.post('/api/nexus/fetch-lendings', json={'cpr': mock_cpr})
        assert response.status_code == 200
        assert response.get_json() == []

    # get_request is empty
    with patch('endpoints.nexus_endpoints.nexus_client') as mock_nexus_client:
        mock_nexus_client.fetch_patient_by_query.return_value = {'_links': {'lendings': {'href': '/mock_url'}}}
        mock_nexus_client.get_request.return_value = []
        mock_cpr = '1234567890'

        response = client.post('/api/nexus/fetch-lendings', json={'cpr': mock_cpr})
        assert response.status_code == 200
        assert response.get_json() == []


def test_fetch_lendings_no_cpr(client):
    response = client.post('/api/nexus/fetch-lendings', json={})
    assert response.status_code == 400
    assert response.get_json() == {"error": "cpr is required"}
