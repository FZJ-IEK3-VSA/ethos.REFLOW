import luigi
import os
import subprocess
from utils.config import ConfigLoader
from scripts.exclusions_placements.exclusions_luigi_task import PerformEligibiliyAnalysisPlacements
import logging
import time

class SensitivityAnalysis(luigi.Task):
    """
    Script to exclude non-available areas from the analysis (including buffers defined in the exclusions_settings.json file).
    This script uses the GLAES package for performing exclusions. 
    """
    def requires(self):
        """
        This task requires the DownloadMeterologicalData task to be completed.
        """
        return [PerformEligibiliyAnalysisPlacements()]
    
    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'SensitivityAnalysis_complete.txt'))
    
    def run(self):
        """
        Main logic for the task.
        """
        #### directory management ####
        config_loader = ConfigLoader()

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'SensitivityAnalysis.log')
        logger = config_loader.setup_task_logging('SensitivityAnalysis', log_file)

        ## run the exclusions wrapper bash script
        subprocess.run(['bash', './scripts/exclusions_placements/sensitivity_wrapper.sh'], check=True, shell=True)

        ############ DO NOT CHANGE ############
        # mark the task as complete
        with self.output().open('w') as file:
            file.write('Complete')