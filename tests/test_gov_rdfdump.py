"""
Created on 2025-05-26

@author: wf
"""

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

    def test_download_rdf_dump(self):
        """
        Test downloading RDF dump from gov.genealogy.net
        """
        downloader = RdfDumpDownloader(
            endpoint_url=self.endpoint_url, limit=5000, max_triples=50000
        )

        if self.debug:
            print(f"Starting download from: {self.endpoint_url}")

        chunk_count = downloader.download()

        if self.debug:
            print(f"Downloaded {chunk_count} chunks")

        self.assertTrue(chunk_count > 0)
