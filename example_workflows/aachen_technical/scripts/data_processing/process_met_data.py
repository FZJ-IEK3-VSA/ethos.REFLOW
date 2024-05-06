import luigi
import os
from utils.config import ConfigLoader
from scripts.data_download.meteorological_data import DownloadMeterologicalData
import logging
from utils.ERA5_processing import ERA5_RESKitWindProccessor
import json

class ProcessERA5WindData(luigi.Task):
    """
    Script to process ERA5 wind data so that it is readable by the RESKit model.
    """
    def requires(self):
        """
        This task requires the DownloadMeterologicalData task to be completed.
        """
        return [DownloadMeterologicalData()]
    
    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessERA5WindData_complete.txt'))
    
    def run(self):
        """
        Main logic for the task.
        """
        ##################### DO NOT CHANGE #################################

        #### directory management ####
        config_loader = ConfigLoader()

        met_data_dir = config_loader.get_path("data", "met_data")
        project_data_dir = config_loader.get_path("data", "project_data")

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessERA5WindData.log')
        logger = config_loader.setup_task_logging('ProcessERA5WindData', log_file)
        logger.info("Starting ProcessERA5WindData task")  

        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)

        start_year = project_settings["start_year"]
        end_year = project_settings["end_year"]
        
        #####################################################################################

        ############## MAIN WORKFLOW #################
        for year in range(start_year, end_year + 1):
            logger.info(f"Processing ERA5 wind data for {year}...")

            # Process the wind data
            wind_processor = ERA5_RESKitWindProccessor(logger=logger)
            wind_processor.process_wind(year)

        # update data paths
        config_loader.update_data_paths()

        ############ DO NOT CHANGE ############
        # mark the task as complete
        logger.info("ProcessRegionBuffers task complete.")
        with self.output().open('w') as file:
            file.write('Complete')