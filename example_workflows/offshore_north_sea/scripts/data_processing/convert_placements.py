import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from utils.config import ConfigLoader
from scripts.exclusions_placements.exclusions_luigi_task import PerformEligibiliyAnalysisPlacements
import luigi
import json


config_loader = ConfigLoader()
output_dir = config_loader.get_path("output", "geodata")
project_settings_path = config_loader.get_path("settings", "project_settings")
with open(project_settings_path, 'r') as file:
    project_settings = json.load(file)
##### running multiple scenarios for exlucsions
scenario = project_settings["scenario"]

# configure logging
log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ConvertPlacements.log')
logger = config_loader.setup_task_logging('ConvertPlacements', log_file)
logger.info("Starting ConvertPlacements task") 

class ConvertAndExtractPlacements(luigi.Task):
    def requires(self):
        return [PerformEligibiliyAnalysisPlacements()]
    
    def output(self):
        return luigi.LocalTarget(os.path.join(output_dir, f"turbine_placements_4326_{scenario}.csv"))
    
    def run(self):
        input_file_path = os.path.join(output_dir, f"turbine_placements_3035_{scenario}.csv")

        # Load turbine placements
        placements_df = pd.read_csv(input_file_path)

        # Convert DataFrame to GeoDataFrame
        gdf_turbines = gpd.GeoDataFrame(
            placements_df,
            geometry=[Point(xy) for xy in zip(placements_df.lon, placements_df.lat)],
            crs="EPSG:3035"
        )

        # Load EEZ polygons
        eez_path = os.path.join(config_loader.get_path("data", "project_data"), "World_EEZ_v12_20231025", "eez_v12.shp")
        eez_polygon = gpd.read_file(eez_path).to_crs("EPSG:3035")

        # Perform spatial join
        turbines_with_countries = gpd.sjoin(gdf_turbines, eez_polygon[['ISO_TER1', 'geometry']], how="left", op='within')
        turbines_with_countries.rename(columns={'ISO_TER1': 'country'}, inplace=True)

        # Convert placements to EPSG:4326
        turbines_with_countries = turbines_with_countries.to_crs("EPSG:4326")

        # Update lat and lon columns
        turbines_with_countries["lat"] = turbines_with_countries.geometry.y
        turbines_with_countries["lon"] = turbines_with_countries.geometry.x

        # Drop geometry column and save
        turbines_with_countries.drop(columns=['geometry'], inplace=True)
        output_file_path = os.path.join(output_dir, f"turbine_placements_4326_{scenario}.csv")
        turbines_with_countries.to_csv(output_file_path, index=True, index_label="FID")

        # Task completion
        logger.info("ConvertPlacementsToEPSG4326 task complete.")
