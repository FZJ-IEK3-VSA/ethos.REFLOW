import luigi
from src.utils.Task1_set_region import Task1
from src.utils.utils import read_config, check_docker_access
import os

if __name__ == '__main__':
    if check_docker_access():
        print("Container has access to the Docker daemon.")
    else:
        print("Container does not have access to the Docker daemon.")

    config = read_config('src/config.json')

    data_dir = config['global_paths']['data_dir']
    output_dir = config['global_paths']['output_dir']
    install_dir = config['task1']['install_dir']
    gadm_version = config['task1']['gadm_version']
    shapefile_params = config['task1']['shapefile_params']
    
    # set the output paths for each of the tasks
    Task1_out = config['task1']['output_dir']

    luigi.build([
        Task1(
            container_name="shapefilegenerator",
            install_dir=install_dir,
            data_dir=data_dir,
            output_dir=os.path.join(output_dir, Task1_out),
            gadm_version=gadm_version,
            shapefile_params=shapefile_params
        )
    ], local_scheduler=True)