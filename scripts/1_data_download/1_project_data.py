import requests
import os
import zipfile
import json
from pathlib import Path

##################### DO NOT CHANGE #################################

#### directory management ####
script_dir = Path(os.path.dirname(__file__))
project_root = script_dir.parent.parent
config_path = project_root / "settings" / "directory_management.json"

# Load the config file
with open(config_path, "r") as f:
    config = json.load(f)

raw_data_dir = Path(project_root / config["data"]["exclusion_data"]["raw"])
print(f"Raw data directory: {raw_data_dir}")


############## MAIN WORKFLOW #################
