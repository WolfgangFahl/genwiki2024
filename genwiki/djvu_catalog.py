"""
Created on 26.08.2024

@author: wf
"""
import os
from genwiki.query_view import QueryView  # Assuming QueryView is in `genwiki.query_view`
from genwiki.djvu_manager import DjVuManager
from genwiki.multilang_querymanager import MultiLanguageQueryManager

class DjVuCatalog(QueryView):
    """
    UI for browsing and querying the DjVu document catalog.
    """

    def __init__(self, solution):
        self.solution=solution
        self.webserver=self.solution.webserver
        storage_path=solution.webserver.config.storage_path
        db_path=os.path.join(storage_path,"genwiki_djvu.db")
        yaml_path = os.path.join(self.webserver.examples_path(), "djvu_queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)
        try:
            self.dvm = DjVuManager(db_path=db_path)
            super().__init__(solution=solution,
                mlqm=self.mlqm,
                sql_db=self.dvm.sql_db,
                wiki=self.webserver.wiki)
            self.query_name = "all_djvu"
        except Exception as ex:
            self.solution.handle_exception(ex)

    def get_query_lod(self):
        """
        Fetches DjVu catalog data based on the selected query.
        """
        return self.dvm.query(self.query_name)

    def setup_ui(self):
        """
        Sets up the UI components for the DjVu catalog.
        """
        super().setup_ui(query_name=self.query_name)
        self.query_select.options = ["all_djvu", "bundled_djvu", "unbundled_djvu"]
