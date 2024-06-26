import os
import json
import logging
import requests
import luigi
from utils.config import ConfigLoader
from utils.data_download import ERA5Downloader
from scripts.data_processing.process_project_data import ProcessProjectData

class DownloadMeterologicalData(luigi.Task):
    """
    Luigi task to download meteorological data for the project.
    """

    def requires(self):
        """
        This task requires the ProcessProjectData task to be completed.
        """
        return [ProcessProjectData()]
    
    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadMeterologicalData_complete.txt'))
    
    def run(self):
        """
        Main logic for the task.
        """

        ##################### DO NOT CHANGE #################################

        #### directory management ####
        config_loader = ConfigLoader()

        met_data_dir = config_loader.get_path("data", "met_data")
        project_data_dir = config_loader.get_path("data", "project_data")

        country_settings_path = config_loader.get_path("settings", "country_settings")

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadMeterologicalData.log')
        logger = config_loader.setup_task_logging('DownloadMeterologicalData', log_file)
        logger.info("Starting DownloadMeterologicalData task")  
        
        #####################################################################################

        ############## MAIN WORKFLOW #################
        logger.info("Downloading meteorological data...")

        ############## 1. Download NEW EUROPEAN WIND ATLAS data ##############
        # Link to datasource info: https://globalwindatlas.info/
        print("Downloading the New European Wind Atlas data...")
        api_url = "https://wps.neweuropeanwindatlas.eu/api/mesoscale-atlas/v1/get-data-bbox?southBoundLatitude=49.124219&northBoundLatitude=61.389704&westBoundLongitude=-6.665037&eastBoundLongitude=13.666992&height=100&variable=wind_speed_mean"

        # Specify the directory and file name for the downloaded data
        file_name = "newa_wind_speed_mean_100m.tif"
        file_path = os.path.join(met_data_dir, file_name)

        # Perform the API request
        response = requests.get(api_url)

        # Check if the request was successful
        if response.status_code == 200:
            # Write the response content to a file
            with open(file_path, 'wb') as file:
                file.write(response.content)
            logger.info(f"Download of {file_name} successful.")
        else:
            logger.error(f"Failed to download data. Status code: {response.status_code}")

        ############### 2. DOWNLOAD OF ERA5 data from CDSAPI service ##############
        try:
            ERA5_downloader = ERA5Downloader(main_polygon_fname="north_sea_polygon.shp", logger=logger)
        except Exception as e:  
            logger.error(f"Failed to initialize ERA5Downloader. Please check filename. Error: {e} More information in the MainWorkflow.log file.")
            return 

        try:
            ERA5_downloader.download_ERA5_data()
        except Exception as e:  
            logger.error(f"Failed to download ERA5 data. Please check the logs for more information. Error: {e}")
            return

        ## Signal that the task is complete
        logger.info("Downloading Meteorological Data task complete.")
        with self.output().open('w') as f:
            f.write('Download Meteorological Data task complete.')