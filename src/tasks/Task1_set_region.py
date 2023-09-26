# task1.py

import docker
import luigi
import json
import os

class Task1(luigi.Task):
    # set all the paths for initialisation and the parameters for running the generator
    install_dir = luigi.Parameter()
    container_name = luigi.Parameter()
    data_dir = luigi.Parameter()
    output_dir = luigi.Parameter()
    gadm_version = luigi.Parameter()
    shapefile_params = luigi.Parameter()

    def _docker_exists(self):
        """
        Check if a Docker container named 'self.container_name' exists.

        This function uses the Docker API to look for a container with the specified name. 
        It returns True if the container exists, and False otherwise.

        Returns:
            bool: True if container exists, False otherwise.
        """
        client = docker.from_env()
        try:
            client.containers.get(self.container_name)
            return True
        except docker.errors.NotFound:
            return False
    
    def _build_and_run_docker(self):
        """
        Build and run a Docker container named 'self.container_name' from a specified directory.

        This function uses the Docker API to first build an image with the tag "self.container_name:reflow"
        from the directory pointed to by self.install_dir. It then runs a container with the name 
        "self.container_name" using this image, detached and with tty enabled.

        Note:
            Assumes that `self.install_dir` is already set and points to the directory containing the 
            Dockerfile to build the image.
        """
        client = docker.from_env()
        tag_name = f"{self.container_name}:reflow"
        client.images.build(path=self.install_dir, tag=tag_name)
        client.containers.run(tag_name, name=self.container_name, detach=True, tty=True)    
    
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
        Build (if necessary) and run a Docker container to generate a shapefile.

        This method first checks if a Docker container named 'self.container_name' already exists using
        `_docker_exists()`. If it does not exist, it will build and run the container using 
        `_build_and_run_docker()`.

        Once the container is running, it initializes an instance of the `self.container_name` class
        inside the container with the necessary parameters. It then imports configuration for 
        shapefile generation from `self.shapefile_params` and runs the `return_shapefile` method from
        the initialized `self.container_name` object.

        Note:
            1. Assumes that `self.data_dir`, `self.output_dir`, `self.gadm_version`, and `self.shapefile_params`
            are already set.
        """
        if not self._docker_exists():
            self._build_and_run_docker()

        client = docker.from_env()
        tag_name = f"{self.container_name}:reflow"
        container = client.containers.get(tag_name)

        # Initialise sg class within Docker container
        # This assumes that it is possible to send commands to the container's bash to initialise
        init_command = f"python -c 'import os; from shpgen import ShapefileGenerator; sg = ShapefileGenerator(\"{self.data_dir}\", \"{self.output_dir}\", \"{self.gadm_version}\")'"
        container.exec_run(cmd=["/bin/bash", "-c", init_command])

        # Import the shapefile_params from the config file
        shapefile_params_str = json.dumps(self.shapefile_params).replace("\"", "\\\"")

        # Run the sg.return_shapefile from within Docker container using the params
        run_shapefile_command = f"python -c 'sg.return_shapefile(**{shapefile_params_str})'"
        container.exec_run(cmd=["/bin/bash", "-c", run_shapefile_command])

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

