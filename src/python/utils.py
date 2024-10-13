import os
from typing import Dict, List, Union
import logging
import csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Utils:
    def __init__(self):
        super(Utils, self).__init__()

    def _load_txt(self, filepath: str) -> List[List[str]]:
        """
        Loads a CSV file into a list of lists. Uses a default file if the provided path is invalid.

        Args:
            filepath (Optional[str]): Path to the CSV file.
        Returns:
            List[List[str]]: Parsed CSV data.

        Raises:
            FileNotFoundError: If neither the provided nor the default file exists.
        """
        if filepath and os.path.exists(filepath) and filepath.endswith('.txt'):
            return self._read_txt_to_list(filepath)
        
        raise FileNotFoundError(f"No valid CSV file found for {filepath}.")

    def _load_csv_as_dict(
        self, 
        filepath: str, 
        key_col: int = 0, 
        value_col: int = 1, 
        delimiter: str = ',', 
        has_header: bool = False, 
        handle_duplicates: str = 'overwrite'
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Loads a CSV file into a dictionary. Uses a default file if the provided path is invalid.

        Args:
            filepath (Optional[str]): Path to the CSV file.
            key_col (int, optional): Zero-based index of the column to use as keys. Defaults to 0.
            value_col (int, optional): Zero-based index of the column to use as values. Defaults to 1.
            delimiter (str, optional): Delimiter used in the CSV file. Defaults to ','.
            has_header (bool, optional): Indicates if the first row is a header. Defaults to False.
            handle_duplicates (str, optional): Strategy to handle duplicate keys. Defaults to 'overwrite'.

        Returns:
            Dict[str, Union[str, List[str]]]: Dictionary mapping keys to values.

        Raises:
            FileNotFoundError: If neither the provided nor the default file exists.
            ValueError: If `handle_duplicates` parameter is invalid.
        """
        if filepath and os.path.exists(filepath) and filepath.endswith('.csv'):
            logger.info(f"Loading CSV from provided path: {filepath}")
            return self._csv_to_dict(
                file_path=filepath, 
                key_col=key_col, 
                value_col=value_col, 
                delimiter=delimiter, 
                has_header=has_header, 
                handle_duplicates=handle_duplicates
            )
        
        logger.error(f"No valid CSV file found for {filepath}.")
        raise FileNotFoundError(f"No valid CSV file found for {filepath}.")

    def _csv_to_dict(
        self, 
        file_path: str, 
        key_col: int = 0, 
        value_col: int = 1, 
        delimiter: str = ',', 
        has_header: bool = False, 
        handle_duplicates: str = 'overwrite'
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Converts a CSV file into a dictionary, using specified key and value columns.
        
        Args:
            file_path (str): Path to the CSV file.
            key_col (int, optional): Zero-based index of the column to use as keys. Defaults to 0.
            value_col (int, optional): Zero-based index of the column to use as values. Defaults to 1.
            delimiter (str, optional): Delimiter used in the CSV file. Defaults to ','.
            has_header (bool, optional): Indicates if the first row is a header. Defaults to False.
            handle_duplicates (str, optional): Strategy to handle duplicate keys ('overwrite', 'ignore', 'accumulate'). Defaults to 'overwrite'.
        
        Returns:
            Dict[str, Union[str, List[str]]]: Dictionary mapping keys to values.
        
        Raises:
            ValueError: If `handle_duplicates` parameter is invalid.
        """
        data_dict = {}

        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=delimiter)

            if has_header:
                next(csv_reader)  # Skip the header row

            for row in csv_reader:
                if len(row) > max(key_col, value_col):  # Ensure row has enough columns
                    key = row[key_col]
                    value = row[value_col]

                    if key in data_dict:
                        if handle_duplicates == 'overwrite':
                            data_dict[key] = value
                        elif handle_duplicates == 'ignore':
                            continue
                        elif handle_duplicates == 'accumulate':
                            if isinstance(data_dict[key], list):
                                data_dict[key].append(value)
                            else:
                                data_dict[key] = [data_dict[key], value]
                        else:
                            raise ValueError(f"Invalid `handle_duplicates` option: {handle_duplicates}")
                    else:
                        data_dict[key] = value
                else:
                    logger.warning(f"Row has fewer columns than expected: {row}")

        return data_dict


    def _read_txt_to_list(self, file_path: str) -> List[List[str]]:
        """
        Reads a CSV file and returns its content as a list of lists.

        Args:
            file_path (str): Path to the CSV file.

        Returns:
            List[List[str]]: Parsed CSV data.
        """
        with open(file_path, mode='r',encoding='utf-8') as file:
            lines = file.readlines()

        # Remove trailing newlines
        lines = [line.rstrip('\n') for line in lines]
    
        return lines
