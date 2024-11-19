import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import json
from scipy.stats import weibull_min
import luigi
from utils.config import ConfigLoader
from scripts.data_processing.extract_monthly_data import ExtractMonthlyData
# from utils.reskit_code import PowerCurve

class VisualizeWeibullPlot(luigi.Task):
    def requires(self):
        return [ExtractMonthlyData()]

    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'weibull_plot.png'))

    def run(self):
        # Load paths and project settings
        config_loader = ConfigLoader()
        data_path = config_loader.get_path("data")
        output_dir = config_loader.get_path("output")
        project_settings_path = config_loader.get_path("settings", "project_settings")
        
        with open(project_settings_path, 'r') as f:
            project_settings = json.load(f)

        years = list(range(project_settings["start_year"], project_settings["end_year"] + 1))
        countries = ["DEU", "DNK", "GBR", "NOR"]

        # Prepare data structures to hold mean values for each country
        country_data_means = {country: {'scale': [], 'shape': [], 'mean_wind_speed': [], 'wind_speed_distribution': []} for country in countries}

        # Load data, compute mean parameters for each country over the years
        for country in countries:
            yearly_distributions = []
            for year in years:
                country_data_path = os.path.join(output_dir, "simulations", "NEWA_timeseries", country, f"wind_power_newa_{year}.json")
                with open(country_data_path, 'r') as f:
                    yearly_data = json.load(f)

                # Append values to respective lists
                country_data_means[country]['scale'].append(yearly_data["weibull_scale"])
                country_data_means[country]['shape'].append(yearly_data["weibull_shape"])
                country_data_means[country]['mean_wind_speed'].append(yearly_data["mean_wind_speed"])
                yearly_distributions.append(yearly_data["wind_speed_distribution"])

            # Calculate mean distribution across years for each bin
            country_data_means[country]['scale'] = np.mean(country_data_means[country]['scale'])
            country_data_means[country]['shape'] = np.mean(country_data_means[country]['shape'])
            country_data_means[country]['mean_wind_speed'] = np.mean(country_data_means[country]['mean_wind_speed'])
            country_data_means[country]['wind_speed_distribution'] = np.mean(yearly_distributions, axis=0)

        # Instantiate the PowerCurve with hardcoded capacity and rotor diameter
        pc = PowerCurve.from_capacity_and_rotor_diam(15, 143)
        print("Wind Speeds:", pc.wind_speed)
        print("Capacity Factors:", pc.capacity_factor)

        # Plot Weibull distribution and histogram for each country
        fig, axs = plt.subplots(2, 2, figsize=(12, 10), sharey=True)
        axs = axs.flatten()  # Flatten for easy indexing

        for i, country in enumerate(countries):
            wind_speeds = country_data_means[country]['wind_speed_distribution']
            shape = country_data_means[country]['shape']
            scale = country_data_means[country]['scale']

            # Define bin centers for plotting
            bin_centers = np.linspace(0, 25, len(wind_speeds))

            # Plot histogram of the wind speed distribution
            ax = axs[i]
            ax.bar(bin_centers, wind_speeds, width=1.0, color='skyblue', alpha=0.6, label='Wind Speed Histogram')

            # Weibull PDF
            x = np.linspace(0, 25, 100)
            weibull_pdf = weibull_min.pdf(x, shape, scale=scale)
            ax.plot(x, weibull_pdf, color='orange', label='Weibull Fit')

            # Create a secondary y-axis for the power curve
            ax2 = ax.twinx()
            power_output = pc.capacity_factor * 15  # Convert capacity factor to MW output
            ax2.plot(pc.wind_speed, power_output, color='green', label='Power Curve')

            ## power curve
            ax.set_title(f"Wind Speed Distribution for {country}")
            ax.set_xlabel("Wind Speed (m/s)")
            ax.set_ylabel("Probability Density")
            ax2.set_ylabel("Power Output (MW)")
            ax2.set_ylim(0, 16)
            ax.legend(loc='upper right')
            ax2.legend(loc='upper left')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(self.output().path)
        plt.close()