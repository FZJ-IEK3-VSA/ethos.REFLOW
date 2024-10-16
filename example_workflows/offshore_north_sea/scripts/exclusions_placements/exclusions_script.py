import glaes as gl
import os
import pandas as pd
from utils.config import ConfigLoader
import logging
import json
import time
import re

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

##### running multiple scenarios for exlucsions
scenario = project_settings["scenario"]

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

#####################################################################################
############## MAIN WORKFLOW #################

## in the line below, you should only update the last part of the path - ie the name of the shapefile that you want to use as the main region polygon
# in this case, "north_sea_polygon.shp" 
main_region_polygon = os.path.join(config_loader.get_path("data", "project_data"), "MAIN_REGION_POLYGON", "north_sea_polygon.shp") 

############## 1. PERFORM THE EXCLUSIONS #################
logger.info("Performing the exclusions...")
logger.info("Initializing the exclusion calculator...")

# initialize the exclusion calculator
ec = gl.ExclusionCalculator(main_region_polygon, srs = int(project_crs.split(":")[1]), pixelRes=100, limitOne=False)

# Initialize the exclusion report dictionary
exclusion_report = {
    "vector_exclusions": {},
    "raster_exclusions": {}
}

# # append the processed directory path to the paths in the exclusions_settings dictionary:
# for category in ["vector", "raster"]:
#     for key, value in exclusions_settings[category].items():
#         updated_paths = [os.path.join(processed_dir, path) for path in value["paths"]]
#         exclusions_settings[category][key]["paths"] = updated_paths

# # perform exclusions 
# for category in ["vector", "raster"]:
#     if category == "vector":
#         for key, exclusion_info in exclusions_settings[category].items():
#             logger.info(f"Processing vector exclusion {key}...")
#             t0 = time.time()

#             for path in exclusion_info["paths"]:
#                 # check if "where" is provided
#                 if "where" in exclusion_info:
#                     try:
#                         ec.excludeVectorType(
#                             path,
#                             where=exclusions_settings[category][key]["where"],
#                             buffer=exclusions_settings[category][key]["buffer"],
#                             bufferMethod="area"
#                             )
#                     except Exception as e:
#                         logger.error(f"Error excluding {key} with where clause: {e}")
#                         continue
#                 else:
#                     try:
#                         ec.excludeVectorType(
#                             path,
#                             buffer=exclusions_settings[category][key]["buffer"],
#                             bufferMethod="area"
#                         )
#                     except Exception as e:
#                         logger.error(f"Error excluding {key}: {e}")
#                         continue

#             t1 = time.time()
#             logger.info(f"Exclusion {key} processed in {t1-t0} seconds.")

#     elif category == "raster":
#         for key, exclusion_info in exclusions_settings[category].items():
#             logger.info(f"Processing raster exclusion {key}...")
#             t0 = time.time()

#             for path in exclusion_info["paths"]:
#                 try:
#                     ec.excludeRasterType(
#                         path,
#                         value=exclusions_settings[category][key]["value"],
#                         buffer=exclusions_settings[category][key]["buffer"],
#                         bufferMethod="area"
#                     )
#                 except Exception as e:
#                     logger.error(f"Error excluding {key}: {e}")
#                     continue

#             t1 = time.time()
#             logger.info(f"Exclusion {key} processed in {t1-t0} seconds.")

# save the exclusions
ec.save(os.path.join(output_dir, f"north_sea_exclusions_{scenario}.tif"), overwrite=True)

######## 2. DISTRIBUTE THE TURBINES #########

# logger.info("Distributing the turbines...")
# t0 = time.time()
# # distribute items
# ec.distributeItems(separation=distance, asArea=True)
# t1 = time.time()
# logger.info(f"Turbines distributed in {t1-t0} seconds.")
# ec.saveItems(os.path.join(output_dir, f"turbine_placements_{scenario}", f"turbine_placements_{scenario}.shp"))

# t0 = time.time()
# ec.saveAreas(os.path.join(output_dir, f"turbine_areas_{scenario}.shp"))
# t1 = time.time()
# logger.info(f"Voronoi polygons distributed in {t1-t0} seconds.")

###############################################################################################################
#####################  SAVE THE PLACEMENTS TO A CSV FILE ##############################################

print("Saving the turbine placements and generating report...")
df_items = pd.DataFrame({
    "lat": [i[1] for i in ec.itemCoords],
    "lon": [i[0] for i in ec.itemCoords]
})

df_items["capacity"] = capacity
df_items["hub_height"] = hub_height
df_items["rotor_diam"] = rotor_diameter

# save the file
df_items.to_csv(os.path.join(output_dir, f"turbine_placements_3035_{scenario}.csv"), index=False)


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
report_path = os.path.join(output, f"report_{scenario}.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=4)