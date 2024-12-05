import pytest
from unittest.mock import patch
from flask import Flask
import base64
from endpoints.sbsys_endpoints import api_sbsys_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(api_sbsys_bp)
    with app.test_client() as client:
        yield client


def test_sag_status_missing_status_id(client):
    response = client.post('/api/sbsys/sag/status', json={})
    assert response.status_code == 400
    assert response.json == {"error": "id (SBSYS sag id) is required"}


@patch('endpoints.sbsys_endpoints.sbsys_client.sag_search')
def test_sag_search(mock_sag_search, client):
    mock_sag_search.return_value = {"result": "success"}
    response = client.post('/api/sbsys/sag/search', json={"query": "test"})
    assert response.status_code == 200
    assert response.json == {"result": "success"}


def test_sag_search_missing_data(client):
    response = client.post('/api/sbsys/sag/search', json={})
    assert response.status_code == 400
    assert response.json == {"error": "JSON payload is required"}


@patch('endpoints.sbsys_endpoints.sbsys_client.sag_search')
def test_sag_search_exception(mock_sag_search, client):
    mock_sag_search.side_effect = Exception("Test exception")
    response = client.post('/api/sbsys/sag/search', json={"query": "test"})
    assert response.status_code == 500


def test_fil_keywords_missing_data(client):
    response = client.post('/api/sbsys/fil/keywords', json={})
    assert response.status_code == 400
    assert response.json == {"error": "'keywords' and 'sagID' properties are required. 'keywords' is an array of strings. 'sagID' is a integer"}


def test_fil_keywords_empty_data(client):
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": [], "sagID": None})
    assert response.status_code == 400
    assert response.json == {"error": "'keywords' and 'sagID' properties are required. 'keywords' is an array of strings. 'sagID' is a integer"}


def test_fil_keywords_invalid_keywords_type(client):
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": "not_a_list", "sagID": 1})
    assert response.status_code == 400
    assert response.json == {"error": "keywords has to be a list"}


def test_fil_keywords_invalid_allowed_filetypes_type(client):
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["test"], "sagID": 1, "allowedFiletypes": "not_a_list"})
    assert response.status_code == 400
    assert response.json == {"error": "allowedFiletypes must be a list of strings. e.g. ['pdf', 'docs']"}


@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_documents')
@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_file')
def test_fil_keywords_with_allowedFiletypes(mock_fetch_file, mock_fetch_documents, client):
    mock_fetch_documents.return_value = [
        {
            'Navn': 'test_document',
            'Filer': [{'ShortId': '1', 'Filnavn': 'test.pdf', 'Filendelse': 'pdf', 'MimeType': 'application/pdf'}]
        }
    ]
    mock_fetch_file.return_value = b'test file content'
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["test"], "allowedFiletypes": ['pdf'], "sagID": 1})
    assert response.status_code == 200
    files = response.json
    assert len(files) == 1
    assert files[0]['filename'] == 'test.pdf'
    assert files[0]['document_name'] == 'test_document'
    assert files[0]['mime_type'] == 'application/pdf'
    assert files[0]['data'] == base64.b64encode(b'test file content').decode('utf-8')


@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_documents')
@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_file')
def test_fil_keywords_without_allowedFiletypes(mock_fetch_file, mock_fetch_documents, client):
    mock_fetch_documents.return_value = [
        {
            'Navn': 'test_document',
            'Filer': [{'ShortId': '1', 'Filnavn': 'test.pdf', 'Filendelse': 'pdf', 'MimeType': 'application/pdf'}]
        }
    ]
    mock_fetch_file.return_value = b'test file content'
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["test"], "sagID": 1})
    assert response.status_code == 200
    files = response.json
    assert len(files) == 1
    assert files[0]['filename'] == 'test.pdf'
    assert files[0]['document_name'] == 'test_document'
    assert files[0]['mime_type'] == 'application/pdf'
    assert files[0]['data'] == base64.b64encode(b'test file content').decode('utf-8')


@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_documents')
@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_file')
def test_fil_keywords_no_files_in_allowedFiletypes(mock_fetch_file, mock_fetch_documents, client):
    mock_fetch_documents.return_value = [
        {
            'Navn': 'test_document',
            'Filer': [{'ShortId': '1', 'Filnavn': 'test.pdf', 'Filendelse': 'pdf', 'MimeType': 'application/pdf'}]
        }
    ]
    mock_fetch_file.return_value = b'test file content'
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["test"], "allowedFiletypes": ['doc'], "sagID": 1})
    assert response.status_code == 200
    files = response.json
    assert len(files) == 0


@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_documents')
@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_file')
def test_fil_keywords_no_file_content(mock_fetch_file, mock_fetch_documents, client):
    mock_fetch_documents.return_value = [
        {
            'Navn': 'test_document',
            'Filer': [{'ShortId': '1', 'Filnavn': 'test.pdf', 'Filendelse': 'pdf', 'MimeType': 'application/pdf'}]
        }
    ]
    mock_fetch_file.return_value = b''
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["test"], "sagID": 1})
    assert response.status_code == 200
    files = response.json
    assert len(files) == 0


@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_documents')
@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_file')
def test_fil_keywords_file_name_not_in_keywords(mock_fetch_file, mock_fetch_documents, client):
    mock_fetch_documents.return_value = [
        {
            'Navn': 'test_document',
            'Filer': [{'ShortId': '1', 'Filnavn': 'test.pdf', 'Filendelse': 'pdf', 'MimeType': 'application/pdf'}]
        }
    ]
    mock_fetch_file.return_value = b'test file content'
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["mock"], "sagID": 1})
    assert response.status_code == 200
    files = response.json
    assert len(files) == 1
    assert files[0]['filename'] == 'test.pdf'
    assert files[0]['document_name'] == 'test_document'
    assert files[0]['mime_type'] == 'application/pdf'
    assert files[0]['data'] == base64.b64encode(b'test file content').decode('utf-8')


@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_documents')
def test_fils_keywords_no_documents(mock_fetch_documents, client):
    mock_fetch_documents.return_value = []
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["test"], "sagID": 1})
    assert response.status_code == 404
    assert response.json == {"error": "No documents were found with sag id: 1"}


@patch('endpoints.sbsys_endpoints.sbsys_client.fetch_documents')
def test_fil_keywords_exception(mock_fetch_documents, client):
    mock_fetch_documents.side_effect = Exception("Test exception")
    response = client.post('/api/sbsys/fil/keywords', json={"keywords": ["test"], "sagID": 1})
    assert response.status_code == 500
    assert response.json == {"error": "Test exception"}
