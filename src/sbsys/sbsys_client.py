import logging
import time
import requests
from typing import Dict, Tuple
from auth_header_api_client import APIClientWithAuthHeaders
from utils.config import SBSIP_URL

logger = logging.getLogger(__name__)


# Sbsys Api Client
class SbsysAPIClient(APIClientWithAuthHeaders):
    _client_cache: Dict[Tuple[str, str, str, str], 'SbsysAPIClient'] = {}

    def __init__(self, client_id, client_secret, username, password, url):
        super().__init__(url)
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.access_token = None
        self.access_token_expiry = None
        self.refresh_token = None
        self.refresh_token_expiry = None

    @classmethod
    def get_client(cls, client_id, client_secret, username, password, url):
        key = (client_id, client_secret, username, password)
        if key in cls._client_cache:
            return cls._client_cache[key]
        client = cls(client_id, client_secret, username, password, url)
        cls._client_cache[key] = client
        return client

    def request_access_token(self):
        token_url = f"{SBSIP_URL}/auth/realms/sbsip/protocol/openid-connect/token"
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        try:
            if not token_url.startswith("https://"):
                token_url = "https://" + token_url
            response = requests.post(token_url, headers=headers, data=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            self.access_token = data['access_token']
            self.access_token_expiry = time.time() + data['expires_in']
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return None

    def get_access_token(self):
        if self.access_token and self.access_token_expiry:
            if time.time() < self.access_token_expiry:
                return self.access_token
        return self.request_access_token()

    def get_auth_headers(self):
        token = self.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None


class SbsysClient:
    def __init__(self, client_id, client_secret, username, password, url):
        self.api_client = SbsysAPIClient.get_client(client_id, client_secret, username, password, url)

    def sag_search(self, payload):
        path = "api/sag/search"
        return self.api_client.post(path=path, json=payload)

    def sag_get(self, cpr):
        path = "api/sag/search"
        if "-" not in cpr:
            cpr = cpr[:6] + "-" + cpr[6:]
        payload = {
            'PrimaerPerson': {
                'CprNummer': cpr
            },
            'SagsTyper': [
                {
                    'Navn': 'PersonaleSag'
                }
            ]
        }
        try:
            response = self.api_client.post(path=path, json=payload)
            return response
        except Exception as e:
            logger.error(f"An error occurred while performing sag_get: {e}")
            return None

    def fetch_documents(self, sag_id):
        path = f"api/sag/{sag_id}/dokumenter"
        return self.api_client.get(path=path)

    def fetch_file(self, file_id):
        path = f"/api/fil/{file_id}"
        return self.api_client.get(path=path)

    def get_request(self, path):
        return self.api_client.get(path)

    def post_request(self, path, data=None, json=None):
        return self.api_client.post(path, data, json)

    def put_request(self, path, data=None, json=None):
        return self.api_client.put(path, data, json)

    def delete_request(self, path):
        return self.api_client.delete(path)
