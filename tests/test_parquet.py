"""
Created on 2024-08-15

@author: wf
"""

import os
import tempfile
from lodstorage.sql import SQLDB
from ngwidgets.basetest import Basetest
from genwiki.parquet import Parquet

class TestParquet(Basetest):
    """
    Test parquet handling using pyarrow
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.parquet_handler = Parquet(debug=self.debug)

    def test_parquet(self):
        """
        Test reading parquet files using pyarrow and converting to SQLite
        """
        # Create a temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name

        try:
            # Define the directory containing the Parquet files
            current_folder = os.path.dirname(__file__)
            genwiki_examples_folder = os.path.join(current_folder, "..", "genwiki_examples")

            # Ensure the directory exists
            self.assertTrue(os.path.exists(genwiki_examples_folder), f"Directory not found: {genwiki_examples_folder}")

            # Read all parquet files
            parquet_data = self.parquet_handler.read_parquet_files(genwiki_examples_folder)

            # Ensure there are parquet files to read
            self.assertTrue(parquet_data, f"No .parquet files found in {genwiki_examples_folder}")

            # Define a column mapping
            column_mapping = {
                "id": "id",
                "page": "page",
                "lastname": "lastname",
                "firstname": "firstname",
                "Beruf o. ä.": "occupation",
                "Straße": "street",
                "Ortsname": "city",
                "Ortskennung": "city_code",
                "Firmenname": "company_name",
                "Familienstand": "marital_status",
                "Vorname Bezugsperson": "reference_person_firstname",
                "Beruf Bezugsperson": "reference_person_occupation",
                "Eigentümer": "owner",
                "Funktionsträger": "official",
                "abweichender Wohnort": "alternate_residence",
                "Bezirk": "district"
            }

            # Convert to SQLite with the correct table name and column mapping
            db = self.parquet_handler.convert_parquet_to_sqlite(parquet_data, db_name=temp_db_path, table_name="address", column_mapping=column_mapping)

            # Verify the conversion
            self.assertIsInstance(db, SQLDB, "Conversion should return an SQLDB instance")

            # Check the address table
            table_info = db.getTableDict().get("address")
            self.assertIsNotNone(table_info, "Address table should exist in SQLite database")

            # Verify some data (first row)
            if parquet_data:
                first_table_data = next(iter(parquet_data.values()))
                if first_table_data:
                    first_row = first_table_data[0]
                    columns = ", ".join(table_info['columns'].keys())
                    query_result = db.query(f"SELECT {columns} FROM address LIMIT 1")
                    self.assertEqual(len(first_row), len(query_result[0]), "Column count should match")

            if self.debug:
                # Print some debug information
                table_list = db.getTableList()
                for table in table_list:
                    self.parquet_handler.log(f"Table: {table['name']}")
                    self.parquet_handler.log(f"Columns: {', '.join(col['name'] for col in table['columns'])}")
                    self.parquet_handler.log("-" * 50)

        finally:
            # Clean up the temporary database file
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)