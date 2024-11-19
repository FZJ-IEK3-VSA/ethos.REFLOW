#!/usr/bin/bash
#SBATCH --output="/fast/home/t-pelser/2022-t-pelser-phd/reflow-offshore-north-sea/output/logs/slurm_out/arrays/slurm-%x-%A-%a.txt"    
#SBATCH --job-name=NEWASIMULATIONS                                
#SBATCH --nodes=1                                     
#SBATCH --cpus-per-task=1
#SBATCH --partition=normal
#SBATCH --exclude=cn[1-14,23-55]
#SBATCH --array=0-7

echo "Starting the script"

source ~/.bashrc

# Define an array of country codes
countries=("GBR" "NOR" "BEL" "FRA" "DEU" "NLD" "SWE" "DNK")

mamba activate reskit-lite

# Get the country for this job array task
country=${countries[$SLURM_ARRAY_TASK_ID]}

# Execute the Python task with the country argument
python -m scripts.simulations.newa_simulations_script --country "$country"

echo "Finished!"