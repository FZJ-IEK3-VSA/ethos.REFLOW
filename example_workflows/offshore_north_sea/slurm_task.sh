#!/bin/bash                                            
                                                       
#SBATCH --output="/fast/home/t-pelser/repos/reflow-offshore-north-sea/output/logs/slurm-%x-%A-%a.txt"    
#SBATCH --job-name=RZTVS5                                
#SBATCH --nodes=1                                     
#SBATCH --cpus-per-task=1
#SBATCH --partition=normal
#SBATCH --exclude=cn[7-14],cn[15-21],cn[22-29],cn[32-39],cn[43-55]

#### JOB LOGIC ###                                     
export OMP_NUM_ATHREADS=1                              
export USE_SIMPLE_THREADED_LEVEL3=1                    
export MKL_NUM_THREADS=1                               

source ~/.bashrc

bash /path/to/this/directory/scripts/environment_setup.sh                                            

micromamba activate reflow-main

python -u reflow_workflow.py