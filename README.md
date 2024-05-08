# REFLOW: Renewable Energy potentials workFLOW manager

REFLOW is a workflow manager tool designed to streamline and automate tasks related to renewable energy potential analyses. It is built with Luigi and provides an automated, robust framework for data acquisition, processing, land/sea eligibility analysis, technology placements, simulations and visualizations. It is build with transparency and reproducibility in mind. 

## Requirements
* Python
* An IDE (e.g. PyCharm, Visual Studio Code, etc.)
* Unix-like system or bash on Windows
* *optional*: Docker Desktop if running in container

## Getting Started

### Try an example project - Aachen technical wind potential

We highly recommend starting with the example workflow to get a feel for how REFLOW works. The example project is a simple technical wind energy potential analysis for a small region in Germany. 

To run this analysis, follow these steps:
1. Clone this repository to your local machine using:
    ```bash
    git clone https://jugit.fz-juelich.de/iek-3/groups/data-and-model-integration/pelser/reflow.git
    ```

2. Navigate to the example project directory:
    ```bash
    cd reflow/example_workflows/aachen_technical
    ```
3. Follow the instructions in the README.md file in the example project directory.


### Initial Setup for a new project

To start your own new project using REFLOW, follow these steps:

1. Clone this repository to your local machine using:
    ```bash
    git clone https://jugit.fz-juelich.de/iek-3/groups/data-and-model-integration/pelser/reflow.git
    ```

2. **Initialize a new Project:** Navigate to the **main REFLOW repo (this repo)** and run the initialize_project.py script by executing:
    ```bash
    python initialize_project.py
    ```
    You will be prompted to enter the name of your new project and the parent directory where it should be created.

3. Create the main REFLOW python environment by running:
    ```bash
    conda env create -f required_software/requirements-reflow.yml
    ```
    Activate the environment by running:
    ```bash
    conda activate reflow
    ```

4. We recommend using a seperate conda environment for each software package which needs to be run outside of the main REFLOW environment. For example, if you are using WAsP, you can create a new environment which contains the PyWAsP package by:

    4.1. Creating an environment file for the WAsP python package under the `required_software` directory. 
    You can use the provided `requirements-glaes.yml` file from the Aachen technical example as a template.

    4.2. If the new environment file is in the required_software directory, the environment will automatically be created during the first task of the REFLOW workflow. 

    4.3. You can then run whichever task's script is needed inside the environment within your main REFLOW workflow. Do this by using a wrapper script which activates the environment, runs the task, and then deactivates the environment. (Again, see the Aachen technical example for reference.)

**Optional but recommended - work with GIT:**

4. **Create a New Git Repository**: Navigate into your new project directory and initilize it as a git repository:
    ```bash
    cd path/to/your-project-name
    git init
    git add .
    git commit -m "Initial commit"
    ```
5. **Create an Empty Repository on Github** (or any other Git hosting service): Ensure the repository name matches your project's name. 
    Do not initialize the repository with a README, .gitignore or license.

6. **Link your local repository to the remote repository**: Make sure you are in your new project directory and run the following commands:
    ```bash
    git remote add origin https://github.com/your-username/your-repo-name.git
    git branch -M main
    git push -u origin main
    ```

You can now start working on your project and push your changes to the remote repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.

## Acknowledgements

The authors would like to thank the German Federal Government, the German State Governments, and the Joint Science Conference (GWK) for their funding and support as part of the NFDI4Ing consortium. Funded by the German Research Foundation (DFG) – 442146713, this work was also supported by the Helmholtz Association as part of the program “Energy System Design”.
