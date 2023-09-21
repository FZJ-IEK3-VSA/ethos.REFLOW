# task1.py

import docker
import luigi
import json

class Task1(luigi.Task):
    # set all the paths for initialisation and the parameters for running the generator
    install_dir = luigi.Parameter()
    data_dir = luigi.Parameter()
    output_dir = luigi.Parameter()
    gadm_version = luigi.Parameter()
    shapefile_params = luigi.Parameter()

    def _docker_exists(self):
        client = docker.from_env()
        try:
            client.containers.get('shapefilegenerator')
            return True
        except docker.errors.NotFound:
            return False
        
    def _build_and_run_docker(self):
        client = docker.from_env()
        client.images.build(path=self.install_dir, tag="shapefilegenerator:reflow")
        client.containers.run("shapefilegenerator:reflow", name="shapefilegenerator", detach=True, tty=True)

    def run(self):
        if not self._docker_exists():
            self._build_and_run_docker()

        client = docker.from_env()
        container = client.containers.get("shapefilegenerator:reflow")

        # Initialise sg class within Docker container
        # This assumes that it is possible to send commands to the container's bash to initialise
        init_command = f"python -c 'import os: from shpgen import ShapefileGenerator; sg = ShapefileGenerator(\"{self.data_dir}\", \"{self.output_dir}\", \"{self.gadm_version}\")'"
        container.exec_run(cmd=["/bin/bash", "-c", init_command])

        # Import the shapefile_params from the config file
        shapefile_params_str = json.dumps(self.shapefile_params).replace("\"", "\\\"")

        # Run the sg.return_shapefile from within Docker container using the params
        run_shapefile_command = f"python -c 'sg.return_shapefile(**{shapefile_params_str})'"
        container.exec_run(cmd=["/bin/bash", "-c", run_shapefile_command])