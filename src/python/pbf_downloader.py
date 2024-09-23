
import wget
import time
import os 

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

