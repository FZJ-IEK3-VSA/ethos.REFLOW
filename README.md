# REFLOW: Renewable Energy potentials workFLOW manager

<a href="https://www.fz-juelich.de/en/iek/iek-3"><img src="https://github.com/FZJ-IEK3-VSA/README_assets/blob/main/FJZ_IEK-3_logo.svg?raw=True" alt="Forschungszentrum Juelich Logo" width="300px"></a>

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

5. **Create a New Git Repository**: Navigate into your new project directory and initilize it as a git repository:
    ```bash
    cd path/to/your-project-name
    git init
    git add .
    git commit -m "Initial commit"
    ```
6. **Create an Empty Repository on Github** (or any other Git hosting service): Ensure the repository name matches your project's name. 
    Do not initialize the repository with a README, .gitignore or license.

7. **Link your local repository to the remote repository**: Make sure you are in your new project directory and run the following commands:
    ```bash
    git remote add origin https://github.com/your-username/your-repo-name.git
    git branch -M main
    git push -u origin main
    ```

You can now start working on your project and push your changes to the remote repository.

## Examples

The example workflows are located in the `example_workflows` directory. Each example contains a README.md file with detailed instructions on how to run the workflow.

We recommend starting with the Aachen technical wind potential example to get a feel for how REFLOW works.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.

Copyright (c) 2024 Tristan Pelser (FZJ IEK-3), Jann Michael Weinand (FZJ IEK-3), Patrick Kuckertz (FZJ IEK-3), Detlef Stolten (FZJ IEK-3)

You should have received a copy of the MIT License along with this program.
If not, see https://opensource.org/licenses/MIT

## About Us

<a href="https://www.fz-juelich.de/en/iek/iek-3"><img src="https://github.com/FZJ-IEK3-VSA/README_assets/blob/main/iek3-square.png?raw=True" alt="Institute image IEK-3" width="280" align="right" style="margin:0px 10px"/></a>

We are the [Complex Energy System Modesl and Data Structures](https://www.fz-juelich.de/en/iek/iek-3/research/integrated-models-and-strategies/complex-energy-system-models-and-data-structures) department at the [Institute of Energy and Climate Research: Techno-economic Systems Analysis (IEK-3)](https://www.fz-juelich.de/en/iek/iek-3), belonging to the Forschungszentrum Jülich. Our interdisciplinary department's research is focusing on energy-related process and systems analyses. Data searches and system simulations are used to determine energy and mass balances, as well as to evaluate performance, emissions and costs of energy systems. The results are used for performing comparative assessment studies between the various systems. Our current priorities include the development of energy strategies, in accordance with the German Federal Government’s greenhouse gas reduction targets, by designing new infrastructures for sustainable and secure energy supply chains and by conducting cost analysis studies for integrating new technologies into future energy market frameworks.

## Acknowledgements

The authors would like to thank the German Federal Government, the German State Governments, and the Joint Science Conference (GWK) for their funding and support as part of the NFDI4Ing consortium. Funded by the German Research Foundation (DFG) – 442146713, this work was also supported by the Helmholtz Association as part of the program “Energy System Design”.

<p float="left">
<a href="https://www.helmholtz.de/en/"><img src="https://www.helmholtz.de/fileadmin/user_upload/05_aktuelles/Marke_Design/logos/HG_LOGO_S_ENG_RGB.jpg" alt="Helmholtz Logo" width="200px"></a>
</p>