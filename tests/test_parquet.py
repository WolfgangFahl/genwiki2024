"""
Created on 2024-08-15

@author: wf
"""

import os

import pyarrow.parquet as pq
from ngwidgets.basetest import Basetest


class TestParquet(Basetest):
    """
    Test parquet handling using pyarrow
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_parquet(self):
        """
        Test reading parquet files using pyarrow
        """
        # Define the directory containing the Parquet files
        current_folder = os.path.dirname(__file__)
        genwiki_examples_folder = os.path.join(current_folder, "..", "genwiki_examples")

        # List all .parquet files in the directory
        parquet_files = [
            f for f in os.listdir(genwiki_examples_folder) if f.endswith(".parquet")
        ]

        # Ensure there are parquet files to read
        assert parquet_files, f"No .parquet files found in {genwiki_examples_folder}"
        debug = self.debug
        # Read each parquet file and print its content
        for parquet_file in parquet_files:
            file_path = os.path.join(genwiki_examples_folder, parquet_file)
            try:
                table = pq.read_table(file_path)
                if debug:
                    print(f"Contents of {parquet_file}:")
                rows = table.to_pylist()
                limit = 100
                if debug:
                    # Print the first few rows
                    for row in rows[:limit]:
                        print(row)
            except Exception as e:
                self.fail(f"Failed to read {parquet_file}: {e}")
