import geopandas as gpd
import matplotlib.pyplot as plt
import os
import pandas as pd
import rasterio
import numpy as np
import matplotlib.colors as mcolors
import json
import luigi
from scripts.simulations.simulations_luigi_task import PerformSimulations
from utils.config import ConfigLoader
from matplotlib.colors import LinearSegmentedColormap

class VisualizeCapacityFactorMaps(luigi.Task):
    def requires(self):
        return [PerformSimulations()]
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'capacity_factor_map.png'))
    
    def run(self):
        config_loader = ConfigLoader()
        data_path = config_loader.get_path("data")
        output_dir = config_loader.get_path("output")
        project_data_path = os.path.join(data_path, "project_data")
        project_settings_path = config_loader.get_path("settings", "project_settings")
        
        with open(project_settings_path, 'r') as f:
            project_settings = json.load(f)

        year = 2016

        aachen_polygon = gpd.read_file(os.path.join(project_data_path, "MAIN_REGION_POLYGON", 'Aachen.shp'))

        fig, ax = plt.subplots(figsize=(10, 10))  # Adjust figsize as needed

        # Plot the coastlines
        aachen_polygon.boundary.plot(ax=ax, color="black", linewidth=1)

        turbine_locations = gpd.read_file(os.path.join(output_dir, f"geodata/aachen_turbine_placements.shp"))
        turbine_areas = gpd.read_file(os.path.join(output_dir, f"geodata/aachen_area.shp"))
        placements = pd.read_csv(os.path.join(output_dir, f"geodata/turbine_placements_4326.csv"))

        with open(os.path.join(output_dir, f"report.json"), "r") as f:
            report = json.load(f)

        with open(os.path.join(output_dir, "report.json"), "r") as f:
            report = json.load(f)

        # Debugging: Print the column names to verify 'FID' columns exist
        print("Turbine Locations Columns:", turbine_locations.columns)
        print("Placements Columns:", placements.columns)
        print("Turbine Areas Columns:", turbine_areas.columns)

        # Create a unique identifier in turbine_areas if it doesn't have one
        if 'FID' not in turbine_areas.columns:
            turbine_areas['FID'] = turbine_areas.index

        # Ensure columns_list only has the necessary columns
        columns_list = ['FID', f'FLH_{year}']

        # Merge turbine_locations with placements based on 'FID'
        merged_points = turbine_locations.merge(placements[columns_list], on='FID')

        # Merge turbine_areas with merged_points based on 'FID'
        turbine_areas = turbine_areas.merge(merged_points[['FID', f'FLH_{year}']], on='FID', how='left')

        # Calculate the capacity factor for the given year
        turbine_areas[f'capacity_factor_{year}'] = (turbine_areas[f'FLH_{year}'] / 8760) * 100

        # Since there's only one year, use the capacity factor for that year
        turbine_areas['capacity_factor'] = turbine_areas[f'capacity_factor_{year}']

        # Define the colors for the custom colormap
        colors_custom = [
                "#00008B",  # Dark Blue
                "#ADD8E6",  # light blue 
                "#FFA500",  # Orange 
                "#8B0000"   # Dark Red 
            ]

        # Create the colormap
        custom_cmap = LinearSegmentedColormap.from_list("custom_wind_farm_cmap", colors_custom)


        # Plot the turbine areas
        plot = turbine_areas.plot(column='capacity_factor', 
                                  ax=ax, 
                                  legend=True, 
                                  legend_kwds={'label': "Capacity Factor (%)", 
                                               'orientation': "vertical", 
                                               'shrink': 0.85},
                                  cmap=custom_cmap, 
                                  vmin=20, 
                                  vmax=40)

        ax.set_xlim(aachen_polygon.total_bounds[[0, 2]])
        ax.set_ylim(aachen_polygon.total_bounds[[1, 3]])
        ax.set_title("Aachen Placements Capacity Factor Map", fontsize=14)
        ax.set_xlabel("Easting (m, ETRS89/LAEA)")
        ax.set_ylabel("Northing (m, ETRS89/LAEA)")

        plt.savefig(self.output().path)
