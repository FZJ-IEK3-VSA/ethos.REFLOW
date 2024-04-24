#!/bin/bash

# Activate the Glaes conda environment
source activate glaes

# Execute the Python task
python -m scripts.exclusions_placements.sensitivity_script "$@"

# Deactivate the environment
conda activate reflow-main
