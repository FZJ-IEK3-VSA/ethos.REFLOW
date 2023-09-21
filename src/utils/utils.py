import json

def read_config(file_path):
    with open(file_path, 'r') as f:
        config = json.load(f)
    return config