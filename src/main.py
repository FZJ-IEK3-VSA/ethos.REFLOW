# define the region          
    # user input    
    # generate shapefile
    # generate geopandas dataframe

# define the type of potential
    # user input 
    # IF:
        # theoretical
        # geographical
        # technical
        # techno-economic
        # feasible
    # DECIDE on type of workflow
    # output a json file with datasets needed 

# check if running on FZJ IEK-3 server or not:
    # IF:
        # yes -> skip the data processing step
        # no -> go through full workflow 

import luigi
import os
import json
import shapefilegenerator

# enter region name here
# can be: full name of a country, any GID level, (NUTS3 levels still coming), or large region area (e.g. "West Africa") - available in RegionsDict.json 
region = "YOUR_REGION_HERE"

# enter potential type here
# can be: theoretical, geographical, technical, techno-economic, feasible
potential_type = "YOUR_POTENTIAL_TYPE_HERE"

# set the output folder
data_path = r"C:\Users\t.pelser\repos\reflow-test-analyses\reflow_south_africa"

