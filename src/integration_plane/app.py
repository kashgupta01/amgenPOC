from flask import Flask, jsonify, request
from src.data_plane.database import initialize_database
from src.control_plane.search import query_targets

app = Flask(__name__)


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})


@app.route("/initialize", methods=["POST"])
def initialize():
    initialize_database()
    return jsonify({"message": "Database initialized"}), 201


@app.route("/targets", methods=["GET"])
def list_targets():
    filters = {
        "disease_context": request.args.get("disease_context"),
        "target_type": request.args.get("target_type"),
        "current_status": request.args.get("current_status"),
    }
    results = query_targets(filters)
    return jsonify([dict(row) for row in results])


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
