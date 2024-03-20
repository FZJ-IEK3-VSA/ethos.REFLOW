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
    def __init__(self, default_crs="EPSG:3035"):
        """
        Initializes the VectorProcessor with a default CRS.

        Parameters:
        - default_crs: The default coordinate reference system in EPSG format.
        """
        self.default_crs = default_crs
        # set up logging in the VectorProcessor
        config_loader = ConfigLoader()

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
            logging.info(f"CRS mismatch. Reprojecting to {crs}...")
            vector_data = vector_data.to_crs(crs)
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
        return buffered_data_gpd

    def process_vector_data(self, data_dict, reference_polygon, buffer_distance, crs=None):
        """
        Processes a dictionary of vector data: reprojects, clips, buffers, and clips buffers against a reference polygon.

        Parameters:
        - data_dict: Dictionary mapping identifiers to their shapefile paths.
        - reference_polygon: GeoDataFrame used as a reference for clipping.
        - buffer_distance: Distance to buffer the vector data, in the same units as the CRS.
        - crs: Coordinate Reference System to which the data should be reprojected.
        """
        if crs is None:
            crs = self.default_crs

        # Reproject the reference polygon to the target CRS
        reference_polygon = self.reproject_vector(reference_polygon, crs)
        # Calculate the bounding box of the reference polygon to use for clipping
        bbox = reference_polygon.total_bounds
        bbox_polygon = box(*bbox)  # Convert bounding box to a polygon

        data_polygons, buffered_data = [], []  # Initialize lists to hold processed data

        for identifier, shapefile_path in data_dict.items():
            t0 = time.time()  # Start timing the processing
            logging.info(f"Processing {identifier}...")

            # Load the vector data from file, reproject, and clip it to the bounding box
            vector_data = gpd.read_file(shapefile_path)
            vector_data = self.reproject_vector(vector_data, crs)
            vector_data_clipped = gpd.clip(vector_data, bbox_polygon)
            data_polygons.append(vector_data_clipped)  # Add to list of processed polygons

            # Buffer the clipped vector data and then clip the buffer to the reference polygon
            logging.info(f"Buffering {identifier} coastline...")
            buffered_vector_data = self.buffer_vector(vector_data_clipped, buffer_distance)
            clipped_buffered_data = gpd.clip(buffered_vector_data, reference_polygon)
            buffered_data.append(clipped_buffered_data)  # Add to list of processed buffers

            t1 = time.time()  # End timing
            logging.info(f"Processed {identifier} in {t1-t0} seconds.")

        # Merge all processed polygons and buffers into single GeoDataFrames
        all_data_polygons = gpd.GeoDataFrame(pd.concat(data_polygons, ignore_index=True), crs=crs)
        all_buffered_data = gpd.GeoDataFrame(pd.concat(buffered_data, ignore_index=True), crs=crs)

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
    
            logging.info("Merged and flattened vector data.")
            return merged_vector