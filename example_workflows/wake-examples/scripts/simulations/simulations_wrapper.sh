#!/bin/bash

# Activate the Glaes conda environment
source activate reskit

# Execute the Python task
python -m scripts.simulations.simulations_script "$@"

# Deactivate the environment
conda deactivate
