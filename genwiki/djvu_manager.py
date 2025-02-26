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
        examples_path = GenWikiPaths.get_examples_path()
        yaml_path = os.path.join(examples_path, "djvu_queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)
        if db_path is None:
            db_path = os.path.join(examples_path, "djvu_data.db")
        self.sql_db = SQLDB(db_path, check_same_thread=False)

    def query(self, query_name: str):
        query = self.mlqm.query4Name(query_name)
        lod = self.sql_db.query(query.query)
        return lod

    def store(self, lod, entity_name: str, primary_key: str, profile: bool = True):
        """
        store my the given list of dicts
        """
        profiler = Profiler(f"caching {entity_name} to SQL", profile=profile)
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
        )
        profiler.time()
