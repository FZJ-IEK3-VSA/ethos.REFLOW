import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from utils.config import ConfigLoader
from scripts.data_download.meteorological_data import DownloadMeterologicalData
import luigi
import json
import xarray as xr


config_loader = ConfigLoader()
output_dir = config_loader.get_path("data", "met_data")

# configure logging
log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'CombineNEWAtimeseries.log')
logger = config_loader.setup_task_logging('CombineNEWAtimeseries', log_file)
logger.info("Starting ConvertPlacements task") 

class CombineNEWAtimeseries(luigi.Task):
    def requires(self):
        return [DownloadMeterologicalData()]
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'completed_tasks', 'CombineNEWATimeseries_complete.txt'))
    
    def run(self):
        # Load the data for NOR and GBR
        countries = ['NOR', 'GBR']
        years = [2014, 2015, 2016, 2017, 2018]

        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)

        heights = project_settings["newa_wind_speed_heights"]

        for country in countries:
            for year in years:
                for height in heights:
                    # Define the output file path
                    output_path = os.path.join(output_dir, 'NEWA', 'time_series', country, f"newa_wind_speed_{country}_{year}_{height}m.nc")

                    # Check if the file already exists
                    if os.path.exists(output_path):
                        logger.info(f"File {output_path} already exists. Skipping.")
                        continue

                    else:
                        logger.info(f"Combining data for {country}, {year}, {height}m.")
                        # Adjust paths as needed based on your chunk naming convention
                        chunk_1_path = os.path.join(output_dir, 'NEWA', 'time_series', country, f"newa_wind_speed_{country}_{year}_chunk_1_{height}m.nc")
                        chunk_2_path = os.path.join(output_dir, 'NEWA', 'time_series', country, f"newa_wind_speed_{country}_{year}_chunk_2_{height}m.nc")
                        chunk_3_path = os.path.join(output_dir, 'NEWA', 'time_series', country, f"newa_wind_speed_{country}_{year}_chunk_3_{height}m.nc")
                        chunk_4_path = os.path.join(output_dir, 'NEWA', 'time_series', country, f"newa_wind_speed_{country}_{year}_chunk_4_{height}m.nc")

                        # Load all four chunks
                        chunk_1 = xr.open_dataset(chunk_1_path)
                        chunk_2 = xr.open_dataset(chunk_2_path)
                        chunk_3 = xr.open_dataset(chunk_3_path)
                        chunk_4 = xr.open_dataset(chunk_4_path)

                        # First, combine horizontally (longitude)
                        combined_lon1 = xr.concat([chunk_1, chunk_2], dim='longitude')
                        combined_lon2 = xr.concat([chunk_3, chunk_4], dim='longitude')

                        # Then, combine vertically (latitude)
                        combined_data = xr.concat([combined_lon1, combined_lon2], dim='latitude')

                        # define the output file path
                        output_path = os.path.join(output_dir, 'NEWA', 'time_series', country, f"newa_wind_speed_{country}_{year}_{height}m.nc")

                        # save the combined data to a new .nc file
                        combined_data.to_netcdf(output_path)
                        logger.info(f"Saved combined data to {output_path}")

                        # close the datasets
                        chunk_1.close()
                        chunk_2.close()
                        combined_data.close()

        # Task completion
        logger.info("ConvertPlacementsToEPSG4326 task complete.")
        with self.output().open('w') as f:
            f.write("Task complete.")