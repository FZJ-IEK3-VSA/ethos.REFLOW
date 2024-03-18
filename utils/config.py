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
        # Initialize the path with the project root
        path_accumulator = self.project_root

        # Initialize the section of the config to start from
        config_section = self.config

        # Iterate over the keys
        for key in keys:
            # Navigate the configuration and build the path
            if key in config_section:
                # Update the path_accumulator if the key is found,
                # but only append it if it's a deeper section, not just a file name.
                # This assumes directory names in the JSON do not end in file extensions.
                if isinstance(config_section[key], dict):
                    path_accumulator = path_accumulator / key
                    config_section = config_section[key]
                elif '.' not in key:  # Assuming it's a directory if there's no file extension
                    path_accumulator = path_accumulator / key
                # If it's a file or a terminal directory, append its specific path
                else:
                    path_accumulator = path_accumulator / config_section[key]
            else:
                # If the key is not found, assume it's a directory and append it
                path_accumulator = path_accumulator / key

        return path_accumulator
    

        
