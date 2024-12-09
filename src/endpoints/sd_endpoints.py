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
        employment_id = request.args.get('employment')
        cpr = request.args.get('cpr')

        if not cpr and not employment_id:
            return jsonify({"error": "cpr or employment (id) required"}), 400

        if date:
            try:
                day, month, year = map(int, date.split('.'))
            except ValueError:
                return jsonify({"error": "date must be in DD.MM.YYYY format"}), 400

        response = sd_client.get_person(cpr, employment_id, SD_INST_ID, date)

        if response is None:
            return jsonify({"error": "No response from function call get_person"}), 500

        try:
            return jsonify(response)
        except Exception:
            return response

    except Exception as e:
        return jsonify({"error": f"{e}"}), 500


@api_sd_bp.route('/employment', methods=['GET'])
def get_employment():
    try:
        date = request.args.get('date')
        employment_id = request.args.get('employment')
        cpr = request.args.get('cpr')

        if not cpr and not employment_id:
            return jsonify({"error": "cpr or employment (id) required"}), 400

        if date:
            try:
                day, month, year = map(int, date.split('.'))
            except ValueError:
                return jsonify({"error": "date must be in DD.MM.YYYY format"}), 400

        response = sd_client.get_employment(cpr, employment_id, SD_INST_ID, date)
        
        if response is None:
            return jsonify({"error": "Employment not found"}), 404
        if not response:
            return jsonify({"error": "No response from function call get_employment"}), 500

        try:
            return jsonify(response)
        except Exception:
            return response

    except Exception as e:
        return jsonify({"error": f"{e}"}), 500


@api_sd_bp.route('/employment-changed', methods=['GET'])
def get_employment_changed():
    try:
        activation_date = request.args.get('activation_date')
        deactivation_date = request.args.get('deactivation_date')
        employment_id = request.args.get('employment')
        cpr = request.args.get('cpr')

        if not activation_date or not deactivation_date:
            return jsonify({"error": "activation_date and deactivation_date is required"}), 400

        try:
            day, month, year = map(int, activation_date.split('.'))
            day, month, year = map(int, deactivation_date.split('.'))
        except ValueError:
            return jsonify({"error": "dates must be in DD.MM.YYYY format"}), 400

        response = sd_client.get_employment_changed(cpr, employment_id, SD_INST_ID, activation_date, deactivation_date)

        if response is None:
            return jsonify({"error": "No response from function call get_employment_changed"}), 500

        try:
            return jsonify(response)
        except Exception:
            return response

    except Exception as e:
        return jsonify({"error": f"{e}"}), 500
