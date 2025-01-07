import logging
from azure.azure_client import AzureClient
from flask import Blueprint, jsonify
from utils.config import AZURE_CLIENTID, AZURE_TENANTID, AZURE_CLIENTSECRET, AZURE_URL, AZURE_TOKEN_URL

logger = logging.getLogger(__name__)
azure_client = AzureClient(AZURE_CLIENTID, AZURE_CLIENTSECRET, AZURE_TENANTID, AZURE_URL, AZURE_TOKEN_URL)

api_azure_bp = Blueprint('api_azure', __name__, url_prefix='/api/azure')


@api_azure_bp.route('/dq', methods=['GET'])
def get_all_dq_numbers():
    try:
        users = azure_client.get_all_users()
        dq_numbers = [user['onPremisesSamAccountName'] for user in users if user.get('onPremisesSamAccountName') and user['onPremisesSamAccountName'].startswith(('DQ', 'AP'))]
        return jsonify({"dq_numbers": dq_numbers}), 200
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return jsonify({"error": f"{e}"}), 500


@api_azure_bp.route('/fullname', methods=['GET'])
def get_all_names():
    try:
        users = azure_client.get_all_users()
        remove_values = ['Vikar', 'Distrikt Bakkegården', 'Afløser', 'Langå', 'Mobil', 'Vorup Plejecenter']
        fullnames = [
            user['displayName'] for user in users
            if user.get('onPremisesSamAccountName') and user['onPremisesSamAccountName'].startswith(('DQ', 'AP')) and
            user.get('displayName') and not any(value in user['displayName'] for value in remove_values)
        ]
        return jsonify({"fullnames": fullnames}), 200
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return jsonify({"error": f"{e}"}), 500


@api_azure_bp.route('/email', methods=['GET'])
def get_all_emails():
    try:
        users = azure_client.get_all_users()
        emails = [user['mail'] for user in users if user.get('onPremisesSamAccountName') and user['onPremisesSamAccountName'].startswith(('DQ', 'AP')) and user.get('mail')]
        return jsonify({"emails": emails}), 200
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return jsonify({"error": f"{e}"}), 500
