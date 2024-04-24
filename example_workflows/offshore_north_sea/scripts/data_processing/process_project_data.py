from utils.config import ConfigLoader
from utils.vector_processing import VectorProcessor
from scripts.data_download.exclusions_data import DownloadExclusionsData
import geopandas as gpd
import luigi
import json
import logging
import os

#### THIS SCRIPT MUST BE RUN AS IT IS A DEPENDENCY FOR THE NEXT TASK ####
#### However, the main logic can be left blank if you do not need to add additional buffers to the regions - eg around coastlines or national borders ####  

class ProcessProjectData(luigi.Task):
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
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessProjectData_complete.txt'))

    def run(self):
        """
        Main run method for the task.
        """
        #### directory management ####
        config_loader = ConfigLoader()

        project_settings_path = config_loader.get_path("settings", "project_settings")
        exclusion_settings_path = config_loader.get_path("settings", "exclusions_settings")
        project_data_dir = config_loader.get_path("data", "project_data")
        raw_data_dir = config_loader.get_path("data", "exclusion_data", "raw")
        processed_data_dir = config_loader.get_path("data", "exclusion_data", "processed")

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessProjectData.log')
        logger = config_loader.setup_task_logging('ProcessProjectData', log_file)
        logger.info("Starting ProcessProjectData task")

        vector_processor = VectorProcessor(logger=logger)

        ############## MAIN WORKFLOW #################

        # load the list of countries and zoom level 
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)

        countries = project_settings["countries"]
        zoom = project_settings["zoom_level"]
        crs = project_settings["crs"]
        buffer_distance = project_settings["min_distance_to_coast"]

        ## get the paths to the country shapefile data
        country_paths = ConfigLoader().get_gadm_file_paths('gadm', country_codes=countries, zoom_level=zoom)

        ###### 1. Create the main region polyon by merging the existing North Sea Polygon with the Skagerrak polygon ######
        config_loader.update_data_paths()

        ## load and reproject the North Sea polygon
        north_sea_path = os.path.join(project_data_dir, "north_sea_polygon", "iho.shp")
        north_sea_polygon = gpd.read_file(north_sea_path)
        north_sea_polygon = vector_processor.reproject_vector(north_sea_polygon, crs)

        ## load and reproject Skagerrak polygon
        skagerrak_path = os.path.join(project_data_dir, "Skagerrak_polygon", "iho.shp")
        skagerrak_polygon = gpd.read_file(skagerrak_path)
        skagerrak_polygon = vector_processor.reproject_vector(skagerrak_polygon, crs)

        ## merge the polygons
        north_sea_processed = vector_processor.merge_two_vectors_and_flatten(north_sea_polygon, skagerrak_polygon)

        # save the merged polygon
        os.makedirs(os.path.join(project_data_dir, "MAIN_REGION_POLYGON"), exist_ok=True)
        output_filepath = os.path.join(project_data_dir, "MAIN_REGION_POLYGON", "north_sea_polygon.shp")
        north_sea_processed.to_file(output_filepath)
        logger.info(f"Saved merged and flattened vector to {output_filepath}")


        ###### 2. Create the coastal buffers ######
        # 1. process all the country shapefiles
        logger.info("Processing coastal buffers")
        all_coastlines, all_coastal_buffers = vector_processor.clip_buffer_merge_vector_data(country_paths, north_sea_processed, buffer_distance)

        #2. save the coastline polygons
        os.makedirs(os.path.join(project_data_dir, "north_sea_coasts"), exist_ok=True)
        coastlines_path = os.path.join(project_data_dir, "north_sea_coasts", "north_sea_coastlines.shp")
        all_coastlines.to_file(coastlines_path)
        logger.info(f"Saved coastlines to {coastlines_path}")

        #3. save the processed polygons
        os.makedirs(os.path.join(processed_data_dir, "north_sea_coastal_buffers"), exist_ok=True)
        # Save GeoDataFrames to shapefiles
        buffers_path = os.path.join(processed_data_dir, "north_sea_coastal_buffers", f"north_sea_coastal_buffers_{buffer_distance // 1000}km.shp")
        all_coastal_buffers.to_file(buffers_path)
        logger.info(f"Saved coastal buffers to {buffers_path}")

        # update data paths
        config_loader.update_data_paths()

        ############ DO NOT CHANGE ############
        # mark the task as complete
        logger.info("ProcessProjectData task complete.")
        with self.output().open('w') as file:
            file.write('Complete')