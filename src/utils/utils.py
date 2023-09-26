import json
import docker


def read_config(file_path):
    with open(file_path, 'r') as f:
        config = json.load(f)
    return config


def check_docker_access():
    client = docker.from_env()
    try:
        client.ping()
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

