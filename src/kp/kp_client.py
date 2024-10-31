import time
import logging
import requests
from typing import Dict, Tuple

from requests.auth import HTTPBasicAuth
from base_api_client import BaseAPIClient
from utils.config import KP_URL, BROWSERLESS_URL, BROWSERLESS_CLIENT_ID, BROWSERLESS_CLIENT_SECRET

logger = logging.getLogger(__name__)


class KPAPIClient(BaseAPIClient):
    _client_cache: Dict[Tuple[str, str], 'KPAPIClient'] = {}

    def __init__(self, username, password):
        super().__init__(KP_URL)
        self.username = username
        self.password = password
        self.session_cookie = None
        self.auth_attempted = False
        self.is_fetching_token = False

    @classmethod
    def get_client(cls, username, password):
        key = (username, password)
        if key in cls._client_cache:
            return cls._client_cache[key]
        client = cls(username, password)
        cls._client_cache[key] = client
        return client

    def request_session_token(self):
        self.is_fetching_token = True
        try:
            login_url = self.base_url
            url = f"{BROWSERLESS_URL.rstrip('/')}/function"
            headers = {
                "Content-Type": "application/javascript",

            }
            data = """
            module.exports = async ({page}) => {
            // Go to the specific URL
            await page.goto('""" + f"{login_url}" + """', { waitUntil: 'networkidle2' });

            // Log in console when loaded
            console.log("Page loaded");

            // Wait for the dropdown to be available
            await page.waitForSelector('#SelectedAuthenticationUrl');

            // Find the option element with the specified text
            const option = (await page.$x(
                '//*[@id = "SelectedAuthenticationUrl"]/option[contains(text(), "Randers Kommune")]'
            ))[0];

            // Check if the option was found
            if (option) {
                // Get the value attribute of the option
                const valueHandle = await option.getProperty('value');
                const value = await valueHandle.jsonValue(); // Ensure value is a string

                // Select the option by its value
                await page.select('#SelectedAuthenticationUrl', value);

                // Wait for some time after selection
                await page.waitForTimeout(2000); // Adjust the timeout as necessary

                // Click the button with class "button"
                await page.click('input.button'); // Since it's an input with class "button"

                // Log a message indicating the button was clicked
                console.log("Button clicked and navigation completed");

                // Wait for the username input field to be available
                await page.waitForSelector('#userNameInput');

                // Type the username
                await page.type('#userNameInput', '""" + f"{self.username}" + """'); // Replace with your actual username

                // Wait for the password input field to be available
                await page.waitForSelector('#passwordInput');

                // Type the password
                await page.type('#passwordInput', '""" + f"{self.password}" + """'); // Replace with your actual password

                // Click the submit button
                await page.click('#submitButton');

                // Log a message indicating the login was attempted
                console.log("Login attempted");

                // Wait for some time after selection
                await page.waitForTimeout(2000); // Adjust the timeout as necessary

                // Retrieve cookies after the login
                const cookies = await page.cookies();

                // Print the cookies
                console.log('Cookies after login:', cookies);
                return {
                data: {
                    cookies
                },
                type: 'application/json'
                };
            } else {
                console.error('Option not found');
            }
            }
            """
            try:
                response = requests.post(url, headers=headers, data=data,
                                         auth=HTTPBasicAuth(username=BROWSERLESS_CLIENT_ID, password=BROWSERLESS_CLIENT_SECRET), timeout=180)
            except requests.exceptions.RequestException as e:
                logger.error("Failed to fetch a response from Browserless: %s", e)

            # Parse the JSON response
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError as e:
                logger.error("Failed to parse JSON response from Browserless: %s", e)

            # Initialize session_cookie
            session_cookie = None

            # Loop through the cookies to find the JSESSIONID
            for cookie in data['cookies']:
                if cookie['name'] == 'JSESSIONID':
                    session_cookie = cookie['value']
                    break

            self.session_cookie = session_cookie
            self.is_fetching_token = False
            return self.session_cookie

        except Exception as e:
            logger.error(e)
            self.is_fetching_token = False
            return None

    def authenticate(self):
        logger.warning("Authenticating now...")
        timeout = time.time() + 180   # 3 minutes timeout
        while self.is_fetching_token:
            if time.time() > timeout:
                break
        if self.session_cookie:
            logger.warning("Session cookie exists, returning...")
            return self.session_cookie
        logger.warning("No session cookie exists, requesting new session token...")
        return self.request_session_token()

    def reauthenticate(self):
        logger.warning("Reauthenticating now...")
        if self.is_fetching_token:  # If is fetching token, wait
            timeout = time.time() + 180   # 3 minutes timeout
            while self.is_fetching_token:
                if time.time() > timeout:
                    break
            return self.session_cookie  # Return token after fetching
        
        if not self.auth_attempted:  # If no attempt to reauthenticate has been made yet, attempt to fetch token
            self.auth_attempted = True
            logger.info("2 Setting auth_attempted to True")
            auth = self.request_session_token()  # Fetch token
            if auth:  # If token is fetched successfully
                return auth  # Return token

        logger.error("Fetching new session token failed.")
        return False

    def get_auth_headers(self):
        session_cookie = self.authenticate()
        headers = {"Cookie": f"JSESSIONID={session_cookie}"}
        return headers
    
    def _retry_request(self, method, path, **kwargs):
        self.auth_attempted = True
        logger.info("1 Setting auth_attempted to True")
        return self._make_request(method, path, **kwargs)

    def _make_request(self, method, path, **kwargs):
        # Override _make_request to handle specific behavior for KPAPIClient
        try:
            headers = self.get_auth_headers()
            logger.info("Making new request using auth header %s", headers)

            if path.startswith("http://") or path.startswith("https://"):
                url = path
            else:
                url = f"{self.base_url}/{path}"

            # Ensure redirects are not followed
            kwargs['allow_redirects'] = False

            try:
                response = method(url, headers=headers, **kwargs)
                response.raise_for_status()

                retry_count = 0
                max_retries = 5
                while response.status_code == 302 and retry_count < max_retries:
                    logger.warning("Received 302 redirect status code, retrying... Attempt %d", retry_count + 1)
                    retry_count += 1
                    response = method(url, headers=headers, **kwargs)
                
                if response.status_code != 200 or 'text/html' in response.headers.get('Content-Type', '').lower():
                    logger.error("Reauthenticating - HTML response received from path %s", path)
                    retry_authenticate = self.reauthenticate()  # Attempt to fetch new session token
                    if retry_authenticate:
                        logger.info("Reauthentication complete, token: %s", retry_authenticate)
                        return self._retry_request(method, path, **kwargs)  # Retry the request
                    else:
                        logger.warning("Reauthentication failed, return False")
                        self.auth_attempted = False
                        logger.info("3 Setting auth_attempted to False")
                        return None

                try:
                    json = response.json()
                    return json

                except requests.exceptions.JSONDecodeError:  # Handle JSON decoding errors
                    if not response.content:
                        return ' '
                    return response.content

            except requests.exceptions.HTTPError as e:  # Handle HTTP errors
                if e.response.status_code == 401 or (e.response.status_code == 500 and b'AccessDeniedException' in e.response.content):
                    logger.error("Reauthenticating: KP authentication failed with status code %s", e.response.status_code)
                    retry_authenticate = self.reauthenticate()  # Attempt to fetch new session token
                    if retry_authenticate:
                        return self._make_request(method, path, **kwargs)  # Retry the request
                    else:
                        return None
                else:
                    logger.error(e)
                    return None

        except Exception as e:
            logger.error(e)
            return None


class KPClient:
    def __init__(self, username, password):
        self.api_client = KPAPIClient.get_client(username, password)

    def fetch_token(self):
        client = self.api_client
        # Step 1: Login with session requests
        # session_cookies = client.login_with_requests()
        # Step 2: Perform RPA tasks with Selenium using the session cookies
        # asyncio.get_event_loop().run_until_complete(client.perform_rpa_with_pyppeteer())
        return client.request_session_token()

    def search_person(self, cpr: str):
        path = "rest/api/search/person"
        payload = {
            "cpr": cpr,
            "sortDirection": "",
            "sortField": ""
        }
        return self.api_client.post(path, json=payload)

    def get_person(self, id: str):
        path = f"rest/api/person/overview/{id}"
        return self.api_client.get(path)

    def get_pension(self, id: str):
        path = f"rest/api/person/overview/{id}/pensionsoplysninger"
        return self.api_client.get(path)

    def get_cases(self, id: str):
        path = f"rest/api/person/overview/{id}/sager?types=aktiv"
        return self.api_client.get(path)

    def get_personal_supplement(self, id: str):
        path = f"rest/api/person/history/{id}/personligTillaegsprocent"
        return self.api_client.get(path)

    def get_health_supplement(self, id: str):
        path = f"rest/api/person/history/{id}/helbredstillaegsprocent"
        return self.api_client.get(path)

    def get_special_information(self, id: str):
        path = f"rest/api/warning/person/{id}"
        return self.api_client.get(path)
