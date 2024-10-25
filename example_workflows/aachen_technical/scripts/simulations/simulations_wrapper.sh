#!/bin/bash

source ~./bashrc

# Activate the Glaes conda environment
conda activate reskit

# Execute the Python task
python -m scripts.simulations.simulations_script "$@"
