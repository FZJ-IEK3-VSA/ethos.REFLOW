import luigi
from utils.config import ConfigLoader
import logging
import os

# Import the tasks
from scripts.environment_setup.env_setup_luigi_task import SetupEnvironments
from scripts.data_download.project_data import DownloadProjectData
from scripts.data_processing.process_project_data import ProcessProjectData
from scripts.data_download.exclusions_data import DownloadExclusionsData
from scripts.data_processing.process_exclusions_data import ProcessExclusionsData
from scripts.exclusions_placements.exclusions_luigi_task import PerformEligibiliyAnalysisPlacements
from scripts.data_download.meteorological_data import DownloadMeterologicalData
from scripts.data_processing.process_met_data import ProcessERA5WindData
from scripts.data_processing.convert_placements import ConvertPlacementsToEPSG4326
from scripts.data_processing.convert_cci_to_tif import ConvertCCItoTIF
from scripts.simulations.simulations_luigi_task import PerformSimulations
from scripts.visualizations.exclusionsMap import VisualizeExclusionMaps

class MainWorkflow(luigi.WrapperTask):
    """
    Main workflow to run the full pipeline.
    """
    def requires(self):
        # First task is the download of the exclusion data
        return [VisualizeExclusionMaps()]

if __name__ == '__main__':
    # Set up basic logging
    config_loader = ConfigLoader()
    
    log_file = os.path.join(ConfigLoader().get_path("output"), 'logs', 'MainWorkflow.log')
    config_loader.setup_global_logging(log_file)
    logging.info("Starting MainWorkflow")

    luigi.run(main_task_cls=MainWorkflow, local_scheduler=True)
    logging.info("Main workflow has been run.")