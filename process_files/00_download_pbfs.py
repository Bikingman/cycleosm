
from pbf_extractor import PBFDownloader

# Source of PBFs: https://download.geofabrik.de/

output_path = r'/src/data/pbf'

urls = {
        'colorado': 'https://download.geofabrik.de/north-america/us/colorado-latest.osm.pbf',
        'florida': 'https://download.geofabrik.de/north-america/us/florida-latest.osm.pbf',
        'oklahoma': 'https://download.geofabrik.de/north-america/us/oklahoma-latest.osm.pbf',
        'texas': 'https://download.geofabrik.de/north-america/us/texas-latest.osm.pbf',
        'virgina': 'https://download.geofabrik.de/north-america/us/virginia-latest.osm.pbf',
        'washington': 'https://download.geofabrik.de/north-america/us/washington-latest.osm.pbf'
}
# download pbfs as specified in urls object 
PBFDownloader(urls, output_path).parse_pbfs()