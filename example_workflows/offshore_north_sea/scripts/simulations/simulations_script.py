import reskit as rk
from reskit.wind.workflows.wind_workflow_manager import WindWorkflowManager
import os
import pandas as pd
import json
from utils.config import ConfigLoader
import numpy as np
import json
from utils.reskit_code import calculate_weibull_params
from utils.synthetic_power_curve import SyntheticPowerCurve
import argparse

##########################################################################################
parser = argparse.ArgumentParser(description='Run the NEWA simulations')
parser.add_argument('--scenario', type=str, help='The scenario to run the simulations for')

scenario = parser.parse_args().scenario 

############ directory management and global variables ############
config_loader = ConfigLoader()
output_dir = config_loader.get_path("output")

met_data_dir = config_loader.get_path("data", "met_data")
project_settings_path = config_loader.get_path("settings", "project_settings")

with open(project_settings_path) as file:
    project_settings = json.load(file)

# configure logging
log_file = os.path.join(config_loader.get_path("output"), 'logs', 'PerformSimulations.log')
logger = config_loader.setup_task_logging('PerformSimulations', log_file)

logger.info("Starting PerformSimulations task")  

exclusions_settings_path = config_loader.get_path("settings", "exclusions_settings")
with open(exclusions_settings_path, 'r') as file:
    exclusions_settings = json.load(file)

technology_settings_path = config_loader.get_path("settings", "technologies")
with open(technology_settings_path, 'r') as file:
    technology_settings = json.load(file)

capacity = technology_settings["wind"]["capacity"] 
rotor_diam = technology_settings["wind"]["rotor_diameter"]
cutin = technology_settings["wind"]["cut_in_wind_speed"]
cutout = technology_settings["wind"]["cut_out_wind_speed"]

## set the year
years = range(project_settings["start_year"], project_settings["end_year"] + 1)

##########################################################################################
############################ DEFINE THE RESKIT WORKFLOW ##############################

# Example input data of wind speed to capacity factor pairs for the synthetic power curve
input_data = [
    (8.0, 0.4566), (8.5, 0.5023), (9.0, 0.5403), (9.5, 0.5860),
    (10.0, 0.6240), (10.5, 0.6545), (11.0, 0.6773), (11.5, 0.7141),
    (12.0, 0.7509), (12.5, 0.7877), (13.0, 0.8245), (13.5, 0.8612),
    (14.0, 0.8980), (14.5, 0.9348), (15.0, 0.9716), (15.5, 1.0)
]

def north_sea_offshore_wind_sim(
    placements,
    year,
    era5_path,
    newa_100m_path,
    output_netcdf_path=os.path.join(output_dir, "wind_power_era5.nc"),
    turbine_availablilty=0.88,
    array_efficiency=0.9,
    report_path=None,
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
    turbine_availablilty : float, optional
        The availability of the turbines, by default 0.88
    array_efficiency : float, optional
        The efficiency of the array, by default 0.9
    report_path : str, optional
        Path to the report file, by default None

    Returns
    -------
    xarray.Dataset
        A xarray dataset including all the output variables you defined as your output variables.

    Sources
    ------
    [1] European Centre for Medium-Range Weather Forecasts. (2024). ERA5 dataset. https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5.

    """
    report = {}

    logger.info(f"Initializing simulation for year {year}...")
    parent_dir = os.path.dirname(report_path)
    sim_dir = os.path.join(parent_dir, "simulations", "ERA5_timeseries")
    if not os.path.exists(sim_dir):
        os.makedirs(sim_dir)

    # Step 1: Initialize a single SyntheticPowerCurve
    logger.debug("Initializing synthetic power curve...")
    synthetic_curve = SyntheticPowerCurve(
        specificCapacity=None,
        capacity=placements['capacity'][0], 
        rotordiam=placements['rotor_diam'][0],  
        cutin=3,    
        cutout=31,
        input_points=input_data
    )
    synthetic_curve = synthetic_curve.convolute_by_gaussian(scaling=0.01, base=0.00)
    logger.debug("Synthetic power curve initialized successfully.") 

    # Step 2: Initialize the Workflow Manager    
    logger.debug("Initializing Wind Workflow Manager...")
    wf = WindWorkflowManager(placements)

    try:
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
        logger.info(f"Data successfully read from ERA5 for year {year}.")
    except Exception as e:
        logger.error(f"Error reading ERA5 data: {e}")
        raise

    ## Step 3: Adjust the wind speeds to the long run average
    logger.info("Adjusting wind speeds to the long-run average...")
    try:
        wf.adjust_variable_to_long_run_average(
            variable='elevated_wind_speed',
            source_long_run_average=os.path.join(met_data_dir, "ERA5_wind_speed_100m_mean.tiff"),
            real_long_run_average=newa_100m_path,
            spatial_interpolation="average"
        )
        logger.info("Wind speed adjustment completed successfully.")
    except Exception as e:
        logger.error(f"Error during wind speed adjustment: {e}")
        raise

    ## Step 4: Extrapolate the wind speeds vertically
    logger.info("Extrapolating wind speeds vertically to hub height...")
    try:
        wf.set_roughness(0.0002)
        wf.logarithmic_projection_of_wind_speeds_to_hub_height(
            consider_boundary_layer_height=True
        )
        wf.apply_air_density_correction_to_wind_speeds()
        logger.info("Extrapolation and corrections applied successfully.")
    except Exception as e:
        logger.error(f"Error during wind speed extrapolation: {e}")
        raise

    # Step 5: Calculate Weibull parameters
    logger.info("Calculating Weibull parameters...")
    try:
        wind_speed_hub = wf.sim_data['elevated_wind_speed']  # Extract hub height wind speed
        shape, scale = calculate_weibull_params(wind_speed_hub.flatten())
        mean_wind_speed = wind_speed_hub.mean().item()
        logger.info(f"Weibull shape: {shape}, scale: {scale}, mean wind speed: {mean_wind_speed:.2f} m/s")
    except Exception as e:
        logger.error(f"Error calculating Weibull parameters: {e}")
        raise

    # Step X: Aggregate Weibull parameters and wind speed distribution per country
    logger.info("Aggregating Weibull parameters and wind speed distribution per country...")
    
    try:
        report["country_stats"] = {}
        
        for country, group in placements.groupby("country"):
            # Initialize stats for the country
            if country not in report["country_stats"]:
                report["country_stats"][country] = []
            
            # Extract wind speeds for the country group
            wind_speeds_country = wf.sim_data['elevated_wind_speed'][:, group.index].flatten()
            
            # Calculate Weibull parameters
            shape_country, scale_country = calculate_weibull_params(wind_speeds_country)
            mean_speed_country = np.mean(wind_speeds_country)
            
            # Calculate wind speed distribution
            wind_speed_bins = np.arange(0, 40, 1)  # Bins from 0 to 40 m/s
            wind_speed_hist_country, _ = np.histogram(wind_speeds_country, bins=wind_speed_bins, density=True)
            wind_speed_distribution_country = wind_speed_hist_country.tolist()
            
            # Add stats to the report
            report["country_stats"][country].append({
                "weibull_shape": shape_country,
                "weibull_scale": scale_country,
                "mean_wind_speed": mean_speed_country,
                "wind_speed_distribution": wind_speed_distribution_country
            })

            output_fname = os.path.join(sim_dir, country)
            if not os.path.exists(output_fname):
                os.makedirs(output_fname)
            try:
                with open(os.path.join(output_fname, f"wind_power_era5_{year}.json"), "w") as file:
                    json.dump(report, file, indent=4)
                logger.info(f"Saved Weibull stats report to {output_fname}")
            except Exception as e:
                logger.error(f"Error saving Weibull stats report: {e}")
                raise
            
        logger.info("Weibull parameters and wind speed distributions aggregated successfully.")
    except Exception as e:
        logger.error(f"Error aggregating Weibull parameters and wind speed distributions: {e}")
        raise
    
    # Step 6: Simulate power output
    logger.info("Simulating power output...")
    try:
        total_loss_factor = turbine_availablilty * array_efficiency
        total_loss_factor = 1 - total_loss_factor
        capacity_factor_array = synthetic_curve.simulate(wf.sim_data['elevated_wind_speed'])
        wf.sim_data['capacity_factor'] = capacity_factor_array
        wf.apply_loss_factor(total_loss_factor)
        logger.info("Power output simulation completed.")
    except Exception as e:
        logger.error(f"Error during power output simulation: {e}")
        raise

    # Step 7: Calculate FLH and AEY
    logger.info("Calculating FLH and AEY metrics...")
    try:
        flh_array = np.sum(capacity_factor_array, axis=0)
        aey_array = (flh_array * wf.placements['capacity'].iloc[0]) / 1000
        placements[f"FLH_{year}"] = flh_array
        placements[f"AEY_{year}_MWh"] = aey_array
        logger.info("FLH, AEY, and Generation metrics calculated successfully.")
    except Exception as e:
        logger.error(f"Error calculating FLH and AEY metrics: {e}")
        raise

    # Step 9: Save results to NetCDF
    logger.info(f"Saving results to NetCDF at {output_netcdf_path}...")
    try:
        xds = wf.to_xarray(output_netcdf_path=output_netcdf_path)
    except Exception as e:
        logger.error(f"Error saving results to NetCDF: {e}")
        raise

    return xds, placements


def calculate_country_generation_stats(report_path, placements, start_year, end_year):
    years = range(start_year, end_year + 1)

    data_by_country_year = placements.groupby("country").agg({f"AEY_{year}_MWh": 'sum' for year in years})

    # Convert MWh to TWh
    data_by_country_year = data_by_country_year / 1e6

    # Prepare data for stacked area chart
    data_for_plotting = data_by_country_year.transpose()

    # Extract labels for each country (keep the 3-letter codes for processing)
    country_codes = data_for_plotting.columns.tolist()

    # open the scenario report file
    with open(report_path, 'r') as file:
        scenario_report = json.load(file)

    # calculate mean, min and max generation for each country
    for country in country_codes:
        country_data = {
            'number of turbines': placements[placements["country"] == country].shape[0],
            'installable_capacity': placements[placements["country"] == country].shape[0] * 15 / 1000,
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

    logger.info("Country generation statistics saved to the report.json file.")


########################################################################################
########################### RUN THE SIMULATION  #########################################

# ##logger.info("Running the simulation...")
output_netcdf_directory = os.path.join(output_dir, "simulations")

## make sure that the output directory exists
if not os.path.exists(output_netcdf_directory):
    os.makedirs(output_netcdf_directory)

report_path = os.path.join(output_dir, f"report_{scenario}.json")

placements_path = os.path.join(output_dir, "geodata", f"turbine_placements_4326_{scenario}.csv")
placements = pd.read_csv(placements_path)

for year in years:
    logger.info(f"Simulating the year {year}...")
    # run the simulation
    era5_path = os.path.join(met_data_dir, "ERA5", "processed", f"{year}")
    newa_100m_path = os.path.join(met_data_dir, "newa_wind_speed_mean_100m.tif")
    xds, placements = north_sea_offshore_wind_sim(placements,
                                                    year,            
                                                    era5_path, 
                                                    newa_100m_path, 
                                                    output_netcdf_path=os.path.join(output_netcdf_directory, f"wind_power_era5_{year}_{scenario}.nc"),
                                                    turbine_availablilty=technology_settings["wind"][f"turbine_availability_{scenario}"],
                                                    array_efficiency=technology_settings["wind"][f"array_efficiency"],
                                                    report_path=report_path
                                                    )

placements.to_csv(placements_path, index=False)

for year in years:
    logger.info("Updating and saving the report...")
    try:
        with open(report_path, "r") as file:
            report = json.load(file)
        report[f"Total_Generation_{year}_TWh"] = placements[f"AEY_{year}_MWh"].sum() / 1e6
        report[f"Mean_Capacity_Factor_{year}"] = (placements[f"FLH_{year}"].mean() / 8760) * 100
        with open(report_path, 'w') as file:
            json.dump(report, file, indent=4)
        logger.info("Report updated and saved successfully.")
    except Exception as e:
        logger.error(f"Error updating/saving the report: {e}")
        raise

#################### GENERATE REPORTS FOR EACH COUNTRY ##############################

placements_path = os.path.join(output_dir, "geodata", f"turbine_placements_4326_{scenario}.csv")
placements = pd.read_csv(placements_path)

#################### GENERATE COUNTRY GENERATION STATS ##############################

logger.info("Calculating country-level generation statistics...")
calculate_country_generation_stats(report_path, placements, project_settings["start_year"], project_settings["end_year"])

logger.info("Simulation completed successfully. Final reports generated.")