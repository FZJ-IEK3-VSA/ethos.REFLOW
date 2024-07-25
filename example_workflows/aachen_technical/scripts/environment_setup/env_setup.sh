#!/bin/bash

# Ensure the script exits on any error
set -e

# Function to log messages
log() {
    echo "[`date +'%Y-%m-%dT%H:%M:%S%z'`] $1"
}

# Make sure to find the correct conda installation
log "Sourcing Conda and Mamba initialization scripts"
if ! source /c/ProgramData/miniforge3/etc/profile.d/conda.sh; then
    log "Failed to source conda.sh"
    exit 1
fi

if ! source /c/ProgramData/miniforge3/etc/profile.d/mamba.sh; then
    log "Failed to source mamba.sh"
    exit 1
fi

# Activate the base environment or a specific environment
conda activate base

# Base directory for requirements files
cd required_software || exit
ls

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
        log "Mamba is available. Continuing with Mamba."
        manager="mamba"
    elif command -v micromamba >/dev/null 2>&1; then
        log "Micromamba is available. Continuing with Micromamba."
        manager="micromamba"
    else
        log "Neither Mamba nor Micromamba is available. Will use Conda."
        manager="conda"
    fi
}

# Ensure appropriate package manager is available
ensure_mamba

# Function to check if the environment already exists
env_exists() {
    local env_name=$1
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
    log "Checking environment: $env_name"
    if [[ $(env_exists "$env_name") -eq 1 ]]; then
        log "Environment $env_name already exists. Skipping creation."
        continue
    fi

    log "Creating environment: $env_name from $file"
    if $manager env create -f "$file" -n "$env_name"; then
        log "Successfully created/updated the $env_name environment."
    else
        log "Failed to create/update the $env_name environment."
        exit 1
    fi
done

log "Environments created."
