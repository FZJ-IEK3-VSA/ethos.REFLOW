# REFLOW

## To build the Docker image run this code:
docker build -t your-image-name --build-arg GITLAB_USERNAME=your-username --build-arg GITLAB_PASSWORD=your-password .

## To run the Docker image run this code:
docker run -it -p 8888:8888 your-image-name

## To develop inside the Docker container in VS Code, do the following:
1. Install the Remote Development extension in VS Code
2. Open the Command Palette (Ctrl+Shift+P) and select Remote-Containers: Open Folder in Container...
3. Select the folder containing the Dockerfile
4. Wait for the container to build and VS Code to connect to it
