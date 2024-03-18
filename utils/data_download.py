import requests
import os
import zipfile
import logging

def download_and_extract(url, folder, filename=None):
    """
    Downloads a file from the given URL to the specified folder.
    If the file is a zip archive, it extracts its contents into the folder.

    Example usage
    download_and_extract("http://example.com/somefile.zip", "/path/to/folder")
    """
    # Check if folder exists and has files
    if os.path.exists(folder) and os.listdir(folder):
        logging.info(f"Folder '{folder}' already exists and is not empty. Skipping download.")
        return None
    
    # Ensuring the folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    if filename:
        local_filename = os.path.join(folder, filename)
    else:   
    # Define the local filename to save the downloaded file
        local_filename = os.path.join(folder, url.split('/')[-1])
    
    # Downloading the file
    logging.info(f"Downloading {url} to {folder}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Checking if the file is a zip file
    if zipfile.is_zipfile(local_filename):
        with zipfile.ZipFile(local_filename, 'r') as zip_ref:
            zip_ref.extractall(folder)
        # deleting the zip file
        os.remove(local_filename)

    return local_filename


def download_gadm_data(country_abrv, gadm_version: str, data_dir):        
    # Create a temporary folder for the extracted data, in the _temp folder within the current directory
    gadm_dir = os.path.join(data_dir, f"gadm")
    temp_folder = os.path.join(gadm_dir, f"_temp/{country_abrv}")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    else:
        logging.info(f"Data for {country_abrv} already exists in temp folder.")
        return True
         
    # Download the ZIP file
    logging.info(f"Using GADM version {gadm_version}.")
    logging.info(f"Downloading data for {country_abrv}...")
    url = f"https://geodata.ucdavis.edu/gadm/gadm{gadm_version[0]}.{gadm_version[1]}/shp/gadm{gadm_version}_{country_abrv}_shp.zip"
    logging.info(url)
    zip_path = f"gadm{gadm_version}_{country_abrv}_shp.zip"
    
    # Download the ZIP file
    response = requests.get(url)
    if response.status_code == 200:
        with open(zip_path, 'wb') as file:
            file.write(response.content)
    else:
        logging.error(f"Failed to download data for {country_abrv}")
        return False
        
    # Extract the ZIP file
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(f"{temp_folder}/gadm{gadm_version}_{country_abrv}")
    except zipfile.BadZipFile:
        logging.error(f"Bad ZIP file for {country_abrv}.)")
        return False
        
    # Delete the ZIP file
    try:
        os.remove(zip_path)
    except FileNotFoundError:
        logging.error(f"Could not delete ZIP file for {country_abrv}.")

    logging.info(f"Processed {country_abrv}.")

    return True