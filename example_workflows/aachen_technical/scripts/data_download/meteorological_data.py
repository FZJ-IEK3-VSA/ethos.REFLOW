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
        # # Link to information about the data = "https://example-URL.com"
        # api_url = "https://example-URL.com"

        # # specify the filename and directory to save the data
        # filename = "example_data.tif"
        # output_dir = os.path.join(met_data_dir, "example-datasource")
        # local_filename = os.path.join(output_dir, filename)

        # # ensure that the target directory exists
        # if not os.path.exists(os.path.dirname(output_dir)):
        #     os.makedirs(os.path.dirname(output_dir))

        # # Perform the API request
        # response = requests.get(api_url)

        # # Check if the request was successful
        # if response.status_code == 200:
        #     # Write the response content to a file
        #     with open(local_filename, 'wb') as file:
        #         file.write(response.content)
        #     logging.info("Download successful.")
        # else:
        #     logging.error(f"Failed to download data. Status code: {response.status_code}")


        ### 2. Example DOWNLOAD OF meteorological data from ERA5 API service ###

        # ERA5_downloader = ERA5Downloader(filename="north_sea_polygon.tif", logger=logger)

        # ERA5_downloader.download_era5_data()

        ## ASignal that the task is complete
        logger.info("Downloading Meterological Data task complete.")
        with self.output().open('w') as f:
            f.write('Download Meterological Data task complete.')