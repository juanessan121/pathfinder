# app/api/routes.py
from flask import Blueprint, request, jsonify
from flask_login import current_user
from app.services.graph_service import GraphService
from app.services.data_service import DataService

api_bp = Blueprint('api', __name__)

graph_service = GraphService()
data_service = DataService()


@api_bp.route('/calculate-path', methods=['POST'])
def calculate_path():
    data = request.json
    try:
        result = graph_service.find_shortest_path(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/save-route', methods=['POST'])
def save_route():
    if not current_user.is_authenticated:
        return jsonify({"error": "No autorizado"}), 401

    data = request.json
    try:
        data_service.save_route(current_user.id, data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/delete-route/<int:route_id>', methods=['DELETE'])
def delete_route(route_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "No autorizado"}), 401

    success = data_service.delete_route(route_id, current_user.id)
    if success:
        return jsonify({"success": True, "message": "Ruta eliminada"}), 200
    else:
        return jsonify({"error": "Ruta no encontrada"}), 404


@api_bp.route('/clear-history', methods=['DELETE'])
def clear_history():
    if not current_user.is_authenticated:
        return jsonify({"error": "No autorizado"}), 401

    data_service.clear_history(current_user.id)
    return jsonify({"success": True, "message": "Historial limpiado"}), 200