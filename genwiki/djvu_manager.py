"""
Created on 2025-02-24

@author: wf
"""

import os

from lodstorage.sql import SQLDB
from ngwidgets.profiler import Profiler

from genwiki.genwiki_paths import GenWikiPaths
from genwiki.multilang_querymanager import MultiLanguageQueryManager


class DjVuManager:
    """
    manager for DjVu files
    """

    def __init__(self, db_path: str = None):
        """
        Initialize a DjVuManager instance.

        Args:
            db_path: Optional path to the SQLite database. If None, a default path
                within the GenWiki examples directory is used.
        """
        examples_path = GenWikiPaths.get_examples_path()
        yaml_path = os.path.join(examples_path, "djvu_queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)
        if db_path is None:
            db_path = os.path.join(examples_path, "djvu_data.db")
        self.sql_db = SQLDB(db_path, check_same_thread=False)

    def query(self, query_name: str, param_dict=None):
        """
        Execute a predefined SQL query based on its name and parameters.

        Args:
            query_name: Name of the query as defined in the YAML configuration.
            param_dict: Dictionary of parameters to substitute into the query.

        Returns:
            A list of dictionaries representing the query result rows.
        """
        if param_dict is None:
            param_dict = {}
        query = self.mlqm.query4Name(query_name)
        sql_query = query.params.apply_parameters_with_check(param_dict)
        lod = self.sql_db.query(sql_query, params=param_dict)
        return lod

    def store(
        self,
        lod,
        entity_name: str,
        primary_key: str,
        with_drop: bool = False,
        profile: bool = True,
    ):
        """
        Store a list of records (list of dicts) into the database.

        Args:
            lod: List of records to be stored.
            entity_name: Name of the target SQL table.
            primary_key: Column name to use as the table’s primary key.
            with_drop: If True, the existing table (if any) is dropped before creation.
            profile: If True, logs performance information using Profiler.
        """
        profiler = Profiler(
            f"storing {len(lod)} {entity_name} records  to SQL", profile=profile
        )
        if with_drop:
            self.sql_db.execute(f"DROP TABLE IF EXISTS {entity_name}")
        self.entity_info = self.sql_db.createTable(
            listOfRecords=lod,
            entityName=entity_name,
            primaryKey=primary_key,
            withCreate=True,
            withDrop=True,
            sampleRecordCount=20,
        )
        self.sql_db.store(
            listOfRecords=lod,
            entityInfo=self.entity_info,
            executeMany=True,
            fixNone=True,
            replace=True,  # avoid UNIQUE constraint errors
        )
        profiler.time()
