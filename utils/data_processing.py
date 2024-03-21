import os
import time 
import logging
from shapely.geometry import box, Polygon, MultiPolygon
import geopandas as gpd
import pandas as pd
import time
import json
from utils.config import ConfigLoader

class VectorProcessor:
    def __init__(self):
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

    def reproject_vector(self, vector_data, logger, crs=None):
        """
        Reprojects vector data to the specified CRS.

        Parameters:
        - vector_data: A GeoDataFrame representing vector data.
        - crs: The target coordinate reference system in EPSG format.
        """
        if crs is None:
            crs = self.default_crs

        if vector_data.crs != crs:
            logger.info(f"CRS mismatch. Reprojecting to {crs}...")
            vector_data = vector_data.to_crs(crs)
        logger.info(f"Reprojected to {crs}.")	
        return vector_data

    def buffer_vector(self, vector_data, buffer_distance, logger):
        """
        Buffers the vector data by a specified distance.

        Parameters:
        - vector_data: A GeoDataFrame representing vector data.
        - buffer_distance: Buffer distance in the unit of the vector data's CRS.
        """
        buffered_data = vector_data.buffer(buffer_distance)
        buffered_data_gpd = gpd.GeoDataFrame(geometry=buffered_data, crs=vector_data.crs)
        logger.info(f"Buffered by {buffer_distance}.")
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

    def merge_geo_dataframes(self, geo_df_list, logger):
        """
        Merges a list of GeoDataFrames into a single GeoDataFrame.

        Parameters:
        - geo_df_list: List of GeoDataFrames to merge.
        - crs: Coordinate Reference System in EPSG format.
        """
        merged_df = gpd.GeoDataFrame(pd.concat(geo_df_list, ignore_index=True), crs=self.default_crs)
        logger.info("Merged GeoDataFrames.")
        return merged_df


    def clip_buffer_merge_vector_data(self, data_dict, reference_polygon, buffer_distance, logger):
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
        reference_polygon_reprojected = self.reproject_vector(reference_polygon, logger)
        # Calculate and convert the bounding box of the reference polygon
        bbox_polygon = self.calculate_bbox_polygon(reference_polygon_reprojected)
    
        data_polygons, buffered_data = [], []  # Initialize lists for processed data
    
        for identifier, shapefile_path in data_dict.items():
            t0 = time.time()
            logger.info(f"Processing {identifier}...")
    
            # Load, reproject, and clip vector data
            vector_data = gpd.read_file(shapefile_path)
            vector_data_reprojected = self.reproject_vector(vector_data, logger)
            logger.info(f"Clipping {identifier}...")
            vector_data_clipped = self.clip_vector_data(vector_data_reprojected, bbox_polygon)
    
            # Buffer and clip the buffered vector data
            logger.info(f"Buffering {identifier}...")
            buffered_vector_data = self.buffer_vector(vector_data_clipped, buffer_distance, logger)
            clipped_buffered_data = self.clip_vector_data(buffered_vector_data, reference_polygon_reprojected)
    
            # Add processed data to lists
            logger.info(f"appending {identifier}.")
            data_polygons.append(vector_data_clipped)
            buffered_data.append(clipped_buffered_data)
            t1 = time.time()
            logger.info(f"Processed {identifier} in {t1 - t0:.2f} seconds.")
    
        # Merge processed data into single GeoDataFrames
        all_data_polygons = self.merge_geo_dataframes(data_polygons, logger)
        all_buffered_data = self.merge_geo_dataframes(buffered_data, logger)

        logger.info("Processed and merged all vector data.")
        return all_data_polygons, all_buffered_data
    

    def merge_two_vectors_and_flatten(self, vector_one, vector_two, logger):
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

        logger.info("Merged and flattened vector data.")
        return merged_vector