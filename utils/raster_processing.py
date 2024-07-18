import os
import logging
import numpy as np
import rasterio
from shapely.geometry import box
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
import geopandas as gpd
import json
from utils.config import ConfigLoader
from utils.utils import check_files_exist, create_target_directories


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
        self.output_dir = config_loader.get_path("data", "exclusion_data", "processed")
        self.raw_data_dir = config_loader.get_path("data", "exclusion_data", "raw")
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

        with rasterio.open(raster_path) as src:
            # Create a GeoDataFrame with the bounding box
            geo = gpd.GeoDataFrame({'geometry': [box(*bbox)]}, crs=src.crs)
            
            # Perform the clipping
            out_image, out_transform = mask(src, geo.geometry, crop=True)
            out_meta = src.meta.copy()
            out_meta.update({"driver": "GTiff",
                            "height": out_image.shape[1],
                            "width": out_image.shape[2],
                            "transform": out_transform})
            
            # Save the clipped raster
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)
        
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
    
    def reproject_raster(self, input_raster_path, output_dir=None, output_filename=None, target_crs=None):
        """
        Reads a TIFF raster and reprojects it to a given CRS.
        
        :param input_raster_path: Path to the input TIFF raster file.
        :param target_crs: The target CRS to reproject the raster to (e.g., 'EPSG:4326').
        :return: A memory file containing the reprojected raster.
        """
        
        self.logger.info("Reprojecting raster...")
        if target_crs == None:
            target_crs = self.default_crs

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
                    self.logger.info("Raster reprojected successfully.")
            
                    # Save the reprojected raster to a file
                    if output_dir:
                        output_path = os.path.join(output_dir, output_filename)
                    else:
                        output_path = os.path.join(output_filename)
                        
                    out_meta = dest.meta.copy()
                    with rasterio.open(output_path, "w", **out_meta) as final_dest:
                        final_dest.write(dest.read())
                    
                    self.logger.info(f"Reprojected raster saved to {output_path}")


    def reproject_clip_raster(self, input_raster_path, gdf, output_dir=None, output_filename=None):
        """
        Reads a TIFF raster, reprojects it to a given CRS, clips it to the extent of a GeoPandas DataFrame,
        and saves the clipped raster in a specified output folder.
    
        :param input_raster_path: Path to the input TIFF raster file.
        :param target_crs: The target CRS to reproject the raster to (e.g., 'EPSG:4326').
        :param gdf: The GeoPandas DataFrame to use for clipping the raster.
        :param output_folder: The folder where the clipped raster should be saved.
        :param output_filename: The filename for the saved clipped raster.
        """
        
        self.logger.info("Reprojecting raster...")
        with rasterio.open(input_raster_path) as src:
            # Calculate the transformation and dimensions for the target CRS
            transform, width, height = calculate_default_transform(
                src.crs, self.default_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': self.default_crs,
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
                        dst_crs=self.default_crs,
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
                if output_dir:
                    output_path = os.path.join(self.output_dir, output_dir, output_filename)
                else:
                    output_path = os.path.join(self.output_dir, output_filename)
                with rasterio.open(output_path, "w", **out_meta) as final_dest:
                    final_dest.write(out_image)
                self.logger.info(f"Reprojected and clipped raster saved to {output_path}")

    def process_and_save_bathymetry(self, bathymetry_path_dict, main_region_polygon, bbox, filename=None):
        """
        Processes bathymetry raster files by clipping to a bounding box, merging, reprojecting, and clipping to a GeoDataFrame extent.
    
        :param bathymetry_path_dict: Dictionary of raster keys and their file paths.
        :param script_dir: Base directory of the script for relative path calculations.
        :param temp_dir: Temporary directory for storing intermediate files.
        :param crs: Target Coordinate Reference System to use for the datasets.
        :param main_region_polygon: GeoDataFrame representing the North Sea region.
        :param output_folder: Folder where the final processed raster will be saved.
        :param bbox: Bounding box for initial clipping in the format (min_lon, min_lat, max_lon, max_lat).
        """

        if not filename:
            filename = "bathymetry_final.tif"
        
        clipped_raster_paths = []
        
        bathymetry_output_dir = os.path.join(self.output_dir, "bathymetry")
        # make the directory if it doesnt exist
        os.makedirs(bathymetry_output_dir, exist_ok=True)

        # Clip each raster to the bounding box and save
        for key, path in bathymetry_path_dict.items():
            self.logger.info(f"Processing {key}...")
            raster_path = os.path.join(self.raw_data_dir, path)
            output_path = os.path.join(bathymetry_output_dir, key + ".tif")
            self.clip_raster_to_bbox(raster_path, bbox, output_path)
            # Append the output path of the clipped raster to the list
            clipped_raster_paths.append(output_path)
    
        # Merge the clipped bathymetry rasters
        merged_raster_path = os.path.join(bathymetry_output_dir, "bathymetry_merged.tif")
        self.merge_rasters(clipped_raster_paths, merged_raster_path)
    
        # Reproject, clip and save the final raster
        final_output_path = os.path.join(bathymetry_output_dir, filename)
        self.reproject_clip_raster(merged_raster_path, main_region_polygon, output_dir=bathymetry_output_dir, output_filename=filename)
    
        self.logger.info(f"Final bathymetry raster processed and saved to {final_output_path}")

    
    def process_and_save_shipping_lanes(self, input_paths, main_region_polygon, filename=None):
        """
        Processes shipping lanes raster files by clipping to a bounding box, merging, reprojecting, and clipping to a GeoDataFrame extent.
    
        :param input_paths: List of paths to the monthly shipping lanes raster files.
        :param crs: Target Coordinate Reference System to use for the datasets.
        :param main_region_polygon: GeoDataFrame representing the study region.
        :param output_folder: Folder where the final processed raster will be saved.
        :param filename: Name of the saved raster file.
        """

        if not filename:
            filename = "shipping_lanes.tif"

        shipping_output_dir = os.path.join(self.output_dir, "shipping_lanes")

        # make the directory if it doesnt exist
        os.makedirs(shipping_output_dir, exist_ok=True)

        # Merge the monthly shipping lanes rasters first
        merged_raster_path = os.path.join(shipping_output_dir, "shipping_lanes_unprojected.tif")
        self.merge_monthly_rasters(input_paths, merged_raster_path)
    
        # Reproject the raster and clip to the North Sea EEZ after merging
        self.reproject_clip_raster(merged_raster_path, main_region_polygon, shipping_output_dir, filename)
    
        final_output_path = os.path.join(shipping_output_dir, filename)
        self.logger.info(f"Annual shipping lanes raster processed and saved to {final_output_path}")