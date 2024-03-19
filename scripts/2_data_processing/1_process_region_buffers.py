import utils.data_processing as dp
from utils.config import ConfigLoader
from utils.data_processing import VectorProcessor as vp
import json
import logging
import os

#### THIS SCRIPT IS ONLY NECESSARY IF YOU ARE ADDING EXCLUSION BUFFERS TO YOUR REGIONAL DATA; 
#### e.g. adding a buffer around coastlines to account for EEZ boundaries, or around national borders ####

#### directory management ####
config_loader = ConfigLoader()
project_settings = config_loader.get_settings("project_settings")

project_settings_path = config_loader.get_path("settings", "project_settings")

# configure logging
logging.basicConfig(filename=os.path.join(config_loader.get_path("output"), 'logs', '2_data_processing.log'), 
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

############## MAIN WORKFLOW #################

