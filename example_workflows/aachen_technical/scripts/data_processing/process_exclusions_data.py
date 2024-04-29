from utils.config import ConfigLoader
from utils.vector_processing import VectorProcessor
from scripts.data_download.exclusions_data import DownloadExclusionsData
import geopandas as gpd
import luigi
import json
import logging
import os
import pyrosm
import matplotlib.pyplot as plt

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
        return [DownloadExclusionsData()]

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessExclusionsData_complete.txt'))

    def run(self):
        """
        Main run method for the task.
        """
        #### directory management ####
        config_loader = ConfigLoader()
        
        project_settings_path = config_loader.get_path("settings", "project_settings")
        project_data_dir = config_loader.get_path("data", "project_data")
        raw_data_dir = config_loader.get_path("data", "exclusion_data", "raw")
        processed_data_dir = config_loader.get_path("data", "exclusion_data", "processed")
        # create the processed data directory if it does not exist
        os.makedirs(processed_data_dir, exist_ok=True)

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessExclusionsData.log')
        logger = config_loader.setup_task_logging('ProcessRegionBuffers', log_file)
        logger.info("Starting ProcessExclusionsData task")

        vector_processor = VectorProcessor(logger=logger)

        # load the project settings
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
        
        region_name = project_settings["OSM_region_name"]
        place_name = project_settings["place_name_short"]
        main_region = gpd.read_file(os.path.join(project_data_dir, "MAIN_REGION_POLYGON", f"{place_name}.shp"))

        ############## MAIN WORKFLOW #################
        # to ensure good logging, remember to pass logger=logger into whichever class you are using
        
        # load up the raw exclusion data
        # fp = os.path.join(raw_data_dir, f"{region_name}.osm.pbf")

        # # initialize the OSM object
        # osm = pyrosm.OSM(fp)

        # logger.info("OSM object loaded.")
        # landuse = osm.get_landuse()
        
        # residential = landuse[landuse["landuse"] == "residential"]

        # residential = residential.to_crs("EPSG:3035")
        # logger.info(f"Data loaded. CRS: {residential.crs}")

        # # Check if the clipped GeoDataFrame is not empty
        # if not residential.empty:
        #     # Save to a Shapefile
        #     vector_processor.save_geodataframe(residential, os.path.join(raw_data_dir, "residential.shp"))
        #     logger.info("Data saved")
        # else:
        #     logger.error("No data after clipping with the main region.")

        # load the clipped data
        # search for different geometry types
        geometry_types = ["polygon", "point", "linestring"]
        for geometry_type in geometry_types:
            if not os.path.exists(os.path.join(raw_data_dir, f"residential_{geometry_type}.shp")):
                logger.error(f"Data not found for geometry type: {geometry_type}")
                continue
            geometry = gpd.read_file(os.path.join(raw_data_dir, f"residential_{geometry_type}.shp"))

            logger.info("Flattening the geometry")
            geometry = vector_processor.flatten_multipolygons(geometry)

            logger.info(f"Clipping geometry type: {geometry_type}")
            
            clipped_geometry = gpd.clip(geometry, main_region)
            if not clipped_geometry.empty:
                vector_processor.save_geodataframe(clipped_geometry, os.path.join(processed_data_dir, f"residential.shp"))
                logger.info(f"Data saved for geometry type: {geometry_type}")
            else:
                logger.error(f"No data after clipping with the main region for geometry type: {geometry_type}")
                continue

        ############ DO NOT CHANGE ############
        # mark the task as complete
        logger.info("ProcessExclusionsData task complete.")
        with self.output().open('w') as file:
            file.write('Complete')