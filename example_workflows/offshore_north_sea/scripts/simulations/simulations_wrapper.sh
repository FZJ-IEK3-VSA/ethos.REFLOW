#!/usr/bin/bash
#!/usr/bin/bash
#SBATCH --output="/fast/home/t-pelser/2022-t-pelser-phd/reflow-offshore-north-sea/output/logs/slurm_out/arrays/slurm-%x-%A-%a.txt"    
#SBATCH --job-name=NorthSeaSimulations                                
#SBATCH --nodes=1                                     
#SBATCH --cpus-per-task=1
#SBATCH --partition=normal
#SBATCH --exclude=cn[1-14,23-55]
#SBATCH --array=0-1

echo "Starting the script"

source ~/.bashrc

scenarios=("50m_depth" "1000m_depth")

scenario=${scenarios[$SLURM_ARRAY_TASK_ID]}

# Activate the Glaes conda environment
mamba activate reskit-lite

# Execute the Python task
python -m scripts.simulations.simulations_script --scenario "$scenario"

echo "Finished!"