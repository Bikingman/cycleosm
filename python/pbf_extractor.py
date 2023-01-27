"""
Set of python classes to download and extract OSM PBF files. 
An OSM PBF is an open source transfer format for vector GIS data created by the OSM community. Generally smaller than OSM XML files.

This module contains two classes: 
    - PBF handler: expected use is for extracting geopandas data frame from PBF file given user inputs. 
    - PBFDownloader: python class for downloading PBF files. 

Source of PBFs: https://download.geofabrik.de/

"""


import osmium
import shapely.wkb as wkblib
import wget
import time
import os 

wkbfab = osmium.geom.WKBFactory()

class PBFHandler(osmium.SimpleHandler):
    """
    This python class is an extension of the osmium library to extract geopandas dataframes of OSM data from OSM PBF files. 
    Workflow: after instantiating the PBFHanlder class with the required inputs, point to a PBF file and use the apply_file() method to get a nodes and ways file.   
    
    Params: 
        - fclass, list type - list of functional classification names 
    """

    def __init__(self, fclass=[]):
        super(PBFHandler, self).__init__()
        self.ways = []
        self.traffic_signal_ids = []
        self.nodes = {'id': [], 'traffic_signals': [], 'geometry': []}
        self.not_bike_facs = ['no', 'none', 'No', 'None', 'sidewalk', 'Sidewalk']
        if len(fclass) > 0:
            self.fclass = fclass
        else:
            self.fclass  = [          
                'motorway', 'motorway_link',
                'primary', 'primary_link',
                'secondary', 'secondary_link',
                'trunk', 'trunk_link',
                'tertiary', 'tertiary_link',
                'residential', 'living_street',
                'bus_guideway', 'busway',
                'road', 'cycleway',
                'service', 'path',
                'steps', 'pedestrian',
                'footway', 'sidewalk',
                'track', 'unclassified'
            ]
 
        self.cycleways = {'crossing': 'Crossing',
                          'shared_lane': 'Shared Road', 
                          'opposite_share_busway': 'Shared Road',
                          'share_busway': 'Shared Road',
                          'lane': 'Bike Lane', 
                          'lanes': 'Bike Lane',
                          'opposite_lane': 'Bike Lane', 
                          'opposite': 'Bike Lane', 
                          'buffer': 'Buffered Bike Lane', 
                          'buffered_lane': 'Buffered Bike Lane',  # Catch possible tagging mistakes
                          'track': 'Protected Bike Lane',
                          'opposite_track': 'Protected Bike Lane',
                          'separate': 'Shared Use Path',
                          'sidepath': 'Shared Use Path',
                          'cycleway': 'Cycleway',
                          'C ycleway': 'Cycleway',
                          'yes': 'Bike Lane',
                          'shared_parking_lane': 'Shared Lane',
                          'shoulder': 'Shoulder',
                          'shared': 'Shared Lane',
                          'path': 'Shared Use Path',
                          '1': 'Bike Lane',
                          'right': 'Bike Lane',
                          'on_street': 'Shared Lane',
                          'unmarked_lane': 'Shoulder',
                          'designated': 'Bike Lane',
                          'both': 'Bike Lane',
                          'lane=exlusive': 'None',
                          'noneno': 'None',
                          'traffic_island': 'None',
                          'link': 'None',
                          '\\': 'None',
                          'lane=exclusive': 'Protected Bike Lane',
                          'protected lane': 'Protected Bike Lane',
                          'closed_lane': 'None',
                          'asl': 'Advanced Stop Line',
                          'proposed': 'Proposed',
                          'use_sidepath': 'None'
                          
        }

 
    def _check(self, name, tags):
        """
        This function is used to check for an existing value within a feature's attribution tag list
        """
        var = None
        if name in tags:
            var = tags[name]
        return var

    # create a geometry value 
    def _create_geometry(self, type, feature):
        """
        This function returns a geometry from a given feature.
        params 
            - type, string: geometry type (i.e., linestring, point, polygon). Only linestrings are currently supported. 
            - feature, feature object - osmium feature object from ways/nodes functions
        """
        if type == 'linestring':
            return wkblib.loads(wkbfab.create_linestring(feature), hex=True)

    # confirm if way has a node with a signalized intersection 
    def _has_signalized_int(self, feature, traffic_sig_ids):
        """
        This function determines if a given way has an associated signal control device.
        params 
            - traffic_sig_ids, list: list of nodes with a signalized intersection 
            - feature, feature object - osmium feature object from ways functions
        """ 
        # does the way have a sigalized intersection 
        for node in feature.nodes:
            if node.ref in traffic_sig_ids:
                return 'Yes'
        return 'No'

    # get a list of nodes from way 
    def _get_ways_node_ids(self, feature):
        """
        Returns a list of nodes associated with a given way feature. 
        params 
            - feature, feature object - osmium feature object from ways functions 
        """ 
        node_ids = []
        for node in feature.nodes:
            node_ids.append(node.ref)
        return node_ids

    # confirm if way has an existing bicycle facility 
    def _existing_bikeway(self, tags):
        """
        Determines if a given way has an existing bicycle facility
        params 
            - feature, feature object - osmium feature object from ways functions 
        """ 

        if tags.get('highway') == 'cycleway': 
            return 'Existing'
        elif tags.get('cycleway') in list(self.cycleways.keys()):
            if tags.get('cycleway') not in self.not_bike_facs:
                return 'Existing'
        if 'cycleway:both' in tags:
            if tags['cycleway:both'] not in self.not_bike_facs:
                return 'Existing'
        elif 'cycleway:right' in tags or 'cycleway:left' in tags:
            if 'cycleway:right' in tags and 'cycleway:left' not in tags:
                if tags['cycleway:right'] not in self.not_bike_facs:
                    return 'Existing'
            elif 'cycleway:right' not in tags and 'cycleway:left' in tags:
                if tags['cycleway:left'] not in self.not_bike_facs:
                    return 'Existing'
            elif 'cycleway:right' in tags and 'cycleway:left' in tags:
                if tags['cycleway:left'] not in self.not_bike_facs and tags['cycleway:right'] in self.not_bike_facs:
                    return 'Existing'
                elif tags['cycleway:left'] in self.not_bike_facs and tags['cycleway:right'] not in self.not_bike_facs:
                    return 'Existing'
                else: 
                    return 'Existing'

    def _bike_infra(self, tags, min_max='max'):
        """
        This function is used to check for an existing value within a feature's attribution tag list
        """
        if 'cycleway:right' in tags or 'cycleway:left' in tags:
            if 'cycleway:right' in tags and 'cycleway:left' not in tags:
                if tags['cycleway:right'] not in self.not_bike_facs:
                    if min_max == 'max':
                        return str(self.cycleways[tags['cycleway:right']])
            elif 'cycleway:right' not in tags and 'cycleway:left' in tags:
                if tags['cycleway:left'] not in self.not_bike_facs:
                    if min_max == 'max':
                        return self.cycleways[tags['cycleway:left']]
            elif 'cycleway:right' in tags and 'cycleway:left' in tags:
                if tags['cycleway:left'] in self.not_bike_facs and tags['cycleway:right'] in self.not_bike_facs:
                    return 'None'
                if tags['cycleway:left'] not in self.not_bike_facs and tags['cycleway:right'] in self.not_bike_facs:
                    if min_max == 'max':
                        return self.cycleways[tags['cycleway:left']]
                elif tags['cycleway:left'] in self.not_bike_facs and tags['cycleway:right'] not in self.not_bike_facs:
                    if min_max == 'max':
                        return self.cycleways[tags['cycleway:right']]
                else: 
                    v1 = list(self.cycleways.keys()).index(tags['cycleway:right'])
                    v2 = list(self.cycleways.keys()).index(tags['cycleway:left'])
                    if min_max == 'min':
                        return list(self.cycleways.values())[min([v2, v1])]
                    else:
                        return list(self.cycleways.values())[max([v2, v1])]

        if 'cycleway:both' in tags:
            if tags['cycleway:both'] not in self.not_bike_facs:
                return self.cycleways[tags['cycleway:both']]

        elif 'cycleway' in tags:
            if tags['cycleway'] not in self.not_bike_facs:
                return list(self.cycleways.values())[list(self.cycleways.keys()).index(tags['cycleway'])]

    def _osmbike_infra(self, tags):
        """
        This function is used to check for an existing value within a feature's attribution tag list
        """
        if 'cycleway:right' in tags or 'cycleway:left' in tags:
            if 'cycleway:right' in tags and 'cycleway:left' not in tags:
                if tags['cycleway:right'] not in self.not_bike_facs:
                    return 'Left: None; Right: ' + tags['cycleway:right'].capitalize()
            elif 'cycleway:right' not in tags and 'cycleway:left' in tags:
                if tags['cycleway:left'] not in self.not_bike_facs:
                    return 'Left: ' + tags['cycleway:left'].capitalize() + '; Right: None'
            elif 'cycleway:right' in tags and 'cycleway:left' in tags:
                if tags['cycleway:left'] not in self.not_bike_facs and tags['cycleway:right'] in self.not_bike_facs:
                    return 'Left: ' + tags['cycleway:left'].capitalize() + '; Right: None'
                elif tags['cycleway:left'] in self.not_bike_facs and tags['cycleway:right'] not in self.not_bike_facs:
                    return 'Left: None; Right: ' + tags['cycleway:right'].capitalize()
                else: 
                    return 'Left: ' + tags['cycleway:left'].capitalize() + '; Right: ' + tags['cycleway:right'].capitalize()
        
        elif 'cycleway' in tags:
            if tags['cycleway'] not in self.not_bike_facs:
                return tags['cycleway'].capitalize()
        
        elif 'cycleway:both' in tags:
                if tags['cycleway:both'] not in self.not_bike_facs:
                    return tags['cycleway:both'].capitalize()
        
        elif tags.get('highway') == 'cycleway':
            return 'Cycleway'

    def _get_integers(self, value):
        if value is not None:
            return ''.join(str(x) for x in [int(x) for x in value.split() if x.isdigit()])
 
    def _capitalize(self, value):
        if value is not None:
            return value.capitalize()

    # handle nodes 
    def node(self, n):
        """
Osmium node function - with apply_file, creates a nodes object on the instantiated PBFHandler object that can be converted into a Geopandas dataframe. 
        To learn more about this osmium and pyosmium, please visit https://docs.osmcode.org/pyosmium/latest/intro.html#reading-osm-data.  
        """ 
        tags = n.tags

        # extract signalized intersections
        if 'highway' in tags and tags.get('highway') == 'traffic_signals':
            self.traffic_signal_ids.append(n.id)
        if 'highway' in tags and tags.get('highway'):
            wkb = wkbfab.create_point(n)
            shp = wkblib.loads(wkb, hex=True)
            self.nodes['id'].append(n.id)
            self.nodes['traffic_signals'].append(tags.get('highway') == 'traffic_signals')
            self.nodes['geometry'].append(shp)

    # handle ways 
    def way(self, w):
        """
        Osmium node function - with apply_file, creates a nodes object on the instantiated PBFHandler object that can be converted into a Geopandas dataframe. 
        To learn more about this osmium and pyosmium, please visit https://docs.osmcode.org/pyosmium/latest/intro.html#reading-osm-data.    
        """ 
        tags = w.tags
        
        # process ways 
        if ('highway' in tags and tags.get('highway') in self.fclass) or ('cycleway' in tags and tags.get('highway') != 'proposed'):

            # create way 
            self.ways.append({'id': w.id, 
                              'fclass': tags.get('highway'), 
                              'name': self._check('name', tags),
                              'maxspeed': self._get_integers(self._check('maxspeed', tags)), 
                              'lanes': self._get_integers(self._check('lanes', tags)),
                              'surface': self._check('surface', tags),
                              'oneway': self._capitalize(self._check('oneway', tags)),
                              'bike_stats': self._existing_bikeway(tags),
                              'osmbk_infra': self._osmbike_infra(tags),
                              # 'desgnatd_bk': self._dsgnatd_bk(tags), # finding this isn't useful. Pulls a lot of sidewalks where bicycles are allowed.
                              'min_bk_inf': self._bike_infra(tags, 'min'),
                              'max_bk_inf': self._bike_infra(tags, 'max'),
                              'trf_signal': self._has_signalized_int(w,self.traffic_signal_ids),
                              'node_ids': ', '.join(str(e) for e in self._get_ways_node_ids(w)),
                              'geometry': self._create_geometry('linestring', w)
                                    })

class PBFDownloader():
    """
    Python class intended to download OSM PBF files from the web. 
    Params: 
        - pbf_dict, dict of URLs to PBF files. Specify the URLs in a 2 part dictionary, where the URLs are in the values and the filename is the key. 
    """ 
    def __init__(self, pbf_dict, output_path):
        super(PBFDownloader, self).__init__()
        self.pbf_dict = pbf_dict
        self.output_path = output_path

    def _download_pbf(self, pbf_url, filename):
        """
        This function downloads individual OSM PBFs from a given URL and saves them to a user-defined output path.
         """
        wget.download(pbf_url, out=filename)
        
    # parse pbfs and download each one
    def parse_pbfs(self):
        """
        This function parses URLs from the user and downloads the associated OSM PBF. 
        """
        for filename, url in self.pbf_dict.items():
            start_time = time. time()
            self._download_pbf(url, os.path.join(self.output_path, filename + '.pbf'))
            print("Time to download file {0}: {1} minutes.".format(url, ((time.time() - start_time)/60)))

