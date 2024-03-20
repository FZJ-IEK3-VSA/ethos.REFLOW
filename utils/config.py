import json
from pathlib import Path
import os
import logging

class ConfigLoader:
    def __init__(self):
        # determine script directory and project root
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        # load the config file
        self.config_path = self.project_root / "settings" / "directory_management.json"
        self.config = self._load_config(self.config_path)

    def _load_config(self, config_path):
        with open(self.config_path, 'r') as file:
            return json.load(file)

    def get_path(self, *keys):
            path_accumulator = self.project_root
            config_section = self.config
    
            # Track if the final key directly maps to a string (path)
            use_final_value = False
            final_value = ""
    
            for key in keys:
                if key in config_section:
                    # Check if we're at the last key and it maps directly to a string
                    if isinstance(config_section[key], str):
                        final_value = config_section[key]
                        use_final_value = True
                        break
                    # Otherwise, dive deeper into the configuration
                    elif isinstance(config_section[key], dict):
                        config_section = config_section[key]
                # If a key isn't found, append it directly (assuming it's a directory)
                else:
                    path_accumulator /= key
    
            if use_final_value:
                # Construct path using all keys (as directories) except for the last,
                # append the final_value at the end.
                return self.project_root / '/'.join(keys[:-1]) / final_value
            else:
                # If not using final_value, build the path from accumulated keys
                for key in keys:
                    path_accumulator /= key
    
            return path_accumulator
    
    def update_data_paths(self):
            data_dir = self.project_root / 'data'
            data_paths_file = self.project_root / 'settings' / 'data_paths.json'
        
            def list_files_recursive(path):
                structure = {}
                for root, dirs, files in os.walk(path):
                    if files:  # Check if there are any files in the directory
                        # Constructing relative path keys from the root
                        relative_path = Path(root).relative_to(data_dir)
                        dict_ref = structure
                        for part in relative_path.parts:
                            dict_ref = dict_ref.setdefault(part, {})
                        # Assigning file list to the last directory key without filtering
                        dict_ref['files'] = files
        
                return structure
                
            data_structure = list_files_recursive(data_dir)
        
            # Writing the structured data to JSON
            with open(data_paths_file, 'w') as file:
                json.dump(data_structure, file, indent=4)
            
            logging.info(f"Data paths have been updated in {data_paths_file}")

    def get_file_paths(self, parent_dir, country_codes=None, zoom_level=None, specific_file=None):
            """
            Constructs file paths using the structure defined in data_paths.json.
        
            Parameters:
            - parent_dir: The parent directory key in the data_paths.json structure (e.g., 'gadm' within 'project_data').
            - country_codes: Optional list of country codes if querying GADM files.
            - zoom_level: Optional GADM zoom level if querying GADM files.
            - specific_file: Optional specific file to locate.
        
            Returns:
            - If specific_file is provided, returns a string path to the file.
            - Otherwise, returns a dictionary with keys as country codes or specific file name and values as full paths.
            """
            data_paths = self.data_paths.get('project_data', {})
        
            data_base_path = os.path.join(self.project_root, 'data')
        
            if specific_file:  # Handle specific file lookup
                for key, section in data_paths.items():
                    if 'files' in section and specific_file in section['files']:
                        # Return the string path directly when a specific file is requested
                        return os.path.normpath(os.path.join(data_base_path, parent_dir, key, specific_file))
                # If the file is not found, return None or raise an error
                logging.error(f"File '{specific_file}' not found in '{parent_dir}' directory.")
                return None
            else:
                result_paths = {}
                if country_codes and zoom_level is not None:  # Handle GADM files by country code and zoom level
                    gadm_section = data_paths.get(parent_dir, {})
                    for code in country_codes:
                        country_section = gadm_section.get(code, {})
                        if not country_section:
                            # Log an error if the country code is not found
                            logging.error(f"Country code {code} not found in {parent_dir}.")
                            continue
                        for gadm_key, gadm_value in country_section.items():
                            if 'files' in gadm_value:
                                zoom_specific_files = [f for f in gadm_value['files'] if f'_{zoom_level}.' in f]
                                for file_name in zoom_specific_files:
                                    result_paths[code] = os.path.normpath(os.path.join(data_base_path, parent_dir, code, gadm_key, file_name))
        
                return result_paths

        
