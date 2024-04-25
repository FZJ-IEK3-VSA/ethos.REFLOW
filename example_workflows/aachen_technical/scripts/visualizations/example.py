import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import matplotlib.lines as mlines
from shapely.geometry import box
from matplotlib.lines import Line2D
import pandas as pd
import rasterio
import numpy as np
import matplotlib.colors as mcolors
import json
import luigi
from scripts.simulations.simulations_luigi_task import PerformSimulations
from utils.config import ConfigLoader

config_loader = ConfigLoader()
output_dir = os.path.join(config_loader.get_path("output"))

data_dir = config_loader.get_path("data")
project_data_dir = os.path.join(data_dir, "project_data")

project_settings_path = config_loader.get_path("settings", "project_settings")
with open(project_settings_path, "r") as f:
    project_settings = json.load(f)


class VisualizeExclusionMaps(luigi.Task):
    def requires(self):
        return [PerformSimulations()]

    def output(self):
        return luigi.LocalTarget(os.path.join(output_dir,"visualizations", f"exlusions_map.png"))


    def run(self):
        """
        Script to create a plot of the existing wind farms and exclusion areas in the North Sea. 
        """        

        ########################################### PLOTTING ###########################################
        
        # Add your logic here for creating plots. 