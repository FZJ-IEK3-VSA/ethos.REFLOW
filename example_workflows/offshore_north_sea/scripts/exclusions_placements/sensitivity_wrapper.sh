#!/usr/bin/bash

echo "Starting the script"

source ~/.bashrc

# Activate the Glaes conda environment
mamba activate glaes

# Execute the Python task
python -m scripts.exclusions_placements.sensitivity_script "$@"

# Deactivate the environment
mamba activate reflow-main

echo "Finished!"