# import geopandas as pd

import os 
import geopandas as gpd
import pandas as pd
from process_national_osm.python.roads import Roads
from process_national_osm.python.h3_process import HandleH3
import time

import csv
output_path = r'C:\Users\dpatterson\OneDrive - Cambridge Systematics\Documents\code\process_national_osm\data'
files =   ['us_midwest', 'us_northeast', 'us_pacific', 'us_source', 'us_west']
# files =   ['washington_dc']

r = Roads() 
h = HandleH3()

def process(filename, output_path):
    start_time = time. time()
    shp = os.path.join(output_path, 'shp', 'osm', filename + '_ways.shp')
    roads = gpd.read_file(shp)


    # add number of lanes based on fclass on each road segment 
    roads = r.infer_lanes_from_fclass(roads, 
                                        new_lns_col='lanes1', 
                                        cur_lns_col='lanes', 
                                        one_way_col='oneway', 
                                        fclass_col='fclass'
                                        )

    # infer the road width based on the number of lanes 
    roads = r.infer_width_from_lanes(roads, 
                                        lanes_col='lanes1', 
                                        fclass_col='fclass',
                                        new_width_col='wid_mtrs')

    # buffer linestring based on the road width 
    roads = r.buffer_roads(roads, width_col='wid_mtrs', convert_to_utm=True, capped_lines=True).to_crs(4326)

    # save output from previous execution 
    roads.to_file(os.path.join(output_path, 'shp', 'osm', filename + '_buffered_ways.shp'), driver='ESRI Shapefile')

    # get the H3 indexes
    h3_indexes = h.get_h3_index(roads, [13], [4])

    h3_indexes.to_parquet(os.path.join(output_path, 'parquet', 'h3_test.gzip'),  index = False)  
    h3_indexes.to_csv(os.path.join(output_path, 'csv', 'h3_test.csv'),  index = False)  

    # save h3 polygon 
    h3_ploys_13 = h.get_hex_df(h3_indexes['h3_index_lv13'])
    h3_ploys_4 = h.get_hex_df(h3_indexes['summary_hex_lv4'])

    h3_ploys_13.to_file(os.path.join(output_path, 'shp', 'hexes', filename + '_h3_ploys_13.shp'), driver='ESRI Shapefile')
    h3_ploys_4.to_file(os.path.join(output_path, 'shp', 'hexes', filename + '_h3_ploys_4.shp'), driver='ESRI Shapefile')


    print("Time to process file {0}: {1} minutes.".format(filename + '_ways.shp', ((time.time() - start_time)/60)))

for i in files: 
    process(i, output_path)

# TODO
# save as a parquet  DONE 
# save the h4 index - DONE but non exist, see HandleH3.get_h3_index need to discuss, created bbox files 
# save h3 indexes as integer, need more infomration - index values include characters. string_to_h3()
# deploy dask 
# take the centorid of the geometry and geocode it as h4, we'l have a few misses 
# take the lat long of the h13 and extract the h4

# output shapefile with linestrings, and the buffers 
# leave one way as is (for now)
# for every state osm id, h13, h4
# save as integer 
# QC here: https://observablehq.com/@nrabinowitz/h3-index-inspector?collection=@nrabinowitz/h3