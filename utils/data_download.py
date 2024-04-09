import requests
import os
import zipfile
import cdsapi
import logging
from utils.config import ConfigLoader
from pyproj import Transformer
import geopandas as gpd
import json
import numpy as np
import time

class DownloaderUtils():
    def __init__(self, logger=None):
        self.config_loader = ConfigLoader()
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        ## open settings files
        self.project_settings_path = self.config_loader.get_path("settings", "project_settings")
        self.era5_settings_path = self.config_loader.get_path("settings", "era5_settings")
        with open(self.project_settings_path, 'r') as file:
            project_settings = json.load(file)
        self.project_crs = project_settings["crs"]
        self.gadm_version = project_settings["gadm_version"]

        self.raw_output_dir = self.config_loader.get_path("data", "exclusion_data", "raw")
        self.project_data_dir = self.config_loader.get_path("data", "project_data")

        with open(self.era5_settings_path, 'r') as file:
            self.era5_config = json.load(file)

    def download_and_extract(self, url, folder_name, filename=None):
        """
        Downloads a file from the given URL to the specified folder.
        If the file is a zip archive, it extracts its contents into the folder.

        Example usage
        download_and_extract("http://example.com/somefile.zip", "/path/to/folder")
        """
        # Check if folder exists and has files
        folder = os.path.join(self.raw_output_dir, folder_name)

        if os.path.exists(folder) and os.listdir(folder):
            self.logger.info(f"Folder '{folder}' already exists and is not empty. Skipping download.")
            return None
        
        # Ensuring the folder exists
        if not os.path.exists(folder):
            os.makedirs(folder)

        if filename:
            local_filename = os.path.join(folder, filename)
        else:   
            # Define the local filename to save the downloaded file based on the URL or a fallback
            filename_from_url = url.split('/')[-1]
            if filename_from_url:
                local_filename = os.path.join(folder, filename_from_url)
            else:
                # Fallback filename if none is provided and the URL doesn't end with one
                filename = "change_filename.zip"  
                local_filename = os.path.join(folder, filename)
        
        # Downloading the file
        try:
            self.logger.info(f"Downloading {url} to {folder}...")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download {url}. Error: {e}")
            return None

        # Check if the file is a zip file
        if zipfile.is_zipfile(local_filename):
            with zipfile.ZipFile(local_filename, 'r') as zip_ref:
                zip_ref.extractall(folder)
            # deleting the zip file
            os.remove(local_filename)
        self.logger.info(f"Downloaded and extracted {folder}.")
        return local_filename


    def download_gadm_data(self, country_abrv):        
        gadm_dir = os.path.join(self.project_data_dir, f"gadm")
        country_folder = os.path.join(gadm_dir, country_abrv)
        if not os.path.exists(country_folder):
            os.makedirs(country_folder)
        else:
            self.logger.info(f"Data for {country_abrv} already exists in temp folder.")
            return True
            
        # Download the ZIP file
        self.logger.info(f"Using GADM version {self.gadm_version}.")
        self.logger.info(f"Downloading data for {country_abrv}...")
        url = f"https://geodata.ucdavis.edu/gadm/gadm{self.gadm_version[0]}.{self.gadm_version[1]}/shp/gadm{self.gadm_version}_{country_abrv}_shp.zip"
        self.logger.info(url)
        zip_path = f"gadm{self.gadm_version}_{country_abrv}_shp.zip"
        
        # Download the ZIP file
        response = requests.get(url)
        if response.status_code == 200:
            with open(zip_path, 'wb') as file:
                file.write(response.content)
        else:
            logging.error(f"Failed to download data for {country_abrv}. Please ensure that the ISO code is correct.")
            return False
            
        # Extract the ZIP file
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(f"{country_folder}/gadm{self.gadm_version}_{country_abrv}")
        except zipfile.BadZipFile:
            logging.error(f"Bad ZIP file for {country_abrv}.)")
            return False
            
        # Delete the ZIP file
        try:
            os.remove(zip_path)
        except FileNotFoundError:
            logging.error(f"Could not delete ZIP file for {country_abrv}.")

        self.logger.info(f"Processed {country_abrv}.")

        return True

    def get_area_bbox(self, polygon_file=None):
        """
        Get the bounding box of the main region polygon.
        """
        polygon = gpd.read_file(polygon_file)
        return polygon.total_bounds
    

class ERA5Downloader():
    def __init__(self, main_polygon_fname=None, logger=None):
        self.config_loader = ConfigLoader()
        self.met_data_dir = self.config_loader.get_path("data", "met_data")
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
        if not main_polygon_fname:
            raise ValueError("Please provide a filename for the main polygon.")
        self.main_region_polygon = os.path.join(self.config_loader.get_path("data", "project_data"), "MAIN_REGION_POLYGON", main_polygon_fname)
        
        # do a check to see if the main region polygon exists
        if not os.path.exists(self.main_region_polygon):
            raise ValueError(f"Main region polygon {self.main_region_polygon} does not exist.")
            logger.error(f"Main region polygon {self.main_region_polygon} does not exist.")

        ## open settings files
        self.project_settings_path = self.config_loader.get_path("settings", "project_settings")
        self.era5_settings_path = self.config_loader.get_path("settings", "era5_settings")
        with open(self.project_settings_path, 'r') as file:
            project_settings = json.load(file)
        self.project_crs = project_settings["crs"]
        self.start_year = project_settings["start_year"]
        self.end_year = project_settings["end_year"]
        with open(self.era5_settings_path, 'r') as file:
            self.era5_config = json.load(file)

    
    def get_area_bbox(self):
        """
        Get the bounding box of the main region polygon.
        """
        polygon = gpd.read_file(self.main_region_polygon)
        return polygon.total_bounds

    def convert_polygon_extent_to_ERA5(self, expanded_distance=8):
        """
        Converts a bounding box to an extent that can be used for the ERA5 API. 
        Expands the bounding box by the specified distance in degrees.

        We use a large buffer to ensure that we get all the data we need especially in case we are going to interpolate later on.
        """
        raw_bbox = self.get_area_bbox()
        transformer = Transformer.from_crs(self.project_crs, "EPSG:4326", always_xy=True)

        # unpack the bounding box for transformation
        x_min, y_min, x_max, y_max = raw_bbox

        # convert the min and max points
        lon_min, lat_min = transformer.transform(x_min, y_min)
        lon_max, lat_max = transformer.transform(x_max, y_max)

        # Correctly apply the expansion to the bounding box directly as degrees
        lat_min_corrected = lat_min - expanded_distance
        lat_max_corrected = lat_max + expanded_distance
        lon_min_corrected = lon_min - expanded_distance
        lon_max_corrected = lon_max + expanded_distance

        # FOrmat the extent for the ERA5 API
        formatted_extent = [lat_max_corrected, lon_min_corrected, lat_min_corrected, lon_max_corrected]

        return formatted_extent
    
    def download_ERA5_data(self, expanded_distance=8):
        '''
        Downloads ERA5 reanalysis data from the Copernicus Climate Data Store using the CDSApi.
        '''
        years_to_download = np.arange(self.start_year, self.end_year + 1, 1)

        area_to_download = self.convert_polygon_extent_to_ERA5(expanded_distance)

        wind_data_types = self.era5_config["ERA5_WIND_DATA_TYPES"]

        for YEAR in years_to_download:
            year_path = os.path.join(self.met_data_dir, "ERA5", "raw", str(YEAR))
            os.makedirs(year_path, exist_ok=True)
            self.logger.info(f"Processing {YEAR}...")

            # access the settings from the config file
            months = self.era5_config["ERA5_SETTINGS"]["months_to_download"]
            days = self.era5_config["ERA5_SETTINGS"]["days_to_download"]
            hours = self.era5_config["ERA5_SETTINGS"]["hours_to_download"]

            for item in wind_data_types:
                SOURCE, VARIABLE = item
                filename = f"{SOURCE}.{YEAR}.{VARIABLE}.nc"
                OUTPUT = os.path.join(year_path, filename)

                if os.path.exists(OUTPUT):
                    self.logger.info(f"ERA5 data for {YEAR} already exists. Skipping...")
                    continue
                else:
                    try:
                        # download and save the data using ERA5 cdsapi
                        self.logger.info(f"Downloading {VARIABLE} for {YEAR}...")
                        t0 = time.time()
                        c = cdsapi.Client(url = self.era5_config["ERA5_ENDPOINT"], key = self.era5_config["ERA5_API_KEY"])
                        c.retrieve(SOURCE,
                                {'product_type': 'reanalysis',
                                    'area': area_to_download,
                                    'variable': [VARIABLE,],
                                    'year': str(YEAR),
                                    'month': months,
                                    'day': days,
                                    'time': hours,
                                    'format': 'netcdf',
                                    },
                                    OUTPUT
                                )
                        t1 = time.time()
                        self.logger.info(f"Downloaded {VARIABLE} in {t1-t0} seconds.")
                    except Exception as e:
                        self.logger.error(f"Failed to download {VARIABLE} for {YEAR}. Error: {str(e)}")