"""
Created on 2025-05-26

@author: wf
"""

from pathlib import Path

from lodstorage.sparql import SPARQL
from ngwidgets.basetest import Basetest

from genwiki.rdfdump import RdfDumpDownloader


class TestRdfDumpDownloader(Basetest):
    """
    Test RDF Dump Downloader
    """

    def setUp(self, debug=True, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.endpoint_url = "https://gov-sparql.genealogy.net/dataset/sparql"
        home_dir = Path.home()
        self.dumps_dir = (
            home_dir / "Projekte" / "2025" / "CompGen2025" / "GOV" / "dumps"
        )

    def test_download_rdf_dump(self):
        """
        Test downloading RDF dump from gov.genealogy.net
        """
        # First, get the total number of triples to download
        sparql = SPARQL(self.endpoint_url)
        count_query = "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }"
        total_triples = int(sparql.getValue(count_query, "count"))

        if self.debug:
            print(f"Total triples in endpoint: {total_triples:,}")
        self.skipTest("rdf dump takes >1h")
        return
        limit = 100000
        # Set max_triples to download all (with some buffer)
        max_triples = total_triples + limit  # Add buffer for safety

        downloader = RdfDumpDownloader(
            endpoint_url=self.endpoint_url,
            output_path=self.dumps_dir,  # Specify output directory
            limit=100000,  # Larger chunks for efficiency
            max_triples=max_triples,
            show_progress=True,
        )

        if self.debug:
            print(
                f"Starting download of {total_triples:,} triples from: {self.endpoint_url}"
            )

        chunks = downloader.download()

        if self.debug:
            print(f"Downloaded {chunks*limit} triples")

        self.assertGreater(chunks, 0)
