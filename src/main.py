from flask import Flask
from healthcheck import HealthCheck
from prometheus_client import generate_latest

from utils.logging import set_logging_configuration, APP_RUNNING
from utils.config import DEBUG, PORT, POD_NAME
from endpoints.nexus_endpoints import api_nexus_bp
from endpoints.kp_endpoints import api_kp_bp
from endpoints.sbsys_endpoints import api_sbsys_bp


def create_app():
    app = Flask(__name__)
    health = HealthCheck()
    app.add_url_rule("/healthz", "healthcheck", view_func=lambda: health.run())
    app.add_url_rule('/metrics', "metrics", view_func=generate_latest)
    app.register_blueprint(api_nexus_bp)
    app.register_blueprint(api_kp_bp)
    app.register_blueprint(api_sbsys_bp)
    APP_RUNNING.labels(POD_NAME).set(1)
    return app


set_logging_configuration()
app = create_app()

if __name__ == "__main__":  # pragma: no cover
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
