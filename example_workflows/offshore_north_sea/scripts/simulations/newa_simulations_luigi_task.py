import luigi
import os
import subprocess
from utils.config import ConfigLoader
from scripts.data_processing.combine_newa_data import CombineNEWAtimeseries
from scripts.simulations.simulations_luigi_task import PerformSimulations
import logging
import time

class PerformNEWASimulations(luigi.Task):
    """
    Script to exclude non-available areas from the analysis (including buffers defined in the exclusions_settings.json file).
    This script uses the GLAES package for performing exclusions. 
    """
    def requires(self):
        """
        This task requires both the PerformEligibiliyAnalysisPlacements and the ProcessERA5WindData tasks to be completed.
        """
        return [PerformSimulations(),
                CombineNEWAtimeseries()]

    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'completed_tasks', 'PerformNEWASimulations_complete.txt'))
    
    def _wait_for_job_completion(self, job_id):
        """Polls SLURM until the job completes."""
        while True:
            command = ["/usr/bin/squeue", "-j", job_id]
            result = subprocess.run(command, capture_output=True, text=True)

            if job_id not in result.stdout:
                print(f"SLURM job {job_id} completed.")
                break
            else:
                time.sleep(30)  # Check job status every 30 seconds


    def run(self):
        """
        Main logic for the task.
        """
        #### directory management ####
        config_loader = ConfigLoader()

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'PerformNEWASimulations.log')
        logger = config_loader.setup_task_logging('PerformNewaSimulations', log_file)

        result = subprocess.run(['/usr/bin/sbatch', './scripts/simulations/newa_simulations_wrapper.sh'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Parse the job ID from the SLURM response
        if result.returncode == 0:
            job_id = result.stdout.strip().split()[-1]
            logger.info(f"SLURM job submitted with ID {job_id}")
        else:
            raise RuntimeError(f"Failed to submit SLURM job: {result.stderr}")

        # Poll SLURM job status until it completes
        self._wait_for_job_completion(job_id)

        ############ DO NOT CHANGE ############
        # mark the task as complete
        #logger.info("ProcessRegionBuffers task complete.")
        with self.output().open('w') as file:
            file.write('Complete')