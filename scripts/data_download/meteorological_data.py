import os
import json
import logging
import requests
import luigi
from utils.config import ConfigLoader
from utils.data_download import ERA5Downloader
from scripts.data_processing.process_project_data import ProcessRegionBuffers

class DownloadMeterologicalData(luigi.Task):
    """
    Luigi task to download meteorological data for the project.
    """

    def requires(self):
        """
        This task requires the ProcessRegionBuffers task to be completed.
        """
        return [ProcessRegionBuffers()]
    
    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadMeterologicalData_complete.txt'))
        ## this creates a file that signifies that the task is complete
        ## BETTER is to set the output to the actual files that are downloaded (but you first need to download them to know what they are!)
        ## this will allow future workflows to check if the files exist and skip this task if they do, but also not bug out in case there is a text file which is not the actual output
        
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
        logging.info("Downloading meteorological data...")

        # to ensure good logging, remember to pass logger=logger into whichever class you are using

        ### 1. Example SIMPLE DOWNLOAD OF meteorological data raster e.g. from Global Wind Atlas or New European Wind Atlas ### 
        
        # # Link to datasource info: https://globalwindatlas.info/
        # logger.info("Downloading the New European Wind Atlas data...")
        # api_url = "https://wps.neweuropeanwindatlas.eu/api/mesoscale-atlas/v1/get-data-bbox?southBoundLatitude=49.001844&northBoundLatitude=52.643063&westBoundLongitude=4.0979&eastBoundLongitude=10.656738&height=100&variable=wind_speed_mean"

        # # Specify the directory and file name for the downloaded data
        # file_name = "newa_wind_speed_mean_100m.tif"
        # file_path = os.path.join(met_data_dir, file_name)

        # # Perform the API request
        # response = requests.get(api_url)

        # # Check if the request was successful
        # if response.status_code == 200:
        #     # Write the response content to a file
        #     with open(file_path, 'wb') as file:
        #         file.write(response.content)
        #     logger.info(f"Download of {file_name} successful.")
        # else:
        #     logger.error(f"Failed to download data. Status code: {response.status_code}")


        ### 2. Example DOWNLOAD OF meteorological data from ERA5 API service ###

        # ERA5_downloader = ERA5Downloader(filename="north_sea_polygon.tif", logger=logger)

        # ERA5_downloader.download_era5_data()

        ## ASignal that the task is complete
        logger.info("Downloading Meterological Data task complete.")

        ### this creates the text file - delete if you set the output to the actual files downloaded
        with self.output().open('w') as f:
            f.write('Download Meterological Data task complete.')