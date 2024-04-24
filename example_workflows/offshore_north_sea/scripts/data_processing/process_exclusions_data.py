from utils.config import ConfigLoader
from utils.vector_processing import VectorProcessor
from utils.raster_processing import RasterProcesser
from utils.utils import check_files_exist, rename_files_in_folder
from scripts.data_processing.process_project_data import ProcessProjectData
import geopandas as gpd
import luigi
import json
import logging
import os

from pyproj import Transformer
from shapely.geometry import shape

#### THIS SCRIPT MUST BE RUN AS IT IS A DEPENDENCY FOR THE NEXT TASK ####
#### However, the main logic can be left blank if you do not need to add additional buffers to the regions - eg around coastlines or national borders ####  

class ProcessExclusionsData(luigi.Task):
    """
    Luigi Task to process the region buffers for the project.
    """
    def requires(self):
        """
        This task requires the DownloadExclusionsData task to be completed.
        """
        return [ProcessProjectData()]

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessExclusionsData_complete.txt'))

    def run(self):
        """
        Main run method for the task.
        """
        #### directory annd variables management ####
        config_loader = ConfigLoader()

        project_settings_path = config_loader.get_path("settings", "project_settings")
        exclusion_settings_path = config_loader.get_path("settings", "exclusions_settings")
        project_data_dir = config_loader.get_path("data", "project_data")
        raw_data_dir = config_loader.get_path("data", "exclusion_data", "raw")
        processed_data_dir = config_loader.get_path("data", "exclusion_data", "processed")

        log_file = os.path.join(config_loader.get_path("output"), 'logs', 'ProcessExclusionsData.log')
        logger = config_loader.setup_task_logging('ProcessRegionBuffers', log_file)
        logger.info("Starting ProcessExclusionsData task")

        vector_processor = VectorProcessor(logger=logger)
        raster_processor = RasterProcesser(logger=logger)

        # load the exclusions dictionary
        with open(exclusion_settings_path, 'r') as file:
            exclusion_settings = json.load(file)

        ## only update the name of the file to chnage for your area of interest ##
        main_polygon_fname = "north_sea_polygon.shp"
        main_polygon_dir = os.path.join(config_loader.get_path("data", "project_data"), "MAIN_REGION_POLYGON")
        main_polygon_path = os.path.join(main_polygon_dir, main_polygon_fname)

        
        ############## MAIN WORKFLOW #################
        #### 1. Process all the vector exclusion data

        with open(os.path.join(raw_data_dir, "exclusion_data_vector_paths.json"), 'r') as file:
            vector_path_dict = json.load(file)

        # iterate through all the raw data, clip the datasets to the main polygon and save
        vector_processor.clip_and_save_vector_datasets(vector_path_dict, main_polygon_path)

        #### 2. Process all the raster exclusion data

        #### 2.1. the bathymetry data
        logger.info("Processing raster data...")
        # logger.info("Processing bathymetry data...")
        with open(os.path.join(raw_data_dir, "exclusion_data_raster_paths.json"), 'r') as file:
            raster_path_dict = json.load(file)

        main_polygon = gpd.read_file(main_polygon_path)
        
        bbox = vector_processor.calculate_and_transform_bbox(main_polygon, expand_size=0.5)
        
        logger.info(f"Bounding box for the main region: {bbox}")

        ## only the following extent is required for the North Sea region ##
        bathymetry_path_dict = {
            "global_bathymetry_e": "global_bathymetry/gebco_2023_sub_ice_n90.0_s0.0_w0.0_e90.0.tif",
            "global_bathymetry_w": "global_bathymetry/gebco_2023_sub_ice_n90.0_s0.0_w-90.0_e0.0.tif"
            }

        raster_processor.process_and_save_bathymetry(bathymetry_path_dict, main_polygon, bbox, filename="north_sea_bathymetry.tif")
        logger.info("Bathymetry data processed.")
        
        
        #### 2.2. process the shipping data
        logger.info("Processing shipping data...")
        shipping_paths = raster_path_dict["shipping_lanes"]

        shipping_paths_2022 = [file for file in shipping_paths if "all_europe-monthly-2022" in file]

        for path in shipping_paths_2022:
            shipping_paths_2022[shipping_paths_2022.index(path)] = os.path.join(raw_data_dir, path)
        
        raster_processor.process_and_save_shipping_lanes(shipping_paths_2022, main_polygon, filename="north_sea_shipping_lanes_2022.tif")
        logger.info("Shipping data processed.")

        rename_files_in_folder(processed_data_dir)

        ############ DO NOT CHANGE ############
        # mark the task as complete
        logger.info("ProcessExclusionsData task complete.")
        with self.output().open('w') as file:
            file.write('Complete')