# REFLOW: North Sea offshore technical wind potential workflow

## Overview

This example of the REFLOW workflow is designed to assess the technical wind potential in the North Sea. It incorporates various data processing steps, sea category exclusions, turbine placements, simulations and visualizations of the wind potential as well as output json files. This automated workflow aims to allow for full transparency and reproducibility, and allows users to modify key exclusions or simulation parameters to assess the impact on the technical wind potential.

## Getting Started

### Prerequisites
- Ensure you have a Unix-like operating system, or have Git Bash installed on your Windows machine.
- Python 3.8 or later.
- Conda package manager at the least - mamba HIGHLY recommended.
- Git
- A working internet connection (fast internet connection recommended for downloading large datasets).
- Sufficeint disk space to store the downloaded data and the processed data (at least 50 GB required).

### Installation
- Installation is taken care of by the `environment_setup.sh` script. 
- If you run the workflow by using the `bash_task.sh` script, then the `environment_setup.sh` script will be run automatically.
- If you want to run the `environment_setup.sh` script manually, you can do so by running the following command in the terminal (from the project's home directory):
    ```bash
    bash scripts/environment_setup.sh
    ```

### Running the workflow
- To run the workflow, you can use the `bash_task.sh` script. This script will run the workflow in the correct order.
- If you prefer to set up the environment manually, you can then run the workflow by activating the "reflow-main" conda environment:
    ```bash
    conda activate reflow-main
    ```
    Then run the workflow by running the following command in the terminal (from the project's home directory):
    ```bash
    python reflow_workflow.py
    ```
- Ensure that the files in the requires(self) function of the reflow_workflow are:
    `[VisualizeExclusionMaps(),`
    `VisualizeBathymetry(),`
    `VisualizeCapacityFactorMaps()]`
- These will ensure that all the required tasks are run in the correct order.

### Debugging
- If you encounter any issues, please check the log files in the `output/logs` directory.
- If you encounter any issues with the workflow, please raise an issue on the GitHub repository.

### Running on a cluster:
- The workflow can be run on a cluster by using the `slurm_task.sh` script.
- You may encounter some issues with setting up the environments, and you may need to do more debugging to get the workflow running on a cluster, due to potential issues with Slurm management and the Linux distro you are using. 
- DO NOT PANIC.
- If you encounter any issues, please raise an issue on the GitHub repository.

## Workflow description

The workflow performs tasks in the following order:

#### 1. environment_setup.sh: 
- Requires: *None*
- Input: *required_software/requirements.yaml*
- Does:
    1. Set up the environment for the workflow
    2. Install the required software from the .yaml files in /required_software
- Output files:
    - ´*None*

#### 2. data_download/DownloadExclusionsData():
- Requires: *environment_setup.sh*
- Input: *project_settings.json*
- Does:
    1. Download the required data for performing the exclusions
    2. Unzip the downloaded data into the raw data directory
- Output files:
    - *data/exclusion_data/raw/*
- Log files:
    - *output/logs/DownloadExclusionsData.log*
    - *output/logs/DownloadExclusionsData_complete.txt*

#### 3. data_processing/ProcessProjectData():
- Requires: *data_download/DownloadExclusionsData()*
- Input: *project_settings.json*
- Does:
    1. Process the project data to create the main region polygon
    2. Create the buffers around the coastlines at the distance set in the project_settings.json file
- Output files:
    - *data/exclusion_data/processed/north_sea_coastal_buffers/north_sea_coastal_buffers.shp*
    - *data/project_data/processed/MAIN_REGION_POLYGON/north_sea_polygon.shp*
    - *data/project_data/processed/north_sea_coasts/north_sea_coasts.shp*
    - *data/exclusion_data/raw/exclusion_data_raster_paths.json*
    - *data/exclusion_data/raw/exclusion_data_vector_paths.json*
- Log files:
    - *output/logs/ProcessProjectData.log*
    - *output/logs/ProcessProjectData_complete.txt*

#### 4. data_processing/ProcessExclusionsData():
- Requires: *data_download/DownloadExclusionsData()*
- Key inputs: 
    - *project_settings.json*
    - *data/project_data/processed/MAIN_REGION_POLYGON/north_sea_polygon.shp*
    - *data/exclusion_data/raw/*
- Does:
    1. Processes the exclusions data by clipping the data to the main region polygon and updating any name/character issues
- Output files:
    - *data/exclusion_data/processed/*
- Log files:
    - *output/logs/ProcessExclusionsData.log*
    - *output/logs/ProcessExclusionsData_complete.txt*

#### 5. data_download/DownloadMeteorologicalData():
- Requires: *data_processing/ProcessProjectData()*
- Key inputs: 
    - *project_settings.json*, 
    - *ERA5_settings.json*, 
    - *project_data/processed/MAIN_REGION_POLYGON/north_sea_polygon.shp*
- Does:
    1. Downloads the meteorological data from the ERA5 database
    2. Unzips the downloaded data into the raw met_data directory
    3. Downloads the geotiff file from the New European Wind Atlas
- Output files:
    - *data/met_data/raw/*
    - *data/met_data/newa_wind_speed_mean_100m.tif*
- Log files:
    - *output/logs/DownloadMeteorologicalData.log*
    - *output/logs/DownloadMeteorologicalData_complete.txt*

#### 6. data_processing/ProcessERA5Data():
- Requires: *data_download/DownloadMeteorologicalData()*
- Key inputs: 
    - *project_settings.json*, 
    - *data/project_data/processed/MAIN_REGION_POLYGON/north_sea_polygon.shp*
    - *data/met_data/raw/*
- Does:
    1. Converts lontitude to the range -180 to 180 (if not already in that range)    
    2. Processes wind speed and direction from u and v components
    3. Creates new datasets from the raw data 
- Output files:
    - *data/met_data/ERA5/processed/*
- Log files:
    - *output/logs/ProcessERA5Data.log*
    - *output/logs/ProcessERA5Data_complete.txt*

#### 7. exclusions_placements/PerformEligibiliyAnalysisPlacements():
- Requires: *data_processing/ProcessExclusionsData()*
- Key inputs: 
    - *project_settings.json*, 
    - *exclusion_settings.json*,
    - *data/project_data/processed/MAIN_REGION_POLYGON/north_sea_polygon.shp*, 
    - *data/exclusion_data/processed/*
- Does:
    1. Performs the eligibility analysis for the given scenario
    2. Distributes the turbines and creates voronoi polygons
    3. Save key results to the report file
- Output files:
    - *output/geodata/turbine_locations_{scenario}/*
    - *output/north_sea_exclusions_{scenario}.tif*
    - *output/turbine_areas_{scenario}.tif*
    - *output/turbine_placements_3035_{scenario}.csv*
    - *output/report.json*
- Log files:
    - *output/logs/PerformEligibilityAnalysisPlacements.log*
    - *output/logs/PerformEligibilityAnalysisPlacements_complete.txt*

#### 8. data_processing/ConvertAndExtractPlacements():
- Requires: *exclusions_placements/PerformEligibilityAnalysisPlacements()*
- Key inputs: 
    - *project_settings.json*, 
    - *data/project_data/World_EEZ_v12_20231025/eez_v12.shp.shp*, 
    - *output/turbine_placements_3035_{scenario}.csv*
- Does:
    1. Converts the placements csv to EPSG:4326 so that they can be processed by RESKit in the simulations task
    2. Extracts the associated country code for each placement
- Output files:
    - *output/turbine_placements_4326_{scenario}.csv*
- Log files:
    - *output/logs/ConvertAndExtractPlacements.log*

#### 9. simulations/PerformSimulations():
- Requires: *data_processing/ConvertAndExtractPlacements()*, *data_download/ProcessERA5WindData()*
- Key inputs: 
    - *project_settings.json*,  
    - *output/turbine_placements_4326_{scenario}.csv*,
    - *data/met_data/ERA5/processed/*
- Does:
    1. Performs the wind farm simulations for the given scenario
    2. Calculates the capacity factor for each turbine
    3. Calculates the full load hours for each turbine
    3. Saves key results to the report file
- Output files:
    - *output/simulations_{scenario}.nc*
    - *output/report.json*
- Log files:
    - *output/logs/PerformSimulations.log*
    - *output/logs/PerformSimulations_complete.txt*

#### 10. visualizations:
- Requires: *simulations/PerformSimulations()*
- Key inputs: 
    - Varied
- Does:
    1. Creates visualizations of the results
- Output files:
    - *output/visualizations/*
- Log files:
    - None

## Contributing

Contributions to the REFLOW workflow are welcome. Whether it's feature enhancements, bug fixes, or documentation improvements, please follow the standard git workflow for submitting changes:

1. Fork the repository.
2. Create your feature branch (git checkout -b feature/AmazingFeature).
3. Commit your changes (git commit -am 'Add some AmazingFeature').
4. Push to the branch (git push origin feature/AmazingFeature).
5. Open a Pull Request.

## License

Distributed under the MIT License. 

## Acknowledgements

The authors would like to thank the German Federal Government, the German State Governments, and the Joint Science Conference (GWK) for their funding and support as part of the NFDI4Ing consortium. Funded by the German Research Foundation (DFG) – 442146713, this work was also supported by the Helmholtz Association as part of the program “Energy System Design”. 