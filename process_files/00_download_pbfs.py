
from process_national_osm.python.pbf_extractor import PBFDownloader

# Source of PBFs: https://download.geofabrik.de/

# output_path = r'C:\Users\dpatterson\OneDrive - Cambridge Systematics\Documents\code\process_national_osm\data\pbf'
output_path = r'C:\Users\dpatterson\OneDrive - Cambridge Systematics\Documents\code\process_national_osm\data\pbf'
# urls =   {
#         'us_midwest': 'https://download.geofabrik.de/north-america/us-midwest-latest.osm.pbf',
#         'us_northeast': 'https://download.geofabrik.de/north-america/us-northeast-latest.osm.pbf',
#         'us_pacific': 'https://download.geofabrik.de/north-america/us-pacific-latest.osm.pbf',
#         'us_source': 'https://download.geofabrik.de/north-america/us-south-latest.osm.pbf',
#         'us_west': 'https://download.geofabrik.de/north-america/us-west-latest.osm.pbf',
#         }
# urls = {
#         'washington_dc': 'https://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf'
# }

urls = {
        'so_cal': 'https://download.geofabrik.de/north-america/us/california/socal-latest.osm.pbf'
}


# download pbfs as specified in urls object 
PBFDownloader(urls, output_path).parse_pbfs()