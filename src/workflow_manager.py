import luigi
from src.utils.Task1 import Task1
from src.utils.utils import read_config
import json

if __name__ == '__main__':
    config = read_config('src/config.json')

    data_dir = config['task1_params']['data_dir']
    output_dir = config['task1_params']['output_dir']
    gadm_version = config['task1_params']['gadm_version']
    shapefile_params = config['task1_params']['shapefile_params']

    luigi.build([
        Task1(
            data_dir=data_dir,
            output_dir=output_dir,
            gadm_version=gadm_version,
            shapefile_params=shapefile_params
        )
    ], local_scheduler=True)