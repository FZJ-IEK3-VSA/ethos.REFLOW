# For more information, please refer to https://aka.ms/vscode-docker-python
FROM mambaorg/micromamba

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install the requirements
COPY /docker/requirements.txt .
RUN pip install -r requirements.txt

# install libmamba to speed up conda environment creation
RUN conda update -n base conda && \ 
    conda install -n base conda-libmamba-solver && \
    conda config --set solver libmamba

WORKDIR /reflow
COPY . /reflow

# expose port 8501
EXPOSE 8501

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["/bin/bash"]
