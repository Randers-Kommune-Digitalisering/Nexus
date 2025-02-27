import logging
import time
import requests
from typing import Dict, Tuple
from auth_header_api_client import APIClientWithAuthHeaders

logger = logging.getLogger(__name__)


class AzureAPIClient(APIClientWithAuthHeaders):
    _client_cache: Dict[Tuple[str, str, str, str], 'AzureAPIClient'] = {}

    def __init__(self, client_id, client_secret, tenant_id, url, token_url):
        super().__init__(url)
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.url = url
        self.token_url = token_url
        self.access_token = None
        self.access_token_expiry = None
        self.refresh_token = None
        self.refresh_token_expiry = None

    @classmethod
    def get_client(cls, client_id, client_secret, tenant_id, url, token_url):
        key = (client_id, client_secret, tenant_id)
        if key in cls._client_cache:
            return cls._client_cache[key]
        client = cls(client_id, client_secret, tenant_id, url, token_url)
        cls._client_cache[key] = client
        return client

    def request_access_token(self):
        token_url = f"{self.token_url}/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
            "client_id": self.client_id,
            "client_secret": self.client_secret
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


class AzureClient:
    def __init__(self, client_id, client_secret, tenant_id, url, token_url):
        self.api_client = AzureAPIClient.get_client(client_id, client_secret, tenant_id, url, token_url)

    def get_all_users(self):
        users = []
        url = f"{self.api_client.url}/v1.0/users?$select=displayName,onPremisesSamAccountName,mail"
        while url:
            response = self.api_client.get(url)
            if response:
                users.extend(response.get('value', []))
                url = response.get('@odata.nextLink')
            else:
                break
        return users
