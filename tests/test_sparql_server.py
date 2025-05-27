"""
Created on 2025-05-26

@author: wf
"""

import json
from pathlib import Path

from ngwidgets.basetest import Basetest
from tqdm import tqdm

from genwiki.sparql_server import Blazegraph, QLever, SparqlServer


class TestSparqlServer(Basetest):
    """
    test starting blazegraph
    """

    def setUp(self, debug=True, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        home_dir = Path.home()
        self.gov_dir = (home_dir / "Projekte" / "2025" / "CompGen2025" / "GOV" )
        self.qlever_data_dir= (self.gov_dir / "qlever")
        self.dumps_dir = (self.gov_dir / "dumps")
        self.servers={
            #"blazegraph": Blazegraph(debug=self.debug),
            "qlever": QLever(debug=self.debug,data_dir=str(self.qlever_data_dir))
        }

    def clear_server(self,server:SparqlServer):
        """
        delete all trips
        """
        if self.debug:
            print("deleting all triples ...")
        clear_query = "DELETE { ?s ?p ?o } WHERE { ?s ?p ?o }"
        server.sparql.insert(clear_query)
        count_triples = server.count_triples()
        self.assertEqual(0, count_triples)

    def start_server(self, server:SparqlServer, verbose: bool = True):
        if server.is_running():
            if self.debug and verbose:
                print(f"{server.name} already running")
        else:
            started = server.start()
            self.assertTrue(started)
        if verbose:
            status = server.status()
            if self.debug:
                print(json.dumps(status, indent=2))
            count_triples = server.count_triples()
            if self.debug:
                print(f"{count_triples} triples found for {server.name}")

    def test_start(self):
        """
        test starting servers
        """
        for server in self.servers.values():
            self.start_server(server)

    def test_load_dump_files(self):
        """
        test loading dump files if available
        """
        if not self.dumps_dir.exists():
            self.skipTest(f"Dumps directory {self.dumps_dir} not available")
        self.start_blazegraph(verbose=False)
        self.skipTest("protect existing blazegraph")
        return
        self.clear_blazegraph()

        # Get all dump files directly
        dump_files = list(self.dumps_dir.glob("dump_*.ttl"))
        if self.debug:
            print(f"Found {len(dump_files)} dump files in {self.dumps_dir}")

        # Load files individually
        loaded_count = 0
        for dump_file in tqdm(dump_files, desc="Loading dump files"):
            file_loaded = self.blazegraph.load_file(str(dump_file))
            if file_loaded:
                loaded_count += 1
            if self.debug:
                status = "✅" if file_loaded else "❌"
                print(f"{status} {dump_file.name}")

        if self.debug:
            print(f"Successfully loaded {loaded_count}/{len(dump_files)} files")

        # Count triples after loading
        final_count = self.blazegraph.count_triples()
        if self.debug:
            print(f"Total triples after loading: {final_count:,}")

        self.assertGreater(loaded_count, 0)
        self.assertGreater(final_count, 0)
