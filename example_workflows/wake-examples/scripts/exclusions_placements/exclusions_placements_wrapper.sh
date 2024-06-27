#!/bin/bash

# Activate the Glaes conda environment
source activate glaes

# Execute the Python task
python -m scripts.exclusions_placements.exclusions_script "$@"

# Deactivate the environment
conda deactivate
