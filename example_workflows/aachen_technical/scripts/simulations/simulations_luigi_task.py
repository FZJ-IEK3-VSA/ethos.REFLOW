import luigi
import os
import subprocess
from utils.config import ConfigLoader
from scripts.data_processing.convert_placements import ConvertPlacementsToEPSG4326
from scripts.data_processing.process_met_data import ProcessERA5WindData
from scripts.exclusions_placements.exclusions_luigi_task import PerformEligibiliyAnalysisPlacements
import logging
import time

class PerformSimulations(luigi.Task):
    """
    Script to exclude non-available areas from the analysis (including buffers defined in the exclusions_settings.json file).
    This script uses the GLAES package for performing exclusions. 
    """
    def requires(self):
        """
        This task requires both the PerformEligibiliyAnalysisPlacements and the ProcessERA5WindData tasks to be completed.
        """
        return [PerformEligibiliyAnalysisPlacements(),
                ConvertPlacementsToEPSG4326(),
                ProcessERA5WindData()]
    
    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        output_filename = "wind_power_era5_2016.nc"
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'simulations', output_filename))
    
    def run(self):
        """
        Main logic for the task.
        """
        #### directory management ####
        config_loader = ConfigLoader()

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformSimulations.log')
        logger = config_loader.setup_task_logging('PerformSimulations', log_file)

        ## run the exclusions wrapper bash script
        subprocess.run(['bash', './scripts/simulations/simulations_wrapper.sh'], check=True, shell=True)