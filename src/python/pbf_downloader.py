import wget
import time
import os

class PBFDownloader:
    """
    Python class intended to download OSM PBF files from the web.
    Params: 
        - pbf_dict: A dictionary of URLs to PBF files. Specify the URLs in a 2-part dictionary, 
                    where the URLs are the values and the filenames are the keys.
        - output_path: The path to save the downloaded PBF files.
    """

    def __init__(self, pbf_dict, output_path):
        self.pbf_dict = pbf_dict
        self.output_path = output_path
