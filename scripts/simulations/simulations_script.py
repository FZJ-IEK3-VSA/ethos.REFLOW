import reskit as rk
import os
from reskit.wind.workflows.wind_workflow_manager import WindWorkflowManager
from reskit import weather as rk_weather
import numpy as np
import pandas as pd
import xarray as xr
import json
import time
from utils.config import ConfigLoader

############ directory management and global variables ############
config_loader = ConfigLoader()
output_dir = config_loader.get_path("output")
placements_path = os.path.join(output_dir, "geodata", "turbine_placements_4326.csv")
placements = pd.read_csv(placements_path)
met_data_dir = config_loader.get_path("data", "met_data")
newa_100m_path = os.path.join(met_data_dir, "newa_wind_speed_mean_100m.tif")
report_path = os.path.join(output_dir, "report.json")

project_settings_path = config_loader.get_path("settings", "project_settings")

with open(project_settings_path) as file:
    project_settings = json.load(file)

# configure logging
log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformSimulations.log')
logger = config_loader.setup_task_logging('PerformSimulations', log_file)
logger.info("Starting PerformSimulations task")  

## set the year
years = range(project_settings["start_year"], project_settings["end_year"] + 1)

##########################################################################################
############################ DEFINE THE RESKIT WORKFLOW ##############################

def north_sea_offshore_wind_sim(
    placements,
    era5_path,
    newa_100m_path,
    output_netcdf_path=os.path.join(output_dir, "wind_power_era5.nc"),
    output_variables=None
):
    """
    Simulates offshore wind generation using NASA's ERA5 database [1].

    Parameters
    ----------
    placements : pandas Dataframe
        A Dataframe object with the parameters needed by the simulation.
    newa_100m_path : str
        Path to the New European Wind Atlas data.
    output_netcdf_path : str, optional
        Path to a directory to put the output files, by default None
    output_variables : str, optional
        Restrict the output variables to these variables, by default None

    Returns
    -------
    xarray.Dataset
        A xarray dataset including all the output variables you defined as your output variables.

    Sources
    ------
    [1] European Centre for Medium-Range Weather Forecasts. (2024). ERA5 dataset. https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5.

    """
    wf = WindWorkflowManager(placements)

    wf.read(
        variables=[
            "elevated_wind_speed",
            "surface_pressure",
            "surface_air_temperature",
            "boundary_layer_height"
        ],
        source_type="ERA5",
        source=era5_path,
        set_time_index=True,
        verbose=False,
    )

    wf.adjust_variable_to_long_run_average(
        variable='elevated_wind_speed',
        source_long_run_average=rk_weather.Era5Source.LONG_RUN_AVERAGE_WINDSPEED,
        real_long_run_average=newa_100m_path,
        spatial_interpolation="average"
    )

    ## set roughness for the sea
    wf.set_roughness(0.0002)

    ## use log law to project wind speeds to hub height
    wf.logarithmic_projection_of_wind_speeds_to_hub_height(
        consider_boundary_layer_height=True
    )

    wf.apply_air_density_correction_to_wind_speeds()
    
    # gaussian convolution of the power curve to account for statistical events in wind speed
    wf.convolute_power_curves(
        scaling=0.01,  # standard deviation of gaussian equals scaling*v + base
        base=0.00,  # values are derived from validation with real wind turbine data
    )

    wf.simulate()

    return wf.to_xarray(
        output_netcdf_path=output_netcdf_path, output_variables=None
    )


##########################################################################################
############################ DEFINE THE FUNCTION TO CALCULATE FLH ##############################
## based on Stanely Risch work

def calculate_flh_generation(xds, placements, turbine_availablilty, array_efficiency, year):
    '''
    Calculate Full Load Hours for wind turbine placements based on capacity factors.
    
    Parameters:
    -----------
    xds : xarray.Dataset
        The wind power production data. Must be hourly time series data.
    placements : pandas DataFrame 
        The placements of the wind turbines.
    year : int
        The year for which to calculate the Full Load Hours.

    Returns:
    --------
    placements: pandas DataFrame
        A DataFrame with the Full Load Hours for each placement.
    '''
    placements[f"FLH_{year}"] = 0.0
    placements[f"Generation_{year}_MWh"] = 0.0

    total_locations = len(xds.location)

    ## calculate the total loss factor from the turbine availability and array0 efficiency
    total_loss_factor = turbine_availablilty * array_efficiency

    for index, location in enumerate(xds.location):
        if index % 1000 == 0:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            logger.info(f"Processing locations {index}-{min(index+999, total_locations-1)} started at: {current_time}")
            batch_start_time = time.time()

        # find the corresponding placement and update the FLH
        match_index = placements.ID == xds.ID[location].values

        # calculate the FLH for each placement
        flh = pd.Series(xds.capacity_factor[:, location]).sum()

        # update the FLH for the placement (including the loss factor)
        placements.loc[match_index, f"FLH_{year}"] = flh #* total_loss_factor

        # Calculate the generation for each turbine, Generation = FLH * Capacity
        placements.loc[match_index, f"Generation_{year}_MWh"] = (flh * placements.loc[match_index, 'capacity']) / 1000

        if (index + 1) % 1000 == 0 or index == total_locations - 1: # After completing each batch or the last location
            batch_time = time.time() - batch_start_time
            logger.info(f"Batch {index-999}-{index} processed in {batch_time:.2f} seconds.")

            # Estimate remaining time
            locations_left = total_locations - (index + 1)
            batches_left = locations_left / 1000
            estimated_time_left = batches_left * batch_time
            logger.info(f"Estimated time left: {estimated_time_left:.2f} seconds.")

    logger.info("All locations processed.")

    return placements

########################################################################################
########################### RUN THE SIMULATION  #########################################

logger.info("Running the simulation...")
output_netcdf_directory = os.path.join(output_dir, "simulations")
# make sure that the output directory exists
if not os.path.exists(output_netcdf_directory):
    os.makedirs(output_netcdf_directory)

for year in years:
    logger.info(f"Simulating the year {year}...")
    # run the simulation
    era5_path = os.path.join(met_data_dir, "ERA5", "processed", f"{year}")
    xds = north_sea_offshore_wind_sim(placements, era5_path, newa_100m_path, output_netcdf_path=os.path.join(output_netcdf_directory, f"wind_power_era5_{year}.nc"))

#######################################################################################
############################# CALCULATE FLH  #########################################

for year in years:
    # in case this was run before, we load up the file instead of using the xds variable directly
    xds = xr.open_dataset(os.path.join(output_netcdf_directory, f"wind_power_era5_{year}.nc"))

    ## calculate the FLH and Generation
    logger.info("Calculating the Full Load Hours and annual Generation per turbine...")
    placements = calculate_flh_generation(xds, placements, turbine_availablilty=0.97, array_efficiency=0.9, year=year)

    # save the placements
    placements.to_csv(os.path.join(output_dir, "geodata", "turbine_placements_4326.csv"), index=False)

    # load the placements
    placements = pd.read_csv(os.path.join(output_dir, "geodata", "turbine_placements_4326.csv"))

    # calculate the total generation
    total_generation = placements[f"Generation_{year}_MWh"].sum() / 1e6

    # calculate the mean capacity factor
    mean_capacity_factor = (placements[f"FLH_{year}"].mean() / 8760) * 100

    # add the results to the output report
    with open(report_path, "r") as file:
        report = json.load(file)

    # add the new columns
    report[f"Total_Generation_{year}_TWh"] = total_generation
    report[f"Mean_Capacity_Factor_{year}"] = mean_capacity_factor

    # Save the updated report back to report.json
    with open(report_path, 'w') as file:
        json.dump(report, file, indent=4)

# calculate the OVERALL mean CF and generation - do this outside the main loop in case certain years are calculated separately
        
# initialize the sums
total_generation_sum = 0
mean_capacity_factor_sum = 0
total_generation_count = 0
mean_capacity_factor_count = 0

# add the results to the output report
with open(report_path, "r") as file:
    report = json.load(file)

# Iterate through report keys and sum values for matching patterns
for key, value in report.items():
    if "Total_Generation" in key and "Overall_Mean_Total_Generation_TWh" not in key:
        total_generation_sum += value
        total_generation_count += 1
    elif "Mean_Capacity_Factor" in key and "Overall_Mean_Capacity_Factor" not in key:
        mean_capacity_factor_sum += value
        mean_capacity_factor_count += 1

# Calculate the mean values
if total_generation_count > 0:
    report["Overall_Mean_Total_Generation_TWh"] = total_generation_sum / total_generation_count
if mean_capacity_factor_count > 0:
    report["Overall_Mean_Capacity_Factor"] = mean_capacity_factor_sum / mean_capacity_factor_count

logger.info("Results saved to the report.json file.")

# Save the updated report back to report.json
with open(report_path, 'w') as file:
    json.dump(report, file, indent=4)