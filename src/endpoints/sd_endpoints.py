import logging
from sd.sd_client import SDClient
from flask import Blueprint, request, jsonify
from utils.config import SD_URL, SD_USERNAME, SD_PASSWORD, SD_INST_ID


logger = logging.getLogger(__name__)
sd_client = SDClient(SD_USERNAME, SD_PASSWORD, SD_URL)

api_sd_bp = Blueprint('api_sd', __name__, url_prefix='/api/sd')


@api_sd_bp.route('/person', methods=['GET'])
def get_person():
    try:
        date = request.args.get('date')
        employment_id = request.args.get('employment_id')
        cpr = request.args.get('cpr')

        # if not date:
        #     return jsonify({"error": "date is required"}), 400

        response = sd_client.get_person(cpr, employment_id, SD_INST_ID, date)

        if response is None:
            return jsonify({"error": "No response from function call GetEmployment20070401"}), 500

        try:
            return jsonify(response)
        except Exception:
            return response

    except Exception as e:
        return jsonify({"error": f"{e}"}), 500
