#!/bin/bash

source /c/ProgramData/miniforge3/etc/profile.d/conda.sh

# Activate the Glaes conda environment
conda activate glaes

# Execute the Python task
python -m scripts.exclusions_placements.exclusions_script "$@"

# Deactivate the environment
conda deactivate
