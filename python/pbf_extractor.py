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
        self.fclass = fclass
 
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
        return(node_ids)

    # confirm if way has an existing bicycle facility 
    def _existing_bikeway(self, feature):
        """
        Determines if a given way has an existing bicycle facility
        params 
            - feature, feature object - osmium feature object from ways functions 
        """ 
        if feature.tags.get('highway') == 'cycleway' or feature.tags.get('bicycle') == 'Yes': 
            return 'existing'
        else:
            return 'not present'

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
        if 'highway' in tags and tags.get('highway') in self.fclass:

            # create way 
            self.ways.append({'id': w.id, 
                              'fclass': tags.get('highway'), 
                              'name': self._check('name', tags),
                              'maxspeed': self._check('maxspeed', tags), 
                              'lanes': self._check('lanes', tags),
                              'surface': self._check('surface', tags),
                              'oneway': self._check('oneway', tags),
                              'bike_status': self._existing_bikeway(w),
                              'traf_signal': self._has_signalized_int(w,self.traffic_signal_ids),
                              'node_ids': ', '.join(str(e) for e in self._get_ways_node_ids(w)),
                              'geometry': self._create_geometry('linestring', w)
                                    })

class PBFDownloader():
    """
    Python class intended to download OSM PBF files from the web. 
    Params: 
        - pbf_urls, dict, list, or string of URLs to PBF files. If using a dictionary, specify the URLs in a 2 part dictionary, where the URLs are in the values. 
    """ 
    def __init__(self, pbf_urls, output_path):
        super(PBFDownloader, self).__init__()
        self.pbf_urls = pbf_urls
        self.output_path = output_path
    

    def _download_pbf(self, pbf_url):
        """
        This function downloads individual OSM PBFs from a given URL and saves them to a user-defined output path.
         """
        wget.download(pbf_url, out=self.output_path)
        
    # parse pbfs and download each one
    def parser_pbfs(self):
        """
        This function parses URLs from the user and downloads the associated OSM PBF. 
        """
        if type(self.pbf_urls) is dict:
            for i in self.pbf_urls.values():
                self._download_pbf(i)
        if type(self.pbf_urls) is list:
            for i in self.download_pbf:
                self._download_pbf(i)
        if type(self.pbf_urls) is str:
            self._download_pbf(self.pbf_urls)


