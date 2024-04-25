from utils.config import ConfigLoader
from utils.data_processing import VectorProcessor
from scripts.data_download.exclusions_data import DownloadExclusionsData
import geopandas as gpd
import luigi
import json
import logging
import os

#### THIS SCRIPT MUST BE RUN AS IT IS A DEPENDENCY FOR THE NEXT TASK ####
#### However, the main logic can be left blank if you do not need to add additional buffers to the regions - eg around coastlines or national borders ####  

class ProcessProjectData(luigi.Task):
    """
    Luigi Task to process the region buffers for the project.
    """
    def requires(self):
        """
        This task requires the DownloadExclusionsData task to be completed.
        """
        return [DownloadExclusionsData()]

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessProjectData_complete.txt'))

    def run(self):
        """
        Main run method for the task.
        """
        ################## DO NOT CHANGE ############################
        #### directory management ####
        config_loader = ConfigLoader()
        vector_processor = VectorProcessor()

        project_settings_path = config_loader.get_path("settings", "project_settings")
        exclusion_settings_path = config_loader.get_path("settings", "exclusions_settings")
        project_data_dir = config_loader.get_path("data", "project_data")
        raw_data_dir = config_loader.get_path("data", "exclusion_data", "raw")
        processed_data_dir = config_loader.get_path("data", "exclusion_data", "processed")

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessProjectData.log')
        logger = config_loader.setup_task_logging('ProcessProjectData', log_file)
        logger.info("Starting ProcessProjectData task")

        # load the exclusions dictionary
        with open(exclusion_settings_path, 'r') as file:
            exclusion_settings = json.load(file)

        ############## MAIN WORKFLOW #################

        ### Add your logic for buffering the regions here ###
        #### Leave blank if not running any coastline or border buffer processing ####

        ############ DO NOT CHANGE ############
        # mark the task as complete
        logger.info("ProcessProjectData task complete.")
        with self.output().open('w') as file:
            file.write('Complete')