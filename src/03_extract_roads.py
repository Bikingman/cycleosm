
import os 
import geopandas as gpd
import pandas as pd
output_path = r'/Users/danielpatterson/Documents/output'
values = ['Bike Lane', 'Buffered Bike Lane', 'Protected Bike Lane', 'Shared Use Path', 'Cycleway']
file_BK = gpd.GeoDataFrame()

files = [
    os.path.abspath(os.path.join(output_path, x))
    for x in os.listdir(output_path)
    if os.path.isfile(os.path.join(output_path, x))
]

for i in files:
    if "_ways" not in i:
        continue
    if ".shp" not in i:
        continue
    print('Working on: ' + i)
    file = gpd.read_file(i)
    bike_infra = file[file['min_bk_inf'].notna()]
    bike_infra['state'] = os.path.splitext(os.path.basename(i.replace(' ', '_').replace('_ways', '')))[0]
    file_BK = pd.concat([file_BK, bike_infra])


file_BK.to_file('bike_infrastrucure_data_usa.shp')
