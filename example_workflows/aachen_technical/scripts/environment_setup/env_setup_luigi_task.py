import os 
import subprocess
import luigi
from utils.config import ConfigLoader

class SetupEnvironments(luigi.Task):
    """
    Script to exclude non-available areas from the analysis (including buffers defined in the exclusions_settings.json file).
    This script uses the GLAES package for performing exclusions. 
    """
    def requires(self):
        """
        This task has no dependencies.
        """
        return None
    
    def output(self):
        """
        Output that signifies that the task has been completed. 
        """
        return luigi.LocalTarget(os.path.join(ConfigLoader().get_path("output"), 'logs', 'EnvSetup_complete.txt'))
    
    def run(self):
        """
        Main logic for the task.
        """
        #### directory management ####
        config_loader = ConfigLoader()

        # configure logging
        log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'EnvSetup.log')
        logger = config_loader.setup_task_logging('EnvSetup', log_file)

        ## run the exclusions wrapper bash script
        result = subprocess.run(
        ['bash', './scripts/environment_setup/env_setup.sh'],
        check=True,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )
        
        logger.info("STDOUT: {}".format(result.stdout.decode()))
        logger.info("STDERR: {}".format(result.stderr.decode()))

        ############ DO NOT CHANGE ############
        # mark the task as complete
        with self.output().open('w') as file:
            file.write('Complete')