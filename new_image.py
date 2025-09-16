from fastapi import FastAPI, Query
import geoai
from geoai.download import download_overture_buildings, extract_building_stats
import json
import os
from datetime import datetime
import leafmap.foliumap as leafmap  # For visualization

app = FastAPI()

# Folder to store geojson files
OUTPUT_DIR = "geojson_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)
MAP_DIR = "MAP_file"
os.makedirs(MAP_DIR, exist_ok=True)


@app.get("/download_buildings")
def download_buildings(
    bbox: str = Query(None, description="Bounding box in format min_lon,min_lat,max_lon,max_lat"),
    min_lon: float = None,
    min_lat: float = None,
    max_lon: float = None,
    max_lat: float = None
):
    bbox_values = None

    # Case 1: If bbox is passed as single string
    if bbox:
        try:
            bbox_values = [float(x) for x in bbox.split(",")]
            if len(bbox_values) != 4:
                return {"error": "Invalid bbox format. Use: min_lon,min_lat,max_lon,max_lat"}
        except ValueError:
            return {"error": "BBox values must be numeric"}

    # Case 2: If separate params are passed
    elif None not in (min_lon, min_lat, max_lon, max_lat):
        bbox_values = [min_lon, min_lat, max_lon, max_lat]

    else:
        return {"error": "Provide bbox either as one parameter or four separate parameters."}

    # Create unique filename using timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"buildings_{timestamp}.geojson")

    # Download buildings using geoai
    download_overture_buildings(bbox_values, output_file)

    # Extract stats (optional)
    stats = extract_building_stats(output_file)

    # Visualization
    try:
        # Load data into Leafmap
        m = leafmap.Map(center=[bbox_values[1], bbox_values[0]], zoom=14)
        m.add_geojson(
            output_file,
            layer_name="Buildings by Height",
            style={"color": "blue", "fillOpacity": 0.5},
            info_mode="on_hover"
        )
        # Save map as HTML file
        map_file = os.path.join(MAP_DIR, f"map_{timestamp}.html")
        m.to_html(map_file)
    except Exception as e:
        map_file = None

    # Read GeoJSON content
    geojson_data = None
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

    return {
        "bbox": bbox_values,
        "output_file": output_file,
        "map_file": map_file,
        "stats": stats,
        "geojson": geojson_data
    }
