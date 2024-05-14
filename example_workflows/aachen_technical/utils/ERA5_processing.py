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
                print(f"Warning: Year in filename {filename} does not match source_year {year}")
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

    def process_other_files(self, year):
        """
        Converts latitute and then moves processed files that are not u_component or v_component to the target directory.
        """
        year = str(year)
        for filename in os.listdir(os.path.join(self.raw_data_dir, year)):
            if filename.endswith('.nc') and 'u_component' not in filename and 'v_component' not in filename:
                # construct the full file path
                file_path = os.path.join(self.raw_data_dir, year, filename)
                # load the dataset
                ds = xr.open_dataset(file_path)
                # convert the longitude if necessary
                ds_processed = self.convert_longitude(ds)
                # construct the target file path
                target_path = os.path.join(self.output_dir, year, filename.rsplit('.', 1)[0] + ".processed.nc")
                # save the processed dataset
                ds_processed.to_netcdf(target_path)
                # ensure resources are released
                ds.close()
                ds_processed.close()

    def process_wind(self, year):
        '''
        Process the ERA5 wind data.  
        '''
        # Load datasets as xarray Datasets
        ds_u = xr.open_dataset(os.path.join(self.raw_data_dir, str(year), f"{self.SOURCE_GROUP}.{year}.{self.height}m_u_component_of_wind.nc"))
        ds_v = xr.open_dataset(os.path.join(self.raw_data_dir, str(year), f"{self.SOURCE_GROUP}.{year}.{self.height}m_v_component_of_wind.nc"))

        # Convert longitude for each dataset to the range -180 to 180
        #ds_u = self.convert_longitude(ds_u)
        #ds_v = self.convert_longitude(ds_v)

        # Extract and process data
        data_u = ds_u[f'u{self.height}']
        data_v = ds_v[f'v{self.height}']
        wind_speed = self.process_wind_speed(data_u.values, data_v.values)
        wind_dir = self.process_wind_direction(data_u.values, data_v.values)

        # Wrap processed data in xarray.DataArray, preserving geographical coordinates
        wind_speed_da = xr.DataArray(wind_speed, dims=['time', 'latitude', 'longitude'],
                                    coords={'time': ds_u['time'], 'latitude': ds_u['latitude'], 'longitude': ds_u['longitude']})
        wind_dir_da = xr.DataArray(wind_dir, dims=['time', 'latitude', 'longitude'],
                                coords={'time': ds_v['time'], 'latitude': ds_v['latitude'], 'longitude': ds_v['longitude']})

        create_target_directories(self.output_dir, year)
        
        # Write output datasets
        filename = f"{self.SOURCE_GROUP}.{year}.{self.height}m_wind_speed.processed.nc"
        self.make_windvar_nc(ds_u, filename, wind_speed_da, year, is_winddir=False)

        filename = f"{self.SOURCE_GROUP}.{year}.{self.height}m_wind_direction.processed.nc"
        self.make_windvar_nc(ds_u, filename, wind_dir_da, year, is_winddir=True)

        # Copy the other files
        self.process_other_files(year)
