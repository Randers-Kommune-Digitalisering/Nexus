import logging
import base64
from sbsys.sbsys_client import SbsysClient
from flask import Blueprint, request, jsonify
from utils.config import (SBSYS_USERNAME, SBSYS_PASSWORD, SBSIP_CLIENT_ID, SBSIP_CLIENT_SECRET,
                          SBSYS_PSAG_USERNAME, SBSYS_PSAG_PASSWORD, SBSIP_PSAG_CLIENT_ID, SBSIP_PSAG_CLIENT_SECRET, SBSYS_URL)

logger = logging.getLogger(__name__)

sbsys_client = SbsysClient(SBSIP_CLIENT_ID, SBSIP_CLIENT_SECRET,
                           SBSYS_USERNAME, SBSYS_PASSWORD, SBSYS_URL)
sbsys_psag_client = SbsysClient(SBSIP_PSAG_CLIENT_ID, SBSIP_PSAG_CLIENT_SECRET,
                                SBSYS_PSAG_USERNAME, SBSYS_PSAG_PASSWORD, SBSYS_URL)

api_sbsys_bp = Blueprint('api_sbsys', __name__, url_prefix='/api/sbsys')


@api_sbsys_bp.route('/sag/status', methods=['POST'])
def change_sag_status():
    try:
        data = request.get_json()
    except Exception:
        data = None
    status_id = data.get('status_id') if data else request.args.get('status_id')
    sag_id = data.get('id') if data else request.args.get('id')

    if not sag_id:
        return jsonify({"error": "id (SBSYS sag id) is required"}), 400
    if not status_id:
        return jsonify({"error": "status_id is required"}), 400

    return jsonify({"result": "success"}), 200

    # TODO journaliser kladder, og udfør erindringer for sager der skal afluttes, lukkes etc.


@api_sbsys_bp.route('/sag/erindringer', methods=['GET'])
def sag_erindringer():
    try:
        data = request.get_json()
    except Exception:
        data = None
    sag_id = data.get('id') if data else request.args.get('id')

    if not sag_id:
        return jsonify({"error": "id (sag id) is required"}), 400

    try:
        response = sbsys_client.get_erindringer(sag_id)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_sbsys_bp.route('/sag/erindringer/complete', methods=['PUT'])
def sag_erindringer_complete():
    try:
        data = request.get_json()
    except Exception:
        data = None
    erindringer_ids = data if data and isinstance(data, list) else [request.args.get('id')]
    try:
        erindringer_ids = [int(i) for i in erindringer_ids if i]
    except Exception:
        return jsonify({"error": "ids (erindring id) must be integers"}), 400

    if not erindringer_ids:
        return jsonify({"error": "ids (erindring id) are required, either as id parameter or JSON list of integers as body"}), 400

    results = []
    for erindring_id in erindringer_ids:
        success = True
        try:
            response = sbsys_client.complete_erindring(erindring_id)
            if not response:
                success = False
        except Exception as e:
            logger.error(f"An error occurred while completing erindring {erindring_id}: {e}")
            success = False
        results.append({"id": erindring_id, "success": success})

    return jsonify(results), 200


@api_sbsys_bp.route('/sag/search', methods=['POST', 'GET'])
def sag_search():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON payload is required"}), 400
    except Exception:
        return jsonify({"error": "JSON payload is required"}), 400

    try:
        response = sbsys_client.sag_search(payload=data)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_sbsys_bp.route('/personalesag', methods=['GET'])
def get_personalesag():
    cpr = request.args.get('cpr')
    if not cpr:
        return jsonify({"error": "cpr is required"}), 400

    try:
        response = sbsys_psag_client.get_personalesag(cpr)
        if not response:
            return jsonify({"error": "No results found"}), 404
        return response, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Returns a files based on Documents name property
# Documents can have multiple files
# Documents are filtered by the name property
@api_sbsys_bp.route('/fil/keywords', methods=['POST'])
def fil_by_keyword():
    allowed_filetypes = []
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "'keywords' and 'sagID' properties are required. 'keywords' is an array of strings. 'sagID' is a integer"}), 400
        if not data['keywords'] or not data['sagID']:
            return jsonify({"error": "'keywords' and 'sagID' properties are required. 'keywords' is an array of strings. 'sagID' is a integer"}), 400
        if not isinstance(data['keywords'], list):
            return jsonify({"error": "keywords has to be a list"}), 400
        if data.get('allowedFiletypes', None):
            if not isinstance(data['allowedFiletypes'], list):
                return jsonify({"error": "allowedFiletypes must be a list of strings. e.g. ['pdf', 'docs']"}), 400
            allowed_filetypes = data['allowedFiletypes']
        documents_response = sbsys_client.fetch_documents(data['sagID'])
        if not documents_response:
            return jsonify({"error": f"No documents were found with sag id: {data['sagID']}"}), 404

        files = []
        for keyword in data['keywords']:
            keyword = keyword.lower()
            filtered_documents = [doc for doc in documents_response if 'Navn' in doc and keyword in doc['Navn'].lower()]
            for document in filtered_documents:
                for fil in document['Filer']:
                    file_content = sbsys_client.fetch_file(fil['ShortId'])
                    if not file_content:
                        continue

                    if allowed_filetypes and not fil['Filendelse'].lower() in allowed_filetypes:
                        continue

                    encoded_file = base64.b64encode(file_content).decode('utf-8')
                    files.append({
                        'filename': fil['Filnavn'],
                        'document_name': document['Navn'],
                        'data': encoded_file,
                        'mime_type': fil['MimeType']
                    })
        if not files:
            for document in documents_response:
                for fil in document['Filer']:
                    file_content = sbsys_client.fetch_file(fil['ShortId'])
                    if not file_content:
                        continue

                    if allowed_filetypes and not fil['Filendelse'].lower() in allowed_filetypes:
                        continue

                    encoded_file = base64.b64encode(file_content).decode('utf-8')
                    files.append({
                        'filename': fil['Filnavn'],
                        'document_name': document['Navn'],
                        'data': encoded_file,
                        'mime_type': fil['MimeType']
                    })

        return jsonify(files), 200
    except Exception as e:
        return jsonify({"error": f"{e}"}), 500
