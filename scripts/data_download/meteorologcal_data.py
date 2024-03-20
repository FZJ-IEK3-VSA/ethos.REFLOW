import os
import json
import logging
import requests
from utils.config import ConfigLoader

##################### DO NOT CHANGE #################################

#### directory management ####
config_loader = ConfigLoader()

met_data_dir = config_loader.get_path("data", "met_data")
project_data_dir = config_loader.get_path("data", "project_data")

country_settings_path = config_loader.get_path("settings", "country_settings")

# configure logging
logging.basicConfig(filename=os.path.join(config_loader.get_path("output"), 'logs', '1_data_download.log'), 
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

############## MAIN WORKFLOW #################
logging.info("Downloading meteorological data...")

### 1. Download example meteorological data raster. 
# Link to information about the data = "https://example-URL.com"
api_url = "https://example-URL.com"

# specify the filename and directory to save the data
filename = "example_data.tif"
output_dir = os.path.join(met_data_dir, "example-datasource")
local_filename = os.path.join(output_dir, filename)

# ensure that the target directory exists
if not os.path.exists(os.path.dirname(output_dir)):
    os.makedirs(os.path.dirname(output_dir))

# Perform the API request
response = requests.get(api_url)

# Check if the request was successful
if response.status_code == 200:
    # Write the response content to a file
    with open(local_filename, 'wb') as file:
        file.write(response.content)
    logging.info("Download successful.")
else:
    logging.error(f"Failed to download data. Status code: {response.status_code}")
