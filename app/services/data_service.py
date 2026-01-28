# app/services/data_service.py
import json
from app import db
from app.models import Route, User


class DataService:
    def save_route(self, user_id, route_data):
        """
        Guarda la ruta en la base de datos.
        route_data debe incluir: start, end, distance, path, weather_summary
        """
        new_route = Route(
            user_id=user_id,
            start_node=route_data['start'],
            end_node=route_data['end'],
            distance=route_data['distance'],
            path_json=json.dumps(route_data['path']),
            weather_summary=route_data.get('weather_summary', 'N/A')  # Aquí se guarda el clima real
        )
        db.session.add(new_route)
        db.session.commit()
        return True

    def get_user_history(self, user_id):
        """Obtiene historial ordenado por fecha descendente"""
        routes = Route.query.filter_by(user_id=user_id).order_by(Route.timestamp.desc()).all()
        return self._format_routes(routes)

    def get_user_stats(self, user_id):
        """Calcula estadísticas para el Dashboard"""
        routes = Route.query.filter_by(user_id=user_id).all()
        total_km = sum(r.distance for r in routes)

        weather_counts = {}
        for r in routes:
            w = r.weather_summary
            # Contamos cuántas veces aparece cada clima (ej: "20.5°C": 1)
            # Para gráficas más limpias, podrías agrupar por rangos aquí si quisieras
            weather_counts[w] = weather_counts.get(w, 0) + 1

        return {
            "total_routes": len(routes),
            "total_km": round(total_km, 2),
            "weather_stats": weather_counts,
            "recent": self._format_routes(routes[:5])
        }

    # --- NUEVAS FUNCIONES DE BORRADO ---
    def delete_route(self, route_id, user_id):
        """Borra una ruta específica si pertenece al usuario"""
        route = Route.query.filter_by(id=route_id, user_id=user_id).first()
        if route:
            db.session.delete(route)
            db.session.commit()
            return True
        return False

    def clear_history(self, user_id):
        """Borra TODO el historial del usuario"""
        try:
            db.session.query(Route).filter_by(user_id=user_id).delete()
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False

    def _format_routes(self, routes_obj):
        data = []
        for r in routes_obj:
            data.append({
                "id": r.id,
                "start": r.start_node,
                "end": r.end_node,
                "distance": r.distance,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M"),
                "weather": r.weather_summary
            })
        return data

    def get_all_users(self):
        return User.query.all()

    def delete_user(self, user_id):
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False