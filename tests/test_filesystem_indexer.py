"""
Created on 2025-12-20

@author: wf
"""

import os
import tempfile

from ngwidgets.basetest import Basetest
from rdflib import RDF

from genwiki.filesystem_indexer import FS, FileSystemRDF


class TestFileSystemIndexer(Basetest):
    """
    Test FileSystemRDF functionality: scanning, saving, and loading.
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ttl_file = os.path.join(self.tmp_dir.name, "test_index.ttl")

        # Create some dummy files to scan
        self.dummy_files = []
        for i in range(3):
            p = os.path.join(self.tmp_dir.name, f"testfile_{i}.txt")
            with open(p, "w") as f:
                f.write("content" * (i + 1))
            self.dummy_files.append(p)

        # Create a nested directory
        self.nested_dir = os.path.join(self.tmp_dir.name, "subdir")
        os.makedirs(self.nested_dir)
        p_nested = os.path.join(self.nested_dir, "nested.txt")
        with open(p_nested, "w") as f:
            f.write("nested content")
        self.dummy_files.append(p_nested)

    def tearDown(self):
        self.tmp_dir.cleanup()
        super().tearDown()

    def test_scan_and_query(self):
        """
        Test scanning a directory and querying the in-memory graph.
        """
        indexer = FileSystemRDF()
        indexer.scan_directory(self.tmp_dir.name)

        # 1. Check if graph has triples
        # We expect at least one triple per file (RDF.type) + properties
        self.assertTrue(len(indexer.g) > 0, "Graph should not be empty after scan")

        if self.debug:
            print(f"Scanned {len(indexer.g)} triples.")

        # 2. Verify specific file exists using SPARQL query logic manually
        # Expected files = 3 in root + 1 in subdir = 4
        files_found = 0

        # Query for all instances of fs:File
        for s, p, o in indexer.g.triples((None, RDF.type, FS.File)):
            files_found += 1

            # Get the path property for this file
            path_literal = indexer.g.value(s, FS.path)
            path_str = str(path_literal)

            if self.debug:
                print(f"Found URI: {s} -> Path: {path_str}")

            self.assertTrue(
                path_str in self.dummy_files,
                f"Scanned path {path_str} should be in created dummy files",
            )

        self.assertEqual(
            4, files_found, "Should find exactly 4 files in the directory structure"
        )

    def test_save_and_load(self):
        """
        Test round-trip serialization (Save to TTL -> Load from TTL).
        """
        # 1. Create and Save
        indexer_w = FileSystemRDF()
        indexer_w.scan_directory(self.tmp_dir.name)
        triples_count_original = len(indexer_w.g)
        indexer_w.save_ttl(self.ttl_file)

        self.assertTrue(os.path.exists(self.ttl_file), "TTL file should be created")

        # 2. Load into new instance
        indexer_r = FileSystemRDF()
        indexer_r.load_ttl(self.ttl_file)

        triples_count_loaded = len(indexer_r.g)

        if self.debug:
            print(
                f"Original Triples: {triples_count_original}, Loaded: {triples_count_loaded}"
            )

        self.assertEqual(
            triples_count_original,
            triples_count_loaded,
            "Loaded graph should have same number of triples as saved graph",
        )

        # 3. Verify content persists
        # Grab a random file path from the dummy list
        target_file = self.dummy_files[0]

        # ASK query equivalent in python
        # Try to find a subject where fs:path matches the target file
        found = False
        for s, p, o in indexer_r.g.triples((None, FS.path, None)):
            if str(o) == target_file:
                found = True

                # Verify size exists
                size = indexer_r.g.value(s, FS.size)
                self.assertIsNotNone(
                    size, "Loaded file should still have a size property"
                )
                break

        self.assertTrue(found, f"Could not find path {target_file} in loaded graph")
