"""
Created on 2024-08-15

@author: wf
"""

import json
import os

from lodstorage.params import Params
from lodstorage.query import QueryManager
from lodstorage.sql import SQLDB
from lodstorage.uml import UML
from ngwidgets.basetest import Basetest

from genwiki.convert import ParquetAdressbokToSql


class TestParquet(Basetest):
    """
    Test parquet handling using pyarrow
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        # Define the directory containing the Parquet files
        current_folder = os.path.dirname(__file__)
        self.genwiki_examples_folder = os.path.join(
            current_folder, "..", "genwiki_examples"
        )
        # Ensure the directory exists
        self.assertTrue(
            os.path.exists(self.genwiki_examples_folder),
            f"Directory not found: {self.genwiki_examples_folder}",
        )

    def get_db(self) -> SQLDB:
        debug = self.debug
        db_path = "/tmp/address.db"
        if not os.path.exists(db_path):
            pats = ParquetAdressbokToSql(folder=self.genwiki_examples_folder)
            parquet_data = pats.read()

            # Ensure there are parquet files to read
            self.assertTrue(
                parquet_data,
                f"No .parquet files found in {self.genwiki_examples_folder}",
            )

            pats.inject_year()
            # Convert to SQLite with the correct table name and column mapping
            sql_db = SQLDB(db_path)
            pats.convert(sql_db)
        else:
            sql_db = SQLDB(db_path)
        return sql_db

    def test_parquet(self):
        """
        Test reading parquet files using pyarrow and converting to SQLite
        """
        debug = self.debug
        debug = True
        sql_db = self.get_db()

        # Check the address table
        table_info = sql_db.getTableDict()
        if debug:
            print(json.dumps(table_info, indent=2))
        for p_name in ["weimarTH1851", "weimarTH1853"]:
            self.assertTrue(p_name in table_info)
        table_list = sql_db.getTableList()
        uml = UML()
        markup = uml.tableListToPlantUml(
            table_list,
            "Adressbücher",
            "de.compgen.genwiki2024",
            "address",
            withSkin=True,
        )
        print(markup)

    def test_queries(self):
        """
        Test SQL queries loaded from a YAML file and executed against the SQLite database.
        """
        debug = self.debug
        debug = True
        sql_db = self.get_db()
        yaml_path = os.path.join(self.genwiki_examples_folder, "queries.yaml")
        # Initialize the QueryManager
        test_params = {
            "Gesamtanzahl": {},
            "Stichprobe": {"limit": "5"},
            "BerufStatistik": {"limit": "10"},
            "PersonenSuche": {"suchbegriff": "Ziegler", "limit": "10"},
            "StraßenStatistik": {"straße": "Frauent", "limit": "50"},
            "StraßenVergleich": {"straße": "Frauent"},
        }
        qm = QueryManager(
            lang="sql", queriesPath=yaml_path, with_default=False, debug=self.debug
        )
        for i, (qname, query) in enumerate(qm.queriesByName.items()):
            query.database = "sqlite"
            self.assertTrue(qname in test_params, qname)
            params_dict = test_params[qname]
            params = Params(query.query)
            query.query = params.apply_parameters_with_check(params_dict)
            if debug:
                print(f"{i:3}:{query}")
            lod = sql_db.query(query.query)
            if debug:
                print(json.dumps(lod, indent=2))
