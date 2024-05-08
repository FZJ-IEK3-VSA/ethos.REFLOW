import os
from utils.config import ConfigLoader

config_loader = ConfigLoader()
# configure logging
log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformEligibiliyAnalysisPlacements.log')
logger = config_loader.setup_task_logging('ProcessERA5WindData', log_file)
logger.info("Starting EligibilityAnalysisPlacements task")  

# Print the path of the active Conda environment
logger.info(f"Current Conda environment:, {os.environ.get('CONDA_DEFAULT_ENV')}")

import glaes as gl
import pandas as pd
import logging
import json
import time

"""
Main logic for the task.
"""
##################### DO NOT CHANGE #################################
#### directory management ####


processed_dir = config_loader.get_path("data", "exclusion_data", "processed")
output = config_loader.get_path("output")
output_dir = config_loader.get_path("output", "geodata")

os.makedirs(output_dir, exist_ok=True)

project_settings_path = config_loader.get_path("settings", "project_settings")
with open(project_settings_path, 'r') as file:
    project_settings = json.load(file)

project_crs = project_settings["crs"]

exclusions_settings_path = config_loader.get_path("settings", "exclusions_settings")
with open(exclusions_settings_path, 'r') as file:
    exclusions_settings = json.load(file)

technology_config_path = config_loader.get_path("settings", "technologies")
with open(technology_config_path, 'r') as file:
    technology_config = json.load(file)

capacity = technology_config["wind"]["capacity"]
hub_height = technology_config["wind"]["hub_height"]
turbine_name = technology_config["wind"]["turbine_name"]
distance = technology_config["wind"]["turbine_spacing"]
rotor_diameter = technology_config["wind"]["rotor_diameter"]

## in the line below, you should only update the last part of the path - ie the name of the shapefile that you want to use as the main region polygon
# in this case, "Aachen.shp" 
main_region_polygon = os.path.join(config_loader.get_path("data", "project_data"), "MAIN_REGION_POLYGON", "Aachen.shp") 

#####################################################################################
############## MAIN WORKFLOW #################

def append_paths_to_data_categories(settings, directory, file_extension):
    # Loop through each category (like vector, raster) in the settings
    for category in settings:
        # Loop through each key (like commercial, residential, etc.) in the category
        for key in settings[category]:
            # Clear the current paths list
            settings[category][key]['paths'] = []
            # Search for matching files in the directory
            for file in os.listdir(directory):
                # Check if the filename contains the key and ends with the specified file extension
                if key in file and file.endswith(file_extension):
                    # Construct the relative path
                    rel_path = os.path.join(directory, file)
                    # Append the relative path to the paths list
                    settings[category][key]['paths'].append(rel_path)
    return settings

# Initialize the exclusion report dictionary
exclusion_report = {
    "vector_exclusions": {},
    "raster_exclusions": {}
}

## append the paths for the exclusions
exclusions_settings = append_paths_to_data_categories(exclusions_settings, processed_dir, ".shp")
# Convert the dictionary to a JSON-formatted string with indentation
formatted_exclusions_settings = json.dumps(exclusions_settings, indent=4)

# Log the formatted string
logger.info(f"Exclusion data paths:\n{formatted_exclusions_settings}")

############## 1. PERFORM THE EXCLUSIONS #################

logger.info("Initializing the exclusion calculator...")

# initialize the exclusion calculator with the main region polygon
ec = gl.ExclusionCalculator(main_region_polygon, srs = int(project_crs.split(":")[1]), pixelRes=100, limitOne=False)

#### Start the exclusions

logger.info("Starting the exclusions...")
for category in ["vector"]:                 ## here we exclude "raster" entirely since we dont have any raster files for this analysis
    for key, exclusion_info in exclusions_settings[category].items():
        logger.info(f"Processing vector exclusion {key}...")
        t0 = time.time()

        for path in exclusion_info["paths"]:
            # check if "where" is provided
            if "where" in exclusion_info:
                try:
                    ec.excludeVectorType(
                        path,
                        where=exclusions_settings[category][key]["where"],
                        buffer=exclusions_settings[category][key]["buffer"],
                        bufferMethod="area"
                        )
                except Exception as e:
                    logger.error(f"Error excluding {key} with where clause: {e}")
                    continue
            else:
                try:
                    ec.excludeVectorType(
                        path,
                        buffer=exclusions_settings[category][key]["buffer"],
                        bufferMethod="area"
                    )
                except Exception as e:
                    logger.error(f"Error excluding {key}: {e}")
                    continue

            t1 = time.time()
            logger.info(f"Exclusion {key} processed in {t1-t0} seconds.")

# save the exclusions
ec.save(os.path.join(output_dir, f"aachen_exclusions.tif"), overwrite=True)

################## 2. Distribute the turbines ####################

logger.info("Distributing the turbines...")
t0 = time.time()
# distribute items
ec.distributeItems(separation=distance, asArea=True)  # we prevent the turbines from being placed on the border of the main region polygon
t1 = time.time()
logger.info(f"Turbines distributed in {t1-t0} seconds.")
ec.saveItems(os.path.join(output_dir, f"aachen_turbine_placements.shp"))

t0 = time.time()
ec.saveAreas(os.path.join(output_dir, f"aachen_turbine_areas.shp"))
t1 = time.time()
logger.info(f"Turbine areas saved in {t1-t0} seconds.")

###############################################################################################
######################### SAVE THE PLACEMENTS TO A CSV FILE ##################################

logger.info("Saving the placements to a CSV file...")
df_items = pd.DataFrame({
    "lat": [i[1] for i in ec.itemCoords],
    "lon": [i[0] for i in ec.itemCoords],
})

df_items["capacity"] = capacity
df_items["hub_height"] = hub_height
df_items["rotor_diam"] = rotor_diameter  # do not change this

# save the file
df_items.to_csv(os.path.join(output_dir, "turbine_placements_3035.csv"), index=False)

##############################################################################################
#####################  GENERATE THE JSON REPORT ##############################################


## create a report dictionary
report = {
    "Items_Number": ec._itemCoords.shape[0],
    "Total_capacity_MW": (capacity * ec._itemCoords.shape[0]) / 1000, # in MW
    "Turbine_capacity_KW": capacity,
    "Hub_height": hub_height,
    "Rotor_diam": rotor_diameter,
    "Turbine_spacing": distance,
    "Turbine_name": turbine_name,
    "Total_area_km2": round(((ec.areaAvailable / ec.percentAvailable) * 1e-4),2), # in km2
    "Eligible_area_km2": round((ec.areaAvailable * 1e-6),2), # in km2
    "Eligible_Percentage": round(ec.percentAvailable,4),
    "Exclude_area_km2": round(((ec.areaAvailable / ec.percentAvailable * 1e-4) - ec.areaAvailable * 1e-6),2), # in km2
    "Exclude_Percentage": round((100 - ec.percentAvailable),4)
}

# save the report dictionary as a json file
report_path = os.path.join(output, f"report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=4)
