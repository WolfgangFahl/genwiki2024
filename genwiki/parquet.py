"""
Created on 2024-08-26

@author: wf
"""
import logging
import os
from typing import List, Dict, Any
import pyarrow.parquet as pq
from lodstorage.sql import SQLDB, EntityInfo
from lodstorage.schema import SchemaManager, Schema

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
                # Add source field to each row
                for row in rows:
                    row['source'] = parquet_file
                tables_data[table_name] = rows
                log_msg=f"Read {len(rows)} rows from {parquet_file}"
                self.log(log_msg)
            except Exception as e:
                log_msg=f"Failed to read {parquet_file}: {e}"
                self.log(log_msg)

        return tables_data


    def convert_parquet_to_sqlite(self, parquet_data: Dict[str, List[Dict[str, Any]]], db: SQLDB,
                              table_name: str = None, column_mapping: Dict[str, str] = None):
        """
        Converts Parquet data to SQLite tables and creates a combined view.

        Args:
            parquet_data (Dict[str, List[Dict[str, Any]]]): A dictionary where keys are table names and values are lists
                of dictionaries representing rows of data. Each dictionary in the list represents a row, with keys as
                column names and values as column values.
            db (SQLDB): An instance of the SQLDB class where the tables will be created.
            table_name (str, optional): The name of the combined view that will be created. If not provided,
                defaults to "combined_view".
            column_mapping (Dict[str, str], optional): A dictionary mapping original column names to new column names.
                If provided, the columns in the Parquet data will be renamed accordingly.

        Raises:
            ValueError: If `parquet_data` is empty.

        Returns:
            None

        Example:
            parquet_data = {
                "table1": [{"col1": "value1", "col2": "value2"}],
                "table2": [{"col1": "value1", "col2": "value2"}]
            }
            db = SQLDB()
            convert_parquet_to_sqlite(parquet_data, db, table_name="my_view", column_mapping={"col1": "new_col1"})

        This method performs the following steps:
            1. Converts each table in `parquet_data` into a corresponding SQLite table.
            2. Applies `column_mapping` to rename columns, if provided.
            3. Creates a combined view in the SQLite database that includes all the tables.
            4. Logs the progress of adding rows to each SQLite table and creating the view.
        """
        if not parquet_data:
            raise ValueError("No data to convert to SQLite")

        table_list = []

        for original_table_name, rows in parquet_data.items():
            if column_mapping:
                rows = self._apply_column_mapping(rows, column_mapping)

            entityInfo = EntityInfo(rows, original_table_name, debug=self.debug)
            db.createTable4EntityInfo(entityInfo)
            db.store(rows, entityInfo)

            table = {
                "name": original_table_name,
                "columns": [{"name": col, "type": str(type_)} for col, type_ in entityInfo.typeMap.items()]
            }
            table_list.append(table)

            self.log(f"Added {len(rows)} rows to SQLite table '{original_table_name}'")

        # Create a view that combines all tables
        view_name = table_name or "combined_view"
        view_ddl = Schema.getGeneralViewDDL(table_list, view_name, debug=self.debug)
        db.execute(view_ddl)
        self.log(f"Created view '{view_name}' combining all tables")


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

