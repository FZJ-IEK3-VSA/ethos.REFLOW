import docker
import os

class DockerManager:
    @staticmethod
    def docker_exists(container_name):
        client = docker.from_env()
        try:
            client.containers.get(container_name)
            return True
        except docker.errors.NotFound:
            return False
        
    @staticmethod
    def build_and_run_docker(container_name, install_dir):
        client = docker.from_env()
        tag_name = f"{container_name}:reflow"
        client.images.build(path=install_dir, tag=tag_name)
        client.containers.run(tag_name, name=container_name, detach=True, tty=True)

    @staticmethod
    def remount_volume(container_name, new_volume_path):
        client = docker.from_env()
        # Automatically determine the bind path. 
        # This assumes you have a way to relate new_volume_path to the bind path.
        # Here I simply mirror it for demonstration purposes. Replace with your logic.
        bind_path = f"/data/shapefilegenerator/"
        container = client.containers.get(container_name)
        container.stop()
        container.remove()

        # Run a new container with the remounted volume
        client.containers.run(
            container_name, 
            name=container_name, 
            detach=True, 
            tty=True, 
            volumes={new_volume_path: {'bind': bind_path, 'mode': 'rw'}}
        )