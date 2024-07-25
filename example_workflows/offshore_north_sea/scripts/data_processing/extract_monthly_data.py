from utils.config import ConfigLoader
from scripts.simulations.simulations_luigi_task import PerformSimulations
import luigi
import xarray as xr
import pandas as pd
import numpy as np
import os
import json

class ExtractMonthlyData(luigi.Task):
    """
    Extracts monthly capacity factor data for each turbine from the output netcdf files.
    """

    def requires(self):
        return [PerformSimulations()]
    
    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'geodata', 'capacity_factor_data_50m_depth.csv'))
    
    def run(self):
        """
        Main run method for the task.
        """
        #### directory annd variables management ####
        config_loader = ConfigLoader()

        log_file = os.path.join(config_loader.get_path("output"), 'logs', 'ProcessExclusionsData.log')
        logger = config_loader.setup_task_logging('ProcessRegionBuffers', log_file)
        logger.info("Starting ProcessExclusionsData task")

        output_dir = config_loader.get_path("output")
        
        scenarios = ["1000m_depth", "50m_depth"]

        def extract_monthly_data(ds):
            # Ensure time is in a datetime format
            ds['time'] = pd.to_datetime(ds['time'].values)
            
            # Extract capacity factor data and add month and year columns
            df = ds['capacity_factor'].to_dataframe().reset_index()
            df['month'] = df['time'].dt.month
            df['year'] = df['time'].dt.year
            
            # Group by year, month, and location, then calculate the mean capacity factor for each group
            monthly_mean = df.groupby(['year', 'month', 'location'])['capacity_factor'].mean().reset_index()
            
            return monthly_mean

        for scenario in scenarios:
            # List of file paths (one per year)
            file_paths = [f'wind_power_era5_{year}_{scenario}.nc' for year in range(2013, 2024)]

            # Initialize a list to collect all data points
            all_data = []

            # Process each file
            for file_path in file_paths:
                logger.info(f'Processing file: {file_path}')
                ds = xr.open_dataset(os.path.join(output_dir, "simulations", file_path))
                yearly_data = extract_monthly_data(ds)
                all_data.append(yearly_data)

            logger.info('All files processed. Concatenating data...')    
            all_data = pd.concat(all_data, ignore_index=True)

            # Pivot the data so that each location has its own row and each column is a month-year combination
            pivoted_data = all_data.pivot_table(index='location', columns=['year', 'month'], values='capacity_factor')

            # Flatten the MultiIndex columns
            pivoted_data.columns = [f'{month:02d}-{year}' for year, month in pivoted_data.columns]

            # Reset index to make 'location' a column
            pivoted_data.reset_index(inplace=True)

            # Reduce precision of floats
            pivoted_data = pivoted_data.round(4)

            # Save the detailed data points to a CSV file with efficient data types
            pivoted_data.to_csv(os.path.join(output_dir, 'geodata', f'capacity_factor_data_{scenario}.csv'), index=False, float_format='%.4f')
