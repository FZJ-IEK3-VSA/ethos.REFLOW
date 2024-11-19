import math
import os
import numpy as np
import xarray as xr
import scipy.stats as stats
from scipy.interpolate import splrep, splev
from scipy.stats import exponweib, norm
from scipy.special import gamma
import json
from utils.config import ConfigLoader
import argparse 
import pandas as pd
## import necessary functions from reskit codebase due to cluster installation problems
from utils.reskit_code import calculate_weibull_params, apply_logarithmic_profile_projection
from utils.synthetic_power_curve import SyntheticPowerCurve

############################################################################################
# get the arguments
parser = argparse.ArgumentParser(description='Run the NEWA simulations')
parser.add_argument('--country', type=str, help='The countries for which to run the simulations')

country = parser.parse_args().country

############ directory management and global variables ############
config_loader = ConfigLoader()
output_dir = config_loader.get_path("output")

met_data_dir = config_loader.get_path("data", "met_data")

project_settings_path = config_loader.get_path("settings", "project_settings")

with open(project_settings_path) as file:
    project_settings = json.load(file)

countries = project_settings["countries"]

# configure logging
log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformNEWASimulations.log')
logger = config_loader.setup_task_logging('PerformNEWASimulations', log_file)
logger.info("Starting PerformNEWASimulations task")  

exclusions_settings_path = config_loader.get_path("settings", "exclusions_settings")
with open(exclusions_settings_path, 'r') as file:
    exclusions_settings = json.load(file)

technology_settings_path = config_loader.get_path("settings", "technologies")
with open(technology_settings_path, 'r') as file:
    technology_settings = json.load(file)

scenarios = ["1000m_depth", "50m_depth"]

## set the year
years = [2014, 2015, 2016, 2017, 2018]

##########################################################################################
############################ DEFINE THE RESKIT WORKFLOW ##############################
# Example input data of wind speed to capacity factor pairs for the synthetic power curve
input_data = [
    (8.0, 0.4566), (8.5, 0.5023), (9.0, 0.5403), (9.5, 0.5860),
    (10.0, 0.6240), (10.5, 0.6545), (11.0, 0.6773), (11.5, 0.7141),
    (12.0, 0.7509), (12.5, 0.7877), (13.0, 0.8245), (13.5, 0.8612),
    (14.0, 0.8980), (14.5, 0.9348), (15.0, 0.9716), (15.5, 1.0)
]

def north_sea_offshore_wind_simplified_sim(
    newa_100m_path,
    year,
    output_json_path=os.path.join(output_dir, "wind_power_newa.json")
):
    """
    Simulates offshore wind generation using the New European Wind Atlas data [1].

    Parameters
    ----------
    newa_100m_path : str
        Path to the New European Wind Atlas data at 100 m.
    year: int
        Year for which to run the simulation.
    output_json_path : str, optional
        Path to a directory to put the output files, by default None
    """

    capacity = technology_settings["wind"]["capacity"] 
    rotor_diam = technology_settings["wind"]["rotor_diameter"]
    cutin = technology_settings["wind"]["cut_in_wind_speed"]
    cutout = technology_settings["wind"]["cut_out_wind_speed"]
    hub_height = technology_settings["wind"]["hub_height"]

    # load the NEWA datasets
    wind_speed = xr.open_dataset(newa_100m_path)

    wind_speed = wind_speed.squeeze("height")

    logger.info("Resampling NEWA data to hourly intervals...")
    # Resample the original NEWA data to hourly frequency
    wind_speed = wind_speed.resample(time="1h").mean()

    #logger.info(wind_speed_100m_hourly.dims)
    logger.info(wind_speed.dims)

     # Define turbine parameters
    capacity = capacity / 1000  # Convert to MW

    logger.info(f"Interpolating wind speeds to {hub_height} m...")

    # Use the logarithmic profile projection for interpolation to hub height
    wind_speed_hub = xr.apply_ufunc(
        apply_logarithmic_profile_projection,
        wind_speed,  # Measured wind speed
        100,  # Measured height
        hub_height,  # Target height
        0.0002,  # Roughness
        kwargs={'displacement': 0, 'stability': 0},
        vectorize=True
    )

    logger.info("Calculating Weibull parameters...")
    # Calculate Weibull parameters for the interpolated wind speeds
    shape, scale = calculate_weibull_params(wind_speed_hub["WS"].values.flatten())
    logger.info(f"Weibull shape: {shape}, Scale: {scale}")

    # Calculate mean wind speed across all times and locations
    mean_wind_speed = wind_speed_hub["WS"].mean().item()

    logger.info(f"Mean wind speed: {mean_wind_speed}")

    logger.info("Synthesizing the power curve..")
    # Generate the synthetic power curve
    pc = SyntheticPowerCurve(
        specificCapacity=None, 
        capacity=capacity, 
        rotordiam=rotor_diam, 
        cutin=cutin, 
        cutout=cutout, 
        input_points=input_data)
    pc = pc.convolute_by_gaussian(scaling=0.01, base=0.00)

    logger.info("Calculating the expected capacity factor...")
    
    # Filter out NaN values before simulation
    wind_speeds_flat = wind_speed_hub["WS"].values.flatten()
    wind_speeds_flat = wind_speeds_flat[~np.isnan(wind_speeds_flat)]  # Remove NaNs

    # Calculate capacity factors for each wind speed point using `simulate`
    capacity_factors = pc.simulate(wind_speeds_flat)

    # Calculate mean and median capacity factor
    mean_capacity_factor = np.mean(capacity_factors)
    median_capacity_factor = np.median(capacity_factors)

    wind_speed_bins = np.arange(0, 40, 1)  # Bins from 0 to 40 m/s, in 1 m/s increments
    wind_speed_hist, _ = np.histogram(wind_speeds_flat, bins=wind_speed_bins, density=True)                                           

    # Convert histogram to a list to make it JSON-serializable
    wind_speed_distribution = wind_speed_hist.tolist()

    # Prepare output data including the wind speed distribution
    output_data = {
        "weibull_shape": shape,
        "weibull_scale": scale,
        "mean_wind_speed": mean_wind_speed,
        "mean_capacity_factor": mean_capacity_factor,
        "median_capacity_factor": median_capacity_factor,
        "wind_speed_distribution": wind_speed_distribution
    }

    logger.info(f"Wind speed distribution (normalized): {wind_speed_distribution}")
    logger.info(f"Expected capacity factor: {mean_capacity_factor}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

    # Save the output data
    with open(output_json_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    logger.info(f"Saved expected capacity factor, Weibull parameters, and mean wind speed to {output_json_path}")
    return output_data


def calculate_mean_monthly_capacity_factors(
        newa_100m_path, 
        year, 
        output_json_path=os.path.join(output_dir, "wind_power_newa.json")
    ):
     # Define turbine parameters
    capacity = technology_settings["wind"]["capacity"] / 1000  # Convert to MW
    rotor_diam = technology_settings["wind"]["rotor_diameter"]
    hub_height = technology_settings["wind"]["hub_height"]
    cutin = technology_settings["wind"]["cut_in_wind_speed"]
    cutout = technology_settings["wind"]["cut_out_wind_speed"]

    logger.info("Synthesizing the power curve..")
    # Generate the synthetic power curve
    # Generate the synthetic power curve
    pc = SyntheticPowerCurve(
        specificCapacity=None, 
        capacity=capacity, 
        rotordiam=rotor_diam, 
        cutin=cutin, 
        cutout=cutout, 
        input_points=input_data)
    pc = pc.convolute_by_gaussian(scaling=0.01, base=0.00)

    # Load the NEWA datasets
    wind_speed = xr.open_dataset(newa_100m_path)
    wind_speed = wind_speed.squeeze("height")

    logger.info("Resampling NEWA data to monthly intervals...")
    # Resample the original NEWA data to monthly frequency
    wind_speed_monthly = wind_speed.resample(time="1ME").mean()

    logger.info(f"Interpolating monthly wind speeds to {hub_height} m...")

    # Interpolate wind speeds to hub height
    wind_speed_hub_monthly = xr.apply_ufunc(
        apply_logarithmic_profile_projection,
        wind_speed_monthly,  # Monthly average wind speed
        100,  # Measured height
        hub_height,  # Target height
        0.0002,  # Roughness
        kwargs={'displacement': 0, 'stability': 0},
        vectorize=True
    )

    logger.info("Calculating mean monthly capacity factors...")

    # Initialize list to store monthly mean capacity factors
    monthly_capacity_factors = []
    for month in range(1, 13):
        # Select wind speed data for the specific month
        wind_speed_month = wind_speed_hub_monthly["WS"].sel(time=wind_speed_hub_monthly["time.month"] == month)
        
        # Flatten data and remove NaNs
        wind_speeds_flat_month = wind_speed_month.values.flatten()
        wind_speeds_flat_month = wind_speeds_flat_month[~np.isnan(wind_speeds_flat_month)]
        
        # Calculate capacity factors for each wind speed point in the month
        capacity_factors_month = pc.simulate(wind_speeds_flat_month)
        mean_capacity_factor_month = np.mean(capacity_factors_month) * 0.87 * 0.88  ## apply availability and array efficiency factors

        monthly_capacity_factors.append(mean_capacity_factor_month)

    # Prepare output data with monthly capacity factors
    output_data = {
        "year": year,
        "monthly_capacity_factors": monthly_capacity_factors
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

    # Save the output data to JSON
    with open(output_json_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    logger.info(f"Saved mean monthly capacity factors to {output_json_path}")
    return monthly_capacity_factors

########################################################################################
########################### RUN THE SIMULATION  #########################################

##logger.info("Running the simulation...")
output_json_directory = os.path.join(output_dir, "simulations", "NEWA_timeseries")
# make sure that the output directory exists
if not os.path.exists(output_json_directory):
    os.makedirs(output_json_directory)

########################################################################

# for year in years:
#     output_file_path = os.path.join(output_json_directory, country, f"wind_power_newa_{year}.json")
    
#     logger.info(f"Running the simulation for {country} in {year}")
#     newa_100m_path = os.path.join(met_data_dir, "NEWA", "time_series", country, f"newa_wind_speed_{country}_{year}_100m.nc")
#     data = north_sea_offshore_wind_simplified_sim(newa_100m_path, year, output_json_path=output_file_path)

# logger.info("PerformNEWASimulations main task completed.")


########################################################################################
########## Do monthly capacity factors ###############################################
for year in years:
    output_file_path = os.path.join(output_json_directory, country, f"wind_power_newa_monthly_CF{year}.json")
    logger.info(f"Running the simulation for {country} in {year}")
    newa_100m_path = os.path.join(met_data_dir, "NEWA", "time_series", country, f"newa_wind_speed_{country}_{year}_100m.nc")
    data = calculate_mean_monthly_capacity_factors(newa_100m_path, year, output_json_path=output_file_path)

logger.info("PerformNEWASimulations monthly cap factors task completed.")