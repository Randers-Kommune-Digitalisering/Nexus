import logging
# import time
import requests
import xmltodict
# import json
# from datetime import datetime
# from bs4 import BeautifulSoup
# from requests.auth import HTTPBasicAuth
from typing import Dict, Tuple, Optional
from auth_header_api_client import APIClientWithAuthHeaders
from utils.config import SD_BASIC_AUTH


logger = logging.getLogger(__name__)


# Sbsys Api Client
class SDAPIClient(APIClientWithAuthHeaders):
    _client_cache: Dict[Tuple[str, str], 'SDAPIClient'] = {}

    def __init__(self, username, password, url):
        super().__init__(url)
        self.username = username
        self.password = password

    @classmethod
    def get_client(cls, username, password, url):
        key = (username, password)
        if key in cls._client_cache:
            return cls._client_cache[key]
        client = cls(username, password, url)
        cls._client_cache[key] = client
        return client

    # def authenticate(self):
    #     self.auth = HTTPBasicAuth(self.username, self.password)

    def get_auth_headers(self):
        return {
            "authorization": "Basic " + SD_BASIC_AUTH,
            "content-type": "application/xml"
        }

    def _make_request(self, method, path, **kwargs):
        # Override _make_request to handle specific behavior for SDAPIClient
        try:
            response = super()._make_request(method, path, **kwargs)

            if not response:
                logger.error(f"Response is None. path: {path}")
                return None

            # Parse XML response to JSON
            try:
                response_dict = xml_to_json(response)
                return response_dict

            except Exception as e:
                logger.error(f"An error occurred while parsing the XML response: {e}")
                return None

        except requests.RequestException as e:
            logger.error(f"An error occurred while making the request: {e}")
            return None


class SDClient:
    def __init__(self, username, password, url):
        self.api_client = SDAPIClient.get_client(username, password, url)

    def get_request(self, path: str, params: Optional[Dict[str, str]] = None):
        try:
            response = self.api_client.get(path, params=params)
            return response
        except Exception as e:
            logger.error(f"An error occurred while performing get_request: {e}")

    def post_request(self, path: str, data=None, json=None, params: Optional[Dict[str, str]] = None):
        try:
            response = self.api_client.post(path, data=data, json=json, params=params)
            return response
        except Exception as e:
            logger.error(f"An error occurred while perform post_request: {e}")

    def put_request(self, path: str, data=None, json=None, params: Optional[Dict[str, str]] = None):
        try:
            response = self.api_client.put(path, data=data, json=json, params=params)
            return response
        except Exception as e:
            logger.error(f"An error occurred while perform put_request: {e}")

    def delete_request(self, path: str, params: Optional[Dict[str, str]] = None):
        try:
            response = self.api_client.delete(path, params=params)
            return response
        except Exception as e:
            logger.error(f"An error occurred while perform delete_request: {e}")

    def get_person(self, cpr, employement_identifier, inst_code, effective_date=None):
        path = 'GetPerson'

        if not effective_date:
            # Get the current date and format it as DD.MM.YYYY
            effective_date = "01.01.5000"

        params = {
            'EmploymentStatusIndicator': 'true',
            'EmploymentIdentifier': employement_identifier,
            'DepartmentIdentifier': '',
            'StatusActiveIndicator': 'true',
            'StatusPassiveIndicator': 'true',
            'InstitutionIdentifier': inst_code,
            'PersonCivilRegistrationIdentifier': cpr,
            'EffectiveDate': effective_date,
            'StatusActiveIndicator': 'true',
            'submit': 'OK'
        }

        try:
            response = self.get_request(path=path, params=params)

            if not response:
                logger.warning("No response from SD client")
                return None

            if not response['GetPerson']:
                logger.warning("GetPerson object not found")
                return None

            person_data = response['GetPerson'].get('Person', None)
            if not person_data:
                logger.warning(f"No person data found for cpr: {cpr}")
                return None

            return person_data

        except Exception as e:
            logger.error(f"An error occured GetPerson: {e}")
            return None

    def get_employment(self, cpr, employment_identifier, inst_code, effective_date=None):
        path = 'GetEmployment20070401'

        if not effective_date:
            # Get the current date and format it as DD.MM.YYYY
            effective_date = "01.01.5000"

        # Define the SD params
        params = {
            'InstitutionIdentifier': inst_code,
            'EmploymentStatusIndicator': 'true',
            'PersonCivilRegistrationIdentifier': cpr,
            'EmploymentIdentifier': employment_identifier,
            'DepartmentIdentifier': '',
            'ProfessionIndicator': 'false',
            'DepartmentIndicator': 'true',
            'WorkingTimeIndicator': 'false',
            'SalaryCodeGroupIndicator': 'false',
            'SalaryAgreementIndicator': 'false',
            'StatusActiveIndicator': 'true',
            'StatusPassiveIndicator': 'true',
            'submit': 'OK',
            'EffectiveDate': effective_date
        }

        try:
            response = self.get_request(path=path, params=params)

            if not response:
                logger.warning("No response from SD client")
                return None

            if not response['GetEmployment20070401']:
                logger.warning("GetEmployment20070401 object not found")
                return None

            person_data = response['GetEmployment20070401'].get('Person', None)
            if not person_data:
                logger.warning(f"No person data found for cpr: {cpr}")
                return None

            employment_data = person_data.get('Employment', None)
            if not employment_data:
                logger.warning(f"No employment data found for cpr: {cpr}")
                return None

            return employment_data

        except Exception as e:
            logger.error(f"An error occured GetEmployment20070401: {e}")

    def get_employment_changed(self, cpr, employment_identifier, inst_code, activation_date, deactivation_date):
        path = 'GetEmploymentChanged20070401'

        # Define the SD params
        params = {
            'InstitutionIdentifier': inst_code,
            'EmploymentStatusIndicator': 'true',
            'PersonCivilRegistrationIdentifier': cpr,
            'EmploymentIdentifier': employment_identifier,
            'DepartmentIdentifier': '',
            'ProfessionIndicator': 'false',
            'DepartmentIndicator': 'true',
            'WorkingTimeIndicator': 'false',
            'SalaryCodeGroupIndicator': 'false',
            'SalaryAgreementIndicator': 'false',
            'StatusActiveIndicator': 'true',
            'StatusPassiveIndicator': 'true',
            'submit': 'OK',
            'ActivationDate': activation_date,
            'DeactivationDate': deactivation_date
        }

        try:
            response = self.get_request(path=path, params=params)

            if not response:
                logger.warning("No response from SD client")
                return None

            if not response['GetEmploymentChanged20070401']:
                logger.warning("GetEmploymentChanged20070401 object not found")
                return None

            person_data = response['GetEmploymentChanged20070401'].get('Person', None)
            if not person_data:
                logger.warning("No employment changes found for dates provided")
                return []

            return person_data

        except Exception as e:
            logger.error(f"An error occured GetEmployment20070401: {e}")


def xml_to_json(xml_data):
    try:
        # Parse the XML data into a dictionary
        dict_data = xmltodict.parse(xml_data)
        return dict_data
    except Exception as e:
        logger.error(f"An error occurred while converting XML to JSON: {e}")
        return None
