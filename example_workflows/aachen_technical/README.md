# REFLOW: Aachen technical wind potential example workflow

## Overview

This example workflow demonstrates how to use the REFLOW workflow manager to generate a technical onshore wind potential for the Aachen region. It includes the following steps:
1. Data download
2. Data preprocessing
3. Land eligibility assessment
4. Wind resource assessment / simulations
5. Visualization of results and generation of output report

## Getting started
### Prerequisites
- A Unix-like operating system (e.g. Linux, MacOS) or Git Bash on Windows
- Python
- Conda package manager (mamba HIGHLY recommended)
- Git
- A working internet connection
- Sufficient disk space to store the downloaded data (approx. 5 GB)
- A Copernicus Climate Data Store API key added to the `era5_settings.json` file (see below). [Register here.](https://cds.climate.copernicus.eu/#!/home)


### Installation and running the workflow
1. Clone the repository:
```bash
git clone https://jugit.fz-juelich.de/iek-3/groups/data-and-model-integration/pelser/reflow-offshore-north-sea.git
```

2. Change into the repository directory:
```bash
cd reflow-offshore-north-sea
cd example_workflows/aachen_technical_wind_potential
```

3. Create the main REFLOW python environment:

If you are using coda:
```bash
conda env create -f required_software/requirements-reflow.yml
```
If you have mamba installed:
```bash
mamba env create -f required_software/requirements-reflow.yml
```

4. Activate the REFLOW environment:
```bash
conda activate reflow
```

5. Run the workflow
```bash
python reflow_workflow.py
```

## Output
1. There are log files in the `logs` directory that contain information about the workflow execution. These contain essential information for debugging in case of errors.

2. The workflow generates a report.json file in the `output` directory. This file contains the results of the wind potential assessment.

3. The workflow also generates a .png file in the `output/visualizations` directory that visualizes the results of the wind potential assessment.

## Import information
The workflow is defined in the `reflow_workflow.py` file. This file contains the workflow definition, which consists of a series of tasks that are executed in sequence. Each task is defined as a Python function that performs a specific action, such as downloading data, preprocessing data, or running simulations. The tasks are connected by dependencies, which specify the order in which they should be executed.

The workflow scripts are located in the `scripts` directory. Each task is defined in a separate Python file, which contains a function that performs the task. In some cases, such as where a seperate python environment from the main reflow environment is required, a bash script is used to run the task. 

The workflow settings are defined in files found in the `settings` directory. These files contain the parameters that are used by the tasks to perform their actions. Take a look through them. `project_settings.json` and `exclusions_settings.json` are arguably the most important.

It is essential to update the Corpernicus API key in the `era5_settings.json` file before running the workflow. This key is required to download the data from the Copernicus Climate Data Store. You can obtain a free API key by [registering on the Copernicus website](https://cds.climate.copernicus.eu/#!/home). In the `era5_settings.json` file, replace the placeholder "ERA5_API_KEY" with the UID and API key that you receive after registering. This needs to be exactly as "UID:API_KEY". 

The Corpernicus Climate Data Store is used to download both the ERA5 reanalysis and the satellite land cover data. 

## Detailed steps
The workflow runs the scripts in the following order:
1. `scripts/environment_setup/env_setup_luigi_task.py`:
    - Create the additional python environments needed to run the eligibility analysis and placement script (GLAES) and the simulations script (ResKIT).
    - This script is run first to ensure that the necessary software is available when the tasks that require them are run.
2. `scripts/data_download/project_data.py`: 
    - Downloads the national boundary data for Germany from the GADM database.
3. `scripts/data_processing/process_project_data.py`: 
    - Processes the national boundary data to create a shapefile for the Aachen region.
    - transforms the shapefile to the correct projection (EPSG:3035).
4. `scripts/data_download/download_exclusions_data.py`:
    - Downloads the satellite land cover data from the Copernicus Climate Data Store (this is only used in the simulations to estimate the land roughness when extrapolating the wind speed to hub height).
    - Downloads the Open Street Map data from using the PyROSM package.
5. `scripts/data_processing/process_exclusions_data.py`:
    - Converts the satellite land cover data from netCDF to a GEOTiff raster file.
    - Processes the Open Street Map data to create shapefiles that can be used in the land eligibility assessment:
        - from the main osm.pfd file, extracts the selected exclusions as outlined in the `project_settings.json` file.
        - for each exclusion type, clips the data to the Aachen region and converts to the correct CRS
        - saves the processed data to the `data/exclusions_data/processed` directory.
6. `scripts/exclusions_placements/exclusions_luigi_task.py`:
    - Runs the GLAES land eligibility assessment using the processed Open Street Map data.
    - The GLAES script is run in a separate python environment to the main reflow environment.
    - Generates the `aachen_exclusions.tif` file in the `output/geodata` directory.
    - Places turbines in the Aachen region based on the land eligibility assessment.
    - Generates the `aachen_turbine_placements.shp` and the `turbine_placements_3035.csv` files in the `output/geodata` directory.
    - Generates the initial `report.json` file in the `output` directory.
7. `scripts/data_download/meteorological_data.py`:
    - Downloads the ERA5 reanalysis data from the Copernicus Climate Data Store.
    - Downloads the New European Wind Atlas (NEWA) long-term mean wind speed data from the NEWA website.
8. `scripts/data_processing/process_met_data.py`:
    - Processes the ERA5 reanalysis data so that it is useable by the RESKIT simulations script:
        - converts the u- and v- wind components to wind speed and direction.
        - ensures that the latitude and longitude coordinates are in the correct format.
9. `scripts/data_processing/convert_placements.py`:
    - Converts the turbine placements from EPSG:3035 to EPSG:4326 so that they can be used in the simulations.
10. `scripts/simulations/simulations_luigi_task.py`:
    - Runs the RESKIT simulations to estimate the wind speed at hub height for each turbine placement.
    - The RESKIT script is run in a separate python environment to the main reflow environment.
    - Generates the `wind_power_era5_2016.csv` file in the `output` directory.
    - Updates the `report.json` file in the `output` directory with the wind speed data.
11. `scripts/visualizations/visualizations_luigi_task.py`:
    - Generates a visualization of the wind speed data using the `report.json` file.
    - Generates the `exclusions_map.png` file in the `output/visualizations` directory.

## License

This project is licensed under the MIT License - see the License in the main REFLOW directory.

## Acknowledgements

The authors would like to thank the German Federal Government, the German State Governments, and the Joint Science Conference (GWK) for their funding and support as part of the NFDI4Ing consortium. Funded by the German Research Foundation (DFG) – 442146713, this work was also supported by the Helmholtz Association as part of the program “Energy System Design”.