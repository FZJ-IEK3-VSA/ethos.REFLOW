import os
import shutil
from pathlib import Path

def copy_project(src, dest, project_name, exclusions):
    """
    Copies the project from src to dest, applying exclusions.

    :param src: Source directory
    :param dest: Destination directory
    :param project_name: Name of the new project
    :param exclusions: Files and directories to exclude
    """
    dest = os.path.join(dest, project_name)
    if os.path.exists(dest):
        print(f"The project {project_name} already exists at the destination.")
        return False

    os.makedirs(dest, exist_ok=True)
    for root, dirs, files in os.walk(src, topdown=True):
        dirs[:] = [d for d in dirs if os.path.join(root, d).replace(src, '') not in exclusions]
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = file_path.replace(src, '').lstrip(os.path.sep)
            if any(excluded in file_path for excluded in exclusions):
                continue
            dest_path = os.path.join(dest, relative_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(file_path, dest_path)

    print(f"Project {project_name} has been initialized at {dest}.")
    return True

def main():
    # Prompt user for project name and destination directory
    project_name = input("Enter the name of the new project: ")
    parent_directory = input("Enter the path to the parent directory where the project should be created: ")

    # Current directory (assuming initialize_project.py is in the root of your template repo)
    current_directory = Path(__file__).parent

    # Exclusions
    exclusions = [
        os.path.join(current_directory, 'example_workflows'),
        os.path.join(current_directory, 'contributors.txt'),
        os.path.join(current_directory, 'LICENSE.txt'),
        os.path.join(current_directory, '__pycache__'),
        os.path.join(current_directory, 'initialize_project.py'),
        os.path.join(current_directory, '.git')  
    ]

    # Copy project
    copy_project(str(current_directory), parent_directory, project_name, exclusions)

if __name__ == "__main__":
    main()
