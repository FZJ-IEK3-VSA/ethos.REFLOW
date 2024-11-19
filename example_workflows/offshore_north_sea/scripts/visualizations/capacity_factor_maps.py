import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
import luigi
import numpy as np
import os
import json
import cartopy.crs as ccrs
from utils.config import ConfigLoader
from scripts.simulations.simulations_luigi_task import PerformSimulations
from utils.raster_processing import RasterProcesser

class VisualizeCapacityFactorMaps(luigi.Task):
    def requires(self):
        return [PerformSimulations()]

    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'capacity_factor_map.png'))

    def run(self):
        # Load vector data
        config_loader = ConfigLoader()
        data_path = config_loader.get_path("data")
        output_dir = config_loader.get_path("output")
        project_data_path = os.path.join(data_path, "project_data")
        project_settings_path = config_loader.get_path("settings", "project_settings")

        raster_processer = RasterProcesser()

        with open(project_settings_path, 'r') as f:
            project_settings = json.load(f)

        countries = project_settings['countries']
        years = range(project_settings["start_year"], project_settings["end_year"] + 1)
        scenarios = ["1000m_depth", "50m_depth"]

        eez_polygon = gpd.read_file(os.path.join(project_data_path, "World_EEZ_v12_20231025", 'eez_v12.shp')).to_crs(epsg=3035)
        north_sea_polygon = gpd.read_file(os.path.join(project_data_path, "MAIN_REGION_POLYGON", 'north_sea_polygon.shp'))
        coastlines_polygon = gpd.read_file(os.path.join(project_data_path, "north_sea_coasts", 'north_sea_coastlines.shp'))

        # Clip EEZ to the North Sea region
        eez_polygon = gpd.clip(eez_polygon, north_sea_polygon)

        fig, axs = plt.subplots(2, 2, figsize=(18, 18), constrained_layout=True, subplot_kw={'projection': ccrs.epsg(3035)})
        axs = axs.flatten()

        plt.rcParams['axes.labelsize'] = 18
        plt.rcParams['legend.fontsize'] = 18

        for index, scenario in enumerate(scenarios):
            # Load vector and CSV data for turbine locations and placements
            turbine_locations = gpd.read_file(os.path.join(output_dir, f"geodata/turbine_locations_{scenario}/default.shp"))
            turbine_areas = gpd.read_file(os.path.join(output_dir, f"geodata/turbine_areas_{scenario}.shp"))
            placements = pd.read_csv(os.path.join(output_dir, f"geodata/turbine_placements_4326_{scenario}.csv"))

            with open(os.path.join(output_dir, f"report_{scenario}.json"), "r") as f:
                report = json.load(f)

            merged_points = turbine_locations.merge(placements, left_on="FID", right_on="FID")
            columns_list = ['FID']

            for year in years:
                col_name = f'FLH_{year}'
                columns_list.append(col_name)

            turbine_areas = turbine_areas.merge(merged_points[columns_list], left_index=True, right_on='FID', how='left')
            for year in years:
                turbine_areas[f'capacity_factor_{year}'] = (turbine_areas[f'FLH_{year}'] / 8760) * 100

            # Calculate the mean capacity factor across all years
            turbine_areas['mean_capacity_factor'] = turbine_areas[[f'capacity_factor_{year}' for year in years]].mean(axis=1)

            # Set colormap
            custom_cmap = LinearSegmentedColormap.from_list("custom_wind_farm_cmap", ["#00008B", "#ADD8E6", "#FFA500", "#8B0000"])
            norm = plt.Normalize(vmin=30, vmax=50)  # Adjust vmin and vmax to match your data range

            # Plot coastlines
            coastlines_polygon.plot(ax=axs[index], color="#b2ab8c", edgecolor="black", linewidth=0.5)
            # Plot turbine areas with mean capacity factor
            turbine_areas.plot(column='mean_capacity_factor', 
                            ax=axs[index], 
                            legend=False,
                            cmap=custom_cmap, 
                            vmin=30, 
                            vmax=50,
                            transform=ccrs.epsg(3035))

            # Set map limits and title
            axs[index].set_xlim(north_sea_polygon.total_bounds[[0,2]])
            axs[index].set_ylim(north_sea_polygon.total_bounds[[1,3]])
            axs[index].set_title(f"Explicit placements, ERA5: {scenario}", fontsize=20)

            # Plot EEZ boundaries and country labels
            for country_code in countries:
                country_eez = eez_polygon[eez_polygon['ISO_TER1'] == country_code]
                if not country_eez.empty:
                    country_eez.boundary.plot(ax=axs[index], edgecolor='#023D6B', linewidth=0.7)
                    for _, row in country_eez.iterrows():
                        # Extract the x and y coordinates from the first element of the Series
                        if country_code == 'NOR':
                            representative_point = country_eez.geometry.representative_point().iloc[1]
                        else:
                            representative_point = country_eez.geometry.representative_point().iloc[0]
                        axs[index].text(representative_point.x, representative_point.y, country_code, 
                                        horizontalalignment='center', verticalalignment='center',
                                        transform=ccrs.epsg(3035), fontsize=16, color='black')

            # Label each subplot
            label = chr(97 + index)
            axs[index].text(0.02, 0.98, label, transform=axs[index].transAxes, fontsize=20, fontweight='bold', va='top', ha='left')

        ##################################### THIRD AND FOURTH SUBPLOTS #####################################
        for index, scenario in enumerate(scenarios):
            # Define the path to the raster file for exclusions
            raster_path = os.path.join(output_dir, f"geodata/north_sea_exclusions_{scenario}.tif")  # or replace with appropriate scenario

            # Convert the raster to polygons where value equals 100 (or whichever exclusion value is needed)
            geoms = raster_processer.raster_to_polygons(raster_path, value=100, scale_factor=10)
            clipped_gdf = gpd.GeoDataFrame(geometry=geoms, crs=3035)
            index += 2  # Start from the third subplot
            # Initialize an empty list to store each country's exclusion polygons with capacity factors
            all_country_exclusions = []

            for country_code in countries:
                country_eez = eez_polygon[eez_polygon['ISO_TER1'] == country_code]
                if not country_eez.empty:
                    # Clip exclusions to the country's EEZ
                    country_exclusions = gpd.clip(clipped_gdf, country_eez)

                    # Calculate the mean capacity factor for the country
                    capacity_factors = []
                    for year in [2014, 2015, 2016, 2017, 2018]:
                        json_path = os.path.join(output_dir, f"simulations/NEWA_timeseries/{country_code}/wind_power_newa_{year}.json")
                        with open(json_path, 'r') as f:
                            year_data = json.load(f)
                            capacity_factors.append(year_data["mean_capacity_factor"])

                    # Assign the mean capacity factor to the country's EEZ
                    mean_capacity_factor = np.mean(capacity_factors) * 100
                    print("Country:", country_code, "Mean capacity factor:", mean_capacity_factor)
                    country_exclusions = country_exclusions.copy()  # Work on a copy
                    country_exclusions['mean_capacity_factor'] = mean_capacity_factor

                    # Append to list for plotting later
                    all_country_exclusions.append(country_exclusions)

            # Combine all country exclusions into a single GeoDataFrame for plotting
            combined_exclusions = gpd.GeoDataFrame(pd.concat(all_country_exclusions, ignore_index=True), crs=3035)

            # Plot the combined exclusions on a single axis
            axs[index].set_title(f"Uniform power density, NEWA: {scenario}", fontsize=20)
            coastlines_polygon.plot(ax=axs[index], color="#b2ab8c", edgecolor="black", linewidth=0.5)  # Plot coastlines
            # Plot combined exclusions
            combined_exclusions.plot(ax=axs[index],
                                column='mean_capacity_factor',
                                cmap=custom_cmap,
                                vmin=30,
                                vmax=50,
                                legend=False,
                                edgecolor="white",
                                linewidth=0.001)

            # Plot EEZ boundaries and country labels
            for country_code in countries:
                country_eez = eez_polygon[eez_polygon['ISO_TER1'] == country_code]
                if not country_eez.empty:
                    country_eez.boundary.plot(ax=axs[index], edgecolor='#023D6B', linewidth=0.7)
                    for _, row in country_eez.iterrows():
                        # Extract the x and y coordinates from the first element of the Series
                        if country_code == 'NOR':
                            representative_point = country_eez.geometry.representative_point().iloc[1]
                        else:
                            representative_point = country_eez.geometry.representative_point().iloc[0]
                        axs[index].text(representative_point.x, representative_point.y, country_code, 
                                        horizontalalignment='center', verticalalignment='center',
                                        transform=ccrs.epsg(3035), fontsize=16, color='black')

            # Adjust axis limits to the North Sea region
            axs[index].set_xlim(north_sea_polygon.total_bounds[[0, 2]])
            axs[index].set_ylim(north_sea_polygon.total_bounds[[1, 3]])
            label = chr(97 + index)  # Dynamically assigns 'c' and 'd' for index 2 and 3
            axs[index].text(0.02, 0.98, label, transform=axs[index].transAxes, fontsize=24, fontweight='bold', va='top', ha='left')


        # ######## CREATE A sINGLE MAIN COLORBAR ON THE RIGHT SIDE OF THE PLOT ########
        # # Create a single, main color bar
        cax = fig.add_axes([1.0, 0.15, 0.04, 0.7])  # Adjust these values to position the colorbar as needed
        sm = ScalarMappable(norm=norm, cmap=custom_cmap)
        sm.set_array([])  # Dummy array for the color bar
        # cbar = fig.colorbar(sm, ax=axs, orientation="vertical", shrink=0.8, pad=1.5)  # Adjust pad to move the colorbar
        # cbar.set_label("Mean capacity factor (%)", fontsize=16)
        # cbar.ax.tick_params(labelsize=14)
        fig.colorbar(sm, cax=cax, orientation='vertical')
        cax.set_ylabel("Mean capacity factor (%)", fontsize=20)
        cax.tick_params(labelsize=18)

        plt.subplots_adjust(wspace=0.05, hspace=0.08)  # Reduce space between subplots
        plt.savefig(os.path.join(output_dir, "visualizations/capacity_factor_map.png"), dpi=300)