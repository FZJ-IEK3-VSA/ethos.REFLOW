# Use the official Python image with Conda pre-installed as the base image
FROM continuumio/miniconda3:latest

# set the working directory in the container
WORKDIR /reflow

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Copy the requirements.yml file first, for separate dependency resolving and downloading
COPY requirements.yml .
COPY /reflow/environment.yml /reflow/environment.yml

# install libmamba to speed up conda environment creation
RUN conda update -n base conda && \ 
    conda install -n base conda-libmamba-solver && \
    conda config --set solver libmamba

# Create the Conda environment 
RUN conda create -n reflow

# install gdal version 3.4.2
RUN conda install -n reflow -c conda-forge gdal=3.4.2

# install mamba
RUN conda install -n base -c conda-forge mamba

# now complete the environment with the rest of the requirements file.
RUN mamba env update -n reflow --file requirements.yml --prune

# activate the environment
RUN echo "source activate reflow" > ~/.bashrc

# Copy the subdirectories into the container
COPY reflow/examples/ examples/
COPY reflow/testing/ testing/
COPY reflow/utils/ utils/

# Copy the private ssh key into the container
COPY ssh_key/id_ed25519 /root/.ssh/id_ed25519

# set up the ssh agent and add the private key
RUN chmod 600 /root/.ssh/id_ed25519 && \
    ssh-keyscan jugit.fz-juelich.de >> /root/.ssh/known_hosts && \
    eval "$(ssh-agent -s)" && ssh-add /root/.ssh/id_ed25519

# Clone the required repositories into the models folder using the ssh key
RUN mkdir -p /reflow/models && \
    git clone git@jugit.fz-juelich.de:iek-3/shared-code/geokit.git /reflow/models/geokit && \
    git clone git@jugit.fz-juelich.de:iek-3/shared-code/glaes.git /reflow/models/glaes && \
    git clone git@jugit.fz-juelich.de:iek-3/shared-code/RESKit.git /reflow/models/reskit

# install the repositories using pip install -e . to allow for changes to be made
RUN /bin/bash -c "conda run -n reflow pip install --no-deps -e /reflow/models/geokit"
RUN /bin/bash -c "conda run -n reflow pip install --no-deps -e /reflow/models/glaes"
RUN /bin/bash -c "conda run -n reflow pip install --no-deps -e /reflow/models/reskit"

# copy the main.py file into the container
COPY reflow/utils/main.py .

# Copy the test file into the container
COPY test.py .

# Run pytest to test the installation
RUN /bin/bash -c "conda run -n reflow pytest -v test.py"

# Create a non-root user with an explicit UID (e.g., 5678), disable password authentication, and set an empty GECOS field
RUN useradd --uid 5678 --password "" -c "" appuser

# Change the ownership of the /app folder to the new user
RUN chown -R appuser:appuser /reflow

# Switch to the new user
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["/bin/bash"]
