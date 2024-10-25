#!/bin/bash

source ~./bashrc

# Activate the Glaes conda environment
conda activate glaes

# Execute the Python task
python -m scripts.exclusions_placements.exclusions_script "$@"