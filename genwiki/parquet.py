"""
Created on 2024-08-26

@author: wf
"""
import logging
import os
from typing import List, Dict, Any
import pyarrow.parquet as pq
from lodstorage.sql import SQLDB, EntityInfo

class Parquet:
    """
    A class to handle Parquet file operations and SQLite conversions.

    This class provides functionality to read Parquet files from a directory
    and convert their contents to an SQLite database using EntityInfo.

    Attributes:
        debug (bool): If True, debug information will be logged.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the Parquet handler.

        Args:
            debug (bool): If True, enables debug output. Defaults to False.
        """
        self.debug = debug

    def log(self, msg: str) -> None:
        """
        Log a message if debug is True.

        Args:
            msg (str): The message to log.
        """
        if self.debug:
            logging.debug(msg)

    def read_parquet_files(self, directory: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Read all Parquet files in the given directory and return their contents as a dictionary of table names to rows.

        Args:
            directory (str): The path to the directory containing Parquet files.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary where keys are table names (derived from file names)
                                             and values are lists of dictionaries representing the rows.

        Raises:
            FileNotFoundError: If the specified directory does not exist.
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")

        parquet_files = [f for f in os.listdir(directory) if f.endswith(".parquet")]
        tables_data = {}

        for parquet_file in parquet_files:
            file_path = os.path.join(directory, parquet_file)
            table_name = os.path.splitext(parquet_file)[0]  # Remove .parquet extension
            try:
                table = pq.read_table(file_path)
                rows = table.to_pylist()
                tables_data[table_name] = rows
                self.log(f"Read {len(rows)} rows from {parquet_file}")
            except Exception as e:
                self.log(f"Failed to read {parquet_file}: {e}")

        return tables_data


    def convert_parquet_to_sqlite(self, parquet_data: Dict[str, List[Dict[str, Any]]], db_name: str = ":memory:",
                              table_name: str = None, column_mapping: Dict[str, str] = None) -> SQLDB:
        if not parquet_data:
            raise ValueError("No data to convert to SQLite")

        db = SQLDB(db_name, debug=self.debug)

        for original_table_name, rows in parquet_data.items():
            actual_table_name = table_name or original_table_name
            if column_mapping:
                rows = self._apply_column_mapping(rows, column_mapping)

            entityInfo = EntityInfo(rows, actual_table_name, debug=self.debug)

            tables=db.getTableList()
            if not any(table['name'] == actual_table_name for table in tables):
                db.createTable4EntityInfo(entityInfo)

            db.store(rows, entityInfo)
            self.log(f"Added {len(rows)} rows to SQLite table '{actual_table_name}'")

        return db


    def _apply_column_mapping(self, rows: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Apply the column mapping to the rows.

        Args:
            rows (List[Dict[str, Any]]): The original rows of data.
            column_mapping (Dict[str, str]): Mapping of Parquet column names to SQLite column names.

        Returns:
            List[Dict[str, Any]]: The rows with updated column names.
        """
        return [{column_mapping.get(k, k): v for k, v in row.items()} for row in rows]

