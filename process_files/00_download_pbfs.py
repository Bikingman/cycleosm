
from process_national_osm.python.pbf_extractor import PBFDownloader

# Source of PBFs: https://download.geofabrik.de/

output_path = r'C:\Users\dpatterson\OneDrive - Cambridge Systematics\Documents\code\process_national_osm\data'
urls =   {
        'washington_dc': 'http://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf',
        'Georgia': 'https://download.geofabrik.de/north-america/us/georgia-latest.osm.pbf',
        'North East': 'https://download.geofabrik.de/north-america/us-northeast-latest.osm.pbf'
        }

# download pbfs as specified in urls object 
PBFDownloader(urls, output_path).parse_pbfs()