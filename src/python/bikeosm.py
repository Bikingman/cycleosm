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
from multiprocessing import Pool
import csv 
import wget

wkbfab = osmium.geom.WKBFactory()

class PBFHandler(osmium.SimpleHandler):
    """
    This python class is an extension of the osmium library to extract geopandas dataframes of OSM data from OSM PBF files. 
    Workflow: after instantiating the PBFHanlder class with the required inputs, point to a PBF file and use the apply_file() method to get a nodes and ways file.   
    
    Params: 
        - fclass, list type - list of functional classification names 
    """

    def __init__(self, fclassfile, biketagsfile, cyclewaysfile):
        super(PBFHandler, self).__init__()
        self.ways = []
        self.traffic_signal_ids = []
        self.nodes = {'id': [], 'traffic_signals': [], 'geometry': []}
        
        if len(fclassfile) > 0 and os.path.exists(fclassfile) and fclassfile.endswith('.csv'):
            self.fclass = list(map(lambda row: row, csv.reader(open(fclassfile, mode='r'))))
        else:
            print(__file__)
            fclasses = os.path.join(os.path.dirname(__file__), 'static', 'osm_links - fclasses.csv')
            if os.path.exists(fclasses) and fclasses.endswith('.csv'):
                self.fclass = self._read_csv_to_list(fclasses)
            else:
                raise FileNotFoundError("No valid CSV file found for fclasses.")


        cycleways = cyclewaysfile if cyclewaysfile and os.path.exists(cyclewaysfile) and cyclewaysfile.endswith('.csv') else os.path.join(os.path.dirname(__file__), 'static', 'osm_links - cycleways.csv')
        if os.path.exists(cycleways) and cycleways.endswith('.csv'):
            with open(cycleways, mode='r') as file:
                self.cycleways = self._read_csv_to_list(file)
        else:
            raise FileNotFoundError("No valid CSV file found for cycleways.")

        not_bike_facs = not_bike_facs if not_bike_facs and os.path.exists(not_bike_facs) and not_bike_facs.endswith('.csv') else os.path.join(os.path.dirname(__file__), 'static', 'osm_links - not_bikelanes.csv')
        if os.path.exists(not_bike_facs) and not_bike_facs.endswith('.csv'):
            with open(not_bike_facs, mode='r') as file:
                self.not_bike_facs = self._read_csv_to_list(file)
        else:
            raise FileNotFoundError("No valid CSV file found for not bike lanes.")



    def _download_pbf(self, pbf_url, filename):
        """
        Downloads an individual OSM PBF file from the given URL and saves it to the specified path.
        """
        try:
            wget.download(pbf_url, out=filename)
            print(f"Download completed: {filename}")
        except Exception as e:
            print(f"Failed to download {filename} from {pbf_url}. Error: {e}")

    def parse_pbfs(self):
        """
        Parses the URLs from the user and downloads the associated OSM PBF files.
        """
        for filename, url in self.pbf_dict.items():
            start_time = time.time()
            file_path = os.path.join(self.output_path, filename + '.pbf')
            
            if os.path.exists(file_path):
                print(f"File {file_path} already exists. Skipping download.")
                continue

            print(f"Starting download for {filename}...")
            self._download_pbf(url, file_path)
            
            download_time = (time.time() - start_time) / 60
            print(f"Time to download file {filename}: {download_time:.2f} minutes.")


    def _read_csv_to_list(self, file_path):
        data_list = []
        with open(file_path, mode='r', newline='') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                data_list.append(row)
        return data_list
        
    def _csv_to_dict(self, file_path):
        data_dict = {}
        with open(file_path, mode='r', newline='') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                # Assuming there are at least two columns
                if len(row) >= 2:
                    key = row[0]   # First column as the key
                    value = row[1] # Second column as the value
                    data_dict[key] = value
        return data_dict


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

        if 'highway' in tags:
            if tags['highway'] == 'cycleway':
                return 'Shared Use Path'


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
        is_traffic_signal = highway_type == 'traffic_signals'
        if is_traffic_signal:
            self.traffic_signal_ids.append(n.id)

        # Process the node if it has a 'highway' tag
        wkb = wkbfab.create_point(n)
        shp = wkblib.loads(wkb, hex=True)

        # Append data to the nodes dictionary
        self.nodes['id'].append(n.id)
        self.nodes['traffic_signals'].append(is_traffic_signal)
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
        if not (('highway' in tags and highway_type in self.fclass) or ('cycleway' in tags and highway_type != 'proposed')):
            return

        # Append the way with pre-fetched values
        self.ways.append({

            'id': w.id, 
            'node_ids': ', '.join(str(e) for e in self._get_ways_node_ids(w)),

            'fclass': tags.get('highway'), 
            'name': self._check('name', tags),
            'lane_markings': self._check('lane_markings', tags),
            'srvc_rd_typ': self._check('service', tags),
            'turn': self._check('turn', tags),

            'maxspeed': self._get_integers(self._check('maxspeed', tags)), 
            'trf_signal': self._has_signalized_int(w,self.traffic_signal_ids),

            'surface': self._check('surface', tags),
            'oneway': self._get_oneway(tags),

            'lanes_fwd': self._get_integers(self._sided_lanes(tags, 'forward')),
            'lanes_bwd': self._get_integers(self._sided_lanes(tags, 'backward')),
            'lanes_tot': self._get_integers(self._check('lanes', tags)),

            'osmbk_left': self._osmbike_infra(tags, 'left'),
            'osmbk_right': self._osmbike_infra(tags, 'right'),
            # 'desgnatd_bk': self._dsgnatd_bk(tags), # finding this isn't useful. Pulls a lot of sidewalks where bicycles are allowed.

            'bkwid_left': self._sided_bike_width(tags, 'left'),
            'bkwid_rght': self._sided_bike_width(tags, 'right'),

            'bkinf_left': self._sided_bike_infra(tags, 'left'),
            'bkinf_rght': self._sided_bike_infra(tags, 'right'),

            'min_bk_inf': self._mm_bike_infra(tags, 'min'),
            'max_bk_inf': self._mm_bike_infra(tags, 'max'),

            'geometry': self._create_geometry('linestring', w)
        })


    def handle_pbfs(self, files, output_path, road_fclasses, handle_ways=True, handle_nodes=True):
        """
        Handles multiple PBF files, processes them, and outputs to Shapefile format.
        """

        start_time = time.time()

        def process_file(filename):
            # Instantiate handler for each file
            handler = PBFHandler(fclass=road_fclasses)
            full_filename = os.path.join(output_path, 'pbf', filename + '.pbf')
            print(f"Processing {full_filename}")

            # Apply file and process nodes and ways
            handler.apply_file(full_filename, locations=True)
            
            # Output file paths
            ways_output = os.path.join(output_path, 'shp', 'osm', filename + '_ways.shp')
            nodes_output = os.path.join(output_path, 'shp', 'osm', filename + '_nodes.shp')

            if handle_ways and handler.ways:
                ways_df = gpd.GeoDataFrame(handler.ways).set_index('id').set_crs(4326, allow_override=True)
                ways_df.to_parquet(ways_output)

            if handle_nodes and handler.nodes:
                nodes_df = gpd.GeoDataFrame(handler.nodes).set_index('id').set_crs(4326, allow_override=True)
                nodes_df.to_parquet(nodes_output)

            print(f"Finished {filename}.pbf in {round((time.time() - start_time) / 60, 2)} minutes.")
        
        # Use multiprocessing to handle files in parallel
        with Pool(3) as pool:
            pool.map(process_file, files)

        total_time = (time.time() - start_time) / 60
        print(f"Total time to process all files: {total_time:.2f} minutes.")
