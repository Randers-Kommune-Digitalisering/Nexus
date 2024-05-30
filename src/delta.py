import os
import time
import base64
import logging
import requests_pkcs12

from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DeltaClient:
    def __init__(self, cert_base64, cert_pass, base_url, top_adm_unit_uuid, assets_path='./assets/delta/'):
        self.cert_base64 = cert_base64
        self.cert_pass = cert_pass
        self.base_url = base_url
        self.top_adm_unit_uuid = top_adm_unit_uuid
        self.assets_path = assets_path
        self.last_adm_unit_list_updated = None
        self.adm_unit_list = None
        self.cert_path = self._decode_and_write_cert()
        self.payloads = {os.path.splitext(file)[0]: os.path.join(os.path.join(self.assets_path, 'payloads/'), file) for file in os.listdir(os.path.join(self.assets_path, 'payloads/')) if file.endswith('.json')}
        self.headers = {'Content-Type': 'application/json'}

    def _decode_and_write_cert(self):
        try:
            decoded_data = base64.b64decode(self.cert_base64)
            cert_dir = os.path.join(self.assets_path, 'tmp/')
            os.makedirs(cert_dir, exist_ok=True)
            cert_path = os.path.join(cert_dir, 'delta_cert.p12')
            with open(cert_path, 'wb') as file:
                file.write(decoded_data)
                return cert_path
        except Exception as e:
            logger.error(f'Error decoding certificate: {e}')
            return

    def _get_cert_path_and_pass(self):
        if self.cert_path is not None and self.cert_pass is not None:
            if os.path.isfile(self.cert_path):
                return self.cert_path, self.cert_pass
        return False, False

    def _get_payload(self, payload_name):
        if payload_name.endswith('.json'):
            payload_name = os.path.splitext(payload_name)[0]
        payload_path = self.payloads.get(payload_name)
        if payload_path:
            with open(payload_path, 'r') as file:
                return file.read()
        else:
            logger.error(f'Payload "{payload_name}" not found.')
            return

    def _set_params(self, payload, params):
        if isinstance(payload, str):
            if isinstance(params, dict):
                for key, value in params.items():
                    key = key.replace('<', '').replace('>', '') if key and '<' in key and '>' in key else key
                    payload = payload.replace(f'<{key}>', value)
            else:
                logger.error('Params must be a dictionary.')
                return
        else:
            logger.error('Payload must be a string.')
            return
        return payload

    def _make_post_request(self, payload):
        cert_path, cert_pass = self._get_cert_path_and_pass()
        if cert_path and cert_pass:
            try:
                path = '/query' if 'queries' in payload else '/graph-query' if 'graphQueries' in payload else '/history' if 'queryList' in payload else None
                if not path:
                    logger.error('Payload is invalid.')
                    return
                url = self.base_url.rstrip('/') + path
                response = requests_pkcs12.post(url, data=payload, headers=self.headers, pkcs12_filename=cert_path, pkcs12_password=cert_pass)
                return response
            except Exception as e:
                logger.error(f'Error making POST request: {e}')
        else:
            logger.error('Certificate path or password is invalid.')
        return

    def _recursive_get_adm_units(self, adm_unit_list, payload, uuid):
        adm_unit_list.append(uuid)
        payload_with_params = self._set_params(payload, {'uuid': uuid})
        if not payload_with_params:
            logger.error('Error setting payload params.')
            return

        r = self._make_post_request(payload_with_params)
        if r.ok:
            try:
                json_res = r.json()
                if 'children' in json_res['queryResults'][0]['instances'][0]:
                    children = json_res['queryResults'][0]['instances'][0]['children']
                    if len(children) > 0:
                        for child in children:
                            self._recursive_get_adm_units(adm_unit_list, payload, child['uuid'])
            except Exception as e:
                logger.error(f'Error parsing JSON response: {e}')
                return

    def _check_has_employees_and_add_teams(self, adm_unit_list, payload):
        adm_unit_list_with_employees = []
        for adm_unit in adm_unit_list:
            payload_with_params = self._set_params(payload, {'uuid': adm_unit})
            if not payload_with_params:
                logger.error('Error setting payload params.')
                return
            r = self._make_post_request(payload_with_params)
            if r.ok:
                try:
                    json_res = r.json()
                    teams = []
                    if len(json_res['graphQueryResult'][0]['instances']) > 0:
                        if 'childrenObjects' in json_res['graphQueryResult'][0]['instances'][0]:
                            children = json_res['graphQueryResult'][0]['instances'][0]['childrenObjects']
                            if len(children) > 0:
                                for child in children:
                                    teams.append(child['identity']['uuid'])
                    adm_unit_list_with_employees.append({adm_unit: teams})
                except Exception as e:
                    logger.error(f'Error parsing JSON response: {e}')
                    return
        return adm_unit_list_with_employees

    # returns a list of dictionaries with the admin unit UUID as the key and a list of team(sub admin units) UUIDs as the value
    def get_adm_unit_list(self):
        if not self.adm_unit_list:
            if self.last_adm_unit_list_updated:
                if (datetime.now() - self.last_adm_unit_list_updated).days > 1:                   
                    try:
                        start = time.time()
                        temp_adm_unit_list = []
                        payload_children = self._get_payload('adm_unit_children')
                        self._recursive_get_adm_units(temp_adm_unit_list, payload_children, self.top_adm_unit_uuid)
                        payload_employees = self._get_payload('adm_unit_with_employees_teams')
                        adm_unit_list = self._check_has_employees_and_add_teams(temp_adm_unit_list, payload_employees)
                        logger.info('Updated admin unit list, time for update: ', str(timedelta(seconds=time.time() - start)))
                        self.adm_unit_list = adm_unit_list
                        self.last_adm_unit_list_updated = datetime.now()
                    except Exception as e:
                        logger.error(f'Error getting ADM unit list: {e}')
                        return
        return self.adm_unit_list
