import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import pandas as pd
import rasterio
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
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
        return luigi.LocalTarget(os.path.join(output_dir, "visualizations", f"exlusions_map.png"))


    def run(self):
        """
        Script to create a plot of the existing wind farms and exclusion areas in the North Sea. 
        """        

        ########################################### PLOTTING ###########################################
        
        # Load vector data
        aachen = gpd.read_file(os.path.join(project_data_dir, "MAIN_REGION_POLYGON", "Aachen.shp"))

        # Load raster data
        all_exclusions = rasterio.open(os.path.join(output_dir, "geodata", "aachen_exclusions.tif"))

        ## open the report.json file 
        with open(os.path.join(output_dir, "report.json"), 'r') as file:
            report = json.load(file)

        # Create the figure
        plt.rcParams['axes.labelsize'] = 14  # Set font size for axis labels
        plt.rcParams['legend.fontsize'] = 14  # Set font size for legend

        fig, ax = plt.subplots(figsize=(10, 10))

        # display the pixels with value 0 from the all_exclusions raster
        with all_exclusions as src:
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
            raster_img = src.read(1)
            # create a masked array so only pixels with value 0 are unmasked
            masked_raster = np.ma.masked_where(raster_img != 0, raster_img)
            # create a new colormap for the masked array
            cmap = mcolors.ListedColormap(['#023D6B'])
            cmap.set_bad(color='none')  # Set color for masked values (transparent)
            # Plot the masked raster with the specified colormap
            ax.imshow(masked_raster, cmap=cmap, extent=extent, interpolation='nearest', zorder=1)

        # Plot the main polygon
        aachen.boundary.plot(ax=ax, color="black", linewidth=2, zorder=2)

        # Create a legend handle for the excluded areas 
        excluded_handles = []

        excluded_area_label = f"Excluded: {round(report['Exclude_Percentage'], 2)}%"
        available_area_label = f"Available: {round(report['Eligible_Percentage'], 2)}%"
        total_area_label = f"Total area: {int(report['Total_area_km2'])} km²"
        total_area_handle = Line2D([], [], marker='', color='w', label=total_area_label, 
                                    markerfacecolor='w', markersize=11, linestyle='None', markeredgecolor='none')
        excluded_handles.append(total_area_handle)
        excluded_area_handle = Line2D([], [], marker='o', color='w', label=excluded_area_label, 
                                    markerfacecolor='#023D6B', markersize=11, linestyle='None', markeredgecolor='k')
        excluded_handles.append(excluded_area_handle)
        available_area_handle = Line2D([], [], marker='o', color='w', label=available_area_label, 
                                    markerfacecolor='w', markersize=11, linestyle='None', markeredgecolor='k')
        excluded_handles.append(available_area_handle)

        # set the extent of the plot to the extent of the north sea polygon
        ax.set_xlim(aachen.total_bounds[[0, 2]])
        ax.set_ylim(aachen.total_bounds[[1, 3]])

        # set aspect to equal
        ax.set_aspect("equal")
        # Set axis labels
        ax.set_xlabel("Easting (m, ETRS89/LAEA)")
        ax.set_ylabel("Northing (m, ETRS89/LAEA)")
        ax.set_title("Aachen eligibility assessment", fontsize=18)
        # add legend
        ax.legend(handles=excluded_handles, loc="lower left")

        print(aachen.crs)
        print(all_exclusions.crs)  # Assuming all_exclusions is your raster data variable name

        # Save the plot
        visualization_dir = os.path.join(output_dir, "visualizations")
        os.makedirs(visualization_dir, exist_ok=True)
        
        plt.savefig(self.output().path)