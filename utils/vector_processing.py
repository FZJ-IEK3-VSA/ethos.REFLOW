import os
import time 
import logging
from pyproj import Transformer
from shapely.geometry import box, Polygon, MultiPolygon
import geopandas as gpd
import pandas as pd
import time
import json
from utils.config import ConfigLoader
from utils.utils import check_files_exist, rename_files_in_folder
import fiona
import logging
import fiona

# set geopandas to use the fiona library
gpd.options.io_engine = "fiona"

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

        self.raw_data_dir = config_loader.get_path("data", "exclusion_data", "raw")
        self.processed_dir = config_loader.get_path("data", "exclusion_data", "processed")
        self.crs = project_settings["crs"]

    def reproject_vector(self, vector_data, crs=None):
        """
        Reprojects vector data to the specified CRS.

        Parameters:
        - vector_data: A GeoDataFrame representing vector data.
        - crs: The target coordinate reference system in EPSG format.
        """
        if crs is None:
            crs = self.crs

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
    
    def calculate_and_transform_bbox(self, reference_polygon, expand_size=0.0):
        """
        Calculate, transform, and optionally expand the bounding box of a reference polygon.

        Parameters:
        reference_polygon (gpd.GeoDataFrame): The reference polygon(s) GeoDataFrame.
        expand_size (float): The amount to expand the bounding box by in degrees. Default is 0.0.

        Returns:
        tuple: The transformed and optionally expanded bounding box as (lon_min, lat_min, lon_max, lat_max).
        """
        # Calculate the bounding box as a polygon
        calculated_bbox_polygon = self.calculate_bbox_polygon(reference_polygon)
        
        # Extract bounds and optionally expand
        minx, miny, maxx, maxy = calculated_bbox_polygon.bounds
        
        # Initialize the transformer to convert from EPSG:3035 to EPSG:4326
        transformer = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
        
        # Transform the corners of the expanded bounding box
        lon_min, lat_min = transformer.transform(minx, miny)
        lon_max, lat_max = transformer.transform(maxx, maxy)

        lon_min -= expand_size
        lat_min -= expand_size
        lon_max += expand_size
        lat_max += expand_size
        
        # Return the transformed and expanded bounding box
        bbox = (lon_min, lat_min, lon_max, lat_max)
        return bbox


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
    
        # Calculate and convert the bounding box of the reference polygon
        bbox_polygon = self.calculate_bbox_polygon(reference_polygon)
    
        data_polygons, buffered_data = [], []  # Initialize lists for processed data
    
        for identifier, shapefile_path in data_dict.items():
            self.logger.info(shapefile_path)
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
            clipped_buffered_data = self.clip_vector_data(buffered_vector_data, reference_polygon)
    
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
        rename_files_in_folder(self.processed_dir)
        self.logger.info("Renamed all files in the processed folder.")

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
        # open the gdb file
        layers = fiona.listlayers(full_path)
        for layer_name in layers:
            gdf = gpd.read_file(full_path, driver="OpenFileGDB", layer=layer_name)
    
            # Check if the layer has a CRS assigned
            if gdf.crs is None:
                self.logger.info(f"Layer {layer_name} does not have a CRS assigned and will be skipped.")
                continue  # Skip this layer and move to the next one
            
            # Remove datetime fields
            gdf = self.remove_datetime_fields(gdf)
    
            gdf = gdf.to_crs(self.crs)
            gdf_clipped = gpd.clip(gdf, region_gdf) # clip the geodataframe
            geom_type = self.get_geometry_type(gdf_clipped).replace(" ", "_").lower()  # get the geometry type
            file_name = f"{layer_name}_{geom_type}"  
    
            self.save_gdf_to_file(gdf_clipped, folder_path, file_name, file_format='shapefile')  # save as a shapefile

    def clip_and_save_vector_datasets(self, vector_path_dict, main_polygon_path):
        """
        Processes and saves datasets for a dictionary of vector paths.
    
        :param vector_path_dict: Dictionary with dataset keys and paths to their source files.
        :param region_gdf: GeoDataFrame representing the clipping region.
        :param folder_base_path: Base path for saving processed datasets.
        :param crs: Coordinate Reference System to use for the datasets.
        """
        region_gdf = gpd.read_file(main_polygon_path)

        for key, paths in vector_path_dict.items():
            for path in paths:
                self.logger.info(f"Processing {key}...")
        
                full_path_to_vector = os.path.join(self.raw_data_dir, path)
                output_folder_path = os.path.join(self.processed_dir, key)
                file_extension = os.path.splitext(path)[1].lower()
        
                # Check if files already exist
                if check_files_exist(full_path_to_vector, key):
                    self.logger.info(f"Files already exist for {key}, skipping processing.")
                    continue
        
                if file_extension == '.gdb':
                    try:
                        self.gbd_clip_to_shp_file(full_path_to_vector, region_gdf, output_folder_path)
                    except Exception as e:
                        self.logger.error(f"Error processing {key}: {e}")
                        continue
                elif file_extension == '.shp':
                    try:
                        self.clip_and_save_shp_file(full_path_to_vector, region_gdf, output_folder_path)
                    except Exception as e:
                        self.logger.error(f"Error processing {key}: {e}")
                        continue
                else:
                    self.logger.info(f"Unsupported file format for {key}: {file_extension}")
                    continue


    def extract_subpolygon(self, vector_data, attribute, value):
        """
        Extracts a subpolygon from a GeoDataFrame based on a specified attribute and value.

        Parameters:
        - vector_data: A GeoDataFrame representing the vector data.
        - attribute: The attribute column to search in.
        - value: The value to search for in the attribute column.

        Returns:
        - GeoDataFrame containing the extracted subpolygon(s) that match the search criteria.
        """
        if attribute not in vector_data.columns:
            self.logger.error(f"Attribute '{attribute}' not found in the vector data.")
            return None

        filtered_data = vector_data[vector_data[attribute] == value]

        if filtered_data.empty:
            self.logger.info(f"No data found for {attribute} = {value}.")
            return None

        self.logger.info(f"Extracted subpolygon for {attribute} = {value}.")
        return filtered_data
    
    def extract_epsg_code(self, epsg_string):
    # Split the string on ':' and extract the second part which should be the numeric code
        parts = epsg_string.split(':')
        if len(parts) == 2 and parts[0].upper() == 'EPSG':
            try:
                # Convert the string number to an integer
                epsg_code = int(parts[1])
                return epsg_code
            except ValueError:
                raise ValueError("Invalid EPSG code provided.")
        else:
            raise ValueError("EPSG string format is incorrect.")
    
    
    def flatten_multipolygons(self, gdf):
        # This will store each row with possibly expanded multipolygons as separate polygons
        new_rows = []
        
        for _, row in gdf.iterrows():
            geom = row.geometry
            if isinstance(geom, MultiPolygon):
                # If the geometry is a MultiPolygon, expand it into individual Polygons
                for poly in geom:
                    new_row = row.copy()
                    new_row.geometry = poly
                    new_rows.append(new_row)
            else:
                # If it's not a MultiPolygon, just append it as is
                new_rows.append(row)
        
        # Create a new GeoDataFrame
        new_gdf = gpd.GeoDataFrame(new_rows, crs=gdf.crs)
        return new_gdf
        
    def save_geodataframe(self, gdf, filepath):
        # Determine the geometry types and group by these types
        grouped = gdf.groupby(gdf.geometry.geom_type)

        for geom_type, group in grouped:
            if geom_type == "GeometryCollection":
                self.logger.error(f"Unhandled GeometryCollection found in data, cannot save to Shapefile.")
                continue  # Skip saving this group
            # Define the filepath for each geometry type
            type_specific_filepath = f"{filepath.rsplit('.', 1)[0]}_{geom_type.lower()}.shp"

            # Define the schema based on the DataFrame structure
            schema = {
                'geometry': geom_type,
                'properties': {name: 'str' for name in group.columns.drop('geometry')}
            }

            # Log the operation
            self.logger.info(f"Saving {geom_type} data to {type_specific_filepath}")

            # Save the GeoDataFrame to a Shapefile with the correct schema
            group.to_file(
                type_specific_filepath,
                driver='ESRI Shapefile',
                schema=schema,
                crs=group.crs
            )

            self.logger.info(f"Data saved successfully to {type_specific_filepath}")