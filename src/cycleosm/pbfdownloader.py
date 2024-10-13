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
        self.output_path = output_path  
        self.pbf_dict = pbf_dict  

    def download_pbf(self, pbf_url: str, filename: str) -> None:
        """
        Downloads an individual OSM PBF file.

        Args:
            pbf_url (str): URL of the PBF file.
            filename (str): Destination filename.
        """
        try:
            wget.download(pbf_url, out=filename)
            print(f"\nDownload completed: {filename}")
        except Exception as e:
            print(f"\nFailed to download {filename} from {pbf_url}. Error: {e}")

    def download_all(self) -> None:
        """
        Downloads all PBF files specified in the pbf_dict.
        """
        for filename, url in self.pbf_dict.items():
            file_path = os.path.join(self.output_path, f"{filename}.pbf")
            if os.path.exists(file_path):
                print(f"File {file_path} already exists. Skipping download.")
                continue

            print(f"Starting download for {filename}...")
            self.download_pbf(url, file_path)
