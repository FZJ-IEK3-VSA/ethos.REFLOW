#!/bin/bash
failure_msg="Please pass desired environment name (no whitespaces, no dashes) after <PATH_TO_CLONE_OF_THIS_PACKAGE>/build_env.sh. e.g.: bash /PATH/build_env.sh <YOUR_ENV_NAME>"
#check if environment name argument is present
if [ -z "$1" ]; then 
    echo $failure_msg
    exit 1 
fi 
# assign user input to variable envname
envname=$1

conda create -n $envname
source activate $envname
# make sure that the environment is activated
if [ $CONDA_DEFAULT_ENV != $envname ]; then
    echo "Your newly created environment was not activated. Exiting here to avoid installing packages into the base environment."
    exit 1
fi

### LETS CHECK FOR MAMBA. If mamba is installed, we use that, otherwise revert to conda
package_name="mamba"
if conda list -n base | grep -q "$package_name"; then
    echo "$package_name is installed: proceeding with $package_name installation"
    conda install -c conda-forge gdal=3.4.2
    mamba env update -n $envname -f requirements-dev.yml --prune
else 
    echo "$package_name is not installed: proceeding with conda install"
    conda env update -n $envname -f requirements-dev.yml
fi
cd ..
cd iek3-models
cd geokit 
pip install -e .
cd ..
cd RESKit
pip install -e .
cd ..
cd glaes
pip install -e .
cd ..
cd ..
cd reflow
pytest -v test.py
echo All packages installed and tested successfully.