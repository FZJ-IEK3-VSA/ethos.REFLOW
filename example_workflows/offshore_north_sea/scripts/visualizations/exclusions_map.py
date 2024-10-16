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
processed_exclusions_dir = os.path.join(data_dir, "exclusion_data/processed")

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

        scenario = "1000m_depth"

        # load vector data
        coastlines = gpd.read_file(os.path.join(project_data_dir, "north_sea_coasts/north_sea_coastlines.shp"))
        north_sea_polygon = gpd.read_file(os.path.join(project_data_dir, "MAIN_REGION_POLYGON/north_sea_polygon.shp"))

        # open the exclusions for this scenario
        all_exclusions = rasterio.open(os.path.join(output_dir, f"geodata/north_sea_exclusions_{scenario}.tif"))

        # open the report.json file as a dictionary
        with open(os.path.join(output_dir, f"report_{scenario}.json"), "r") as f:
            report = json.load(f)

        ########################################### PLOTTING ###########################################
        # Set global font sizes using rcParams
        plt.rcParams['axes.labelsize'] = 14  # Set font size for axis labels
        plt.rcParams['legend.fontsize'] = 14  # Set font size for legend

        # initialize the plot
        fig, axs = plt.subplots(1, 2, figsize=(16, 8))

        # Flatten the axs array for easy indexing
        axs = axs.flatten()

        #plot coastlines data
        coastlines.plot(ax=axs[0], color="#b2ab8c", edgecolor="black", linewidth=0.5)
        
        # Display only pixels with value 0 from the all_exclusions raster on axs[1]
        with rasterio.open(os.path.join(output_dir, f"geodata/north_sea_exclusions_{scenario}.tif")) as src:
            raster_extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

            # Downsample the raster data by a factor of 50
            downsample_factor = 50
            downsampled_raster = downscale_local_mean(masked_raster, (downsample_factor, downsample_factor))

            # Update the extent accordingly
            new_extent = (
                raster_extent[0],
                raster_extent[0] + (raster_extent[1] - raster_extent[0]) * downsampled_raster.shape[1] / masked_raster.shape[1],
                raster_extent[2],
                raster_extent[2] + (raster_extent[3] - raster_extent[2]) * downsampled_raster.shape[0] / masked_raster.shape[0],
            )

            # Plot the downsampled raster
            ax.imshow(downsampled_raster, cmap=cmap, extent=new_extent, interpolation='nearest')
            raster_img = src.read(1)

            # Create a masked array where only the pixels with value 0 are unmasked
            masked_raster = np.ma.masked_where(raster_img != 0, raster_img)

            # Create a new colormap for the masked array
            # Set the color for masked values and the unique unmasked value (0)
            cmap = mcolors.ListedColormap(['#023D6B'])
            cmap.set_bad(color='none')  # Set color for masked values (transparent)

            # Plot the masked raster with the specified colormap
            axs[0].imshow(masked_raster, cmap=cmap, extent=extent, interpolation='nearest')

        # Create a legend handle for the excluded areas 
        excluded_handles = []

        excluded_area_label = f"Excluded: {round(report['Exclude_Percentage'], 2)}%"
        available_area_label = f"Available: {round(report['Eligible_Percentage'], 2)}%"
        total_area_label = f"Total area: \n{int(report['Total_area_km2'])} km²"
        total_area_handle = Line2D([], [], marker='', color='w', label=total_area_label, 
                                    markerfacecolor='w', markersize=11, linestyle='None', markeredgecolor='none')
        excluded_handles.append(total_area_handle)
        excluded_area_handle = Line2D([], [], marker='o', color='w', label=excluded_area_label, 
                                    markerfacecolor='#023D6B', markersize=11, linestyle='None', markeredgecolor='none')
        excluded_handles.append(excluded_area_handle)
        available_area_handle = Line2D([], [], marker='o', color='w', label=available_area_label, 
                                    markerfacecolor='w', markersize=11, linestyle='None', markeredgecolor='none')
        excluded_handles.append(available_area_handle)

        # set the extent of the plot to the extent of the north sea polygon
        axs[0].set_xlim(north_sea_polygon.total_bounds[[0, 2]])
        axs[0].set_ylim(north_sea_polygon.total_bounds[[1, 3]])

        # set aspect to equal
        axs[0].set_aspect("equal")
        # Set axis labels
        axs[0].set_xlabel("Easting (m, ETRS89/LAEA)")
        axs[0].set_ylabel("Northing (m, ETRS89/LAEA)")
        axs[0].set_title("Max. depth: 1000 m", fontsize=18)
        # add legend
        axs[0].legend(handles=excluded_handles, loc="upper right")
        
        ############### ADD IN THE THIRD PLOT ################
        scenario = "50m_depth"
        
        # open the exclusions for this scenario
        all_exclusions = rasterio.open(os.path.join(output_dir, f"geodata/north_sea_exclusions_{scenario}.tif"))

        # open the report.json file as a dictionary
        with open(os.path.join(output_dir, f"report_{scenario}.json"), "r") as f:
            report = json.load(f)

        coastlines.plot(ax=axs[1], color="#b2ab8c", edgecolor="black", linewidth=0.5)

        # Display only pixels with value 0 from the all_exclusions raster on axs[1]
        with rasterio.open(os.path.join(output_dir, f"geodata/north_sea_exclusions_{scenario}.tif")) as src:
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
            raster_img = src.read(1)

            # Create a masked array where only the pixels with value 0 are unmasked
            masked_raster = np.ma.masked_where(raster_img != 0, raster_img)

            # Create a new colormap for the masked array
            # Set the color for masked values and the unique unmasked value (0)
            cmap = mcolors.ListedColormap(['#023D6B'])
            cmap.set_bad(color='none')  # Set color for masked values (transparent)

            # Plot the masked raster with the specified colormap
            axs[1].imshow(masked_raster, cmap=cmap, extent=extent, interpolation='nearest')


        # Create a legend handle for the excluded areas 
        excluded_handles = []

        excluded_area_label = f"Excluded: {round(report['Exclude_Percentage'], 2)}%"
        available_area_label = f"Available: {round(report['Eligible_Percentage'], 2)}%"
        total_area_label = f"Total area: \n{int(report['Total_area_km2'])} km²"
        total_area_handle = Line2D([], [], marker='', color='w', label=total_area_label, 
                                    markerfacecolor='w', markersize=11, linestyle='None', markeredgecolor='none')
        excluded_handles.append(total_area_handle)
        excluded_area_handle = Line2D([], [], marker='o', color='w', label=excluded_area_label, 
                                    markerfacecolor='#023D6B', markersize=11, linestyle='None', markeredgecolor='none')
        excluded_handles.append(excluded_area_handle)
        available_area_handle = Line2D([], [], marker='o', color='w', label=available_area_label, 
                                    markerfacecolor='w', markersize=11, linestyle='None', markeredgecolor='none')
        excluded_handles.append(available_area_handle)

        axs[1].set_xlim(north_sea_polygon.total_bounds[[0, 2]])
        axs[1].set_ylim(north_sea_polygon.total_bounds[[1, 3]])
        axs[1].set_aspect("equal")
        axs[1].set_xlabel("Easting (m, ETRS89/LAEA)")
        axs[1].set_ylabel("Northing (m, ETRS89/LAEA)")
        axs[1].legend(handles=excluded_handles, loc='upper right')
        axs[1].set_title("Max. depth: 50 m", fontsize=18)

        ########### Global settings for the plot ###########

        plt.tight_layout()
        plt.subplots_adjust(wspace=0.07)  # 'wspace' controls the width of the space between subplots
        
        visualizations_dir = os.path.join(output_dir, "visualizations")
        if not os.path.exists(visualizations_dir):
            os.makedirs(visualizations_dir)

        plt.savefig(os.path.join(visualizations_dir, f"exlusions_map.png"), dpi=300)