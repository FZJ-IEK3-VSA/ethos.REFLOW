import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.lines as mlines
from shapely.geometry import box
from utils.config import ConfigLoader
from matplotlib import cm
from scripts.simulations.simulations_luigi_task import PerformSimulations
import cartopy.crs as ccrs
import luigi
import numpy as np
import os
import json
import math

class VisualizeCapacityFactorMaps(luigi.Task):
    def requires(self):
        return [PerformSimulations()]
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'capacity_factor_map.png'))
    
    def run(self):
        # load vector data
        config_loader = ConfigLoader()
        data_path = config_loader.get_path("data")
        output_dir = config_loader.get_path("output")
        project_data_path = os.path.join(data_path, "project_data")
        processed_exclusions_dir = os.path.join(data_path, "exclusion_data/processed")
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as f:
            project_settings = json.load(f)

        countries = project_settings['countries']
        years = range(project_settings["start_year"], project_settings["end_year"] + 1)
        countries = project_settings['countries']
        scenarios = ["1000m_depth", "50m_depth"]

        eez_polygon = gpd.read_file(os.path.join(project_data_path, "World_EEZ_v12_20231025", 'eez_v12.shp'))

        # Adjust CRS for coastlines_polygon if necessary to match CartoPy projection (EPSG:3035)
        eez_polygon = eez_polygon.to_crs(epsg=3035)

        north_sea_polygon = gpd.read_file(os.path.join(project_data_path, "MAIN_REGION_POLYGON", 'north_sea_polygon.shp'))
        coastlines_polygon = gpd.read_file(os.path.join(project_data_path, "north_sea_coasts", 'north_sea_coastlines.shp'))

        # clip the EEZ to the main polygon
        eez_polygon = gpd.clip(eez_polygon, north_sea_polygon)

        fig, axs = plt.subplots(2, 2, figsize=(18, 20), subplot_kw={'projection': ccrs.epsg(3035)})  # Adjust figsize as needed

        axs = axs.flatten()

        plt.rcParams['axes.labelsize'] = 14  # Set font size for axis labels
        plt.rcParams['legend.fontsize'] = 14  # Set font size for legend

        for index, scenario in enumerate(scenarios):

            # Load the vector data
            
            turbine_locations = gpd.read_file(os.path.join(output_dir, f"geodata/turbine_locations_{scenario}/turbine_locations_{scenario}.shp"))
            turbine_areas = gpd.read_file(os.path.join(output_dir, f"geodata/turbine_areas_{scenario}.shp"))
            placements = pd.read_csv(os.path.join(output_dir, f"geodata/turbine_placements_4326_{scenario}.csv"))
            
            # open the report.json file as a dictionary
            with open(os.path.join(output_dir, f"report_{scenario}.json"), "r") as f:
                report = json.load(f)


            # STEP 1: Load the data
            ### merge the CSV data with the geodataframe
            merged_points = turbine_locations.merge(placements, left_on="FID", right_on="FID")

            # map this information to the turbine_areas geodataframe
            columns_list = ['FID']

            for year in years:
                col_name = f'FLH_{year}'
                columns_list.append(col_name)

            turbine_areas = turbine_areas.merge(merged_points[columns_list], left_index=True, right_on='FID', how='left')

            # STEP 2: Calculate the % capacity factor for each year
            print("Calculating the Capacity Factor...")
            for year in years:
                # calculate the capacity factor for each year
                turbine_areas[f'capacity_factor_{year}'] = (turbine_areas[f'FLH_{year}'] / 8760) * 100

            # STEP 3: get the mean capacity factor across all years
            print("Calculating the mean capacity factor...")
            turbine_areas['mean_capacity_factor'] = turbine_areas[[f'capacity_factor_{year}' for year in years]].mean(axis=1)
            #print the min and max mean capacity factor

            min_mean_capacity_factor = turbine_areas['mean_capacity_factor'].min()
            max_mean_capacity_factor = turbine_areas['mean_capacity_factor'].max()

            # round the min and max capacity factors to the nearest 5
            rounded_min_mean_capacity_factor = 45
            rounded_max_mean_capacity_factor = 70

            # STEP 4: Plot the data

            # Set global font sizes using rcParams
            plt.rcParams['axes.labelsize'] = 14  # Set font size for axis labels
            plt.rcParams['legend.fontsize'] = 14  # Set font size for legend

            # Define the colors for the custom colormap
            colors_custom = [
                    "#00008B",  # Dark Blue
                    "#ADD8E6",  # light blue 
                    "#FFA500",  # Orange 
                    "#8B0000"   # Dark Red 
                ]

            # Create the colormap
            custom_cmap = LinearSegmentedColormap.from_list("custom_wind_farm_cmap", colors_custom)

            # plot the coastlines
            coastlines_polygon.plot(ax=axs[index], color="#b2ab8c", edgecolor="black", linewidth=0.5)

            turbine_areas.plot(column='mean_capacity_factor', 
                            ax=axs[index], 
                            legend=True,
                            legend_kwds={
                                'label': "Capacity Factor (%)", 
                                'orientation': "vertical",
                                'shrink': 0.75,
                                },
                            cmap=custom_cmap, 
                            vmin=rounded_min_mean_capacity_factor, 
                            vmax=rounded_max_mean_capacity_factor,
                            transform=ccrs.epsg(3035))  
            # set map limits
            axs[index].set_xlim(north_sea_polygon.total_bounds[[0,2]])
            axs[index].set_ylim(north_sea_polygon.total_bounds[[1,3]])

            axs[index].set_title(f"Scenario: {scenario}")

            legend_handles = []

            ## plot the EEZ boundaries
            for country_code in countries:
                country_eez = eez_polygon[eez_polygon['ISO_TER1'] == country_code]
                # check if there are any polygons for the country
                if not country_eez.empty:
                    country_eez.boundary.plot(ax=axs[index], edgecolor='#023D6B', linewidth=0.7)
                    # Add ISO code text label
                    # Compute a representative point within each polygon to place the text
                    for _, row in country_eez.iterrows():
                        representative_point = row.geometry.representative_point()
                        axs[index].text(representative_point.x, representative_point.y, country_code, 
                                horizontalalignment='center', verticalalignment='center',
                                transform=ccrs.epsg(3035), fontsize=12, color='black')

            # After all plotting commands for the subplot, add the label
            label = chr(97 + index)  # 97 is the ASCII code for 'a'
            axs[index].text(0.02, 0.98, label, transform=axs[index].transAxes, fontsize=20, fontweight='bold', va='top', ha='left')
            
            # Define the colors for the custom colormap
            colors = ["#FFFFFF", "#023D6B"]  # From white to dark blue
            custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", colors)

            # After plotting the mean capacity factor maps, calculate and plot the variability
            # Calculate the standard deviation across the years for each turbine
            std_dev_column_name = f'std_dev_{scenario}'
            turbine_areas[std_dev_column_name] = turbine_areas[[f'FLH_{year}' for year in years]].std(axis=1)

            # Convert the standard deviation from FLH to %CF
            std_dev_cf_column_name = f'std_dev_cf_{scenario}'
            turbine_areas[std_dev_cf_column_name] = (turbine_areas[std_dev_column_name] / 8760) * 100

            # Plot the variability for the current scenario
            variability_plot_index = index + 2  # This will use the third (c) and fourth (d) subplot positions

            # plot the coastlines
            coastlines_polygon.plot(ax=axs[variability_plot_index], color="#b2ab8c", edgecolor="black", linewidth=0.5)

            turbine_areas.plot(column=std_dev_cf_column_name, 
                            ax=axs[variability_plot_index], 
                            legend=True, 
                            legend_kwds={'label': "Variability (Standard Deviation) [ CF % ]", 'orientation': "vertical", 'shrink': 0.75},
                            cmap=custom_cmap, 
                            vmin=6, 
                            vmax=12,
                            transform=ccrs.epsg(3035))

            ## plot the EEZ boundaries
            for country_code in countries:
                country_eez = eez_polygon[eez_polygon['ISO_TER1'] == country_code]
                # check if there are any polygons for the country
                if not country_eez.empty:
                    country_eez.boundary.plot(ax=axs[variability_plot_index], edgecolor='#023D6B', linewidth=0.7)
                    # Add ISO code text label
                    # Compute a representative point within each polygon to place the text
                    for _, row in country_eez.iterrows():
                        representative_point = row.geometry.representative_point()
                        axs[variability_plot_index].text(representative_point.x, representative_point.y, country_code, 
                                horizontalalignment='center', verticalalignment='center',
                                transform=ccrs.epsg(3035), fontsize=12, color='black')
            # set map limits
            axs[variability_plot_index].set_xlim(north_sea_polygon.total_bounds[[0,2]])
            axs[variability_plot_index].set_ylim(north_sea_polygon.total_bounds[[1,3]])

            # Add labels 'c' and 'd' to the variability plots
            label = chr(99 + index)  # 'c', 'd'
            axs[variability_plot_index].text(0.02, 0.98, label, transform=axs[variability_plot_index].transAxes, fontsize=20, fontweight='bold', va='top', ha='left')

            # Set the title for the variability plots
            axs[variability_plot_index].set_title(f"Variability of Scenario: {scenario}")

        # Set common labels and adjustments
        for ax in axs:
            ax.set_xlabel("Easting (m, ETRS89/LAEA)")
            ax.set_ylabel("Northing (m, ETRS89/LAEA)")
                    
        plt.tight_layout()
        # save the figure
        plt.savefig(os.path.join(output_dir, "visualizations/capacity_factor_map.png"), dpi=300)