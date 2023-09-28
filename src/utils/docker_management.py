import docker

class DockerManager:
    @staticmethod
    def container_exists(container_name):
        client = docker.from_env()
        try:
            client.containers.get(container_name)
            return True
        except docker.errors.NotFound:
            return False

    @staticmethod
    def image_exists(image_name):
        client = docker.from_env()
        try:
            client.images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False

    @staticmethod
    def build_image(image_name, install_dir):
        client = docker.from_env()
        client.images.build(path=install_dir, tag=image_name)
        return image_name
    
    @staticmethod
    def create_container(container_name, image_name, host_volume_mapping=None):
        client = docker.from_env()

        if host_volume_mapping:
            client.containers.run(
                image_name,
                name=container_name,
                volumes=host_volume_mapping,
                detach=True,
                tty=True,
                command='bash'
            )

    @staticmethod
    def ensure_container_running(container_name):
        client = docker.from_env()
        container = client.containers.get(container_name)
        if container.status != 'running':
            print("Container not running, starting container...")
            container.start()
        else:
            print("Container already running.")

    @staticmethod
    def get_or_create_container(container_name, image_name, host_volume_mapping, install_dir=None):
        print("Checking if container exists...")
        if DockerManager.container_exists(container_name):
            DockerManager.ensure_container_running(container_name)
            return
        print("Checking if image exists...")
        if DockerManager.image_exists(image_name):
            print("Image exists, creating container...")
            DockerManager.create_container(container_name, image_name, host_volume_mapping)
            return
        print("Image does not exist, building image...")
        if install_dir:
            DockerManager.build_image(image_name, install_dir)
            print("Image built, creating container...")
            DockerManager.create_container(container_name, image_name, host_volume_mapping)
            return
        
        raise ValueError("No install_dir provided and image does not exist. Cannot create container.")
    
    @staticmethod
    def check_volumes_attached(container_name, expected_volumes):
        client = docker.from_env()
        container = client.containers.get(container_name)
        existing_volumes = container.attrs['Mounts']

        # Debug prints
        print(f"Existing Volumes from Container: {existing_volumes}")

        # Extract existing volume paths from the container
        existing_volume_paths = [vol['Destination'] for vol in existing_volumes]

        # Debug prints
        print(f"Extracted Paths: {existing_volume_paths}")
        print(f"Expected Paths: {expected_volumes}")

        # Check if expected volumes are attached to the container
        return all(path in existing_volume_paths for path in expected_volumes)
    
    @staticmethod
    def attach_volumes(container_name, image_name, host_volume_mapping):
        client = docker.from_env()

        # Check if expected volumes are already attached to the container
        expected_volumes = list(host_volume_mapping.values())
        if DockerManager.check_volumes_attached(container_name, expected_volumes):
            print("Volumes already attached to container.")
            return
        
        print("Volumes not attached to container. Recreating container and attaching volumes...")
        print("Stopping and removing container...")
        DockerManager.stop_and_remove_container(container_name)
        print("Creating container...")
        DockerManager.create_container(container_name, image_name, host_volume_mapping)


    @staticmethod
    def stop_and_remove_container(container_name):
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        print(f"Container {container_name} stopped and removed.")

    @staticmethod
    def setup_container(container_name, image_name, install_dir, data_dir, output_dir, prev_task_output=None):
        """
        Sets up the Docker container for the Luigi task.
        
        This method ensures that the Docker container specified by `self.container_name`
        and `self.image_name` is up and running. It also maps the host volumes specified
        by `self.data_dir` and `self.output_dir` to '/input' and '/output' respectively 
        in the container.

        Raises:
            RuntimeError: If the container volumes are not correctly attached.
        """
        print("Doing the Docker stuff...")
        # set the volume mapping for the container
        host_volume_mapping = {
            data_dir: {'bind': '/input', 'mode': 'rw'},
            output_dir: {'bind': '/output', 'mode': 'rw'}
        }

        # if it is not Task1, add an extra volume
        if prev_task_output:
            host_volume_mapping[prev_task_output] = {'bind': '/prev_task_output', 'mode': 'rw'}

        DockerManager.get_or_create_container(container_name, image_name, host_volume_mapping, install_dir)
        expected_volumes = [vol['bind'] for vol in host_volume_mapping.values()]
        
        if not DockerManager.check_volumes_attached(container_name, expected_volumes):
            print("Volumes are not correctly attached. Recreating container...")
            DockerManager.stop_and_remove_container(container_name)
            DockerManager.create_container(container_name, image_name, host_volume_mapping)

        else:
            print("Volumes correctly attached to container.")