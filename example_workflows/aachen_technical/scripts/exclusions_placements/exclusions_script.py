import glaes as gl
import os
import pandas as pd
from utils.config import ConfigLoader
import logging
import json
import time

"""
Main logic for the task.
"""
##################### DO NOT CHANGE #################################
#### directory management ####
config_loader = ConfigLoader()

processed_dir = config_loader.get_path("data", "exclusion_data", "processed")
output = config_loader.get_path("output")
output_dir = config_loader.get_path("output", "geodata")

os.makedirs(output_dir, exist_ok=True)

# configure logging
log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformEligibiliyAnalysisPlacements.log')
logger = config_loader.setup_task_logging('ProcessERA5WindData', log_file)
logger.info("Starting ProcessERA5WindData task")  

project_settings_path = config_loader.get_path("settings", "project_settings")
with open(project_settings_path, 'r') as file:
    project_settings = json.load(file)

start_year = project_settings["start_year"]
end_year = project_settings["end_year"]
project_crs = project_settings["crs"]

exclusions_settings_path = config_loader.get_path("settings", "exclusions_settings")
with open(exclusions_settings_path, 'r') as file:
    exclusions_settings = json.load(file)

# append the processed directory path to the paths in the exclusions_settings dictionary:
for category in ["vector", "raster"]:
    for key, value in exclusions_settings[category].items():
        updated_paths = [os.path.join(processed_dir, path) for path in value["paths"]]
        exclusions_settings[category][key]["paths"] = updated_paths

technology_config_path = config_loader.get_path("settings", "technologies")
with open(technology_config_path, 'r') as file:
    technology_config = json.load(file)

capacity = technology_config["wind"]["capacity"]
hub_height = technology_config["wind"]["hub_height"]
turbine_name = technology_config["wind"]["turbine_name"]
distance = technology_config["wind"]["turbine_spacing"]
rotor_diameter = technology_config["wind"]["rotor_diameter"]

## in the line below, you should only update the last part of the path - ie the name of the shapefile that you want to use as the main region polygon
# in this case, "north_sea_polygon.shp" 
main_region_polygon = os.path.join(config_loader.get_path("data", "project_data"), "MAIN_REGION_POLYGON", "north_sea_polygon.shp") 

#####################################################################################
############## MAIN WORKFLOW #################

############## 1. PERFORM THE EXCLUSIONS #################

# enter your logic for performing exclusions here

###############################################################################################################
#####################  SAVE THE PLACEMENTS TO A CSV FILE ##############################################

print("Saving the turbine placements...")

# enter logic to export placements to a csv


##############################################################################################
#####################  GENERATE THE JSON REPORT ##############################################

## create a report dictionary
report = {
    "Items_Number": "", #
    "Total_capacity_MW": "", # turbine capacity * total turbines / 100
    "Turbine_capacity_KW": capacity,
    "Hub_height": hub_height,
    "Rotor_diam": rotor_diameter,
    "Turbine_spacing": distance,
    "Turbine_name": turbine_name
    ### add other details to your report here
}

# save the report dictionary as a json file
report_path = os.path.join(output, "report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=4)