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

countries = project_settings["countries"]

##### running multiple scenarios for exclusions
scenarios = project_settings["scenarios"]

start_year = project_settings["start_year"]
end_year = project_settings["end_year"]
project_crs = project_settings["crs"]

exclusions_settings_path = config_loader.get_path("settings", "exclusions_settings")
with open(exclusions_settings_path, 'r') as file:
    exclusions_settings = json.load(file)

# append the processed directory path to the paths in the exclusions_settings dictionary:
for category in ["vector", "raster"]:
    for key, value in exclusions_settings[category].items():
        if "paths" in value:
            updated_paths = [os.path.join(processed_dir, path) for path in value["paths"]]
            exclusions_settings[category][key]["paths"] = updated_paths
        else:
            logger.warning(f"Key 'paths' not found for {key} in {category} category.")

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

# ############## 1. PERFORM THE EXCLUSIONS #################
# logger.info("Performing the exclusions...")
# logger.info("Initializing the exclusion calculator...")

# # initialize the exclusion calculator
# ec = gl.ExclusionCalculator(main_region_polygon, srs = int(project_crs.split(":")[1]), pixelRes=100, limitOne=False)

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

# # save the exclusions
# ec.save(os.path.join(output_dir, f"north_sea_exclusions_{scenario}.tif"), overwrite=True)

# ######## 2. DISTRIBUTE THE TURBINES #########

# logger.info("Distributing the turbines...")
# t0 = time.time()
# # distribute items
# ec.distributeItems(separation=distance, asArea=True)
# ec.saveItems(output=os.path.join(output_dir, f"turbine_locations_{scenario}"))
# t1 = time.time()
# logger.info(f"Turbines distributed in {t1-t0} seconds.")

# # distribute areas
# logger.info("Distributing the areas...")
# t0 = time.time()
# #ec.distributeAreas()
# ec.saveAreas(os.path.join(output_dir, f"turbine_areas_{scenario}.shp"))
# t1 = time.time()
# logger.info(f"Voronoi polygons distributed in {t1-t0} seconds.")


# ###############################################################################################################
# #####################  SAVE THE PLACEMENTS TO A CSV FILE ##############################################

# print("Saving the turbine placements and generating report...")
# df_items = pd.DataFrame({
#     "lat": [i[1] for i in ec.itemCoords],
#     "lon": [i[0] for i in ec.itemCoords]
# })

# df_items["capacity"] = capacity
# df_items["hub_height"] = hub_height
# df_items["rotor_diam"] = rotor_diameter

# # save the file
# df_items.to_csv(os.path.join(output_dir, f"turbine_placements_3035_{scenario}.csv"), index=False)


# ##############################################################################################
# #####################  GENERATE THE JSON REPORT ##############################################

# ## create a report dictionary
# report = {
#     "Items_Number": ec._itemCoords.shape[0],
#     "Total_capacity_MW": (capacity * ec._itemCoords.shape[0]) / 1000, # in MW
#     "Turbine_capacity_KW": capacity,
#     "Hub_height": hub_height,
#     "Rotor_diam": rotor_diameter,
#     "Turbine_spacing": distance,
#     "Turbine_name": turbine_name,
#     "Total_area_km2": round(((ec.areaAvailable / ec.percentAvailable) * 1e-4),2), # in km2
#     "Eligible_area_km2": round((ec.areaAvailable * 1e-6),2), # in km2
#     "Eligible_Percentage": round(ec.percentAvailable,4),
#     "Exclude_area_km2": round(((ec.areaAvailable / ec.percentAvailable * 1e-4) - ec.areaAvailable * 1e-6),2), # in km2
#     "Exclude_Percentage": round((100 - ec.percentAvailable),4)
# }

# # save the report dictionary as a json file
# report_path = os.path.join(output, f"report_{scenario}.json")
# with open(report_path, "w") as f:
#     json.dump(report, f, indent=4)


##############################################################################################
####################### NOW RUN FOR EACH COUNTRY #############################################

# Directory for country-specific EEZs
eez_dir = os.path.join(config_loader.get_path("data", "project_data"), "national_EEZ")

country_report = {}

# Run exclusion calculations for each country
for country_code in countries:
    country_report[country_code] = {}

    # Load country's EEZ polygon
    country_eez_path = os.path.join(eez_dir, f"{country_code}_eez.shp")
    logger.info(f"Loading EEZ shapefile for {country_code} from {country_eez_path}")
    
    if not os.path.exists(country_eez_path):
        logger.warning(f"EEZ shapefile for {country_code} not found, skipping.")
        continue

    # Initialize ExclusionCalculator with country's EEZ polygon
    ec = gl.ExclusionCalculator(country_eez_path, srs=int(project_crs.split(":")[1]), pixelRes=100, limitOne=False)

    # Calculate Total Area once, as it is common across scenarios
    total_area_km2 = round(((ec.areaAvailable / ec.percentAvailable) * 1e-4), 2)
    
    # Initialize the country report with the total area and an empty Scenarios dictionary
    country_report[country_code] = {
        "Total_area_km2": total_area_km2,
        "Scenarios": {}
    }

    for scenario in scenarios:
        # Initialize ExclusionCalculator with country's EEZ polygon each time to reset exclusions
        ec = gl.ExclusionCalculator(country_eez_path, srs=int(project_crs.split(":")[1]), pixelRes=100, limitOne=False)
        logger.info(f"Processing exclusions for country: {country_code} under scenario: {scenario}")
        t0 = time.time()

        # Apply raster exclusion using the specific scenario's exclusions file
        exclusion_file_path = os.path.join(output_dir, f"north_sea_exclusions_{scenario}.tif")
        try:
            ec.excludeRasterType(
                exclusion_file_path,
                value=0,
                buffer=None,
                bufferMethod="area"
            )
        except Exception as e:
            logger.error(f"Error processing exclusions for {scenario} in {country_code}: {e}")
            continue

        t1 = time.time()
        logger.info(f"Exclusions for {scenario} processed in {t1-t0} seconds.")

        # Calculate exclusion metrics for the scenario
        total_area_km2 = round(((ec.areaAvailable / ec.percentAvailable) * 1e-4), 2)
        eligible_area_km2 = round((ec.areaAvailable * 1e-6), 2)
        exclude_area_km2 = round(((ec.areaAvailable / ec.percentAvailable * 1e-4) - ec.areaAvailable * 1e-6), 2)

        # Store results for this scenario in the country report
        country_report[country_code]["Scenarios"][scenario] = {
            "Eligible_area_km2": eligible_area_km2,
            "Eligible_Percentage": round(ec.percentAvailable, 4),
            "Exclude_area_km2": exclude_area_km2,
            "Exclude_Percentage": round((100 - ec.percentAvailable), 4)
        }

    logger.info(f"Completed exclusions analysis for {country_code}.")

country_report_path = os.path.join(config_loader.get_path("output"), "report_NEWA_sim.json")
with open(country_report_path, "w") as f:
    json.dump(country_report, f, indent=4)
    
logger.info("Country-specific exclusions analysis for all scenarios complete.")
