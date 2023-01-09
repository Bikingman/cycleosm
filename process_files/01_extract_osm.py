# import geopandas as pd

import os 
import geopandas as gpd
from pbf_extractor import PBFHandler 
import time

output_path = r'/src/data'

files = ['washington_dc']
fclass  = [          
    'motorway', 'motorway_link',
    'primary', 'primary_link',
    'secondary', 'secondary_link',
    'trunk', 'trunk_link',
    'tertiary', 'tertiary_link',
    'residential', 'living_street',
    'bus_guideway', 'busway',
    'road', 'cycleway',
    'track', 'unclassified'
]

# extract roads and nodes 
def process(filename, output_path, road_fclasses):
    start_time = time. time()
    handler = PBFHandler(fclass=road_fclasses)
    handler.apply_file(os.path.join(output_path, 'pbf', filename + '.pbf'), locations=True )

    # convert the nodes and ways to geopandas dataframes 
    ways = gpd.GeoDataFrame(handler.ways).set_index('id').set_crs(4326, allow_override=True)
    # nodes = gpd.GeoDataFrame(handler.nodes).set_index('id')

    # save the geopandas dataframes as shapefiles
    ways.to_file(os.path.join(output_path, 'shp', 'osm', filename + '_ways.shp'), driver='ESRI Shapefile')
    # nodes.to_file(os.path.join(output_path, 'shp', 'osm', filename + '_nodes.shp'), driver='ESRI Shapefile')

    print("Time to process file {0}: {1} minutes.".format(filename + '.pbf', ((time.time() - start_time)/60)))

for i in files:
    process(i, output_path, road_fclasses=fclass)

