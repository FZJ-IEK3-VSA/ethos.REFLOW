import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from utils.config import ConfigLoader
from scripts.exclusions_placements.exclusions_luigi_task import PerformEligibiliyAnalysisPlacements
import luigi
import json

class ConvertPlacementsToEPSG4326(luigi.Task):
    def requires(self):
        return [PerformEligibiliyAnalysisPlacements()]
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output", "geodata"), f"turbine_placements_4326.csv"))
    
    def run(self):
        input_file_path = os.path.join(output_dir, f"turbine_placements_3035.csv")

        config_loader = ConfigLoader()
        output_dir = config_loader.get_path("output", "geodata")
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
    
        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ConvertPlacements.log')
        logger = config_loader.setup_task_logging('ConvertPlacements', log_file)
        logger.info("Starting ConvertPlacements task") 

        # Load turbine placements
        placements_df = pd.read_csv(input_file_path)

        # Convert DataFrame to GeoDataFrame
        gdf_turbines = gpd.GeoDataFrame(
            placements_df,
            geometry=[Point(xy) for xy in zip(placements_df.lon, placements_df.lat)],
            crs="EPSG:3035"
        )

        # Convert placements to EPSG:4326
        gdf_turbines = gdf_turbines.to_crs("EPSG:4326")

        # Update lat and lon columns
        gdf_turbines["lat"] = gdf_turbines.geometry.y
        gdf_turbines["lon"] = gdf_turbines.geometry.x

        # Drop geometry column and save
        gdf_turbines.drop(columns=['geometry'], inplace=True)
        output_file_path = os.path.join(output_dir, f"turbine_placements_4326.csv")
        gdf_turbines.to_csv(output_file_path, index=True, index_label="FID")

        # Task completion
        logger.info("ConvertPlacementsToEPSG4326 task complete.")
