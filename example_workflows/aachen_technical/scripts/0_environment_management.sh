#!/bin/bash

# list of environment names
environments=("reflow-north-sea" "glaes" "reskit")

# Check if mamba is available
if command -v mamba >/dev/null 2>&1; then
    echo "Mamba is available. Using mamba to create environments."
    manager="mamba"
else
    echo "Mamba is not available. We highly recommend using Mamba. Now proceeding with conda install."
    manager="conda"
fi


echo "Creating main environment using $manager."
$manager env create -f "requirements.yml"

cd required_software
cd environment_files

# create the reskit environment
echo "Creating reskit environment using $manager."
$manager env create -f "requirements-reskit.yml"

# create the glaes environment
echo "Creating glaes environment using $manager."
$manager env create -f "requirements-glaes.yml"