import os
from utils.config import ConfigLoader
from scripts.data_download.meteorological_data import DownloadMeterologicalData
import luigi
import json
import subprocess

class ConvertCCItoTIF(luigi.Task):
    year = 2016
    band_name = "lccs_class"

    def requires(self):
        return [DownloadMeterologicalData()]
    
    def output(self):
        output_filename = f"C3S-LC-L4-LCCS-Map-300m-P1Y-{self.year}-v2.1.1.tif"
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("data", "met_data"), 'CCI', f"{self.year}", output_filename))
    
    def run(self):
        #### directory management ####
        ## set up the logger ## 
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'ProcessExclusionsData.log')
        logger = ConfigLoader().setup_task_logging('ProcessRegionBuffers', log_file)
        logger.info("Starting ProcessExclusionsData task")

        cci_data_dir = os.path.join(ConfigLoader().get_path("data", "met_data"), "CCI", f"{self.year}")
        

        ## start it up 
        input_filename = os.path.join(cci_data_dir, f"C3S-LC-L4-LCCS-Map-300m-P1Y-{self.year}-v2.1.1.nc")
        output_filename = self.output().path

        cmd = [
            'gdalwarp', '-of', 'Gtiff', '-co', 'COMPRESS=LZW', '-co', 'TILED=YES', '-ot', 'Byte',
            '-te', '-180.0000000', '-90.0000000', '180.0000000', '90.0000000',
            '-tr', '0.002777777777778', '0.002777777777778', '-t_srs', 'EPSG:4326',
            f'NETCDF:"{input_filename}":{self.band_name}', output_filename
        ]

        # Run the GDAL command
        subprocess.check_call(cmd)

        # Task completion
        logger.info("CCI data conversion task complete.")
