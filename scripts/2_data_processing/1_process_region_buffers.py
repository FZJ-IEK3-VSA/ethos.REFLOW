import utils.data_processing as dp
from utils.config import ConfigLoader
import json
import logging

#### directory management ####
config_loader = ConfigLoader()
project_settings = config_loader.get_settings("project_settings")

project_settings_path = config_loader.get_path("settings", "project_settings")

# configure logging
logging.basicConfig(filename=os.path.join(config_loader.get_path("output"), 'logs', '2_data_processing.log'), 
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

############## MAIN WORKFLOW #################