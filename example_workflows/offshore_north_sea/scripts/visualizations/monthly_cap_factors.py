import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import json
import cartopy.crs as ccrs
from utils.config import ConfigLoader
from utils.raster_processing import RasterProcesser
import xarray as xr 
from scipy.stats import weibull_min
import luigi
from scripts.data_processing.extract_monthly_data import ExtractMonthlyData

class VisualizeMonthlyCapacityFactors(luigi.Task):
    def requires(self):
        return [ExtractMonthlyData()]

    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'capacity_factors_monthly.png'))

    def run(self):
       # Load vector data
        config_loader = ConfigLoader()
        data_path = config_loader.get_path("data")
        output_dir = config_loader.get_path("output")

        # Load the datasets
        file_name_mixed = "capacity_factor_data_1000m_depth.csv"
        file_name_fixed = "capacity_factor_data_50m_depth.csv"
        df_mixed = pd.read_csv(os.path.join(output_dir, "geodata", file_name_mixed))
        df_fixed = pd.read_csv(os.path.join(output_dir, "geodata", file_name_fixed))

        # Add scenario column
        df_mixed['scenario'] = '1000m_depth'
        df_fixed['scenario'] = '50m_depth'

        # Melt the dataframes to long format
        df_mixed_melted = df_mixed.melt(id_vars=['location', 'scenario', 'country'], var_name='month_year', value_name='capacity_factor')
        df_fixed_melted = df_fixed.melt(id_vars=['location', 'scenario', 'country'], var_name='month_year', value_name='capacity_factor')

        # Combine the dataframes
        df_combined = pd.concat([df_mixed_melted, df_fixed_melted], ignore_index=True)

        # Extract month and year from the 'month_year' column
        df_combined['month'] = df_combined['month_year'].apply(lambda x: x[:2])
        df_combined['year'] = df_combined['month_year'].apply(lambda x: x[3:])

        # Convert capacity_factor to numeric
        df_combined['capacity_factor'] = pd.to_numeric(df_combined['capacity_factor'], errors='coerce')

        # Convert capacity factor values to percentages
        df_combined['capacity_factor'] = df_combined['capacity_factor'] * 100

        # Map month abbreviations to month numbers for correct ordering
        month_map = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
            '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        df_combined['month'] = df_combined['month'].map(month_map)

        # Drop rows with NaN values in 'capacity_factor'
        df_combined.dropna(subset=['capacity_factor'], inplace=True)

        # Sort the dataframe by month number for plotting
        df_combined['month_num'] = df_combined['month'].apply(lambda x: list(month_map.values()).index(x) + 1)
        df_combined = df_combined.sort_values(['year', 'month_num'])

        # Specify the countries to plot
        countries = ['DEU', 'DNK', 'GBR', 'NOR']

        # Set up subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
        axes = axes.flatten()

        for idx, country in enumerate(countries):
            ########## PLOT THE ERA5 DATA ##########
            ax = axes[idx]
            country_data = df_combined[df_combined['country'] == country]

            # Calculate the mean capacity factor for each month and scenario
            monthly_means = country_data.groupby(['month_num', 'scenario'])['capacity_factor'].mean().unstack()

            # Plot each scenario for the country
            for scenario in monthly_means.columns:
                ax.plot(monthly_means.index, monthly_means[scenario], marker='o', linestyle='-', label=f"ERA5, {scenario}")

            ############ PLOT THE NEWA DATA ############
            # Load NEWA data and calculate monthly means
            newa_data_path = os.path.join(output_dir, 'simulations', 'NEWA_timeseries', country)
            newa_monthly_means = []

            if os.path.exists(newa_data_path):  # Check if the directory exists
                for year_file in os.listdir(newa_data_path):
                    if year_file.endswith('.json') and 'wind_power_newa_monthly_CF' in year_file:
                        with open(os.path.join(newa_data_path, year_file), 'r') as f:
                            data = json.load(f)
                            newa_monthly_means.append(data['monthly_capacity_factors'])

                if newa_monthly_means:  # Ensure there is data before proceeding
                    # Calculate the mean for each month across years
                    newa_monthly_means = np.mean(newa_monthly_means, axis=0) * 100
                    print(f"NEWA monthly means for {country}: {newa_monthly_means}")

                    # Plot the NEWA line, matching x-values with month numbers
                    ax.plot(range(1, 13), newa_monthly_means, marker='^', linestyle='-', linewidth=2, label='NEWA, uniform\npower density')  # Plot the NEWA data

            ax.set_title(f"{country}", fontsize=20)
            ax.set_xticks(monthly_means.index)
            ax.set_xticklabels([month_map[f'{i:02d}'] for i in monthly_means.index], rotation=45, fontsize=12)
            
            ax.set_yticks(ax.get_yticks())  # Ensure y-ticks are set
            ax.set_yticklabels(ax.get_yticks(), fontsize=12)
            # Set y-axis label only for the leftmost subplots (first and third)
            if idx in [0, 2]:
                ax.set_ylabel("Mean Capacity Factor (%)", fontsize=18)
        
            ax.set_xlim(1, 12)  # Set x-axis limits to remove white space
            ax.set_ylim(20, 60)
            ax.grid(True)
            if ax == axes[0]:
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, loc="lower left", ncol=2, fontsize=14)

        fig.tight_layout(rect=[0, 0, 1, 0.96])

        # Save the plot
        plt.savefig(os.path.join(output_dir, 'visualizations', 'capacity_factors_monthly.png'))
        plt.close()