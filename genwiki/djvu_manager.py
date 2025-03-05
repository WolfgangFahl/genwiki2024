"""
Created on 2025-02-24

@author: wf
"""

import os

from lodstorage.sql import SQLDB
from ngwidgets.profiler import Profiler
from setuptools.package_index import REL

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

    def query(self, query_name: str, param_dict=None):
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
        store my the given list of dicts
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
