
from pbf_extractor import PBFDownloader

# Source of PBFs: https://download.geofabrik.de/

output_path = r'/src/data/pbf'

urls = {
        'so_cal': 'http://download.geofabrik.de/north-america/us/california/socal-latest.osm.pbf'
}
# download pbfs as specified in urls object 
PBFDownloader(urls, output_path).parse_pbfs()