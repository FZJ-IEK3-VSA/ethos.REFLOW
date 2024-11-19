import os
import luigi
import json
from utils.config import ConfigLoader
from scripts.simulations.newa_simulations_luigi_task import PerformNEWASimulations

# set up logging 
config_loader = ConfigLoader()
log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformNEWASimulations.log')
logger = config_loader.setup_task_logging('PerformNEWASimulations', log_file)

class PerformNewaSimulationsFinalData(luigi.Task):
    """
    This task will generate the final data for the NEWA simulations.
    """

    def calculate_annual_power_yield(
        self,
        mean_capacity_factor,
        power_density,
        area_km2,
        availability,
        array_efficiency
        ):
        """
        Calculates the annual power yield in TWh for a wind farm.

        Parameters
        ----------
        mean_capacity_factor : float
            The mean capacity factor for the turbines.
        power_density : float
            The power density in MW/km².
        area_km2 : float
            The size of the area in km².
        availability : float
            The availability factor (between 0 and 1).
        array_efficiency : float
            The efficiency of the wind farm array (between 0 and 1).

        Returns
        -------
        float
            Annual power yield in TWh.
        """
        # Convert area to MW based on power density
        total_capacity_mw = power_density * area_km2  # in MW

        # Annual yield in TWh
        annual_yield_twh = (
            (total_capacity_mw * mean_capacity_factor * 8760 * (availability * array_efficiency)) / 1e6
        )  # Convert MWh to TWh

        return annual_yield_twh


    def requires(self):
        return [PerformNEWASimulations()]

    def output(self):
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'completed_tasks', 'PerformNEWASimulationsFinal_complete.txt'))

    def run(self):
        output_dir = config_loader.get_path("output")
        output_json_directory = os.path.join(output_dir, "simulations", "NEWA_timeseries")

        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path) as file:
            project_settings = json.load(file)
        countries = project_settings["countries"]
        capacity_density_MW_km2 = project_settings["newa_sim_power_density"]
        
        exclusions_settings_path = config_loader.get_path("settings", "exclusions_settings")
        with open(exclusions_settings_path, 'r') as file:
            exclusions_settings = json.load(file)

        technology_settings_path = config_loader.get_path("settings", "technologies")
        with open(technology_settings_path, 'r') as file:
            technology_settings = json.load(file)

        scenarios = ["1000m_depth", "50m_depth"]

        # Initialize aggregators for North Sea summary
        north_sea_summary = {}

        for scenario in scenarios:
            north_sea_summary[scenario] = {
                "Total_installed_capacity_MW": 0,
                "Annual_power_yield_TWh": {},  # Will hold year-specific data
                "Mean_annual_generation_TWh": 0  # Placeholder for mean generation
            }

        ## set the year
        years = [2014, 2015, 2016, 2017, 2018]
        for scenario in scenarios:
            for year in years:
                north_sea_summary[scenario]["Annual_power_yield_TWh"][year] = 0

        report_path = os.path.join(config_loader.get_path("output"), "report_NEWA_sim.json")
        with open(report_path) as file:
            report = json.load(file)

        for country in countries:
            for scenario in scenarios:
                total_yield = 0  # Accumulate total yield for calculating the mea
                for year in years:
                    logger.info(f"Calculating the annual power yield for {country} in {year} for scenario {scenario}...")
                    sim_data_path = os.path.join(output_json_directory, country, f"wind_power_newa_{year}.json")
                    with open(sim_data_path) as file:
                        sim_data = json.load(file)

                    # Calculate the annual power yield with example values or load from settings
                    expected_capacity_factor = sim_data["mean_capacity_factor"]  # expected capacity factor
                    power_density = project_settings["newa_sim_power_density"]  # assumed power density in MW/km²
                    area_km2 = report[country]["Scenarios"][scenario]["Eligible_area_km2"]   # available area in km2
                    total_capacity = capacity_density_MW_km2 * area_km2  # total capacity in MW
                    availability = technology_settings["wind"][f"turbine_availability_{scenario}"]  # turbine availability factor
                    array_efficiency = technology_settings["wind"]["array_efficiency"]  # e.g., 0.9

                    # Calculate the annual yield using the previously computed capacity factor
                    annual_power_yield_twh = self.calculate_annual_power_yield(
                        expected_capacity_factor,
                        power_density,
                        area_km2,
                        availability,
                        array_efficiency
                    )

                    report[country]["Scenarios"][scenario][f"Annual_power_yield_{year}"] = annual_power_yield_twh
                    report[country]["Scenarios"][scenario]["Total_capacity"] = total_capacity

                    # Update the total yield for mean calculation
                    total_yield += annual_power_yield_twh

                    # Update North Sea summary
                    north_sea_summary[scenario]["Total_installed_capacity_MW"] += total_capacity
                    north_sea_summary[scenario]["Annual_power_yield_TWh"][year] += annual_power_yield_twh
                
                # Calculate and add the mean power yield for the scenario
                mean_yield = total_yield / len(years)
                report[country]["Scenarios"][scenario]["Mean_power_yield"] = mean_yield

        # Finalize and add the North Sea summary to the report
        total_generation = {
            scenario: sum(north_sea_summary[scenario]["Annual_power_yield_TWh"].values())
            for scenario in scenarios
        }
        for scenario in scenarios:
            north_sea_summary[scenario]["Mean_annual_generation_TWh"] = total_generation[scenario] / len(years)

        report["North_Sea"] = north_sea_summary

        # Save the updated report after processing all countries and scenarios
        with open(report_path, 'w') as json_file:
            json.dump(report, json_file, indent=4)

        # Write the completion flag
        with self.output().open("w") as f:
            f.write("Completed NEWA simulations final data processing.")