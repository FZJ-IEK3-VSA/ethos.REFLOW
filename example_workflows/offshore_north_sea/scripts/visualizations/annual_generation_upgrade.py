import json
import matplotlib.pyplot as plt
import os
from utils.config import ConfigLoader
import luigi
import pandas as pd
import numpy as np
from scripts.simulations.simulations_luigi_task import PerformSimulations

class VisualizeAnnualGenerationByCountryNew(luigi.Task):
    def requires(self):
        return [PerformSimulations()]
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'annual_generation_update.png'))
    
    def run(self):
        config_loader = ConfigLoader()
        output_dir = config_loader.get_path("output")    
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
        
        years = list(range(2014, 2019))  # Limit to 2014-2018
        scenarios = ["1000m_depth", "50m_depth"]

        plt.rcParams.update({
        'axes.labelsize': 18,   # Axis label size
        'axes.titlesize': 20,   # Axis title size
        'xtick.labelsize': 14,  # X-axis tick label size
        'ytick.labelsize': 14,  # Y-axis tick label size
        'legend.fontsize': 16,   # Legend font size
        'legend.title_fontsize': 18,  # Legend title font size
        })
        
        country_codes_fixed = ["BEL", "FRA", "SWE", "DEU", "DNK", "NLD", "NOR", "GBR"]
        earthy_colors = ['#8c510a', '#1aa675', '#f6e8c3', '#5ab4ac', '#01665e', '#543005', '#bf812d', '#dfc27d']

        # Ensure axs is a 2D array regardless of the subplot configuration
        fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(18, 14), sharey=True, squeeze=False)
        
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

        # Extract the y positions for the country code labels
        y_positions = {}
        
        # First row: Original scenarios
        for col_idx, scenario in enumerate(scenarios):
            ax = axs[0, col_idx]  # Select individual Axes in the first row
            df = pd.read_csv(os.path.join(output_dir, "geodata", f"turbine_placements_4326_{scenario}.csv"))
            data_by_country_year = df.groupby("country").agg({f"AEY_{year}_MWh": 'sum' for year in years}) / 1e6  # Convert to TWh

            # Ensure we only have data for the specified years
            #data_for_plotting = data_by_country_year.reindex(columns=[f"Generation_{year}_MWh" for year in years]).transpose()
            data_for_plotting = data_by_country_year.reindex(country_codes_fixed).transpose()
            data_for_plotting.index = years
            generation_data = data_for_plotting.transpose().values.tolist()

            # stackplot and set axis properties
            ax.stackplot(years, generation_data, labels=country_codes_fixed, colors=earthy_colors, alpha=0.8)
            ax.set_xlim(years[0], years[-1])
            ax.set_xticks(years)
            ax.set_title(f'ERA5, explicit placement {scenario.replace("_", " ").title()}')
            if col_idx == 0:
                ax.set_ylabel('Generation (TWh)')

            print("Data for plotting preview:", data_for_plotting.head())  # Preview data structure
           
            # Calculate y positions for each country
            cumulative_sum = 0
            for country in data_for_plotting.columns:
                print("Accessing year:", years[0], "and country:", country)  # Check specific access values
                generation = data_for_plotting.loc[years[0], country]
                y_positions[country] = cumulative_sum + (generation / 2.0)
                cumulative_sum += generation

            # Add country code labels to the right of the plots
            for code, y_pos in zip(country_codes_fixed, y_positions.values()):
                full_label = country_name_mapping.get(code, code)
                if scenario == "1000m_depth":
                    if full_label not in ["Belgium", "France"]:
                        ax.text(years[0] + 0.01, y_pos, full_label, va='center', ha='left', fontsize=11, color='black', weight='bold')
                elif scenario == "50m_depth":
                    if full_label not in ["Belgium", "France", "Sweden", "Norway"]:
                        ax.text(years[0] + 0.01, y_pos, full_label, va='center', ha='left', fontsize=11, color='black', weight='bold')

        # Second row: New scenarios from JSON file
        report_path = os.path.join(output_dir, "report_NEWA_sim.json")
        with open(report_path, 'r') as f:
            new_sim_data = json.load(f)

        for col_idx, scenario in enumerate(scenarios):
            ax = axs[1, col_idx]  # Select individual Axes in the second row
            data_by_country_year = pd.DataFrame(index=years)

            for country, values in new_sim_data.items():
                if country == "North_Sea":  # Skip aggregate data
                    continue
                scenario_data = values["Scenarios"].get(scenario, {})
                yearly_generation = [scenario_data.get(f"Annual_power_yield_{year}", 0) for year in years]
                data_by_country_year[country] = yearly_generation

            # Debugging: Check structure and contents of `data_by_country_year`
            print((f"Index of data_for_plotting: {data_for_plotting.index}"))
            print(f"Shape of generation_data for plotting: {data_by_country_year.shape}")

            # Ensure we only have data for the specified years
            data_for_plotting = data_by_country_year[country_codes_fixed].transpose()
            # Adjust data_for_plotting to match `years`
            generation_data = data_for_plotting.values.tolist()
            #country_codes = data_for_plotting.index.tolist()

            ax.stackplot(years, generation_data, labels=country_codes_fixed, colors=earthy_colors, alpha=0.8)
            ax.set_xlim(years[0], years[-1])
            ax.set_xticks(years)
            ax.set_title(f'NEWA, uniform power density: {scenario.replace("_", " ").title()}')
            if col_idx == 0:
                ax.set_ylabel('Generation (TWh)')

            # Calculate y positions and add labels for the second row
            cumulative_sum = 0
            for country in data_for_plotting.index:
                generation = data_for_plotting.loc[country, years[0]]
                y_positions[country] = cumulative_sum + (generation / 2.0)
                cumulative_sum += generation

            for code, y_pos in zip(country_codes_fixed, y_positions.values()):
                full_label = country_name_mapping.get(code, code)
                if scenario == "1000m_depth":
                    if full_label not in ["Belgium", "France"]:
                        ax.text(years[0] + 0.01, y_pos, full_label, va='center', ha='left', fontsize=11, color='black', weight='bold')
                elif scenario == "50m_depth":
                    if full_label not in ["Belgium", "France", "Sweden", "Norway"]:
                        ax.text(years[0] + 0.01, y_pos, full_label, va='center', ha='left', fontsize=11, color='black', weight='bold')

        # Adjust legend for final plot
        handles, labels = axs[0, 1].get_legend_handles_labels()
        filtered_handles, filtered_labels = [], []
        for handle, label in zip(handles, labels):
            if label not in ['BEL', 'FRA']:
                filtered_handles.append(handle)
                filtered_labels.append(country_name_mapping.get(label, label))

        axs[0, 1].legend(filtered_handles, filtered_labels, loc='upper left', bbox_to_anchor=(1.0, 1), title="Countries")
        
        plt.tight_layout(rect=[0, 0, 0.9, 1])
        plt.savefig(os.path.join(output_dir, 'visualizations', 'annual_generation_update.png'), dpi=300)
        plt.close()