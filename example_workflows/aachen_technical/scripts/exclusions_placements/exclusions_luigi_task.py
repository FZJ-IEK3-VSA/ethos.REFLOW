import luigi
import os
import subprocess
from utils.config import ConfigLoader
from scripts.data_processing.process_exclusions_data import ProcessExclusionsData
import logging
import time

class PerformEligibiliyAnalysisPlacements(luigi.Task):
    """
    Script to exclude non-available areas from the analysis (including buffers defined in the exclusions_settings.json file).
    This script uses the GLAES package for performing exclusions. 
    """
    def requires(self):
        """
        This task requires the DownloadMeterologicalData task to be completed.
        """
        return [ProcessExclusionsData()]
    
    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'geodata', 'turbine_placements_3035.csv'))
    
    def run(self):
        """
        Main logic for the task.
        """
        #### directory management ####
        config_loader = ConfigLoader()

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformEligibiliyAnalysisPlacements.log')
        logger = config_loader.setup_task_logging('PerformEligibiliyAnalysisPlacements', log_file)

        ## run the exclusions wrapper bash script
        subprocess.run(['bash', './scripts/exclusions_placements/exclusions_placements_wrapper.sh'], check=True, shell=True)