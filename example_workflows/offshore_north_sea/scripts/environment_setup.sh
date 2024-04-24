#!/bin/bash

# Base directory for requirements files
cd required_software || exit

# Paths to requirements files
declare -A REQUIREMENTS=(
    ["reflow-main"]="requirements-reflow.yml"
    ["reskit"]="requirements-reskit.yml"
    ["glaes"]="requirements-glaes.yml"
)

# Set the package manager to use
manager="micromamba"

# Function to check and install Mamba if not present
ensure_mamba() {
    if command -v $manager >/dev/null 2>&1; then
        echo "Mamba is available. Continuing with Mamba."
    else
        echo "Mamba is not available. Attempting to install Mamba."
        # Attempt to install Mamba using the provided command
        if ! "${SHELL}" <(curl -L micro.mamba.pm/install.sh); then
            echo "Failed to install Mamba. Please install Mamba manually and retry."
            exit 1
        fi

        # Verify Mamba installation
        if command -v $manager >/dev/null 2>&1; then
            echo "Mamba installation successful."
        else
            echo "Mamba installation failed. Exiting."
            exit 1
        fi
    fi
}

# Ensure Mamba is available or attempt to install it
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

echo "To activate the main environment, use: micromamba activate $ENV_NAME"
