# import geopandas as pd

import os 
import geopandas as gpd
import pandas as pd
from process_national_osm.python.roads import Roads
from process_national_osm.python.h3_process import HandleH3
import csv
output_path = r'C:\Users\dpatterson\OneDrive - Cambridge Systematics\Documents\code\process_national_osm\data'
shp = os.path.join(output_path, 'shp', 'washington_dc_ways.shp')
roads = gpd.read_file(shp)
r = Roads() 
h = HandleH3()

roads = r.infer_lanes_from_fclass(roads, 
                                    new_lns_col='lanes1', 
                                    cur_lns_col='lanes', 
                                    one_way_col='oneway', 
                                    fclass_col='fclass'
                                    )
roads = r.infer_width_from_lanes(roads, 
                                    lanes_col='lanes1', 
                                    fclass_col='fclass',
                                    new_width_col='wid_mtrs')

roads = r.buffer_roads(roads, width_col='wid_mtrs', convert_to_utm=True, capped_lines=True).to_crs(4326)

roads.to_file(os.path.join(output_path, 'shp', 'washington_dc_ways1.shp'), driver='ESRI Shapefile')

h3 = h.polygon_get_inner_h3_id(roads, 13)

keys = h3[0][0].keys()
with open(os.path.join(output_path, 'csv', 'osmids_h3.csv'), 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    for i in h3:
        dict_writer.writerows(i)

# QC here: https://observablehq.com/@nrabinowitz/h3-index-inspector?collection=@nrabinowitz/h3