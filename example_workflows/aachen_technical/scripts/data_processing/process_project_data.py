from utils.config import ConfigLoader
from utils.vector_processing import VectorProcessor
from scripts.data_download.project_data import DownloadProjectData
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
        return [DownloadProjectData()]

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("data", "project_data"), 'MAIN_REGION_POLYGON', 'Aachen.shp'))
    
    def run(self):
        """
        Main run method for the task.
        """
        ################## DO NOT CHANGE ############################
        #### directory management ####
        config_loader = ConfigLoader()

        project_settings_path = config_loader.get_path("settings", "project_settings")
        project_data_dir = config_loader.get_path("data", "project_data")

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessProjectData.log')
        logger = config_loader.setup_task_logging('ProcessProjectData', log_file)
        logger.info("Starting ProcessProjectData task")

        vector_processor = VectorProcessor(logger=logger)
        
        # load the list of countries and zoom level 
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)

        countries = project_settings["countries"]  ## in this example there is only one country
        zoom = project_settings["zoom_level"]
        crs = project_settings["crs"]
        place = project_settings["GID_2"]  # this is Aachen for our example but can be changed. 
        place_short = project_settings["place_name_short"]  # this is the short name for the place - used for file naming

        ############## MAIN WORKFLOW #################

        ## first load the GADM data for Germany at the correct zoom level ##
        logger.info(f"Loading GADM data for Germany at zoom level {zoom} from {config_loader.get_gadm_file_paths('gadm', ['DEU'], zoom)['DEU']}")
        germany_gdf = gpd.read_file(config_loader.get_gadm_file_paths('gadm', ['DEU'], zoom)['DEU'])

        ### here we will extract the region from the country polygon and save to the MAIN POLYGON folder ##
        place_gdf = vector_processor.extract_subpolygon(germany_gdf, 'GID_2', place)

        ## now we need to convert the extracted polygon to the correct CRS ##
        logger.info(f"CRS of the extracted polygon: {place_gdf.crs}")
        place_gdf = place_gdf.to_crs(crs)
        logger.info(f"Converted CRS of the extracted polygon: {place_gdf.crs}")
       
        ## save the extracted polygon to the MAIN POLYGON folder ##
        main_region_dir = os.path.join(project_data_dir, 'MAIN_REGION_POLYGON')
        if not os.path.exists(main_region_dir):
            os.makedirs(main_region_dir)

        place_gdf.to_file(os.path.join(main_region_dir, f'{place_short}.shp'))

        ############ DO NOT CHANGE ################

        logger.info("Exclusion data download complete.")