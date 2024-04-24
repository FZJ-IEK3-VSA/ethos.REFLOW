import luigi
import requests
import os
import zipfile
import json
from pathlib import Path
from utils.config import ConfigLoader
from utils.data_download import DownloaderUtils
from utils.utils import populate_exclusion_data_paths
import logging

class DownloadExclusionsData(luigi.Task):
    """
    Luigi Task to download the exclusion data.
    """
    def requires(self):
        """
        Define any dependencies here. If this is a first step, return None 
        """
        return None

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadExclusionsData_complete.txt'))
    
    def run(self):
        """
        Main run method for the task. 
        """
        ##################### DO NOT CHANGE ######################################

        #### directory management ####
        config_loader = ConfigLoader()       

        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'DownloadExclusionsData.log')
        logger = config_loader.setup_task_logging('DownloadExclusionsData', log_file)
        logger.info("Starting DownloadExclusionsData task")        

        # load the project settings
        with open(config_loader.get_path("settings", "project_settings"), 'r') as file:
            project_settings = json.load(file)

        download_utils = DownloaderUtils(logger=logger)

        gadm_version = project_settings["gadm_version"]
        countries = project_settings["countries"]
        logger.info(f"List of countries: {countries}")

        exclusion_data_vector_paths = {}
        exclusion_data_raster_paths = {}

        ###########################################################################

        ############## MAIN WORKFLOW #################
        ######## 1. Download GADM data ########
        logger.info("Downloading GADM data...")
        for country in countries:
            download_utils.download_gadm_data(country)

        ################# 2. Download and extract the VECTOR exclusion data ##################
        logger.info("Downloading and extracting vector exclusion data...")
        
        ### 2.1. download existing wind farms from EMODnet 
        # Link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/8201070b-4b0b-4d54-8910-abcea5dce57f   
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/8201070b-4b0b-4d54-8910-abcea5dce57f/attachments/EMODnet_HA_Energy_WindFarms_20231124.zip"
        folder = "existing_wind_farms"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.2. download existing military areas from EMODnet
        # Link to datasource info: https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/579e4a3b-95e4-48c6-8352-914ebae0ae1d/attachments/EMODnet_HA_MilitaryAreas_20221216.zip 
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/579e4a3b-95e4-48c6-8352-914ebae0ae1d/attachments/EMODnet_HA_MilitaryAreas_20221216.zip"
        folder = "military_areas"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.3. download cultural hertiage and shipwrecks from EMODnet
        # Link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/e965088b-a265-4517-84df-c49b156af8a7
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/e965088b-a265-4517-84df-c49b156af8a7/attachments/EMODnet_HA_Heritage_Shipwrecks_20220720.zip"
        folder = "cultural_heritage"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.4. download protected areas from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/f727edd7-87b8-4b02-b173-14ca13025f6f
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/f727edd7-87b8-4b02-b173-14ca13025f6f/attachments/EMODnet_HA_Environment_WDPA_Sep2023_20230911.zip"
        folder = "protected_areas"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.5. download desalination plants from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/18d9daa1-eee4-4380-a2d0-fd20e4b47081
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/18d9daa1-eee4-4380-a2d0-fd20e4b47081/attachments/EMODnet_HA_Desalination_Plants_20210830.zip"
        folder = "desalination_plants"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.6. download data on ocean energy projects
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/srv/eng/catalog.search#/metadata/6414b069-8cb5-443e-a0d7-d08e909c43e2 
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/6414b069-8cb5-443e-a0d7-d08e909c43e2/attachments/EMODnet_HA_OceanEnergy_20231120.zip"
        folder = "ocean_energy_projects"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.7. download oil and gas platforms from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/d9da64ae-4bff-4cae-9ee8-58d9acc1d0fe 
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/d9da64ae-4bff-4cae-9ee8-58d9acc1d0fe/attachments/EMODnet_HA_OG_Active_Licences_20230228.zip"
        folder = "oil_and_gas"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.8. download data on pipelines from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/aca3dd01-77ac-47fe-8291-6ca916daaa6d
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/aca3dd01-77ac-47fe-8291-6ca916daaa6d/attachments/EMODnet_HA_Pipelines_20230705.zip"
        folder = "pipelines"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.9. download data on dumped munitions from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/661aa259-8ea9-49ae-a39d-49685057b013
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/661aa259-8ea9-49ae-a39d-49685057b013/attachments/EMODnet_HA_WasteDisposal_DumpedMunitions_20220623.zip"
        folder = "dumped_munitions"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.10. download data on telecommunication cables from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/39ebe289-410b-4a5d-88a4-51bfcde538de
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/39ebe289-410b-4a5d-88a4-51bfcde538de/attachments/EMODnet_HA_Cables_Telecommunication_20230628.zip"
        folder = "telecommunication_cables"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.11. download data on power cables from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/41b339f8-b29c-4550-b787-3d68f08fdbcc
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/41b339f8-b29c-4550-b787-3d68f08fdbcc/attachments/EMODnet_HA_Cables_Power_20230628.zip"
        folder = "power_cables"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        
        ### 2.12. download data on nuclear power plants from EMODnet
        # link to datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/9a095778-75a1-45fc-a458-bb0b2ff8e412
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/9a095778-75a1-45fc-a458-bb0b2ff8e412/attachments/EMODnet_HA_Nuclear_Plants_20190329.zip"
        folder = "nuclear_power_plants"
        download_utils.download_and_extract(url, folder)
        exclusion_data_vector_paths[folder] = []
        

        ########### 3 Download and extract the RASTER exclusion data ###########

        ### 3.1. download shipping lanes from EU (around 1 GB)
        # Link to datasource info: https://emodnet.ec.europa.eu/geonetwork/srv/eng/catalog.search#/metadata/74eef9c6-13fe-4630-b935-f26871c8b661
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/74eef9c6-13fe-4630-b935-f26871c8b661/attachments/EMODnet_HA_EMSA_Route_Density_all_2019-2022.zip"
        folder = "shipping_lanes"
        download_utils.download_and_extract(url, folder)
        exclusion_data_raster_paths[folder] = []

        ### 3.2. download the bathymetry data from EMODnet (around 4 GB)
        # Link to datasource info: https://www.gebco.net/data_and_products/gridded_bathymetry_data/
        url = "https://www.bodc.ac.uk/data/open_download/gebco/gebco_2023_sub_ice_topo/geotiff/"
        folder = "global_bathymetry"
        download_utils.download_and_extract(url, folder, filename="global_bathymetry.zip")  ## we need to add a filename since the URL does not end with a file extension
        exclusion_data_raster_paths[folder] = []

        ### 3.3. download data on fishing route density from EMODnet
        # link to the datasource info: https://emodnet.ec.europa.eu/geonetwork/emodnet/eng/catalog.search#/metadata/74eef9c6-13fe-4630-b935-f26871c8b661
        url = "https://ows.emodnet-humanactivities.eu/geonetwork/srv/api/records/74eef9c6-13fe-4630-b935-f26871c8b661/attachments/EMODnet_HA_EMSA_Route_Density_02_2019-2022.zip"
        folder = "fishing_route_density"
        download_utils.download_and_extract(url, folder)
        exclusion_data_raster_paths[folder] = []

        ## update the data paths
        ## update the directory structure in the data folder
        config_loader.update_data_paths()

        ## populate the exclusion_data_vector_paths and exclusion_data_raster_paths dictionaries
        exclusion_data_vector_paths = populate_exclusion_data_paths(config_loader.get_path("data", "exclusion_data", "raw"), exclusion_data_vector_paths)
        exclusion_data_raster_paths = populate_exclusion_data_paths(config_loader.get_path("data", "exclusion_data", "raw"), exclusion_data_raster_paths)

        ### save the dictionaries as json files
        exclusion_data_vector_paths_path = os.path.join(config_loader.get_path("data", "exclusion_data", "raw"), "exclusion_data_vector_paths.json")
        exclusion_data_raster_paths_path = os.path.join(config_loader.get_path("data", "exclusion_data", "raw"), "exclusion_data_raster_paths.json")

        with open(exclusion_data_vector_paths_path, 'w') as file:
            json.dump(exclusion_data_vector_paths, file, indent=4)

        with open(exclusion_data_raster_paths_path, 'w') as file:
            json.dump(exclusion_data_raster_paths, file, indent=4)

        # Signify that the task has been completed
        logger.info("Exclusion data download complete.")
        with self.output().open('w') as f:
            f.write('Exclusion data download complete.')