# REFLOW: Renewable Energy potentials workFLOW manager

REFLOW is a workflow manager tool designed to streamline and automate tasks related to renewable energy potential analyses. It is built with Luigi and aims to provide an automated, robust framework for data ingestion, processing, analysis, validation and storage. It is build with transparency and reproducibility in mind. 

## Requirements
* Docker Desktop
* An IDE (VS Code recommended)
* Remote Development extension for VS Code (recommended)

## Getting Started

### Initial Setup
1. Make sure that Docker Desktop is installed on your computer
2. Clone this repo to a directory of your choice using 
```git clone https://gitlab.com/your-repo-link.git```

### For End Users: 
1. Build the Docker Image
To build the Docker image, navigate to the project root and run the following code:
```docker build -t <<your-image-name>> .```

Replace "<<your-image-name>>" with your desired image name. 

2. Run the Docker Image
To run the Docker image, execute:
```docker run -it -p 8501:8501 <<your-image-name>>```


### For Development in VS Code
1. Make sure that Docker Desktop is installed on your computer
2. Install the Dev Containers extension in VS Code. 
3. Clone the repo and open it in VS Code. 
4. Press CTRL+Shift+P and type "Reopen folder in Container". Select this.

VS Code will then build your container based on the '.devcontainer/devcontainer.json' configuration and you'll be able to develop from within the container. 