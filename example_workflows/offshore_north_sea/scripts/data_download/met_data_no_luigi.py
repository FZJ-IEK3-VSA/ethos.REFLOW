import os
import json
import logging
from utils.config import ConfigLoader
from utils.data_download import ERA5Downloader

def main():
    """
    Main logic for the task.
    """
    ##################### DO NOT CHANGE #################################

    #### directory management ####
    config_loader = ConfigLoader()

    met_data_dir = config_loader.get_path("data", "met_data")
    project_data_dir = config_loader.get_path("data", "project_data")

    project_settings_path = config_loader.get_path("settings", "project_settings")
    with open(project_settings_path, 'r') as f:
        project_settings = json.load(f)

    years = list(range(project_settings["start_year"], project_settings["end_year"]+1))

    # configure logging
    log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadMeterologicalData.log')
    logger = config_loader.setup_task_logging('DownloadMeterologicalData', log_file)
    logger.info("Starting DownloadMeterologicalData task")  
    
    ####################################################################################
    ############## MAIN WORKFLOW #################
    logging.info("Downloading meteorological data...")

    ### 1.  DOWNLOAD OF meteorological data from ERA5 API service ###

    try:
        ERA5_downloader = ERA5Downloader(main_polygon_fname="north_sea_polygon.shp", logger=logger)
    except Exception as e:  
        logger.error(f"Failed to initialize ERA5Downloader. Please check filename. Error: {e} More information in the MainWorkflow.log file.")
    
    for year in years:
        try:
            ERA5_downloader.download_ERA5_data(expanded_distance=8, year=year)
        except Exception as e:  
            logger.error(f"Failed to download ERA5 data. Please check the logs for more information. Error: {e}")

if __name__ == "__main__":
    main()