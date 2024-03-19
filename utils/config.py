import json
from pathlib import Path

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
                    # Filtering for .shp files
                    shp_files = [file for file in files if file.endswith('.shp')]
                    if shp_files:
                        # Constructing relative path keys from the root
                        relative_path = Path(root).relative_to(data_dir)
                        dict_ref = structure
                        for part in relative_path.parts:
                            dict_ref = dict_ref.setdefault(part, {})
                        # Assuming shp_files is not empty, assigning file list to the last directory key
                        dict_ref['files'] = shp_files
    
                return structure
                
            data_structure = list_files_recursive(data_dir)
    
            # Writing the structured data to JSON
            with open(data_paths_file, 'w') as file:
                json.dump(data_structure, file, indent=4)
            
            print(f"Data paths have been updated in {data_paths_file}")

        
