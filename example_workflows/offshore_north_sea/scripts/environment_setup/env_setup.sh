#!/bin/bash

# make sure to find the correct conda installation
source /c/ProgramData/miniforge3/etc/profile.d/conda.sh
source /c/ProgramData/miniforge3/etc/profile.d/mamba.sh
conda activate

# Base directory for requirements files
cd required_software || exit

# Paths to requirements files
declare -A REQUIREMENTS=(
    ["reskit"]="requirements-reskit.yml"
    ["glaes"]="requirements-glaes.yml"
)

# Set the package manager to use
manager="mamba"

# Function to check and use Mamba, Micromamba, or fall back to Conda
ensure_mamba() {
    if command -v mamba >/dev/null 2>&1; then
        echo "Mamba is available. Continuing with Mamba."
        manager="mamba"
    elif command -v micromamba >/dev/null 2>&1; then
        echo "Micromamba is available. Continuing with Micromamba."
        manager="micromamba"
    else
        echo "Neither Mamba nor Micromamba is available. Will use Conda."
        manager="conda"
    fi
}

# Ensure appropriate package manager is available
ensure_mamba

# Function to check if the environment already exists
env_exists() {
    # Check if the environment already exists
    env_name=$1
    if $manager env list | grep -q "$env_name"; then
        echo "1"
    else
        echo "0"
    fi
}

# Loop through the REQUIREMENTS associative array
for env_key in "${!REQUIREMENTS[@]}"; do
    file="${REQUIREMENTS[$env_key]}"

    # Use the key directly as the environment name
    env_name=$env_key
    echo "Checking environment: $env_name"
    if [[ $(env_exists $env_name) -eq 1 ]]; then
        echo "Environment $env_name already exists. Skipping creation."
        continue
    fi

    echo "Creating environment: $env_name from $file"
    $manager env create -f $file -n $env_name

    if [ $? -eq 0 ]; then
        echo "Successfully created/updated the $env_name environment."
    else
        echo "Failed to create/update the $env_name environment."
        exit 1
    fi
done

echo "Environments created."
