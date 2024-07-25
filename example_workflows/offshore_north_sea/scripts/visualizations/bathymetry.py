import os
import luigi
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import rasterio
import geopandas as gpd
import json
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.lines import Line2D
from utils.config import ConfigLoader
from scripts.data_processing.process_exclusions_data import ProcessExclusionsData
import pandas as pd
from matplotlib import cm

class VisualizeBathymetry(luigi.Task):
    def requires(self):
        return None
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'bathymetry_and_wind_farms.png'))
    
    def run(self):
        config_loader = ConfigLoader()
        data_path = config_loader.get_path("data")
        output_dir = config_loader.get_path("output")
        project_data_path = os.path.join(data_path, "project_data")
        processed_exclusions_dir = os.path.join(data_path, "exclusion_data/processed")
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as f:
            project_settings = json.load(f)

        countries = project_settings['countries']

        # Load the vector data
        main_polygon = gpd.read_file(os.path.join(project_data_path, "MAIN_REGION_POLYGON", 'north_sea_polygon.shp'))
        coastlines_polygon = gpd.read_file(os.path.join(project_data_path, "north_sea_coasts", 'north_sea_coastlines.shp'))
        eez_polygon = gpd.read_file(os.path.join(project_data_path, "World_EEZ_v12_20231025", 'eez_v12.shp'))

        # Adjust CRS for coastlines_polygon if necessary to match CartoPy projection (EPSG:3035)
        eez_polygon = eez_polygon.to_crs(epsg=3035)

        # clip the EEZ to the main polygon
        eez_polygon = gpd.clip(eez_polygon, main_polygon)

        # Load vector data for wind farms
        wind_farms_polygon = gpd.read_file(os.path.join(processed_exclusions_dir, "existing_wind_farms/EMODnet_HA_Energy_WindFarms_pg_20231124_polygon.shp")).to_crs(epsg=3035)
        wind_farms_points = gpd.read_file(os.path.join(processed_exclusions_dir, "existing_wind_farms/EMODnet_HA_Energy_WindFarms_pt_20231124_point.shp")).to_crs(epsg=3035)

        # combine "Approved" and "Construction" into one category and execlude "Dismantled" FOR POLYGON DATA
        wind_farms_polygon['STATUS_COMBINED'] = wind_farms_polygon['STATUS'].replace({
            "Approved": "Approved / \nConstruction",
            "Construction": "Approved / \nConstruction"
        })
        wind_farms_polygon = wind_farms_polygon[wind_farms_polygon['STATUS'] != "Dismantled"]

        # Combine "Approved" and "Construction" into one category and exclude "Dismantled" FOR POINT DATA
        wind_farms_points['STATUS_COMBINED'] = wind_farms_points['STATUS'].replace({
            "Approved": "Approved / \nConstruction",
            "Construction": "Approved / \nConstruction"
        })
        wind_farms_points = wind_farms_points[wind_farms_points['STATUS'] != "Dismantled"]

        # make sure only wind farm points in the North Sea are plotted
        coastline_union = coastlines_polygon.unary_union
        wind_farms_points = wind_farms_points[wind_farms_points.geometry.apply(lambda x: not x.within(coastline_union))]

        # Combine polygon and point datasets for power sum calculation
        combined_wind_farms = pd.concat([wind_farms_polygon[['STATUS_COMBINED', 'POWER_MW']], wind_farms_points[['STATUS_COMBINED', 'POWER_MW']]])

        # Plot setup
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.epsg(3035)})
        ax.set_extent([main_polygon.total_bounds[0], main_polygon.total_bounds[2], main_polygon.total_bounds[1], main_polygon.total_bounds[3]], crs=ccrs.epsg(3035))
        
        # Set global font sizes using rcParams
        plt.rcParams['axes.labelsize'] = 14  # Set font size for axis labels
        plt.rcParams['legend.fontsize'] = 14  # Set font size for legend

        # Load and plot the bathymetry data and colorbar
        bathymetry = rasterio.open(os.path.join(processed_exclusions_dir, 'bathymetry', 'north_sea_bathymetry.tif'))
        bathymetry_data = bathymetry.read(1)

        no_data = -32767

        ## Adjust the colormap and normalization
        # Define the depth range and interval
        min_depth = -800
        max_depth = 0
        depth_interval = 50
        levels = np.arange(min_depth, max_depth + depth_interval, depth_interval)

        # Mask the no-data values
        masked_data = np.ma.masked_where((bathymetry_data == no_data) | (bathymetry_data > max_depth), bathymetry_data)
        masked_data = np.clip(masked_data, min_depth, max_depth)

        # Create a discrete colormap for the bathymetry data
        colors = ["#01579b", "#e0f7fa"]
        colormap = LinearSegmentedColormap.from_list("custom_blue", colors, N=len(levels))
        norm = BoundaryNorm(levels, ncolors=colormap.N, clip=True)

        ## add a custom colorbar
        sm = cm.ScalarMappable(cmap=colormap, norm=norm)
        sm.set_array([])

        # Define ticks at every 100m depth
        tick_values = np.arange(-800, 0 + 100, 100)

        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', label='Depth (m)', shrink=0.7, aspect=17, ticks=tick_values)
        # Remove minor ticks by setting them to an empty list
        cbar.ax.yaxis.set_minor_locator(plt.NullLocator())
        cbar.ax.tick_params(labelsize=11)

        # Show the bathymetry using imshow
        c = ax.imshow(masked_data, cmap=colormap, norm=norm, extent=[bathymetry.bounds.left, bathymetry.bounds.right, bathymetry.bounds.bottom, bathymetry.bounds.top], transform=ccrs.epsg('3035'), interpolation='nearest')
        
        # Plot wind farms as points and polygons
        # 1. group by STATUS_COMBINED and sum the POWER_MW
        power_sums_combined  = combined_wind_farms.groupby('STATUS_COMBINED')['POWER_MW'].sum() / 1000  # convert to GW

        # Get a subset of colors from the "tab20" colormap
        
        wind_farm_colors = [
            "#ff4500"  #production
            "#ffd700",  #approved/construction
            "#006400",  #planned
        ]
        
        colormap = LinearSegmentedColormap.from_list("wind_farm_colors", wind_farm_colors, N=len(wind_farm_colors))
        colors = [colormap(i) for i in range(len(wind_farms_polygon['STATUS_COMBINED'].unique()))]

        # Map each unique status to a color from "tab20"
        status_colors = dict(zip(wind_farms_polygon['STATUS_COMBINED'].unique(), colors))

        for status, color in status_colors.items():
            wind_farms_subset = wind_farms_polygon[wind_farms_polygon['STATUS_COMBINED'] == status]
            if not wind_farms_points.empty:
                wind_farms_subset.plot(ax=ax, color=color)

        for status, color in status_colors.items():
            subset = wind_farms_points[wind_farms_points['STATUS_COMBINED'] == status]
            if not wind_farms_subset.empty:
                ax.scatter(subset.geometry.x, subset.geometry.y, color=color, label=f"{status} points", s=8)  # s is the marker size
        
        # Create legend entries with circle markers
        legend_handles = []
        for status, color in status_colors.items():
            # Use 'o' for circle markers, adjust markersize as needed
            label = f"{status}: {power_sums_combined[status]:.0f} GW"
            handle = Line2D([], [], marker='o', color='w', label=label,
                            markerfacecolor=color, markersize=11, linestyle='None', markeredgecolor='none')
            legend_handles.append(handle)

        ax.legend(handles=legend_handles, loc='upper right')
        
        #plot coastlines data
        coastlines_polygon.plot(ax=ax, color="#b2ab8c", edgecolor="black", linewidth=0.5)

        ## plot the EEZ boundaries
        for country_code in countries:
            country_eez = eez_polygon[eez_polygon['ISO_TER1'] == country_code]
            # check if there are any polygons for the country
            if not country_eez.empty:
                country_eez.boundary.plot(ax=ax, edgecolor='#023D6B', linewidth=0.7)
                # Add ISO code text label
                # Compute a representative point within each polygon to place the text
                for _, row in country_eez.iterrows():
                    representative_point = row.geometry.representative_point()
                    ax.text(representative_point.x, representative_point.y, country_code, 
                            horizontalalignment='center', verticalalignment='center',
                            transform=ccrs.epsg(3035), fontsize=12, color='black')

        ## Final touches
        ax.set_aspect("equal")
        ax.set_xlabel("Easting (m, ETRS89/LAEA)")
        ax.set_ylabel("Northing (m, ETRS89/LAEA)")

        ## save the plot
        visualizations_dir = os.path.join(output_dir, "visualizations")
        if not os.path.exists(visualizations_dir):
            os.makedirs(visualizations_dir)

        plt.savefig(os.path.join(config_loader.get_path("output"), 'visualizations', 'bathymetry_and_wind_farms.png'), dpi=300)