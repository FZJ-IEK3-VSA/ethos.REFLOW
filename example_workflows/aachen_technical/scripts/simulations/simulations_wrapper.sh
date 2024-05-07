#!/bin/bash

source /c/ProgramData/miniforge3/etc/profile.d/conda.sh

# Activate the Glaes conda environment
conda activate reskit

# Execute the Python task
python -m scripts.simulations.simulations_script "$@"

# Deactivate the environment
conda deactivate
