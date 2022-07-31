# import geopandas as pd

import os 
import geopandas as gpd
from process_national_osm.python.pbf_extractor import PBFDownloader, RoadsHandler


output_path = r'C:\Users\dpatterson\OneDrive - Cambridge Systematics\Documents\code\process_national_osm\data'
url = 'http://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf'
road_fclasses = [          
                'motorway',
                'motorway_link',
                'primary',
                'primary_link',
                'secondary',
                'secondary_link',
                'trunk',
                'trunk_link',
                'tertiary',
                'tertiary_link'
            ]

# download pbfs 
PBFDownloader(url, output_path=os.path.join(output_path, 'pbf', 'washington_dc.pbf')).download_pbfs()

# extract roads and nodes 
handler = RoadsHandler(fclass=road_fclasses)
handler.apply_file(os.path.join(output_path, 'pbf', 'washington_dc.pbf'), locations=True )

ways = gpd.GeoDataFrame(handler.ways).set_index('id').set_crs(4326, allow_override=True)
nodes = gpd.GeoDataFrame(handler.nodes).set_index('id')

ways.to_file(os.path.join(output_path, 'shp', 'washington_dc_ways.shp'), driver='ESRI Shapefile')
nodes.to_file(os.path.join(output_path, 'shp', 'washington_dc_nodes.shp'), driver='ESRI Shapefile')

