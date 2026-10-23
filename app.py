import os
import socket
import time
from flask import Flask, render_template, request, jsonify
from weather_service import fetch_weather_data, format_weather_response

app = Flask(__name__)

# Application metadata (Used for Step 9: Demonstrating source-code redeployment)
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
HOSTNAME = socket.gethostname()
START_TIME = time.time()


@app.route("/")
def index():
    default_city = request.args.get("city", "Pune")
    units = request.args.get("units", "metric")
    
    raw_weather = fetch_weather_data(default_city)
    weather_data = format_weather_response(raw_weather, units=units)

    return render_template(
        "index.html",
        weather=weather_data,
        app_version=APP_VERSION,
        environment=ENVIRONMENT,
        hostname=HOSTNAME
    )


@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "Pune").strip()
    units = request.args.get("units", "metric").strip().lower()

    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    raw_weather = fetch_weather_data(city)
    weather_data = format_weather_response(raw_weather, units=units)
    return jsonify(weather_data)


@app.route("/health")
@app.route("/healthz")
def health():
    """
    Health check endpoint for Kubernetes Liveness/Readiness probes
    and Jenkins automated pipeline verification.
    """
    uptime_seconds = int(time.time() - START_TIME)
    return jsonify({
        "status": "UP",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "hostname": HOSTNAME,
        "uptime_seconds": uptime_seconds
    }), 200


@app.route("/api/info")
def info():
    """System information useful for viva demonstration and pod identification."""
    return jsonify({
        "application": "Weather Dashboard CI/CD App",
        "version": APP_VERSION,
        "node_hostname": HOSTNAME,
        "framework": "Flask 3.x / Python",
        "container_ready": True
    })


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", error_code=404, message="Page not found", app_version=APP_VERSION), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error_code=500, message="Internal server error", app_version=APP_VERSION), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
