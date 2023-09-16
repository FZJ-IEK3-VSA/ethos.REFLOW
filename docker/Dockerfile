# For more information, please refer to https://aka.ms/vscode-docker-python
FROM mambaorg/micromamba

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install the PIP requirements
COPY requirements.yml .
RUN micromamba install -y -n base -f requirements.yml && \
    micromamba clean --all --yes

WORKDIR /reflow
COPY . /reflow

# expose port 8501
EXPOSE 8501

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["/bin/bash"]
