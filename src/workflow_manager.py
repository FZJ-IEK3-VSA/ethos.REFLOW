import luigi
from src.tasks.Task1_set_region import Task1
from src.tasks.Task2_download_weather_data import Task2
from src.utils.utils import read_config, check_docker_access
import os

def build_tasks_from_config(config):
    task_list = []

    # Global paths
    data_dir = config['global_paths']['data_dir']
    output_dir = config['global_paths']['output_dir']

    # Task 1
    task1_config = config.get('Task1_shapefile-generator')
    if task1_config:
        task1 = Task1(
            image_name=task1_config['image_name'],
            container_name=task1_config['container_name'],
            install_dir=task1_config['install_dir'],
            data_dir=data_dir,
            output_dir=os.path.join(output_dir, task1_config['output_dir']),
            gadm_version=task1_config['gadm_version'],
            shapefile_params=task1_config['shapefile_params']
        )
        task_list.append(task1)

    # Task 2
    task2_config = config.get('Task2_download-data')
    if task2_config:
        task2 = Task2(
            image_name=task2_config['image_name'],
            container_name=task2_config['container_name'],
            install_dir=task2_config['install_dir'],
            data_dir=data_dir,
            output_dir=os.path.join(output_dir, task2_config['output_dir']),
            weather_data_params=task2_config['weather_data_params'],
            task1_config=task1_config,
            task1_output_dir=os.path.join(output_dir, task1_config['output_dir'])
        )
        task_list.append(task2)

    return task_list

if __name__ == '__main__':
    if check_docker_access():
        print("Container has access to the Docker daemon.")
    else:
        print("Container does not have access to the Docker daemon.")

    ## set the paths for the config file and read it
    config = read_config('src/config.json')
    tasks_to_run = build_tasks_from_config(config)
    luigi.build(tasks_to_run, local_scheduler=True)