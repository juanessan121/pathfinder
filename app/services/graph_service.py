import heapq
from app.utils.geometry import haversine_distance
from app.utils.osrm_client import get_road_data


class GraphService:
    def find_shortest_path(self, data):
        nodes = data.get('nodes', {})
        edges_input = data.get('edges', [])
        start_node = data.get('start')
        end_node = data.get('end')

        adjacency = {node: [] for node in nodes}
        segment_details = {}

        for edge in edges_input:
            u, v = edge['from'], edge['to']
            if u in nodes and v in nodes:
                road_data = get_road_data(nodes[u], nodes[v])

                if road_data:
                    weight = road_data['distance_km']
                    duration = road_data['duration_min']
                    raw_geo = road_data['geometry']
                    geometry = [[p[1], p[0]] for p in raw_geo]
                else:
                    weight = haversine_distance(nodes[u], nodes[v])
                    duration = (weight / 60) * 60
                    geometry = [nodes[u], nodes[v]]

                adjacency[u].append((v, weight))
                adjacency[v].append((u, weight))

                segment_details[f"{u}->{v}"] = {"time": duration, "geo": geometry}
                segment_details[f"{v}->{u}"] = {"time": duration, "geo": geometry[::-1]}

        queue = [(0, start_node)]
        distances = {node: float('inf') for node in nodes}
        previous_nodes = {node: None for node in nodes}
        distances[start_node] = 0

        while queue:
            current_dist, current_node = heapq.heappop(queue)

            if current_dist > distances[current_node]: continue
            if current_node == end_node: break

            for neighbor, weight in adjacency[current_node]:
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(queue, (distance, neighbor))

        path = []
        current = end_node
        if distances[end_node] == float('inf'):
            return {"error": "No hay camino posible", "path": []}

        while current is not None:
            path.append(current)
            current = previous_nodes[current]
        path = path[::-1]

        total_time_minutes = 0
        full_geometry = []

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            key = f"{u}->{v}"
            if key in segment_details:
                info = segment_details[key]
                total_time_minutes += info['time']
                full_geometry.extend(info['geo'])

        total_km = round(distances[end_node], 2)

        total_seconds = int(total_time_minutes * 60)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        time_parts = []
        if hours > 0: time_parts.append(f"{hours}h")
        if minutes > 0 or hours > 0: time_parts.append(f"{minutes}m")
        time_parts.append(f"{seconds}s")

        formatted_time = " ".join(time_parts)

        avg_speed = 0
        if total_time_minutes > 0:
            avg_speed = round(total_km / (total_time_minutes / 60), 1)

        return {
            "path": path,
            "total_distance": total_km,
            "formatted_time": formatted_time,  # Enviamos el texto listo
            "avg_speed": avg_speed,
            "geometry": full_geometry
        }