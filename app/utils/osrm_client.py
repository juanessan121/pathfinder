import requests

# URL del servicio público y gratuito de OSRM
OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving/"


def get_road_data(coord_start, coord_end):
    """
    Consulta la ruta real entre dos puntos.
    Input: coord_start [lat, lng], coord_end [lat, lng]
    Output: { 'distance_km': float, 'duration_min': float, 'geometry': list } o None
    """
    try:
        # OSRM requiere formato: longitud,latitud (al revés que Leaflet)
        start_str = f"{coord_start[1]},{coord_start[0]}"
        end_str = f"{coord_end[1]},{coord_end[0]}"

        # geometries=geojson nos devuelve los cientos de puntos que forman las curvas
        url = f"{OSRM_BASE_URL}{start_str};{end_str}?overview=full&geometries=geojson"

        # Timeout corto para no bloquear la app si falla internet
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok' and len(data['routes']) > 0:
                route = data['routes'][0]
                return {
                    "distance_km": route['distance'] / 1000,  # Metros a KM
                    "duration_min": route['duration'] / 60,  # Segundos a Minutos
                    "geometry": route['geometry']['coordinates']  # Lista de puntos [lon, lat]
                }
    except Exception as e:
        print(f"⚠️ Error conectando a OSRM: {e}")
        return None

    return None