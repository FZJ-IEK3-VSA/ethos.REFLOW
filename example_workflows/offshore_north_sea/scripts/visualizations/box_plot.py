import json
import matplotlib.pyplot as plt
import os
from utils.config import ConfigLoader
import luigi
import pandas as pd
import numpy as np
import seaborn as sns

class VisualizeBoxPlot(luigi.Task):
    def requires(self):
        return None
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'visualizations', 'capacity_monthly_box.png'))
    
    def run(self):
        config_loader = ConfigLoader()
        output_dir = config_loader.get_path("output")   
        data_dir = config_loader.get_path("data") 
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
        
        # Load the datasets
        file_name_mixed = "capacity_factor_data.csv"
        file_name_fixed = "capacity_factor_data_50m.csv"
        df_mixed = pd.read_csv(os.path.join(output_dir, file_name_mixed))
        df_fixed = pd.read_csv(os.path.join(output_dir, file_name_fixed))

        # Add scenario column
        df_mixed['scenario'] = 'Mixed Technology'
        df_fixed['scenario'] = 'Fixed Foundation'

        # Melt the dataframes to long format
        df_mixed_melted = df_mixed.melt(id_vars=['location', 'scenario'], var_name='month_year', value_name='capacity_factor')
        df_fixed_melted = df_fixed.melt(id_vars=['location', 'scenario'], var_name='month_year', value_name='capacity_factor')

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
        df_combined = df_combined.sort_values('month_num')

        # Create the split violin plot
        plt.figure(figsize=(16, 6))
        sns.violinplot(x='month', y='capacity_factor', hue='scenario', data=df_combined, split=True, order=list(month_map.values()), width=0.8)

        # Set plot labels and title
        plt.xlabel('Month', fontsize=14)
        plt.ylabel('Capacity Factor [ % ]', fontsize=14)
        plt.title('Distribution of Capacity Factors by Month (2013-2023)', fontsize=16)
        plt.grid(True)

        # Add legend
        plt.legend(title='Scenario')

        # Adjust layout for better spacing
        plt.tight_layout()

        # Save the plot to a file
        output_path = self.output().path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        #plt.show()
        plt.savefig(output_path)
        plt.close()