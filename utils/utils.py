#### set of helper functions
import unicodedata
import os
import xarray as xr

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

