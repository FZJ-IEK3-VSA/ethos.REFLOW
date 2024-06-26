import luigi
import requests
import os
import zipfile
import json
from pathlib import Path
from utils.config import ConfigLoader
from utils.data_download import DownloaderUtils, ERA5Downloader
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

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadExclusionsData.log')
        logger = config_loader.setup_task_logging('DownloadExclusionsData', log_file)
        logger.info("Starting DownloadExclusionsData task")        

        raw_data_dir = config_loader.get_path("data", "exclusion_data", "raw")
        # create the raw data directory if it does not exist
        os.makedirs(raw_data_dir, exist_ok=True)

        met_data_dir = config_loader.get_path("data", "met_data")
        # create the met data directory if it does not exist
        os.makedirs(met_data_dir, exist_ok=True)

        # load the project settings
        with open(config_loader.get_path("settings", "project_settings"), 'r') as file:
            project_settings = json.load(file)

        download_utils = DownloaderUtils(logger=logger)

        gadm_version = project_settings["gadm_version"]
        countries = project_settings["countries"]
        logger.info(f"List of countries: {countries}")

        place_name = project_settings["OSM_region_name"]

        exclusion_data_vector_paths = {}
        exclusion_data_raster_paths = {}

        ###########################################################################

        # ############## MAIN WORKFLOW #################

        ### ADD YOUR DOWNLOAD WORKFLOW HERE ###

        # to ensure good logging, remember to pass logger=logger into whichever class you are using 


        ############ DO NOT CHANGE ################
        # Signify that the task has been completed
        logger.info("Exclusion data download complete.")
        with self.output().open('w') as f:
            f.write('Exclusion data download complete.')