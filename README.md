## CycleOSM

[![PyPI version](https://img.shields.io/pypi/v/cycleosm.svg)](https://pypi.org/project/cycleosm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The purpose of CycleOSM is to download structured bike infrastructure data from Open Street Map (OSM).

Now on [PyPi](https://pypi.org/project/cycleosm/)

This package is easy to use. You can get started by installing the package: 
```
pip install cycleosm
```

Then import the BikeOSM module.  
```
from cycleosm.bikeosm import BikeOSM
```

Next define the output directory and the .pbf url
```
output_path = r'/Users/danielpatterson/Documents/GitHub/ExtractOSM/src/output'
urls = {'District of Columbia': 'http://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf'}
```

Finally, extract the pbf
```
BikeOSM(urls, output_path).handle_pbfs()
```

![Denver Bike Facs](https://user-images.githubusercontent.com/22425199/218263077-a6554521-5697-40fa-824e-1051c4b46009.png)

![image](https://user-images.githubusercontent.com/22425199/218263087-fe33097f-ae0b-4449-9c7d-3e9585d0d560.png)
