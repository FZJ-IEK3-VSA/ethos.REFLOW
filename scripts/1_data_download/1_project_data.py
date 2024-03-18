import requests
import os
import zipfile
import json
from pathlib import Path
from utils.config import ConfigLoader
from utils.data_download import download_gadm_data, download_and_extract
import logging

##################### DO NOT CHANGE #################################

#### directory management ####
config_loader = ConfigLoader()

raw_output_dir = config_loader.get_path("data", "exclusion_data", "raw")
project_data_dir = config_loader.get_path("data", "project_data")
gadm_dir = os.path.join(project_data_dir, "gadm")

country_settings_path = config_loader.get_path("settings", "country_settings")

# configure logging
logging.basicConfig(filename=os.path.join(config_loader.get_path("output"), 'logs', 'data_download.log'), 
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

############## MAIN WORKFLOW #################

### 1. Download GADM data
# Define the version of GADM data to download
gadm_version = "41"

# load the list of countries
with open(country_settings_path, 'r') as file:
    country_settings = json.load(file)

countries = country_settings["countries"]

for country in countries:
    download_gadm_data(country, gadm_version, gadm_dir)