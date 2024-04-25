import luigi
from utils.config import ConfigLoader
import logging
import os

# Import the tasks
from scripts.data_download.project_data import DownloadProjectData
from scripts.data_processing.process_project_data import ProcessProjectData


class MainWorkflow(luigi.WrapperTask):
    """
    Main workflow to run the full pipeline.
    """
    def requires(self):
        # First task is the download of the exclusion data
        return [ProcessProjectData()]

if __name__ == '__main__':
    # Set up basic logging
    config_loader = ConfigLoader()
    
    log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'MainWorkflow.log')
    config_loader.setup_global_logging(log_file)
    logging.info("Starting MainWorkflow")

    luigi.run(main_task_cls=MainWorkflow, local_scheduler=True)
    logging.info("Main workflow has been run.")