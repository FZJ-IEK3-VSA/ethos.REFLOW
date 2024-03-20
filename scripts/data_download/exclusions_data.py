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

project_settings_path = config_loader.get_path("settings", "project_settings")

# load the list of countries
with open(project_settings_path, 'r') as file:
    country_settings = json.load(file)

countries = country_settings["countries"]

# configure logging
logging.basicConfig(filename=os.path.join(config_loader.get_path("output"), 'logs', '1_data_download.log'), 
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

############## MAIN WORKFLOW #################

### 1. Download GADM data
# Define the version of GADM data to download
gadm_version = "41"

for country in countries:
    download_gadm_data(country, gadm_version, project_data_dir)

#### 2. Download and extract the exclusion data
logging.info("Downloading and extracting exclusion data...")
### 2.1. Example of downloading and extracting a single file
# Link to information about the data = "https://example-URL.com"
download_and_extract("https://example-URL.com", raw_output_dir)