"""
Created on 26.08.2024

@author: wf
"""
import os
from genwiki.query_view import QueryView  # Assuming QueryView is in `genwiki.query_view`
from genwiki.djvu_manager import DjVuManager
from genwiki.multilang_querymanager import MultiLanguageQueryManager
from ngwidgets.widgets import Link

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

    def get_view_record(self, record: dict, index: int) -> dict:
        """
        get the view record for the given record

        Convert path entries to two urls:
            1. GenWiki URL: Links to the file on the Genealogy Wiki.
            2. Local URL: Links to the local DjVu viewer.

        Args:
            record (dict): The source record to convert
            index (int): The row index

        Returns:
            dict: The view record with formatted links and properties
        """
        view_record = {"#": index}  # Number first
        record_copy = record.copy()
        for key, value in record_copy.items():
            if isinstance(value, str) and value.startswith("/images/"):
                filename = value.split("/")[-1]
                wiki_url = f"https://wiki.genealogy.net/index.php?title=Datei%3A{filename}"
                local_url = f"/djvu/{filename}"
                view_record["wiki"]=Link.create(url=wiki_url,text=filename)
                view_record["view"]=Link.create(url=local_url,text=filename)
            else:
                view_record[key] = value
            pass
        return view_record

    def get_view_lod(self, lod: list) -> list:
        """
        Convert records to view format with row numbers and links
        """
        view_lod = []
        for i, record in enumerate(lod):
            index = i + 1
            view_record = self.get_view_record(record, index)
            view_lod.append(view_record)
        return view_lod

    def get_query_lod(self):
        """
        Fetches DjVu catalog data based on the selected query.
        """
        self.lod=self.dvm.query(self.query_name)
        self.view_lod=self.get_view_lod(self.lod)
        return self.view_lod

    def setup_ui(self):
        """
        Sets up the UI components for the DjVu catalog.
        """
        super().setup_ui(query_name=self.query_name)
        self.query_select.options = ["all_djvu", "bundled_djvu", "unbundled_djvu"]
