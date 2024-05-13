import luigi
import requests
import os
import zipfile
import json
from pathlib import Path
from utils.config import ConfigLoader
from utils.data_download import DownloaderUtils
import logging
from scripts.environment_setup.env_setup_luigi_task import SetupEnvironments

class DownloadProjectData(luigi.Task):
    """
    Luigi Task to download the exclusion data.
    """
    gadm_version = luigi.Parameter(default="41")

    def requires(self):
        """
        Define any dependencies here. If this is a first step, return None 
        """
        return [SetupEnvironments()]

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        # return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("data" "project_data"), 'gadm', 'DEU', 'gadm41_DEU', 'gadm41_DEU_2.shp'))
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadProjectData_complete.txt'))
    
    def run(self):
        """
        Main run method for the task. 
        """
        ##################### DO NOT CHANGE ######################################

        #### directory management ####
        config_loader = ConfigLoader()       

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadProjectData.log')
        logger = config_loader.setup_task_logging('DownloadProjectData', log_file)
        logger.info("Starting DownloadProjectData task")        

        # load the project settings
        with open(config_loader.get_path("settings", "project_settings"), 'r') as file:
            project_settings = json.load(file)

        download_utils = DownloaderUtils(logger=logger)

        gadm_version = project_settings["gadm_version"]
        countries = project_settings["countries"]
        logger.info(f"List of countries: {countries}")

        exclusion_data_vector_paths = {}
        exclusion_data_raster_paths = {}

        ###########################################################################

        # ############## MAIN WORKFLOW #################

        ### ADD YOUR DOWNLOAD WORKFLOW HERE ###
        
        ##### FIRST, we will download the GADM data for Germany ####

        for country in countries:
            download_utils.download_gadm_data(country) 

        # to ensure good logging, remember to pass logger=logger into whichever class you are using 

        # update the project data paths
        # update data paths
        config_loader.update_data_paths()

        ## Signal that the task is complete
        logger.info("Project data download complete.")
        with self.output().open('w') as f:
            f.write('Download Project Data task complete.')