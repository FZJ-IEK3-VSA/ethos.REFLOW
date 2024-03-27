#### set of helper functions
import unicodedata
import os
import xarray as xr
from pathlib import Path

def check_files_exist(folder_path, file_name_base):
    """
    Checks if there are already files in the folder that start with the file_name_base.

    :param folder_path: Path to the folder where files are saved.
    :param file_name_base: Base name of the file to check for.
    :return: True if files exist, False otherwise.
    """
    # Ensure the folder exists to avoid errors when listing contents
    if not os.path.exists(folder_path):
        return False
    
    # List all files in the directory
    for file in os.listdir(folder_path):
        if file.startswith(file_name_base):
            return True  # File(s) found with the base name
    return False  # No files found with the base name

def normalize_letter(char):
    # Normalize the character and return the base character if it's a letter
    return unicodedata.normalize('NFKD', char).encode('ASCII', 'ignore').decode()

def normalize_filename(filename):
    # Normalize each character in the filename
    return ''.join(normalize_letter(char) for char in filename)


def rename_files_in_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            normalized_filename = normalize_filename(filename)
            original_filepath = os.path.join(root, filename)
            new_filepath = os.path.join(root, normalized_filename)
            if original_filepath != new_filepath:
                os.rename(original_filepath, new_filepath)
                print(f"Renamed '{filename}' to '{normalized_filename}' in '{root}'")


def create_target_directories(output_dir, year):
    """
    Create the target directories for the year.

    :param year: The year for which to create the directories.
    """
    ## create processed dir
    os.makedirs(output_dir, exist_ok=True)

    ## create year directory 
    target_dir = os.path.join(output_dir, str(year))
    os.makedirs(target_dir, exist_ok=True)

def find_raw_netcdf_files(year):
    """
    Find the raw files for a specific variable.
    """
    raw_dir = os.path.join(raw_dir, year)
    raw_files = [os.path.join(raw_dir, file) for file in os.listdir(raw_dir) if file.endswith(".nc")]
    return raw_dir, raw_files

def copy_basic(raw_ds, target_ds):
    """
    Copy attributes, dimensions, and specific variables from the raw dataset to the target dataset.
    """
    # Merge the datasets, keeping the existing variables in target_ds
    target_ds = xr.merge([target_ds, raw_ds[['latitude', 'longitude', 'time']]])
    return target_ds

def remove_key_from_paths(exclusion_data_paths):
    """
    Modifies the exclusion data paths dictionary in-place, removing the key from the start of each path.

    :param exclusion_data_paths: Dictionary of exclusion data paths to modify.
    """
    for key, paths in exclusion_data_paths.items():
        new_paths = []
        for path in paths:
            # Construct the pattern to remove from the start of the path
            pattern = key + "\\"
            # Check if the pattern is at the start and remove it
            if path.startswith(pattern):
                new_path = path[len(pattern):]
                new_paths.append(new_path)
            else:
                new_paths.append(path)
        # Update the dictionary with the modified paths
        exclusion_data_paths[key] = new_paths

def populate_exclusion_data_paths(base_dir, exclusion_data_paths, file_exts=None):
    """
    Populate the exclusion data paths dictionary with files from the specified directories,
    ensuring the key is part of the path in the output.

    :param base_dir: Base directory to search for files.
    :param exclusion_data_paths: Dictionary of exclusion data paths to populate.
    :param file_exts: List of file extensions to include (e.g., ['.shp', '.tif']).
    """
    if not file_exts:
        file_exts = ['.gdb', '.shp', '.tif']

    base_dir_path = Path(base_dir)

    for key in exclusion_data_paths.keys():
        folder_path = base_dir_path / key
        found_files = []

        # Check for .gdb directories first
        if '.gdb' in file_exts:
            gdb_dirs = [x for x in folder_path.iterdir() if x.is_dir() and x.suffix == '.gdb']
            if gdb_dirs:
                found_files.extend([os.path.join(key, x.name).replace('\\', '/') for x in gdb_dirs])
                exclusion_data_paths[key] = found_files
                continue  # Skip searching for other file types if .gdb is found

        # If no .gdb is found, or other extensions are specified, search for files
        for ext in file_exts:
            if ext != '.gdb':  # Since .gdb was already checked
                for file in folder_path.rglob(f'*{ext}'):
                    if file.is_file():
                        # Here, we simply include the key and use the file's relative path
                        # No need to strip the key or adjust the path
                        str_path = str(file.relative_to(base_dir_path)).replace('\\', '/')
                        found_files.append(str_path)

        if not found_files:
            found_files.append("No files found")
        exclusion_data_paths[key] = found_files

    return exclusion_data_paths



