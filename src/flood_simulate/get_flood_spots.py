import os
import json

# List of districts
taipei_areas = [
    "北投區",
    "士林區",
    "內湖區",
    "南港區",
    "松山區",
    "信義區",
    "中山區",
    "大同區",
    "中正區",
    "萬華區",
    "大安區",
    "文山區",
]

# Dictionary to store districts and their coordinates
area_coordinates = {}
base_directory = "./src/flood_simulate/台北市"

# Read GeoJSON files and store coordinates
for file in os.listdir(base_directory):
    if file.endswith(".json"):
        path_to_file = os.path.join(base_directory, file)
        with open(path_to_file) as json_file:
            coords = json.load(json_file)
            area_coordinates[file[:-5]] = coords


# Check if a point is inside a given polygon
def check_point_in_polygon(lat, lon, area):
    vertices = len(area_coordinates[area])
    is_inside = False

    vertex1_lat, vertex1_lon = area_coordinates[area][0]
    for index in range(vertices + 1):
        vertex2_lat, vertex2_lon = area_coordinates[area][index % vertices]
        if lon > min(vertex1_lon, vertex2_lon):
            if lon <= max(vertex1_lon, vertex2_lon):
                if lat <= max(vertex1_lat, vertex2_lat):
                    if vertex1_lon != vertex2_lon:
                        intersection = (lon - vertex1_lon) * (
                            vertex2_lat - vertex1_lat
                        ) / (vertex2_lon - vertex1_lon) + vertex1_lat
                    if vertex1_lat == vertex2_lat or lat <= intersection:
                        is_inside = not is_inside
        vertex1_lat, vertex1_lon = vertex2_lat, vertex2_lon

    return is_inside


# Calculate the center point of a polygon
def find_polygon_center(points):
    total_lat = sum(point[0] for point in points)
    total_lon = sum(point[1] for point in points)
    count_points = len(points)
    center_lat = total_lat / count_points
    center_lon = total_lon / count_points
    return center_lat, center_lon


# Process MultiPolygon data to get counts
def process_multipolygon(coordinates):
    area_data = [0] * len(taipei_areas)
    for index, area in enumerate(taipei_areas):
        for coordinate_group in coordinates:
            polygon = coordinate_group[0]
            polygon_center_lon, polygon_center_lat = find_polygon_center(polygon)
            if check_point_in_polygon(polygon_center_lat, polygon_center_lon, area):
                area_data[index] += 1
    return area_data


# Generate data for each district from a GeoJSON file
def create_area_data_from_geojson(json_path):
    area_data = []
    with open(json_path) as json_file:
        geojson_data = json.load(json_file)
        for feature in geojson_data["features"]:
            district_data = {}
            district_name = feature["properties"]["Name"]
            district_data["name"] = district_name
            if feature["geometry"]["type"] == "MultiPolygon":
                district_data["data"] = process_multipolygon(
                    feature["geometry"]["coordinates"]
                )
            else:
                print("Not Implemented")
            area_data.append(district_data)
    return area_data


# Main execution to generate and save flood data
geojson_file_path = "./public/mapData/flood_simulate.geojson"
final_flood_data = create_area_data_from_geojson(geojson_file_path)
data = {"data": final_flood_data}
with open("./public/chartData/163.json", "w+") as output_file:
    json.dump(data, output_file)
