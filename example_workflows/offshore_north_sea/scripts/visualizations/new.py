import json
import matplotlib.pyplot as plt
import os
from utils.config import ConfigLoader
import luigi
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

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
        file_name_mixed = "capacity_factor_data_1000m_depth.csv"
        #file_name_fixed = "capacity_factor_data_50m.csv"
        df_mixed = pd.read_csv(os.path.join(output_dir, "geodata", file_name_mixed))
        #df_fixed = pd.read_csv(os.path.join(output_dir, file_name_fixed))

        # Add scenario column
        df_mixed['scenario'] = 'Mixed Technology'
        #df_fixed['scenario'] = 'Fixed Foundation'

        # Melt the dataframes to long format
        df_mixed_melted = df_mixed.melt(id_vars=['location', 'scenario'], var_name='month_year', value_name='capacity_factor')
       # df_fixed_melted = df_fixed.melt(id_vars=['location', 'scenario'], var_name='month_year', value_name='capacity_factor')

        # Combine the dataframes
        #df_combined = pd.concat([df_mixed_melted, df_fixed_melted], ignore_index=True)

        # Extract month and year from the 'month_year' column
        df_combined['month'] = df_mixed['month_year'].apply(lambda x: x[:2])
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

        # Filter data for the heatmap to include only the years 2019-2023
        df_heatmap = df_combined[df_combined['year'].astype(int).between(2019, 2023)].copy()

        # Aggregate and bin capacity factors for the heatmap
        def aggregate_and_bin_capacity_factors(df):
            bins = np.arange(0, 110, 10)  # 0-100% capacity factor in 10% bins
            bin_labels = [f'{edge}%' for edge in bins[:-1]]
            monthly_binned_percentages = pd.DataFrame(columns=bin_labels)
            df['month_year'] = df['year'] + '-' + df['month']

            for month_year, group in df.groupby('month_year'):
                flattened_data = group['capacity_factor'].dropna()
                if flattened_data.empty:
                    continue
                binned_counts, _ = np.histogram(flattened_data, bins=bins)
                binned_percentages = (binned_counts / flattened_data.size) * 100
                temp_df = pd.DataFrame([binned_percentages], columns=bin_labels, index=[month_year])
                monthly_binned_percentages = pd.concat([monthly_binned_percentages, temp_df])

            return monthly_binned_percentages

        # Create the heatmap data
        binned_capacity_factors = aggregate_and_bin_capacity_factors(df_heatmap)
        binned_capacity_factors = binned_capacity_factors.reset_index().rename(columns={'index': 'Month-Year'})
        binned_capacity_factors['Month-Year'] = pd.to_datetime(binned_capacity_factors['Month-Year'], format='%Y-%b')
        binned_capacity_factors = binned_capacity_factors.sort_values('Month-Year')
        binned_capacity_factors.set_index('Month-Year', inplace=True)
        binned_capacity_factors = binned_capacity_factors.transpose()

        # Create the figure and the subplots
        fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(16, 12), gridspec_kw={'height_ratios': [1, 2]})

        # Plot the heatmap
        ax1 = axes[0]
        end_color = '#023D6B'  # Dark blue color
        cmap = LinearSegmentedColormap.from_list('custom_cmap', ['white', end_color])
        sns.heatmap(binned_capacity_factors, cmap=cmap, ax=ax1, annot=False, fmt=".1f", 
                    cbar_kws={
                        'label': '', 
                        'location': 'top', 
                        'orientation': 'horizontal',
                        'shrink': 0.25,
                        'anchor': (1.0, -0.5),
                        'ticks': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],  # Adjusted ticks
                        'format': FuncFormatter(lambda x, pos: f'{x:.0f}%'),
                        'aspect': 15,
                    },
                    xticklabels=True,
                    yticklabels=True,
                    vmax=80
                    )
        ax1.set_ylabel("Capacity Factor (%)")
        ax1.invert_yaxis()

        # Add year labels
        df_dates = binned_capacity_factors.columns.to_series()
        year_change_positions = [i for i in range(1, len(df_dates)) if df_dates.iloc[i].year != df_dates.iloc[i-1].year]
        year_labels = [df_dates.iloc[pos].strftime('%Y') for pos in year_change_positions]

        # Create month initials for x-ticks
        month_initials = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
        xtick_labels = []
        for year in range(2019, 2024):
            xtick_labels.extend(month_initials)

        # Shift the x-tick positions slightly to the right for centering
        xtick_positions = np.arange(len(xtick_labels)) + 0.5

        ax1.set_xticks(xtick_positions)
        ax1.set_xticklabels(xtick_labels, rotation=0)
        
        # Add vertical lines and year labels
        for pos in year_change_positions:
            ax1.axvline(x=pos * 12, color='grey', linestyle='-', lw=0.5, alpha=0.7)
        for pos, label in zip([pos * 12 for pos in year_change_positions], year_labels):
            ax1.text(pos, len(binned_capacity_factors) + 0.5, label, ha='center', fontsize=12)

        # Plot the split violin plot
        ax2 = axes[1]
        sns.violinplot(x='month', y='capacity_factor', hue='scenario', data=df_combined, split=True, order=list(month_map.values()), width=0.8, ax=ax2)
        ax2.set_xlabel('Month', fontsize=14)
        ax2.set_ylabel('Capacity Factor [ % ]', fontsize=14)
        ax2.legend(title='Scenario', loc='upper right')
        ax2.grid(True)

        plt.tight_layout()

        # Save the combined plot to a file
        output_path = self.output().path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()