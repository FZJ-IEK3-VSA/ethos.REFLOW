import luigi
import requests
import os
import zipfile
import json
from pathlib import Path
from utils.config import ConfigLoader
from utils.data_download import download_gadm_data, download_and_extract
import logging

class DownloadExclusionsData(luigi.Task):
    """
    Luigi Task to download the exclusion data.
    """
    gadm_version = luigi.Parameter(default="41")

    def requires(self):
        """
        Define any dependencies here. If this is a first step, return None 
        """
        return None

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'exclusions_data_download_complete.txt'))
    
    def run(self):
        """
        Main run method for the task. 
        """
        ##################### DO NOT CHANGE ######################################

        #### directory management ####
        config_loader = ConfigLoader()

        raw_output_dir = config_loader.get_path("data", "exclusion_data", "raw")
        project_data_dir = config_loader.get_path("data", "project_data")
        project_settings_path = config_loader.get_path("settings", "project_settings")

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadExclusionsData.log')
        logger = config_loader.setup_task_logging('DownloadExclusionsData', log_file)
        logger.info("Starting DownloadExclusionsData task")

        # load the list of countries
        with open(project_settings_path, 'r') as file:
            country_settings = json.load(file)

        countries = country_settings["countries"]
        logger.info(f"List of countries: {countries}")
        ###########################################################################

        # ############## MAIN WORKFLOW #################

        ### ADD YOUR DOWNLOAD WORKFLOW HERE ###

        # to ensure good logging, remember to pass logger=logger into whichever class you are using 


        ############ DO NOT CHANGE ################
        # Signify that the task has been completed
        logger.info("Exclusion data download complete.")
        with self.output().open('w') as f:
            f.write('Exclusion data download complete.')