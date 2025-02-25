"""
Created on 2025-02-24

@author: wf
"""

import os
from lodstorage.sql import SQLDB
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
        self.sql_db = SQLDB(db_path)

    def query(self, query_name: str):
        query = self.mlqm.query4Name(query_name)
        lod = self.sql_db.query(query.query)
        return lod
