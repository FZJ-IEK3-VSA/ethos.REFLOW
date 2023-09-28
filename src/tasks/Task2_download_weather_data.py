import luigi
import docker
from src.utils.docker_management import DockerManager
from src.tasks.Task1_set_region import Task1
import os
import textwrap

## PART 2 OF THE WORKFLOW ##
## Previous: Task1_set_region.py
## Next: data_processing.py

class Task2(luigi.Task):
    # set all the paths for initialisation and the parameters for running the generator
    image_name = luigi.Parameter()
    container_name = luigi.Parameter()
    data_dir = luigi.Parameter()
    install_dir = luigi.Parameter()
    output_dir = luigi.Parameter()
    weather_data_params = luigi.Parameter()
    task1_config = luigi.Parameter()
    task1_output_dir = luigi.Parameter()

    def requires(self):
        return Task1(
            image_name=self.task1_config['image_name'],
            container_name=self.task1_config['container_name'],
            install_dir=self.task1_config['install_dir'],
            data_dir=self.data_dir,
            output_dir=os.path.join(self.task1_output_dir),
            gadm_version=self.task1_config['gadm_version'],
            shapefile_params=self.task1_config['shapefile_params']
        )

    def output(self):
        """
        Returns the target output for this task. 
        """
        return None
    
    def run(self):
        """
        The code to actually run the task.
        """
        task1_output_target = self.requires().output()
        if not task1_output_target and task1_output_target.exists():
            print("Task 1 output does not exist. Cannot run Task 2.")

        else:
            print("Task 1 output exists. Continuing to Task 2...")

            # Get the directory containing the .shp file
            dir_path = os.path.dirname(task1_output_target.path)
            # Get just the file name
            shp_file_name = os.path.basename(task1_output_target.path)

            # Extract the region_name from the path
            region_name = os.path.basename(dir_path)
            print(f"Region name: {region_name}")

            DockerManager.setup_container(self.container_name, self.image_name, self.install_dir, self.data_dir, self.output_dir, dir_path)
            print("Container setup complete.")

            # The container should now be correctly configured, so it can be used
            client = docker.from_env()
            container = client.containers.get(self.container_name)
            print("Running Task_2 container")
            
            cmd_str_one_line = """from downloader.downloader import main as download_main; (lambda: [print(message) for message in download_main(data_source='ERA5', data_type='wind', start_year='2000', end_year='2005', region_input='/prev_task_output/shp_Western Cape_GID_1.shp', name='Western Cape', dl_path='/output', test='True', process_raw='True', delete_raw='True')])()"""

            # Run the command
            print("Running exec command...")
            result = container.exec_run(cmd=["/opt/conda/bin/python", "-c", cmd_str_one_line])

            # Print the results for debugging
            print("Exec output:", result.output.decode())
            print("Exec exit code:", result.exit_code)