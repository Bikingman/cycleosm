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
import time
import os
import geopandas as gpd
from typing import Dict, Optional
import logging
from cycleosm.pbfdownloader import PBFDownloader
from cycleosm.utils import Utils 

wkbfab = osmium.geom.WKBFactory()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BikeOSM(osmium.SimpleHandler, Utils):
    """
        This module provides classes to download and extract OpenStreetMap (OSM) PBF files. 
        OSM PBF is an efficient binary format for storing OSM data, generally smaller and faster to process than OSM XML files.

        Classes:
            - PBFDownloader: Downloads OSM PBF files from a specified source.
            - BikeOSMHandler: Parses OSM PBF files to extract bike-related GIS data into GeoPandas DataFrames.

        Source of PBF Files:
            https://download.geofabrik.de/

        Dependencies:
            - osmium
            - shapely
            - geopandas
            - wget

        Example:
            ```python
            downloader = PBFDownloader(pbf_dict, output_path)
            downloader.download_all()

            handler = BikeOSMHandler(fclassfile, biketagsfile, cyclewaysfile, pbf_dict, output_path)
            handler.handle_pbfs(files, output_path)
            ```
        """

    def __init__( self, 
        pbf_dict: Dict[str, str], 
        output_path: str,
        fclassfile: Optional[str] = None,
        biketagsfile: Optional[str] = None,
        cyclewaysfile: Optional[str]  = None,
        not_bike_facsfile: Optional[str] = None
        ):
        self.ways = []
        self.traffic_signal_ids = []
        self.nodes = {'id': [], 'trfc_sgnls': [], 'geometry': []}
        self.pbf_dict = pbf_dict
        self.output_path = output_path

        cpp = os.path.dirname(__file__)
        sttc = 'static'
        t = 'osm_links - cycleways.txt'
        cy = 'osm_links - tags.csv'
        nb = 'osm_links - not_bikelanes.txt'
        fc = 'osm_links - fclasses.txt'

        def static_filepath(c, s, f):
            return os.path.join(c, s, f)
        
        self.biketagsfile  = static_filepath(cpp, sttc, t) if biketagsfile == None else biketagsfile
        self.cyclewaysfile  = static_filepath(cpp, sttc, cy) if cyclewaysfile == None else cyclewaysfile
        self.not_bike_facsfile  = static_filepath(cpp, sttc, nb) if not_bike_facsfile == None else not_bike_facsfile
        self.fclassfile  = static_filepath(cpp, sttc, fc) if fclassfile == None else fclassfile
         
   
        self.fclass = self._load_txt(self.fclassfile)
        self.not_bike_facs = self._load_txt(self.not_bike_facsfile)
        self.biketags = self._load_txt(self.biketagsfile) 
        self.cycleways = self._load_csv_as_dict(self.cyclewaysfile)


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
            try: 
                return wkblib.loads(wkbfab.create_linestring(feature), hex=True)
            except: 
                pass

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
        
        if 'highway' in tags:
            if tags['highway'] == 'cycleway':
                return 'Shared Use Path'

    def _sided_bike_infra(self, tags, side): 
        try: 
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

            if 'highway' in tags:
                if tags['highway'] == 'cycleway':
                    return 'Shared Use Path'
        except:
            return 'Unkown'

    def _bicycle_route(self, tags):
        """
        This function is used determine if a route is a bicycle route.
        """
        if 'route' in tags:
            if tags['route'] == 'bicycle':
                return 'Bicycle Route'
        else:
            return None
        
    def _osmbike_infra(self, tags, side):
        """
        This function is used to check for an existing value within a feature's attribution tag list
        """
        if 'highway' in tags:
            if tags['highway'] == 'cycleway':
                return 'Cycleway'
                
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

        


    def _sided_bike_width(self, tags, side):

        if 'cycleway:{0}:width'.format(side) in tags:
            return tags['cycleway:{0}:width'.format(side)]
        
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
        highway_type = tags.get('highway')

        # If 'highway' tag doesn't exist, return early
        if not highway_type:
            return

        # Extract signalized intersections
        is_traffic_signal = highway_type == 'trfc_sgnls'
        if is_traffic_signal:
            self.traffic_signal_ids.append(n.id)

        # Process the node if it has a 'highway' tag
        wkb = wkbfab.create_point(n)
        shp = wkblib.loads(wkb, hex=True)

        # Append data to the nodes dictionary
        self.nodes['id'].append(n.id)
        self.nodes['trfc_sgnls'].append(is_traffic_signal)
        self.nodes['geometry'].append(shp)


    # handle ways 
    def way(self, w):
        """
        Osmium node function - with apply_file, creates a nodes object on the instantiated PBFHandler object that can be converted into a Geopandas dataframe. 
        To learn more about this osmium and pyosmium, please visit https://docs.osmcode.org/pyosmium/latest/intro.html#reading-osm-data.    
        """ 
        tags = w.tags

        highway_type = tags.get('highway')

        # Early return if conditions are not met
        if not (('highway' in tags and highway_type in self.fclass)):
            return

        # Append the way with pre-fetched values
        self.ways.append({

            'id': w.id, 
            #'node_ids': ', '.join(str(e) for e in self._get_ways_node_ids(w)),

            'fclass': tags.get('highway'), 
            'name': self._check('name', tags),
            'ln_mrkngs': self._check('lane_markings', tags),
            'svc_rd_typ': self._check('service', tags),
            'turn': self._check('turn', tags),

            'maxspeed': self._get_integers(self._check('maxspeed', tags)), 
            'trf_sgnl': self._has_signalized_int(w,self.traffic_signal_ids),

            'surface': self._check('surface', tags),
            'oneway': self._get_oneway(tags),

            'lanes_fwd': self._get_integers(self._sided_lanes(tags, 'forward')),
            'lanes_bwd': self._get_integers(self._sided_lanes(tags, 'backward')),
            'lanes_tot': self._get_integers(self._check('lanes', tags)),

            'osmbk_left': self._osmbike_infra(tags, 'left'),
            'osmbk_rght': self._osmbike_infra(tags, 'right'),
            # 'desgnatd_bk': self._dsgnatd_bk(tags), # finding this isn't useful. Pulls a lot of sidewalks where bicycles are allowed.

            'bk_route': self._bicycle_route(tags),

            'bkwid_left': self._sided_bike_width(tags, 'left'),
            'bkwid_rght': self._sided_bike_width(tags, 'right'),

            'bkinf_left': self._sided_bike_infra(tags, 'left'),
            'bkinf_rght': self._sided_bike_infra(tags, 'right'),

            'min_bk_inf': self._mm_bike_infra(tags, 'min'),
            'max_bk_inf': self._mm_bike_infra(tags, 'max'),

            'geometry': self._create_geometry('linestring', w)
        })


    def handle_pbfs(self, files=None, output_path=None, handle_ways=True, handle_nodes=True):
        """
        Handles  PBF files, processes them, and outputs to Shapefile format.
        """
        files = self.pbf_dict if files == None else files 
        output_path = self.output_path if output_path == None else output_path
        downloader = PBFDownloader(self.pbf_dict, self.output_path)
        o_startime = time.time()
        def process_file(filename, output_path):
            # set start time to output time taken for each iteration 
            start_time = time.time()

            # Instantiate handler for each file
            full_filename = os.path.join(output_path, filename + '.pbf')
            print(f"Processing {full_filename}")

            # Apply file and process nodes and ways
            self.apply_file(full_filename, locations=True)
            
            # Output file paths
            ways_output = os.path.join(output_path, filename + '_ways.shp')
            nodes_output = os.path.join(output_path, filename + '_nodes.shp')

            if handle_ways and self.ways:
                ways_df = gpd.GeoDataFrame(self.ways).set_index('id').set_crs(4326, allow_override=True)
                ways_df.to_file(ways_output)

            if handle_nodes and self.nodes:
                nodes_df = gpd.GeoDataFrame(self.nodes).set_index('id').set_crs(4326, allow_override=True)
                nodes_df.to_file(nodes_output)

            print(f"Finished {filename}.pbf in {round((time.time() - start_time) / 60, 2)} minutes.")

        for f, url in files.items():
            downloader.download_pbf(url, f)
            self.ways = []
            self.traffic_signal_ids = []
            self.nodes = {'id': [], 'trfc_sgnls': [], 'geometry': []}
            process_file(f, output_path)
        total_time = (time.time() - o_startime) / 60
        print(f"Total time to process all files: {total_time:.2f} minutes.")
