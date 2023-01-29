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
 
        self.bike_tags = [
            'cycleway', 
            'cycleway:right', 
            'cycleway:left', 
            'cycleway:both', 
            'cycleway:buffer', 
            'cycleway:right:buffer', 
            'cycleway:left:buffer', 
            'cycleway:both:buffer' 
        ]


        self.not_bike_facs = [
                              'no', 
                              'none', 
                              'No', 
                              'None', 
                              'sidewalk', 
                              'Sidewalk',
                              'noneno',
                              'traffic_island',
                              'link',
                              '\\',
                              'closed_lane',
                              'unmarked_lane'
                              ]
        # important this list needs to be ordered from least protection to greatest protection 
        self.cycleways = {'proposed': 'Proposed', 
                          'crossing': 'Crossing',
                          'asl': 'Advanced Stop Line',
                          'shoulder': 'Shoulder',
                          'shared_lane': 'Shared Road', 
                          'opposite_share_busway': 'Shared Road',
                          'share_busway': 'Shared Road',
                          'on_street': 'Shared Road',
                          'shared_parking_lane': 'Shared Road',
                          'shared': 'Shared Road',
                          'lane': 'Bike Lane', 
                          'lanes': 'Bike Lane',
                          'opposite_lane': 'Bike Lane', 
                          'opposite': 'Bike Lane', 
                          'designated': 'Bike Lane',
                          'both': 'Bike Lane',
                          'yes': 'Bike Lane',
                          '1': 'Bike Lane',
                          '5': 'Bike Lane',
                          'right': 'Bike Lane',
                          'left': 'Bike Lane',
                          'buffer': 'Buffered Bike Lane', 
                          'buffered_lane': 'Buffered Bike Lane', 
                          'track': 'Protected Bike Lane',
                          'opposite_track': 'Protected Bike Lane',
                          'lane=exlusive': 'Protected Bike Lane',
                          'lane=exclusive': 'Protected Bike Lane',
                          'protected lane': 'Protected Bike Lane',
                          'separate': 'Shared Use Path',
                          'sidepath': 'Shared Use Path',
                          'path': 'Shared Use Path',
                          'use_sidepath': 'Shared Use Path',
                          'cycleway': 'Cycleway'
                          
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
            else:
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

    def _get_buffered_bike_lane(self, tags, sides):
        for side in sides:
            if 'cycleway:{0}:buffer'.format(side) in tags:
                if tags['cycleway:{0}:buffer'.format(side)] not in self.not_bike_facs:
                    buf_index = list(self.cycleways.keys()).index(tags['cycleway:{0}:buffer'.format(side)])
                    if list(self.cycleways.values())[buf_index] == 'Bike Lane':
                        return 'Buffered Bike Lane'


    # get an indexed list of bike infra for use with self.cycleways
    def _get_min_bike_infra(self, tags):
        if self._get_oneway(tags) == 'Yes':
            return self._get_max_bike_infra(tags)
        if self._sided_bike_infra(tags, 'left') == None:
            return None
        if self._sided_bike_infra(tags, 'right') == None:
            return None
        else:
            left = list(self.cycleways.values()).index(self._sided_bike_infra(tags, 'left'))
            right = list(self.cycleways.values()).index(self._sided_bike_infra(tags, 'right'))
            if left <= right:
                return self._sided_bike_infra(tags, 'left')
            else:
                return self._sided_bike_infra(tags, 'right')

    def _get_max_bike_infra(self, tags):
        left = None
        right = None

        if self._sided_bike_infra(tags, 'left') is not None:
            left = list(self.cycleways.values()).index(self._sided_bike_infra(tags, 'left'))
        if self._sided_bike_infra(tags, 'right') is not None:
            right = list(self.cycleways.values()).index(self._sided_bike_infra(tags, 'right'))

        if left is not None and right is not None:
            if left > right:
                return self._sided_bike_infra(tags, 'left')
            else:
                return self._sided_bike_infra(tags, 'right')
        if left is None and right is not None:
            return self._sided_bike_infra(tags, 'right')
        if left is not None and right is None:
            return self._sided_bike_infra(tags, 'left')

    def _get_oneway(self, tags):
        #todo if null then no
        if 'oneway' in tags:
            if tags['oneway'] == 'yes':
                return 'Yes'
            else:
                return 'No'
        else:
            return 'No'

    def _mm_bike_infra(self, tags, min_max):
        """
        This function is used to check for an existing value within a feature's attribution tag list
        """

        if min_max == 'min':
            return self._get_min_bike_infra(tags)
            
        if min_max == 'max':
            return self._get_max_bike_infra(tags)
        
        if tags['highway'] == 'cycleway':
            return 'Shared Use Path'

    def _sided_bike_infra(self, tags, side): 

        if 'cycleway:{0}'.format(side) in tags:
            if 'cycleway:{0}:buffer'.format(side) in tags:
                if tags['cycleway:{0}:buffer'.format(side)] not in self.not_bike_facs:
                    index = list(self.cycleways.keys()).index(tags['cycleway:{0}:buffer'.format(side)])
                    bl = list(self.cycleways.values())[index]
                    if bl == 'Bike Lane':
                        return 'Buffered Bike Lane'
                    else:
                        return bl
            if tags['cycleway:{0}'.format(side)] not in self.not_bike_facs:
                index = list(self.cycleways.keys()).index(tags['cycleway:{0}'.format(side)])
                return list(self.cycleways.values())[index]
        if 'cycleway:both' in tags:
            if 'cycleway:both:buffer' in tags:           
                if tags['cycleway:both:buffer'] not in self.not_bike_facs:
                    index = list(self.cycleways.keys()).index(tags['cycleway:both:buffer'])
                    bl = list(self.cycleways.values())[index]
                    if bl == 'Bike Lane':
                        return 'Buffered Bike Lane'
                    else:
                        return bl
            
            if tags['cycleway:both'] not in self.not_bike_facs:
                index = list(self.cycleways.keys()).index(tags['cycleway:both'])
                return list(self.cycleways.values())[index]
        if 'cycleway' in tags:
            if tags['cycleway'] not in self.not_bike_facs:
                index = list(self.cycleways.keys()).index(tags['cycleway'])
                return list(self.cycleways.values())[index]

        if 'oneway:bicycle' in tags:
            if tags['oneway:bicycle'] not in self.not_bike_facs:
                index = list(self.cycleways.keys()).index(tags['oneway:bicycle'])
                return list(self.cycleways.values())[index]

        if tags['highway'] == 'cycleway':
            return 'Shared Use Path'

    def _osmbike_infra(self, tags, side):
        """
        This function is used to check for an existing value within a feature's attribution tag list
        """
        if 'cycleway:{0}:buffer'.format(side) in tags:
            if tags['cycleway:{0}:buffer'.format(side)] not in self.not_bike_facs:
                return tags['cycleway:{0}:buffer'.format(side)].capitalize()
        
        if 'cycleway:{0}'.format(side) in tags:
            if tags['cycleway:{0}'.format(side)] not in self.not_bike_facs:
                return tags['cycleway:{0}'.format(side)].capitalize()

        if 'cycleway:both:buffer' in tags:
            if tags['cycleway:both:buffer'] not in self.not_bike_facs:
                return tags['cycleway:both:buffer'].capitalize()

        if 'cycleway:both' in tags:
            if tags['cycleway:both'] not in self.not_bike_facs:
                return tags['cycleway:both'].capitalize()

        if 'cycleway' in tags:
            if tags['cycleway'] not in self.not_bike_facs:
                return tags['cycleway'].capitalize()

        if 'oneway:bicycle' in tags:
            if tags['oneway:bicycle'] not in self.not_bike_facs:
                index = list(self.cycleways.keys()).index(tags['oneway:bicycle'])
                return list(self.cycleways.values())[index]

        if tags['highway'] == 'cycleway':
            return 'cycleway'


    def _sided_bike_width(self, tags, side):

        if 'cycleway:{0}:width'.format(side) in tags:
            return tags['cycleway:{0}:buffer'.format(side)]
        
        if 'cycleway:both:width' in tags:
            return tags['cycleway:both:width']

        if 'cycleway:width' in tags:
            return tags['cycleway:width']

    def _sided_lanes(self, tags, direction):
        if 'lanes:{0}'.format(direction) in tags:
            return tags['lanes:{0}'.format(direction)]

    def _get_integers(self, value):
        if value is not None:
            return ''.join(str(x) for x in [int(x) for x in value.split() if x.isdigit()])
 
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

                              'lanes_fwd': self._get_integers(self._sided_lanes(tags, 'forward')),
                              'lanes_bwd': self._get_integers(self._sided_lanes(tags, 'backward')),

                              'lanes_tot': self._get_integers(self._check('lanes', tags)),

                              'surface': self._check('surface', tags),
                              'oneway': self._get_oneway(tags),
                              'osmbk_left': self._osmbike_infra(tags, 'left'),
                              'osmbk_right': self._osmbike_infra(tags, 'right'),
                              # 'desgnatd_bk': self._dsgnatd_bk(tags), # finding this isn't useful. Pulls a lot of sidewalks where bicycles are allowed.

                              'bkwid_left': self._sided_bike_width(tags, 'left'),
                              'bkwid_rght': self._sided_bike_width(tags, 'right'),

                              'bkinf_left': self._sided_bike_infra(tags, 'left'),
                              'bkinf_rght': self._sided_bike_infra(tags, 'right'),

                              'min_bk_inf': self._mm_bike_infra(tags, 'min'),
                              'max_bk_inf': self._mm_bike_infra(tags, 'max'),

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

