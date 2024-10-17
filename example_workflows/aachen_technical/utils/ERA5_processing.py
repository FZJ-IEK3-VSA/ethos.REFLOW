import os
import logging
import numpy as np
import json
import xarray as xr
from utils.config import ConfigLoader
from utils.utils import check_files_exist, create_target_directories


class ERA5_RESKitWindProccessor():
    """
    Functions for processing ERA5 wind data to be readable into the RESKit model.
    The functions can, of course be used for other purposes as well.
    """
    def __init__(self, logger=None):
        """
        Initializes the ERA5_RESKitProccessor with a the CRS.

        Parameters:
        - default_crs: The default coordinate reference system in EPSG format.
        """
        # set up logging in the VectorProcessor
        config_loader = ConfigLoader()
        project_settings_path = config_loader.get_path("settings", "project_settings")
        self.met_data_dir = config_loader.get_path("data", "met_data")
        self.output_dir = os.path.join(self.met_data_dir, "ERA5", "processed")
        self.raw_data_dir = os.path.join(self.met_data_dir, "ERA5", "raw")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
        self.default_crs = project_settings["crs"]
        self.start_year = project_settings["start_year"]
        self.end_year = project_settings["end_year"]
        self.height = project_settings["wind_speed_height"]

        self.NO_DATA = 2**16 - 1
        self.MAX_DATA = 2**16 - 2
        self.SCALE_FACTOR = 1400 / self.MAX_DATA
        self.SOURCE_GROUP = "reanalysis-era5-single-levels"

        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def extract_ERA5_variable(self, file_path, year):
        """
        Extract the variable from the raw file and check if it matches the source year.
        """
        filename = os.path.basename(file_path)
        if filename.endswith('.nc') and filename.startswith(self.SOURCE_GROUP):
            year_in_filename = filename.split('.')[1]
            if year_in_filename != str(year):
                self.logger.warning(f"Warning: Year in filename {filename} does not match source_year {year}")
                return None
            variable = filename.split('.')[2]
            return variable
        else:
            self.logger.error(f"Warning: File {filename} does not match the expected pattern.")
            return None
        
    def convert_longitude(self, ds):
        '''
        Convert longitude to the range -180 to 180.
        '''

        # Determine the naming convention for latitude and longitude in the dataset
        lat_name = 'latitude' if 'latitude' in ds.coords else 'lat'
        lon_name = 'longitude' if 'longitude' in ds.coords else 'lon'

        # Ensure longitude is in the correct range
        lon_data = ds.coords[lon_name]
        if (lon_data >= 0).all() and (lon_data <= 360).all():
            # Subtract 180 to shift to -180 to 180 range
            adjusted_lon = lon_data - 180
            # Adjust values less than -180
            adjusted_lon = xr.where(adjusted_lon < -180, adjusted_lon + 360, adjusted_lon)
            ds.coords[lon_name] = adjusted_lon

        # Rename lat and lon to latitude and longitude if necessary
        if lat_name != 'latitude' or lon_name != 'longitude':
            ds = ds.rename({lat_name: 'latitude', lon_name: 'longitude'})

        return ds
    
    def process_wind_speed(self, data_u, data_v):
        '''
        Calculate wind speed from u and v components.
        '''
        return np.sqrt(np.power(data_u, 2) + np.power(data_v, 2))
    
    def process_wind_direction(self, data_u, data_v):
        '''
        Calculate wind direction from u and v components.
        '''
        data_uvdir = np.arctan2(data_v, data_u)
        data_uvdir = np.degrees(data_uvdir)
        sel = data_uvdir < 0
        data_uvdir[sel] = data_uvdir[sel] + 360
        return data_uvdir

    def make_windvar_nc(self, ref_ds, output_name, data, year, is_winddir=False):
        '''
        Make a wind variable netcdf file.
        '''
        # Make main variable
        if is_winddir:
            var_name = f"wd{self.height}"
            standard_name = f"wind_direction_at_{self.height}m"
            long_name = f"Total wind direction at {self.height} m. Processed from ERA5:u100,v100"
            max_value = 360
            units = "degrees"
        else:
            var_name = f"ws{self.height}"
            standard_name = f"wind_speed_at_{self.height}m"
            long_name = f"Total wind speed at {self.height} m. ERA5:u100,v100."
            max_value = 80
            units = "m s**-1"

        # Create a new xarray DataArray with the data
        da = xr.DataArray(data, 
                        dims=["time", "latitude", "longitude"], 
                        coords={"time": ref_ds["time"], 
                                "latitude": ref_ds["latitude"], 
                                "longitude": ref_ds["longitude"]},
                                name=var_name, 
                                attrs={"standard_name": standard_name, 
                                                        "long_name": long_name, 
                                                        "units": units,
                                                        "max_value": max_value}
                                                        )

        # Create a new xarray Dataset
        new_ds = da.to_dataset()

        # Set additional encoding options
        new_ds[var_name].encoding.update({"scale_factor": self.SCALE_FACTOR, "_FillValue": self.NO_DATA})

        # Define the target path
        target_path = os.path.join(self.output_dir, str(year), output_name)

        # Write the processed data to a file
        new_ds.to_netcdf(target_path)

        # Close the reference dataset
        ref_ds.close()

    def process_wind(self, year):
        '''
        Process the ERA5 wind data from a single combined file.  
        '''
        self.logger.info(f"Starting wind data processing for year {year}.")

        # Load the combined dataset
        combined_file_path = os.path.join(self.raw_data_dir, str(year), f"{self.SOURCE_GROUP}.{year}.combined_variables.nc")
        ds = xr.open_dataset(combined_file_path)

        # Extract u100 and v100 wind components
        self.logger.info(f"Extracting u and v wind components from combined file for year {year}.")
        data_u = ds['u100']
        data_v = ds['v100']

        # Calculate wind speed and direction
        self.logger.info(f"Calculating wind speed and direction for year {year}.")
        wind_speed = self.process_wind_speed(data_u.values, data_v.values)
        wind_dir = self.process_wind_direction(data_u.values, data_v.values)

        # Convert longitude if necessary
        self.logger.info(f"Converting longitude in the dataset for year {year}.")
        ds = self.convert_longitude(ds)

        # Ensure that the time coordinate is named "time"
        if 'valid_time' in ds.coords:
            ds = ds.rename({'valid_time': 'time'})

        # Create wind speed and direction DataArrays
        self.logger.info(f"Creating wind speed DataArray for year {year}.")
        wind_speed_da = xr.DataArray(wind_speed, dims=['time', 'latitude', 'longitude'],
                                    coords={'time': ds['time'], 'latitude': ds['latitude'], 'longitude': ds['longitude']})

        self.logger.info(f"Creating wind direction DataArray for year {year}.")
        wind_dir_da = xr.DataArray(wind_dir, dims=['time', 'latitude', 'longitude'],
                                coords={'time': ds['time'], 'latitude': ds['latitude'], 'longitude': ds['longitude']})

        # Create target directories
        self.logger.info(f"Creating target directories for processed data for year {year}.")
        create_target_directories(self.output_dir, year)

        # Save wind speed and direction data to NetCDF files
        self.logger.info(f"Saving processed wind speed data to NetCDF for year {year}.")
        wind_speed_filename = f"{self.SOURCE_GROUP}.{year}.{self.height}m_wind_speed.processed.nc"
        self.make_windvar_nc(ds, wind_speed_filename, wind_speed_da, year, is_winddir=False)

        self.logger.info(f"Saving processed wind direction data to NetCDF for year {year}.")
        wind_dir_filename = f"{self.SOURCE_GROUP}.{year}.{self.height}m_wind_direction.processed.nc"
        self.make_windvar_nc(ds, wind_dir_filename, wind_dir_da, year, is_winddir=True)

        # Process and save other variables (blh, t2m, sp)
        self.logger.info(f"Processing other variables (blh, t2m, sp) for year {year}.")
        self.process_other_files(ds, year)

        # Close the dataset
        ds.close()


    def process_other_files(self, ds, year):
        """
        Process other variables (blh, t2m, sp) from the combined file and save them separately.
        """
        variables_to_process = ['blh', 't2m', 'sp']
        
        for var in variables_to_process:
            self.logger.info(f"Processing variable {var} for year {year}.")
            # Extract the data for the variable
            data = ds[var]

            # Create a new xarray DataArray
            da = xr.DataArray(data.values, dims=['time', 'latitude', 'longitude'],
                              coords={'time': ds['time'], 'latitude': ds['latitude'], 'longitude': ds['longitude']},
                              name=var)

            # Construct the filename for the processed file
            output_name = f"{self.SOURCE_GROUP}.{year}.{var}.processed.nc"
            target_path = os.path.join(self.output_dir, str(year), output_name)

            # Save the processed data to a NetCDF file
            self.logger.info(f"Saving processed {var} data to {target_path}.")
            da.to_netcdf(target_path)
        
        self.logger.info(f"Processing of other variables completed for year {year}.")

    