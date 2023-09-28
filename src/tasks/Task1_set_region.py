# task1.py
import docker
import luigi
import json
import os
from src.utils.docker_management import DockerManager

class Task1(luigi.Task):
    # set all the paths for initialisation and the parameters for running the generator
    image_name = luigi.Parameter()
    container_name = luigi.Parameter()
    data_dir = luigi.Parameter()
    install_dir = luigi.Parameter()
    output_dir = luigi.Parameter()
    gadm_version = luigi.Parameter()
    shapefile_params = luigi.Parameter()
    
    def output(self):
        """
        Dynamically finds a .shp file in the specified self.output_dir directory (excluding '_temp').
        Returns a LocalTarget pointing to the found .shp file.
        
        Returns:
            luigi.LocalTarget: A LocalTarget object pointing to the found .shp file.
        """
        for dir_name, _, file_names in os.walk(self.output_dir):
            if "_temp" in dir_name:
                continue
            for file_name in file_names:
                if file_name.endswith('.shp'):
                    return luigi.LocalTarget(os.path.join(dir_name, file_name))
        return None


    def setup_container(self):
        print("Doing the Docker stuff...")
        # set the volume mapping for the container
        host_volume_mapping = {
            self.data_dir: {'bind': '/input', 'mode': 'rw'},
            self.output_dir: {'bind': '/output', 'mode': 'rw'}
        }

        DockerManager.get_or_create_container(self.container_name, self.image_name, host_volume_mapping, self.install_dir)
        expected_volumes = [vol['bind'] for vol in host_volume_mapping.values()]
        if not DockerManager.check_volumes_attached(self.container_name, expected_volumes):
            print("Volumes are not correctly attached. Recreating container...")
            DockerManager.stop_and_remove_container(self.container_name)
            DockerManager.create_container(self.container_name, self.image_name, host_volume_mapping)

        else:
            print("Volumes correctly attached to container.")

    def run(self):
        self.setup_container()
        print("Container setup complete.")
        # The container should now be correctly configured, so you can proceed to use it
        client = docker.from_env()
        container = client.containers.get(self.container_name)
        print("Running Task_1 container")

        # set the command to initialise the generator
        init_command = f'''import os
        from shpgen import ShapefileGenerator
        sg = ShapefileGenerator("/input", "/output", "{self.gadm_version}")
        sg.return_shapefile(region='{self.shapefile_params['region_name']}', crs='{self.shapefile_params['crs']}', place='{self.shapefile_params['place_name']}', admin_depth={self.shapefile_params['admin_depth']}, savefile={self.shapefile_params['savefile']}, plot={self.shapefile_params['plot']})
        '''
        init_command_escaped = init_command.replace("\n", "; ")
        result = container.exec_run(cmd=["/opt/conda/bin/python", "-c", init_command_escaped])

        # Print the results for debugging
        print("Exec output:", result.output.decode())
        print("Exec exit code:", result.exit_code)

    def complete(self):
        """
        Checks whether the task is complete based on the dynamic output() method.
        Calls output() to get the LocalTarget and checks if it exists.
        
        Returns:
            bool: True if the .shp file exists, False otherwise.
        """
        output_target = self.output()
        if output_target is not None:
            return output_target.exists()
        else:
            return False

