import os
import requests
import luigi
import json
from utils.config import ConfigLoader
from utils.vector_processing import VectorProcessor
from scripts.data_processing.process_project_data import ProcessProjectData
import geopandas as gpd
from utils.data_download import ERA5Downloader

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
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'completed_tasks', 'DownloadMeterologicalData_complete.txt'))
    
    def run(self):
        """
        Main logic for the task.
        """

        ##################### DO NOT CHANGE #################################

        #### directory management ####
        config_loader = ConfigLoader()

        met_data_dir = config_loader.get_path("data", "met_data")

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadMeterologicalData.log')
        logger = config_loader.setup_task_logging('DownloadMeterologicalData', log_file)
        logger.info("Starting DownloadMeterologicalData task")  

        with open (os.path.join(ConfigLoader().get_path("settings"), 'project_settings.json'), 'r') as f:
            project_settings = json.load(f)

        countries = project_settings['countries']

        vector_processor = VectorProcessor(logger=logger)
        
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

        # ############### 2. DOWNLOAD OF ERA5 data from CDSAPI service ##############
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

        ########## 3. Download of NEWA data from the API ##############
        # logger.info("Loading the World EEZ shapefile...")
        # world_eez = gpd.read_file(os.path.join(config_loader.get_path("data"), "project_data", "World_EEZ_v12_20231025", "eez_v12.shp"))
        # eez_filtered = world_eez[world_eez['ISO_TER1'].isin(countries)]

        # ## clip the EEZs to the North Sea
        # main_polygon = gpd.read_file(os.path.join(config_loader.get_path("data"), "project_data", "MAIN_REGION_POLYGON", "north_sea_polygon.shp"))
        # main_polygon = main_polygon.to_crs(epsg=4326)

        # # Clip the EEZs to the North Sea polygon
        # logger.info("Clipping the EEZs to the North Sea...")
        # eez_clipped = gpd.clip(eez_filtered, main_polygon)

        # for _, country in eez_clipped.iterrows():
        #     for height in ["100"]:
        #         for year in [2014, 2015, 2016, 2017, 2018]:
        #             # Extract and expand the bounding box
        #             minx, miny, maxx, maxy = country['geometry'].bounds
        #             expanded_minx = minx - 0.02  # normally 0.25
        #             expanded_miny = miny - 0.02
        #             expanded_maxx = maxx + 0.02
        #             expanded_maxy = maxy + 0.02

        #             if country['ISO_TER1'] == 'NOR' or country['ISO_TER1'] == 'GBR':
        #                 logger.info(f"Bounding box for {country['ISO_TER1']} expanded to: {expanded_minx}, {expanded_miny}, {expanded_maxx}, {expanded_maxy}")
        #                 # Calculate midpoints to split the bounding box into four parts
        #                 midpoint_x = (expanded_minx + expanded_maxx) / 2  # Vertical split (longitude)
        #                 midpoint_y = (expanded_miny + expanded_maxy) / 2  # Horizontal split (latitude)

        #                 # Define the four bounding boxes
        #                 bounding_boxes = [
        #                     {'minx': expanded_minx, 'maxx': midpoint_x, 'miny': expanded_miny, 'maxy': midpoint_y},  # Bottom-left
        #                     {'minx': midpoint_x, 'maxx': expanded_maxx, 'miny': expanded_miny, 'maxy': midpoint_y},  # Bottom-right
        #                     {'minx': expanded_minx, 'maxx': midpoint_x, 'miny': midpoint_y, 'maxy': expanded_maxy},  # Top-left
        #                     {'minx': midpoint_x, 'maxx': expanded_maxx, 'miny': midpoint_y, 'maxy': expanded_maxy}   # Top-right
        #                 ]

        #                 # Download data for each half
        #                 for i, bbox in enumerate(bounding_boxes, start=1):
        #                     api_url = (
        #                         f"https://wps.neweuropeanwindatlas.eu/api/mesoscale-ts/v1/get-data-bbox?"
        #                         f"southBoundLatitude={bbox['miny']}&northBoundLatitude={bbox['maxy']}&"
        #                         f"westBoundLongitude={bbox['minx']}&eastBoundLongitude={bbox['maxx']}&"
        #                         f"height={height}&variable=WS&dt_start={year}-01-01T00:00:00&dt_stop={year}-12-31T23:30:00"
        #                     )

        #                     output_dir = os.path.join(met_data_dir, 'NEWA', 'time_series', country['ISO_TER1'])
        #                     os.makedirs(output_dir, exist_ok=True)

        #                     file_name = f"newa_wind_speed_{country['ISO_TER1']}_{year}_chunk_{i}_{height}m.nc"
        #                     file_path = os.path.join(output_dir, file_name)
        #                      # Check if file already exists
        #                     if os.path.exists(file_path):
        #                         logger.info(f"{file_name} already exists. Skipping download.")
        #                     else:
        #                         logger.info(f"Downloading the New European Wind Atlas time series data chunk {i} for {country['ISO_TER1']} in {year} at height {height}...")
        #                         response = requests.get(api_url)
        #                         # Check if the request was successful
        #                         if response.status_code == 200:
        #                             # Write the response content to a file
        #                             with open(file_path, 'wb') as file:
        #                                 file.write(response.content)
        #                             logger.info(f"Download of {file_name} successful.")
        #                         else:
        #                             logger.error(f"Failed to download data for {country['ISO_TER1']}, year {year}. Status code: {response.status_code}")

        #             else:
        #                 # # Construct the API URL with expanded bounding box parameters
        #                 logger.info(f"Downloading the New European Wind Atlas time series data for {country['ISO_TER1']} in {year} at height {height}...")
        #                 api_url = (
        #                     f"https://wps.neweuropeanwindatlas.eu/api/mesoscale-ts/v1/get-data-bbox?"
        #                     f"southBoundLatitude={expanded_miny}&northBoundLatitude={expanded_maxy}&"
        #                     f"westBoundLongitude={expanded_minx}&eastBoundLongitude={expanded_maxx}&"
        #                     f"height={height}&variable=WS&dt_start={year}-01-01T00:00:00&dt_stop={year}-12-31T23:30:00"
        #                 )

        #                 output_dir = os.path.join(met_data_dir, 'NEWA', 'time_series', country['ISO_TER1'])
        #                 os.makedirs(output_dir, exist_ok=True)

        #                 file_name = f"newa_wind_speed_{country['ISO_TER1']}_{year}_{height}m.nc"
        #                 file_path = os.path.join(output_dir, file_name)

        #                 # Check if file already exists
        #                 if os.path.exists(file_path):
        #                     logger.info(f"{file_name} already exists. Skipping download.")
        #                 else:
        #                     response = requests.get(api_url)
        #                     # Check if the request was successful
        #                     if response.status_code == 200:
        #                         # Write the response content to a file
        #                         with open(file_path, 'wb') as file:
        #                             file.write(response.content)
        #                         logger.info(f"Download of {file_name} successful.")
        #                     else:
        #                         logger.error(f"Failed to download data for {country['ISO_TER1']}, year {year}. Status code: {response.status_code}")
        #                         logger.info("Trying with the original bounding box...")
        #                         # Construct the API URL with original bounding box parameters
        #                         api_url = (
        #                             f"https://wps.neweuropeanwindatlas.eu/api/mesoscale-ts/v1/get-data-bbox?"
        #                             f"southBoundLatitude={miny}&northBoundLatitude={maxy}&"
        #                             f"westBoundLongitude={minx}&eastBoundLongitude={maxx}&"
        #                             f"height={height}&variable=WS&dt_start={year}-01-01T00:00:00&dt_stop={year}-12-31T23:30:00"
        #                         )
        #                         response = requests.get(api_url)
        #                         # Check if the request was successful
        #                         if response.status_code == 200:
        #                             # Write the response content to a file
        #                             with open(file_path, 'wb') as file:
        #                                 file.write(response.content)
        #                             logger.info(f"Download of {file_name} successful.")
        #                         else:
        #                             logger.error(f"Failed to download data for {country['ISO_TER1']}, year {year}. Status code: {response.status_code}")

        ## Signal that the task is complete
        logger.info("Downloading Meteorological Data task complete.")
        with self.output().open('w') as f:
            f.write('Download Meteorological Data task complete.')