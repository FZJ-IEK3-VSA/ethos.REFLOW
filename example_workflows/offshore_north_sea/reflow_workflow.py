import luigi
from utils.config import ConfigLoader
import logging
import os

# Import the tasks
from scripts.environment_setup.env_setup_luigi_task import SetupEnvironments
from scripts.visualizations.box_plot import VisualizeBoxPlot
from scripts.visualizations.monthly_cf_distr import VisualizeMonthlyDistribution

class MainWorkflow(luigi.WrapperTask):
    """
    Main workflow to run the full pipeline.
    """
    def requires(self):
        return [VisualizeMonthlyDistribution()]  
    
if __name__ == '__main__':
    config_loader = ConfigLoader()
    log_directory = os.path.join(ConfigLoader().get_path("output"), 'logs')
    os.makedirs(log_directory, exist_ok=True) # ensure the directory exists
    log_file = os.path.join(log_directory, 'MainWorkflow.log')

    config_loader.setup_global_logging(log_file)
    logging.info("Starting MainWorkflow")

    luigi.run(main_task_cls=MainWorkflow, local_scheduler=True)
    logging.info("Main workflow has been run.")