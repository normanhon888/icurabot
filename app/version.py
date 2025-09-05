from flask import Blueprint, jsonify

bp = Blueprint("version", __name__)

@bp.route("/version")
def version():
    return jsonify({
        "service": "icura",
        "status": "ok",
        "version": "1.0"
    })

