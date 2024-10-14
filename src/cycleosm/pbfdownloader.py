import osmium
import os
import wget
from typing import Dict
from cycleosm.utils import Utils
wkbfab = osmium.geom.WKBFactory()

class PBFDownloader:
    """
    Handles downloading of OSM PBF files.
    """
    def __init__(self, pbf_dict: Dict[str, str], output_path: str):
        """
        Initializes the downloader with a dictionary of filenames and URLs.

        Args:
            pbf_dict (Dict[str, str]): Mapping of filename to PBF URL.
            output_path (str): Directory to save downloaded PBF files.
        """
        if pbf_dict is None:
           raise ValueError(
                """
                A dictionary of .pbf file URLs was not provided. 
                Hint: Supply a dictionary where the key is the desired filename, 
                and the value is the URL to the corresponding .pbf file.
                
                Example:
                    urls = {
                        'District of Columbia': 'http://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf'
                    }
                """
            )

        if output_path is None:
            raise ValueError(f"\nOutput folder was not supplied. Hint: provide an output directory path.")

        self.output_path = output_path  
        self.pbf_dict = pbf_dict  

    def download_pbf(self, pbf_url: str, filename: str) -> None:
        """
        Downloads an individual OSM PBF file.

        Args:
            pbf_url (str): URL of the PBF file.
            filename (str): Destination filename.
        """
        
        com_filename = os.path.join(self.output_path, f"{filename}.pbf")
            
        if os.path.exists(com_filename):
            print(f"File {com_filename} already exists. Skipping download.")
            return

        try:
            wget.download(pbf_url, out=com_filename)
            print(f"\nDownload completed: {filename}")
        except Exception as e:
            print(f"\nFailed to download {filename} from {pbf_url}. Error: {e}")

    def download_all(self, replace=False) -> None:
        """
        Downloads all PBF files specified in the pbf_dict.
        """
        for filename, url in self.pbf_dict.items():

            complete_file_path = os.path.join(self.output_path, f"{filename}")
            
            if os.path.exists(complete_file_path) and replace==False:
                print(f"File {complete_file_path} already exists. Skipping download.")
                continue

            elif os.path.exists(complete_file_path) and replace==True:
                os.remove(complete_file_path)

            print(f"Starting download for {filename}...")

            self.download_pbf(url, f"{filename}.pbf")
