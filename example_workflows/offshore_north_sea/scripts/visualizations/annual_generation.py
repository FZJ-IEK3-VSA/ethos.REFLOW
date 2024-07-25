import json
import matplotlib.pyplot as plt
import os
from utils.config import ConfigLoader
import luigi
import pandas as pd
import numpy as np
from scripts.simulations.simulations_luigi_task import PerformSimulations

class VisualizeAnnualGenerationByCountry(luigi.Task):
    def requires(self):
        # return [PerformSimulations()]
        return None
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'annual_generation_by_country.png'))
    
    def run(self):
        config_loader = ConfigLoader()
        output_dir = config_loader.get_path("output")    
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
        
        years = range(project_settings["start_year"], project_settings["end_year"] + 1)
        scenarios = ["1000m_depth", "50m_depth"]   

        plt.rcParams['axes.labelsize'] = 14  # Set font size for axis labels
        plt.rcParams['legend.fontsize'] = 12  # Set font size for legend
        plt.rcParams['xtick.labelsize'] = 12
        plt.rcParams['ytick.labelsize'] = 12
        
        # Define an earthy color palette
        earthy_colors = ['#8c510a', '#1aa675', '#f6e8c3', '#5ab4ac', '#01665e', '#543005', '#bf812d', '#dfc27d']

        # Creating a figure and axes for the subplots
        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(18, 7), sharey=True)

        # Country code to name mapping
        country_name_mapping = {
            "BEL": "Belgium",
            "FRA": "France",
            "SWE": "Sweden",
            "DEU": "Germany",
            "DNK": "Denmark",
            "NLD": "Netherlands",
            "NOR": "Norway",
            "GBR": "United Kingdom"
        }

        for ax, scenario in zip(axs, scenarios):
            df = pd.read_csv(os.path.join(output_dir, "geodata", f"turbine_placements_4326_{scenario}.csv"))

            data_by_country_year = df.groupby("country").agg({f"Generation_{year}_MWh": 'sum' for year in years})

            # Convert MWh to TWh
            data_by_country_year = data_by_country_year / 1e6

            # Prepare data for stacked area chart
            data_for_plotting = data_by_country_year.transpose()
            data_for_plotting.index = years  # Ensure years are integers

            # Extract generation data as a list of lists
            generation_data = data_for_plotting.transpose().values.tolist()

            # Extract labels for each country (keep the 3-letter codes for processing)
            country_codes = data_for_plotting.columns.tolist()

            # Plotting on the specific subplot axis
            ax.stackplot(years, generation_data, labels=country_codes, colors=earthy_colors, alpha=0.8)
            ax.set_xlim(years[0], years[-1])  # Remove white space by setting x-axis limits
            ax.set_xticks(years)  # Mark every year on the x-axis
            ax.set_title(f'{scenario.replace("_", " ").title()} Scenario', fontsize=16)
            ax.set_xlabel('Year')
            if ax is axs[0]:  # Only add ylabel to the first subplot to avoid repetition
                ax.set_ylabel('Generation (TWh)')  # Adjust label for TWh

            # open the scenario report file
            with open(os.path.join(output_dir, f'report_{scenario}.json'), 'r') as file:
                scenario_report = json.load(file)

            # calculate mean, min and max generation for each country
            for country in country_codes:
                country_data = {
                    'mean_generation': data_by_country_year.loc[country].mean(),
                    'max_generation': data_by_country_year.loc[country].max(),
                    'min_generation': data_by_country_year.loc[country].min()
                }
                if country in scenario_report:
                    scenario_report[country].update(country_data)
                else:
                    scenario_report[country] = country_data

            # save the updated scenario report
            with open(os.path.join(output_dir, f'report_{scenario}.json'), 'w') as file:
                json.dump(scenario_report, file, indent=4)

            # extract the y positions for the country code labels
            y_positions = {}

            # iterate through the DataFrame to fill the dictionary with the y-positions
            for country in data_by_country_year.index:
                y_positions[country] = data_by_country_year.loc[country, "Generation_2014_MWh"]

            # Initialize a variable to keep track of the cumulative sum
            cumulative_sum = 0

            for country, generation in y_positions.items():
                # Calculate the new value as half of the current generation + the cumulative sum so far
                new_value = cumulative_sum + (generation / 2.0)
                # Update the cumulative sum to include the current country's full generation
                cumulative_sum += generation
                # Update the dictionary with the new value
                y_positions[country] = new_value

            # Add country code labels to the right of the plots
            for code, y_pos in zip(country_codes, y_positions.values()):
                full_label = country_name_mapping.get(code, code)
                if scenario == "1000m_depth":
                    if full_label in ["Belgium", "France"]:
                        continue
                    else:
                        ax.text(years[1] - 0.85, y_pos, full_label, va='center', ha='left', fontsize=10, color='black', fontweight='bold')
                elif scenario == "50m_depth":
                    if full_label in ["Belgium", "France", "Sweden"]:
                        continue
                    else:
                        ax.text(years[1] - 0.85, y_pos, full_label, va='center', ha='left', fontsize=10, color='black', fontweight='bold')
        
        handles, labels = ax.get_legend_handles_labels()

        # Filter out 'BEL' and 'FRA' from the legend and replace with full names
        filtered_handles = []
        filtered_labels = []
        for handle, label in zip(handles, labels):
            if label not in ['BEL', 'FRA']:
                filtered_handles.append(handle)
                filtered_labels.append(country_name_mapping.get(label, label))

        # Add a legend outside the rightmost subplot
        axs[1].legend(filtered_handles, filtered_labels, loc='upper left', bbox_to_anchor=(0.7, 1), title="Countries", title_fontsize=14)

        plt.tight_layout(rect=[0, 0, 0.9, 1])  # Adjust the layout to make room for the legend

        plt.savefig(os.path.join(output_dir, 'visualizations', 'annual_generation_by_country.png'), dpi=300)
        plt.close()
