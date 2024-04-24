import glaes as gl
import os
import pandas as pd
from utils.config import ConfigLoader
import logging
import json
import time
from copy import copy


"""
Main logic for the task.
"""
##################### DO NOT CHANGE #################################

# Initialize configuration loader and logging
config_loader = ConfigLoader()
log_file = os.path.join(config_loader.get_path("output"), 'logs', 'SensitivityAnalysis.log')
logger = config_loader.setup_task_logging('ProcessERA5WindData', log_file)
output = config_loader.get_path("output")
logger.info("Starting ProcessERA5WindData task")

# Load project settings
project_settings_path = config_loader.get_path("settings", "project_settings")
with open(project_settings_path, 'r') as file:
    project_settings = json.load(file)

# Load exclusions settings and update paths
exclusions_settings_path = config_loader.get_path("settings", "exclusions_settings")
with open(exclusions_settings_path, 'r') as file:
    exclusions_settings = json.load(file)

processed_dir = config_loader.get_path("data", "exclusion_data", "processed")
for category in ["vector", "raster"]:
    for key, value in exclusions_settings[category].items():
        value["paths"] = [os.path.join(processed_dir, path) for path in value["paths"]]

# Initialize main variables
main_region_polygon = os.path.join(config_loader.get_path("data", "project_data"), "MAIN_REGION_POLYGON", "north_sea_polygon.shp")
project_crs = project_settings["crs"]

# Initialize the exclusion calculator
logger.info("Initializing the exclusion calculator...")
ec = gl.ExclusionCalculator(main_region_polygon, srs=int(project_crs.split(":")[1]), pixelRes=100, limitOne=False)

# create a backup of the exclusion calculator
ec_backup = copy(ec)

initial_area = ec.areaAvailable

# append the processed directory path to the paths in the exclusions_settings dictionary:
for category in ["vector", "raster"]:
    for key, value in exclusions_settings[category].items():
        updated_paths = [os.path.join(processed_dir, path) for path in value["paths"]]
        exclusions_settings[category][key]["paths"] = updated_paths


#####################################################################################
############## MAIN WORKFLOW #################

############## 1. PERFORM THE EXCLUSIONS #################
logger.info("Performing the exclusions...")

# Initialize the exclusion report dictionary
sensitivity_report = {
    "inital_area:": round(initial_area * 1e-6, 3),
    "vector_exclusions": {},
    "raster_exclusions": {}
}

# perform exclusions 
for category in ["vector", "raster"]:
    if category == "vector":
        for key, exclusion_info in exclusions_settings[category].items():
            t0 = time.time()
            ec = copy(ec_backup)
            
            logger.info(f"Processing vector exclusion {key}...")
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
                        final_area = ec.areaAvailable  # Capture area after exclusion
                        excluded_area = round((initial_area - ec.areaAvailable) * 1e-6, 2)
                        excluded_percentage = round((100 - ec.percentAvailable), 4)

                        # Document exclusion impact
                        sensitivity_report["vector_exclusions"][key] = {
                            "excluded_area_km2": excluded_area,
                            "excluded_percentage": excluded_percentage
                        }
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
                        final_area = ec.areaAvailable  # Capture area after exclusion
                        excluded_area = round((initial_area - ec.areaAvailable) *1e-6, 2)
                        excluded_percentage = round((100 - ec.percentAvailable), 4)

                        # Document exclusion impact
                        sensitivity_report["vector_exclusions"][key] = {
                            "excluded_area_km2": excluded_area,
                            "excluded_percentage": excluded_percentage
                        }
                    except Exception as e:
                        logger.error(f"Error excluding {key}: {e}")
                        continue

            t1 = time.time()
            logger.info(f"Exclusion {key} processed in {t1-t0} seconds.")

    elif category == "raster":
        for key, exclusion_info in exclusions_settings[category].items():
            ec = copy(ec_backup)
            if key == "bathymetry":
                sensitivity_report["raster_exclusions"]["bathymetry"] = {}

                bathymetry_scenarios = {
                    "1000m_depth": "[--1000)",
                    "50m_depth": "[--50)"        
                    }
                for scenario, max_depth in bathymetry_scenarios.items():
                    logger.info(f"Processing raster exclusion {key} with max depth {max_depth}...")
                    t0 = time.time()
                    for path in exclusion_info["paths"]:
                        try:
                            ec.excludeRasterType(
                                path,
                                value=max_depth,
                                buffer=exclusions_settings[category][key]["buffer"],
                                bufferMethod="area"
                            )
                            final_area = ec.areaAvailable  # Capture area after exclusion
                            excluded_area = round(((initial_area - ec.areaAvailable) * 1e-6), 2)
                            excluded_percentage = round((100 - ec.percentAvailable), 4)

                            # Document exclusion impact
                            sensitivity_report["raster_exclusions"][key][scenario] = {
                                "excluded_area_km2": excluded_area,
                                "excluded_percentage": excluded_percentage
                            }
                        except Exception as e:
                            logger.error(f"Error excluding {key}: {e}")
                            continue
                    t1 = time.time()
                    logger.info(f"Exclusion {key} processed in {t1-t0} seconds.")
            else:
                logger.info(f"Processing raster exclusion {key}...")
                t0 = time.time()
                for path in exclusion_info["paths"]:
                    try:
                        ec.excludeRasterType(
                            path,
                            value=exclusions_settings[category][key]["value"],
                            buffer=exclusions_settings[category][key]["buffer"],
                            bufferMethod="area"
                        )

                        final_area = ec.areaAvailable  # Capture area after exclusion
                        excluded_area = round(((initial_area - ec.areaAvailable) * 1e-6),2)
                        excluded_percentage = round((100 - ec.percentAvailable), 4)

                        # Document exclusion impact
                        sensitivity_report["raster_exclusions"][key] = {
                            "excluded_area_km2": excluded_area,
                            "excluded_percentage": excluded_percentage
                        }
                    except Exception as e:
                        logger.error(f"Error excluding {key}: {e}")
                        continue
                t1 = time.time()
                logger.info(f"Exclusion {key} processed in {t1-t0} seconds.")

##############################################################################################
#####################  ADD TO THE JSON REPORT ##############################################

# save the report dictionary as a json file
report_path = os.path.join(output, f"sensitivity_analysis.json")

# Save the updated report back to the JSON file
with open(report_path, 'w') as file:
    json.dump(sensitivity_report, file, indent=4)