# REFLOW: Renewable Energy potentials workFLOW manager

REFLOW is a workflow manager tool designed to streamline and automate tasks related to renewable energy potential analyses. It is built with Luigi and aims to provide an automated, robust framework for data acquisition, processing, eligibility analysis, technology placements, simulations and visualizations. It is build with transparency and reproducibility in mind. 

## Requirements
* Python
* An IDE (VS Code recommended)
* Docker Desktop if running in container

## Getting Started

### Initial Setup
1. Clone the repository to your local machine using:
    ```bash
    git clone https://jugit.fz-juelich.de/iek-3/groups/data-and-model-integration/pelser/reflow.git
    ```

### Setting up your project
1. **Create an Empty Git Repository** on your GitHub account (or any other Git hosting service) where you want to host the new project. The repository should have an appropriate name for your project. 
2. **Clone your new repository** to your local machine using:
```bash
git clone https://github.com/your-username/your-repo-name.git
```
3. **Initialize Your Project into the empty repository:** Navigate to the **main REFLOW repo (this repo)** and run the initialize_project.py script by executing:
```bash
python initialize_project.py
```

You will be prompted to enter the name of your new project and the parent directory where it should be created.
**Make sure you enter the same project name as the empty repository you created in step 1.** 

The script will copy the necessary files while excluding specific files and directories such as *'example_workflows'*, *'contributors.txt'*, *'LICENSE.txt'*, and the *.git* directory.

4. Navigate back to **your own project repo** to make your first commit and then push to the remote repository:
```bash
git add .
```
```bash
git commit -m "Initial commit"
```
```bash
git push origin master
```
You can now start working on your project and push your changes to the remote repository.