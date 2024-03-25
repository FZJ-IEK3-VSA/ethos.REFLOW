import os
import time 
import logging
import numpy as np
import rasterio
from shapely.geometry import box, Polygon, MultiPolygon
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
import geopandas as gpd
import pandas as pd
import time
import json
from utils.config import ConfigLoader
from utils.utils import check_files_exist, create_target_directories
import fiona
import logging
import xarray as xr

class VectorProcessor:
    def __init__(self, logger=None):
        """
        Initializes the VectorProcessor with a default CRS.

        Parameters:
        - default_crs: The default coordinate reference system in EPSG format.
        """
        # set up logging in the VectorProcessor
        config_loader = ConfigLoader()
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
        self.default_crs = project_settings["crs"]

        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def reproject_vector(self, vector_data, crs=None):
        """
        Reprojects vector data to the specified CRS.

        Parameters:
        - vector_data: A GeoDataFrame representing vector data.
        - crs: The target coordinate reference system in EPSG format.
        """
        if crs is None:
            crs = self.default_crs

        if vector_data.crs != crs:
            self.logger.info(f"CRS mismatch. Reprojecting to {crs}...")
            vector_data = vector_data.to_crs(crs)
        self.logger.info(f"Reprojected to {crs}.")	
        return vector_data

    def buffer_vector(self, vector_data, buffer_distance):
        """
        Buffers the vector data by a specified distance.

        Parameters:
        - vector_data: A GeoDataFrame representing vector data.
        - buffer_distance: Buffer distance in the unit of the vector data's CRS.
        """
        buffered_data = vector_data.buffer(buffer_distance)
        buffered_data_gpd = gpd.GeoDataFrame(geometry=buffered_data, crs=vector_data.crs)
        self.logger.info(f"Buffered by {buffer_distance}.")
        return buffered_data_gpd
    

    def calculate_bbox_polygon(self, reference_polygon):
        """
        Calculate the bounding box of the reference polygon and convert it to a polygon for clipping.

        Parameters:
        reference_polygon (gpd.GeoDataFrame): A GeoDataFrame containing the reference polygon(s).

        Returns:
        shapely.geometry.polygon.Polygon: The bounding box of the reference polygon as a polygon.
        """
        if not isinstance(reference_polygon, gpd.GeoDataFrame):
            raise ValueError("reference_polygon must be a GeoDataFrame")

        bbox = reference_polygon.total_bounds  # Get the bounding box (minx, miny, maxx, maxy)
        bbox_polygon = box(*bbox)  # Convert bounding box to a polygon
        return bbox_polygon
    

    def clip_vector_data(self, vector_data, reference_polygon):
        """
        Clips vector data to a reference polygon.

        Parameters:
        - vector_data: A GeoDataFrame representing vector data.
        - reference_polygon: A GeoDataFrame representing the reference polygon.
        """
        clipped_data = gpd.clip(vector_data, reference_polygon)
        return clipped_data

    def merge_geo_dataframes(self, geo_df_list):
        """
        Merges a list of GeoDataFrames into a single GeoDataFrame.

        Parameters:
        - geo_df_list: List of GeoDataFrames to merge.
        - crs: Coordinate Reference System in EPSG format.
        """
        merged_df = gpd.GeoDataFrame(pd.concat(geo_df_list, ignore_index=True), crs=self.default_crs)
        self.logger.info("Merged GeoDataFrames.")
        return merged_df


    def clip_buffer_merge_vector_data(self, data_dict, reference_polygon, buffer_distance):
        """
        Reprojects, clips, buffers, and merges vector data based on a reference polygon and buffer distance.
    
        Parameters:
        - data_dict: Dictionary mapping identifiers to their shapefile paths.
        - reference_polygon: GeoDataFrame used as a reference for clipping and buffering.
        - buffer_distance: Distance to buffer the vector data, in the same units as the CRS.
    
        Returns:
        Tuple of GeoDataFrames: All processed vector data polygons and all buffered data.
        """
    
        # Reproject the reference polygon to the target CRS
        reference_polygon_reprojected = self.reproject_vector(reference_polygon)
        # Calculate and convert the bounding box of the reference polygon
        bbox_polygon = self.calculate_bbox_polygon(reference_polygon_reprojected)
    
        data_polygons, buffered_data = [], []  # Initialize lists for processed data
    
        for identifier, shapefile_path in data_dict.items():
            t0 = time.time()
            self.logger.info(f"Processing {identifier}...")
    
            # Load, reproject, and clip vector data
            vector_data = gpd.read_file(shapefile_path)
            vector_data_reprojected = self.reproject_vector(vector_data)
            self.logger.info(f"Clipping {identifier}...")
            vector_data_clipped = self.clip_vector_data(vector_data_reprojected, bbox_polygon)
    
            # Buffer and clip the buffered vector data
            self.logger.info(f"Buffering {identifier}...")
            buffered_vector_data = self.buffer_vector(vector_data_clipped, buffer_distance)
            clipped_buffered_data = self.clip_vector_data(buffered_vector_data, reference_polygon_reprojected)
    
            # Add processed data to lists
            self.logger.info(f"appending {identifier}.")
            data_polygons.append(vector_data_clipped)
            buffered_data.append(clipped_buffered_data)
            t1 = time.time()
            self.logger.info(f"Processed {identifier} in {t1 - t0:.2f} seconds.")
    
        # Merge processed data into single GeoDataFrames
        all_data_polygons = self.merge_geo_dataframes(data_polygons)
        all_buffered_data = self.merge_geo_dataframes(buffered_data)

        self.logger.info("Processed and merged all vector data.")
        return all_data_polygons, all_buffered_data
    

    def merge_two_vectors_and_flatten(self, vector_one, vector_two):
        """
        Merges two GeoDataFrame objects into one and attempts to flatten the geometry to a single polygon.

        Parameters:
        - vector_one: First GeoDataFrame.
        - vector_two: Second GeoDataFrame.
        """
        # Concatenate the two GeoDataFrames into one
        merged_vector = gpd.GeoDataFrame(pd.concat([vector_one, vector_two], ignore_index=True), crs=vector_one.crs)

        # Attempt to dissolve all geometries into a single geometry
        dissolved = merged_vector.unary_union

        # Determine if the dissolved geometry is a Polygon or MultiPolygon and handle accordingly
        if isinstance(dissolved, Polygon):
            # If it's a single Polygon, use it as is
            single_polygon = dissolved
        elif isinstance(dissolved, MultiPolygon):
            # If it's a MultiPolygon, select the largest polygon based on area
            single_polygon = max(dissolved, key=lambda a: a.area)
        else:
            # Log an error if the geometry is neither a Polygon nor a MultiPolygon
            logging.error("The merged geometry is neither a Polygon nor a MultiPolygon.")
            single_polygon = None

        if single_polygon:
            # Create a new GeoDataFrame with the single polygon if it exists
            merged_vector = gpd.GeoDataFrame(gpd.GeoSeries(single_polygon), columns=['geometry'])
            merged_vector.set_crs(vector_one.crs, inplace=True)

        self.logger.info("Merged and flattened vector data.")
        return merged_vector
    
    def remove_datetime_fields(self, gdf):
        """
        Removes datetime fields from a GeoDataFrame or converts them to strings.
    
        :param gdf: GeoDataFrame to be processed.
        :return: Processed GeoDataFrame without datetime fields or with them converted to strings.
        """
        for col in gdf.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                self.logger.info("Datetime column found, removing...")
                # Remove the datetime column
                gdf.drop(columns=[col], inplace=True)
        
        return gdf
    
    def get_geometry_type(self, gdf):
        """
        Determines the predominant geometry type in a GeoDataFrame.
    
        :param gdf: GeoDataFrame
        :return: String representing the predominant geometry type (e.g., 'Point', 'MultiPolygon').
        """
        geom_types = gdf.geometry.type.unique()
        # Assuming the first geometry type in the array is representative for the dataset
        return geom_types[0] if geom_types.size else 'Unknown'
    
    
    def save_gdf_to_file(self, gdf, folder_path, file_name, file_format='Shapefile'):
        """
        Saves a GeoDataFrame to a specified folder in a given format.
    
        :param gdf: GeoDataFrame to be saved.
        :param folder_path: Path to the folder where the file should be saved.
        :param file_name: Name of the file to save the GeoDataFrame as.
        :param file_format: Format of the file. Default is 'Shapefile'.
        :return: None
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    
        file_path = os.path.join(folder_path, file_name)
        if file_format.lower() == 'shapefile':
            file_path += '.shp'
        elif file_format.lower() == 'geojson':
            file_path += '.geojson'
        else:
            raise ValueError("Unsupported file format. Please choose 'Shapefile' or 'GeoJSON'.")
    
        gdf.to_file(file_path, driver='ESRI Shapefile' if file_format.lower() == 'shapefile' else 'GeoJSON')
    
        self.logger.info(f"GeoDataFrame successfully saved to {file_path}")
    
    def clip_and_save_shp_file(self, full_path, region_gdf, folder_path):
        """
        Processes a Shapefile, clips it, and saves it with geometry type in the filename.
    
        :param full_path: Full path to the Shapefile.
        :param region_gdf: GeoDataFrame representing the clipping region.
        :param folder_path: Folder path where the processed files will be saved.
        :param crs: Coordinate Reference System to use for the datasets.
        """
        # Load the Shapefile
        gdf = gpd.read_file(full_path)
    
        # Reproject and clip the GeoDataFrame
        gdf = gdf.to_crs(self.crs)
        gdf_clipped = gpd.clip(gdf, region_gdf)
    
        # Determine geometry type and construct the file name
        geom_type = self.get_geometry_type(gdf_clipped).replace(" ", "_").lower()
        file_name = os.path.splitext(os.path.basename(full_path))[0] + f"_{geom_type}"
    
        # Save the processed GeoDataFrame
        self.save_gdf_to_file(gdf_clipped, folder_path, file_name, file_format='shapefile')
    
    def gbd_clip_to_shp_file(self, full_path, region_gdf, folder_path):
        """
        Processes each layer within a .gdb file, clips it, and saves it with geometry type in the filename.
    
        :param full_path: Full path to the .gdb file.
        :param region_gdf: GeoDataFrame representing the clipping region.
        :param folder_path: Folder path where the processed files will be saved.
        :param crs: Coordinate Reference System to use for the datasets.
        """
        layers = fiona.listlayers(full_path)
        for layer_name in layers:
            gdf = gpd.read_file(full_path, driver="OpenFileGDB", layer=layer_name)
    
            # Check if the layer has a CRS assigned
            if gdf.crs is None:
                self.logger.info(f"Layer {layer_name} does not have a CRS assigned and will be skipped.")
                continue  # Skip this layer and move to the next one
            
            # Remove datetime fields
            gdf = self.remove_datetime_fields(gdf, self.logger)
    
            gdf = gdf.to_crs(self.crs)
            gdf_clipped = gpd.clip(gdf, region_gdf) # clip the geodataframe
            geom_type = self.get_geometry_type(gdf_clipped).replace(" ", "_").lower()  # get the geometry type
            file_name = f"{layer_name}_{geom_type}"  
    
            self.save_gdf_to_file(gdf_clipped, folder_path, file_name, file_format='shapefile')  # save as a shapefile

    def clip_and_save_vector_datasets(self, vector_path_dict, region_gdf):
        """
        Processes and saves datasets for a dictionary of vector paths.
    
        :param vector_path_dict: Dictionary with dataset keys and paths to their source files.
        :param region_gdf: GeoDataFrame representing the clipping region.
        :param folder_base_path: Base path for saving processed datasets.
        :param crs: Coordinate Reference System to use for the datasets.
        """
        for key, path in vector_path_dict.items():
            self.logger.info(f"Processing {key}...")
    
            full_path_to_vector = os.path.join(self.raw_data_dir, path)
            output_folder_path = os.path.join(self.processed_dir, key)
            file_extension = os.path.splitext(path)[1].lower()
    
            # Check if files already exist
            if check_files_exist(full_path_to_vector, key):
                self.logger.info(f"Files already exist for {key}, skipping processing.")
                continue
    
            if file_extension == '.gdb':
                self.gbd_clip_to_shp_file(full_path_to_vector, region_gdf, output_folder_path, self.crs)
            elif file_extension == '.shp':
                self.clip_and_save_shp_file(full_path_to_vector, region_gdf, output_folder_path, self.crs)
            else:
                self.logger.info(f"Unsupported file format for {key}: {file_extension}")

class RasterProcesser:
    def __init__(self, logger=None):
        """
        Initializes the RasterProcessor with a the CRS.

        Parameters:
        - default_crs: The default coordinate reference system in EPSG format.
        """
        # set up logging in the VectorProcessor
        config_loader = ConfigLoader()
        project_settings_path = config_loader.get_path("settings", "project_settings")
        with open(project_settings_path, 'r') as file:
            project_settings = json.load(file)
        self.default_crs = project_settings["crs"]

        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def clip_raster_to_bbox(self, raster_path, bbox, output_path):
        """
        Clips a raster file to a specified bounding box.
    
        :param raster_path: Path to the input raster file.
        :param bbox: Bounding box as a tuple (minx, miny, maxx, maxy).
        :param output_path: Path to save the clipped raster.
        """
        # Check if the output directory exists, create it if not
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
    def merge_rasters(self, raster_paths, output_path):
        """
        Merges multiple raster files into a single raster.
    
        :param raster_paths: List of paths to the raster files to be merged.
        :param output_path: Path to save the merged raster.
        """
        src_files_to_mosaic = []
        for raster_path in raster_paths:
            src = rasterio.open(raster_path)
            src_files_to_mosaic.append(src)
        
        mosaic, out_trans = merge(src_files_to_mosaic)
        
        out_meta = src_files_to_mosaic[0].meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": mosaic.shape[1],
                         "width": mosaic.shape[2],
                         "transform": out_trans,
                         "crs": src_files_to_mosaic[0].crs})
        
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic)

    def merge_monthly_rasters(self, raster_paths, output_path):
        """
        Merges multiple monthly raster files into a single raster.
    
        :param raster_paths: List of paths to the monthly raster files to be merged.
        :param output_path: Path to save the merged raster.
        """
        # initialize an empty array to store the raster files
        summed_data = None
    
        # loop through the raster files
        for raster_path in raster_paths:
            with rasterio.open(raster_path) as src:
                # if summed_data is None, initialize it with the first raster
                if summed_data is None:
                    summed_data = np.zeros((src.count, src.height, src.width), dtype=np.float32)
    
                # read the raster data and add it to the summed_data array
                data = src.read(out_dtype=np.float32)
                summed_data += data
    
        # use the metadata of the last raster to save the merged raster
        with rasterio.open(raster_paths[-1]) as src:
            out_meta = src.meta
    
        # write the summed data to a new file 
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(summed_data)
        self.logger.info(f"Monthly rasters merged and saved to {output_path}")

    def reproject_clip_raster(self, input_raster_path, target_crs, gdf, output_folder, output_filename):
        """
        Reads a TIFF raster, reprojects it to a given CRS, clips it to the extent of a GeoPandas DataFrame,
        and saves the clipped raster in a specified output folder.
    
        :param input_raster_path: Path to the input TIFF raster file.
        :param target_crs: The target CRS to reproject the raster to (e.g., 'EPSG:4326').
        :param gdf: The GeoPandas DataFrame to use for clipping the raster.
        :param output_folder: The folder where the clipped raster should be saved.
        :param output_filename: The filename for the saved clipped raster.
        """
        # Ensure the output directory exists
        os.makedirs(output_folder, exist_ok=True)
        
        self.logger.info("Reprojecting raster...")
        with rasterio.open(input_raster_path) as src:
            # Calculate the transformation and dimensions for the target CRS
            transform, width, height = calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': target_crs,
                'transform': transform,
                'width': width,
                'height': height
            })
            
            # Create a memory file for the reprojected raster
            with rasterio.MemoryFile() as memfile:
                with memfile.open(**kwargs) as dest:
                    # Perform the reprojection
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=rasterio.band(dest, 1),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=target_crs,
                        resampling=Resampling.nearest)
                    
                    # Clip the raster with the GeoDataFrame's geometry
                    self.logger.info("Clipping raster...")
                    out_image, out_transform = mask(dest, gdf.geometry, crop=True)
                    out_meta = dest.meta.copy()
                    out_meta.update({"driver": "GTiff",
                                     "height": out_image.shape[1],
                                     "width": out_image.shape[2],
                                     "transform": out_transform})
                    
                # Save the clipped raster to the specified output folder
                output_path = os.path.join(output_folder, output_filename)
                with rasterio.open(output_path, "w", **out_meta) as final_dest:
                    final_dest.write(out_image)
                self.logger.info(f"Reprojected and clipped raster saved to {output_path}")

    def process_and_save_bathymetry(self, bathymetry_path_dict, raw_data_dir, temp_dir, crs, north_sea_EEZ, output_folder, bbox, logger, filename=None):
        """
        Processes bathymetry raster files by clipping to a bounding box, merging, reprojecting, and clipping to a GeoDataFrame extent.
    
        :param bathymetry_path_dict: Dictionary of raster keys and their file paths.
        :param script_dir: Base directory of the script for relative path calculations.
        :param temp_dir: Temporary directory for storing intermediate files.
        :param crs: Target Coordinate Reference System to use for the datasets.
        :param north_sea_EEZ: GeoDataFrame representing the North Sea region.
        :param output_folder: Folder where the final processed raster will be saved.
        :param bbox: Bounding box for initial clipping in the format (min_lon, min_lat, max_lon, max_lat).
        """
        # Ensure the temp and output directories exist
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

        if not filename:
            filename = "bathymetry.tif"
        
        clipped_raster_paths = []
    
        # Clip each raster to the bounding box and save
        for key, path in bathymetry_path_dict.items():
            logger.info(f"Processing {key}...")
            raster_path = os.path.join(raw_data_dir, path)
            output_path = os.path.join(temp_dir, key + ".tif")
            self.clip_raster_to_bbox(raster_path, bbox, output_path)
            # Append the output path of the clipped raster to the list
            clipped_raster_paths.append(output_path)
    
        # Merge the clipped bathymetry rasters
        merged_raster_path = os.path.join(output_folder, "bathymetry_merged.tif")
        self.merge_rasters(clipped_raster_paths, merged_raster_path)
    
        # Reproject, clip and save the final raster
        final_output_path = os.path.join(output_folder, filename)
        self.reproject_clip_raster(merged_raster_path, crs, north_sea_EEZ, output_folder, filename, logger)
    
        logger.info(f"Final bathymetry raster processed and saved to {final_output_path}")

    
    def process_and_save_shipping_lanes(self, input_paths, crs, north_sea_EEZ, output_folder, logger, filename=None):
        """
        Processes shipping lanes raster files by clipping to a bounding box, merging, reprojecting, and clipping to a GeoDataFrame extent.
    
        :param input_paths: List of paths to the monthly shipping lanes raster files.
        :param crs: Target Coordinate Reference System to use for the datasets.
        :param north_sea_EEZ: GeoDataFrame representing the North Sea region.
        :param output_folder: Folder where the final processed raster will be saved.
        :param filename: Name of the saved raster file.
        """
        os.makedirs(output_folder, exist_ok=True)

        if not filename:
            filename = "shipping_lanes.tif"
    
        # Merge the monthly shipping lanes rasters first
        merged_raster_path = os.path.join(output_folder, "shipping_lanes_unprojected.tif")
        self.merge_monthly_rasters(input_paths, merged_raster_path, logger)
    
        # Reproject the raster and clip to the North Sea EEZ after merging
        self.reproject_clip_raster(merged_raster_path, crs, north_sea_EEZ, output_folder, logger, filename)
    
        final_output_path = os.path.join(output_folder, filename)
        logger.info(f"Annual shipping lanes raster processed and saved to {final_output_path}")

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
        ds_u = self.convert_longitude(ds_u)
        ds_v = self.convert_longitude(ds_v)

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