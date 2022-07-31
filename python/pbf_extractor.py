import osmium
import shapely.wkb as wkblib
import wget
wkbfab = osmium.geom.WKBFactory()

class PBFHandler(osmium.SimpleHandler):
    def __init__(self, fclass=[]):
        super(PBFHandler, self).__init__()
        self.ways = []
        self.traffic_signal_ids = []
        self.nodes = {'id': [], 'traffic_signals': [], 'geometry': []}
        self.fclass = fclass

    # check for existing value in attriubte tag    
    def _check(self, name, tags):
        var = None
        if name in tags:
            var = tags[name]
        return var

    # create a geometry value 
    def _create_geometry(self, type, feature):
        if type == 'linestring':
            return wkblib.loads(wkbfab.create_linestring(feature), hex=True)

    # confirm if way has a node with a signalized intersection 
    def _has_signalized_int(self, feature, traffic_sig_ids):
        # does the way have a sigalized intersection 
        for node in feature.nodes:
            if node.ref in traffic_sig_ids:
                return 'Yes'
        return 'No'

    # get a list of nodes from way 
    def _get_ways_node_ids(self, feature):
        node_ids = []
        for node in feature.nodes:
            node_ids.append(node.ref)
        return(node_ids)

    # confirm if way has an existing bicycle facility 
    def _existing_bikeway(self, feature):
        if feature.tags.get('highway') == 'cycleway' or feature.tags.get('bicycle') == 'Yes': 
            return 'existing'
        else:
            return 'not present'

    # handle nodes 
    def node(self, n):
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
    def __init__(self, pbf_urls, output_path):
        super(PBFDownloader, self).__init__()
        self.pbf_urls = pbf_urls
        self.output_path = output_path
    
    # actual downloader
    def download_pbf(self, pbf_url):
        wget.download(pbf_url, out=self.output_path)
        
    # parse pbfs and download each one
    def parser_pbfs(self):
        if type(self.pbf_urls) is dict:
            for i in self.download_pbf.values():
                self.download_pbf(i)
        if type(self.pbf_urls) is list:
            for i in self.download_pbf:
                self.download_pbf(i)
        if type(self.pbf_urls) is str:
            self.download_pbf(self.pbf_urls)


