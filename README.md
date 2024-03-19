# REFLOW: Renewable Energy potentials workFLOW manager

REFLOW is a workflow manager tool designed to streamline and automate tasks related to renewable energy potential analyses. It is built with Luigi and aims to provide an automated, robust framework for data acquisition, processing, eligibility analysis, technology placements, simulations and visualizations. It is build with transparency and reproducibility in mind. 

## Requirements
* Python
* An IDE (e.g. PyCharm, Visual Studio Code, etc.)
* *optional*: Docker Desktop if running in container

## Getting Started

### Initial Setup
1. Clone this repository to your local machine using:
    ```bash
    git clone https://jugit.fz-juelich.de/iek-3/groups/data-and-model-integration/pelser/reflow.git
    ```

### Setting up a new project
1. **Initialize Your Project into the empty repository:** Navigate to the **main REFLOW repo (this repo)** and run the initialize_project.py script by executing:
    ```bash
    python initialize_project.py
    ```
    You will be prompted to enter the name of your new project and the parent directory where it should be created.
2. **Create a New Git Repository**: Navigate into your new project directory and initilize it as a git repository:
    ```bash
    cd path/to/your-project-name
    git init
    git add .
    git commit -m "Initial commit"
    ```
3. **Create an Empty Repository on Github** (or any other Git hosting service): Ensure the repository name matches your project's name. 
    Do not initialize the repository with a README, .gitignore or license.

4. **Link your local repository to the remote repository**: Make sure you are in your new project directory and run the following commands:
    ```bash
    git remote add origin https://github.com/your-username/your-repo-name.git
    git branch -M main
    git push -u origin main
    ```

You can now start working on your project and push your changes to the remote repository.