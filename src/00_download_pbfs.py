
from cycleosm.bikeosm import BikeOSM
output_path = r'/Users/danielpatterson/Documents/GitHub/ExtractOSM/src/output'
urls = {'District of Columbia': 'http://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf'}

#urls = {'Massachusetts': 'http://download.geofabrik.de/north-america/us/massachusetts-latest.osm.pbf'}
#urls = {'Colorado': 'http://download.geofabrik.de/north-america/us/colorado-latest.osm.pbf',
#        'Massachusetts': 'http://download.geofabrik.de/north-america/us/massachusetts-latest.osm.pbf'}

BikeOSM(urls, output_path).handle_pbfs()