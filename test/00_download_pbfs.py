
from pbf_downloader import PBFDownloader
import pandas as pd
# Source of PBFs: https://download.geofabrik.de/
output_path = r'/src/data/pbf'
filepath = r'/src/data/pbf'
def read_csv(filename):
    return pd.read_csv(filename).to_dict('records')

urls = read_csv(filepath)

# download pbfs as specified in urls object 
PBFDownloader(urls, output_path).parse_pbfs()