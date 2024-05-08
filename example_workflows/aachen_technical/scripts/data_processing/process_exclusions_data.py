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
import pandas as pd

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

        landuse_exclusions = project_settings["landuse_exclusions"]
        nature_exclusions = project_settings["nature_exclusions"]
        protected_exclusions = project_settings["boundary_exclusions"]
        road_types = project_settings["road_exclusions"]

        ############## MAIN WORKFLOW #################
        # to ensure good logging, remember to pass logger=logger into whichever class you are using
        geometry_types = ["polygon", "point", "linestring"]
        # load up the raw exclusion data
        fp = os.path.join(raw_data_dir, f"{region_name}.osm.pbf")

        # initialize the OSM object
        osm = pyrosm.OSM(fp)

        logger.info("OSM object loaded.")
        
        ### START by processing the nature data ####
        ## 1.1. load the data, convert to correct CRS, and save as shp files for each type of nature data type
        nature = osm.get_natural()
        logger.info("Nature data loaded.")
        # print all the nature types in the logger
        
        for nature_type in nature_exclusions:
            nature_type_data = nature[nature["natural"] == nature_type]
            if not nature_type_data.empty:
                nature_type_data = nature_type_data.to_crs("EPSG:3035")
                vector_processor.save_geodataframe(nature_type_data, os.path.join(raw_data_dir, f"{nature_type}.shp"))
                logger.info(f"Data saved for nature type: {nature_type}")
            else:
                logger.error(f"No data found for nature type: {nature_type}")
                continue

        ### 1.2. Clip the nature data to the main Aachen polygon
        # search for different geometry types in the nature data
        for nature_type in nature_exclusions:
            for geometry_type in geometry_types:
                if not os.path.exists(os.path.join(raw_data_dir, f"{nature_type}_{geometry_type}.shp")):
                    logger.error(f"Data not found for nature type: {nature_type} and geometry type: {geometry_type}")
                    continue
                geometry = gpd.read_file(os.path.join(raw_data_dir, f"{nature_type}_{geometry_type}.shp"))

                logger.info("Flattening the geometry")
                geometry = vector_processor.flatten_multipolygons(geometry)

                logger.info(f"Clipping geometry type: {geometry_type}")
                clipped_geometry = gpd.clip(geometry, main_region)

                if not clipped_geometry.empty:
                    vector_processor.save_geodataframe(clipped_geometry, os.path.join(processed_data_dir, f"{nature_type}.shp"))
                    logger.info(f"Data saved for nature type: {nature_type} and geometry type: {geometry_type}")
                else:
                    logger.error(f"No data after clipping with the main region for nature type: {nature_type} and geometry type: {geometry_type}")
                    continue
        
        ### 2.1. Now we get the boundary data for national parks and protected areas
        for protection_type in protected_exclusions:
            logger.info("Loading national park / protected area data")
            boundary = osm.get_boundaries(boundary_type=protection_type)
            protected_area = boundary[boundary["boundary"] == protection_type]
            if not protected_area.empty:
                protected_area = protected_area.to_crs("EPSG:3035")
                save_path = os.path.join(raw_data_dir, f"{protection_type}.shp")
                vector_processor.save_geodataframe(protected_area, save_path)
                logger.info(f"Data saved for {protection_type}")
            else:
                logger.error(f"No data found for {protection_type}")

        ### 2.2. Clip the protected area data to the main Aachen polygon
        for protection_type in protected_exclusions:
            for geometry_type in geometry_types:
                if not os.path.exists(os.path.join(raw_data_dir, f"{protection_type}_{geometry_type}.shp")):
                    logger.error(f"Data not found for protection type: {protection_type} and geometry type: {geometry_type}")
                    continue
                geometry = gpd.read_file(os.path.join(raw_data_dir, f"{protection_type}_{geometry_type}.shp"))

                logger.info("Flattening the geometry")
                geometry = vector_processor.flatten_multipolygons(geometry)

                logger.info(f"Clipping geometry type: {geometry_type}")
                clipped_geometry = gpd.clip(geometry, main_region)

                if not clipped_geometry.empty:
                    vector_processor.save_geodataframe(clipped_geometry, os.path.join(processed_data_dir, f"{protection_type}.shp"))
                    logger.info(f"Data saved for protection type: {protection_type} and geometry type: {geometry_type}")
                else:
                    logger.error(f"No data after clipping with the main region for protection type: {protection_type} and geometry type: {geometry_type}")
                    continue

        ### 3.1. Next process for the landuse data
        landuse = osm.get_landuse()
        logger.info("Landuse data loaded.")

        for landuse_type in landuse_exclusions:
            landuse_type_data = landuse[landuse["landuse"] == landuse_type]
            if not landuse_type_data.empty:
                landuse_type_data = landuse_type_data.to_crs("EPSG:3035")
                vector_processor.save_geodataframe(landuse_type_data, os.path.join(raw_data_dir, f"{landuse_type}.shp"))
                logger.info(f"Data saved for landuse type: {landuse_type}")
            else:
                logger.error(f"No data found for landuse type: {landuse_type}")
                continue
        
        ### 3.2. Clip the landuse data to the main Aachen polygon
        # search for different geometry types in the landuse data
        for landuse_type in landuse_exclusions:
            for geometry_type in geometry_types:
                try:
                    logger.info(f"Processing landuse type: {landuse_type} and geometry type: {geometry_type}")
                    if not os.path.exists(os.path.join(raw_data_dir, f"{landuse_type}_{geometry_type}.shp")):
                        logger.error(f"Data not found for landuse type: {landuse_type} and geometry type: {geometry_type}")
                        continue
                    geometry = gpd.read_file(os.path.join(raw_data_dir, f"{landuse_type}_{geometry_type}.shp"))

                    logger.info("Flattening the geometry")
                    geometry = vector_processor.flatten_multipolygons(geometry)

                    if geometry_type == "polygon" and landuse_type in ["military"]:
                        # add a small buffer around the military polygons
                        geometry = geometry.buffer(0)

                    logger.info(f"Clipping geometry type: {geometry_type}")
                    clipped_geometry = gpd.clip(geometry, main_region)

                    if not clipped_geometry.empty:
                        vector_processor.save_geodataframe(clipped_geometry, os.path.join(processed_data_dir, f"{landuse_type}.shp"))
                        logger.info(f"Data saved for landuse type: {landuse_type} and geometry type: {geometry_type}")
                    else:
                        logger.error(f"No data after clipping with the main region for landuse type: {landuse_type} and geometry type: {geometry_type}")
                        continue
                except Exception as e:
                    logger.error(f"Error processing landuse type: {landuse_type} and geometry type: {geometry_type}, error: {e}")
                    continue

    
        ### 4.1. Now the get the roads data
        roads = osm.get_network(network_type="driving")
        logger.info("Road data loaded.")

        for road_type in road_types:
            road_type_data = roads[roads["highway"] == road_type]
            if not road_type_data.empty:
                road_type_data = road_type_data.to_crs("EPSG:3035")
                vector_processor.save_geodataframe(road_type_data, os.path.join(raw_data_dir, f"{road_type}.shp"))
                logger.info(f"Data saved for road type: {road_type}")
            else:
                logger.error(f"No data found for road type: {road_type}")
                continue

        ### 4.2. Clip the road data to the main Aachen polygon
        # search for different geometry types in the road data
        for road_type in road_types:
            for geometry_type in ["multilinestring"]:
                try:
                    logger.info(f"Processing road type: {road_type} and geometry type: {geometry_type}")
                    if not os.path.exists(os.path.join(raw_data_dir, f"{road_type}_{geometry_type}.shp")):
                        logger.error(f"Data not found for road type: {road_type} and geometry type: {geometry_type}")
                        continue
                    geometry = gpd.read_file(os.path.join(raw_data_dir, f"{road_type}_{geometry_type}.shp"))

                    logger.info("Flattening the geometry")
                    geometry = vector_processor.flatten_multipolygons(geometry)

                    logger.info(f"Clipping geometry type: {geometry_type}")
                    clipped_geometry = gpd.clip(geometry, main_region)

                    if not clipped_geometry.empty:
                        vector_processor.save_geodataframe(clipped_geometry, os.path.join(processed_data_dir, f"{road_type}.shp"))
                        logger.info(f"Data saved for road type: {road_type} and geometry type: {geometry_type}")
                    else:
                        logger.error(f"No data after clipping with the main region for road type: {road_type} and geometry type: {geometry_type}")
                        continue
                except Exception as e:
                    logger.error(f"Error processing road type: {road_type} and geometry type: {geometry_type}, error: {e}")
                    continue

        ############ DO NOT CHANGE ############
        # mark the task as complete
        logger.info("ProcessExclusionsData task complete.")
        with self.output().open('w') as file:
            file.write('Complete')