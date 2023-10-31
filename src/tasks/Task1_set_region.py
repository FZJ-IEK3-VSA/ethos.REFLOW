# task1.py
import docker
import luigi
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


    def run(self):
        """
        Executes the main logic of the Luigi task in the Docker container.
        
        This method sets up the container using `setup_container()` and then runs a Python
        script within the container. The script imports necessary modules, initializes the 
        `ShapefileGenerator`, and runs its `return_shapefile` method with the parameters 
        specified in `self.shapefile_params`.

        Returns:
            None
        
        Side-effects:
            - Logs are printed for debugging.
            - Files may be generated in the mapped volumes of the container.

        Raises:
            RuntimeError: If any step in the container setup or script execution fails.
        """
        DockerManager.setup_container(self.container_name, self.image_name, self.install_dir, self.data_dir, self.output_dir)
        print("Container setup complete.")

        # The container should now be correctly configured, so it can be used
        client = docker.from_env()
        container = client.containers.get(self.container_name)
        print("Running Task_1 container")

        # set the command to initialise the generator
        init_command = f'''import os
        from shpgen import ShapefileGenerator
        sg = ShapefileGenerator("/output", "{self.gadm_version}")
        sg.return_shapefile(region='{self.shapefile_params['region_name']}', crs='{self.shapefile_params['crs']}', place='{self.shapefile_params['place_name']}', admin_depth={self.shapefile_params['admin_depth']}, savefile={self.shapefile_params['savefile']}, plot={self.shapefile_params['plot']})
        '''
        init_command_escaped = init_command.replace("\n", "; ")
        result = container.exec_run(cmd=["/opt/conda/bin/python", "-c", init_command_escaped])

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

