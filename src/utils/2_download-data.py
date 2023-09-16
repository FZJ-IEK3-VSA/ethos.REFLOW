import luigi
import os

## PART 2 OF THE WORKFLOW ##
## Previous: region_type.py
## Next: data_processing.py

# set the output folder
data_path = r"C:\Users\t.pelser\repos\reflow-test-analyses\reflow_south_africa"
raw_data = os.path.join(data_path, "raw_data")

class DownloadData(luigi.Task):
    def requires(self):
        '''
        No dependecies for this task so we can return [] or None
        '''
        return []
    
    def output(self):
        """
        Returns the target output for this task. 
        """
        return [luigi.LocalTarget(os.path.join(raw_data, "ERA5_data.nc")),
                luigi.LocalTarget(os.path.join(raw_data, "OSM_data.nc")),
                luigi.LocalTarget(os.path.join(raw_data, "global_shapefile.nc"))]
    
    def run(self):
        """
        The code to actually run the task.
        """