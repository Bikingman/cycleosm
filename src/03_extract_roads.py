
import os 
import geopandas as gpd
import pandas as pd

output_path = r'/src/data'
values = ['Bike Lane', 'Buffered Bike Lane', 'Protected Bike Lane', 'Shared Use Path', 'Cycleway']
file_BK = gpd.GeoDataFrame()

files = 'states'

for i in files:
    file = gpd.read_file(os.path.join(output_path, 'shp', 'osm', i + '_ways.shp'))
    bike_infra = file[file['min_bk_inf'].isin(values)]
    file_BK = pd.concat([file_BK, bike_infra])

file_BK.to_file('zzfile_BK.shp')
