import requests
import os
import zipfile
import json
from pathlib import Path
from utils.config import ConfigLoader

##################### DO NOT CHANGE #################################

#### directory management ####
config_loader = ConfigLoader()
output_dir = config_loader.get_path("data")
print(output_dir)
############## MAIN WORKFLOW #################
