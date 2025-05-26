"""
Created on 2025-05-26

@author: wf
"""

import json

from ngwidgets.basetest import Basetest

from genwiki.blazegraph import Blazegraph


class TestBlazegraph(Basetest):
    """
    test starting blazegraph
    """

    def setUp(self, debug=True, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_start_blazegraph(self):
        """
        test starting blazegraph
        """
        blazegraph = Blazegraph(debug=self.debug)
        started = blazegraph.start()
        self.assertTrue(started)
        status = blazegraph.status()
        if self.debug:
            print(json.dumps(status, indent=2))
        count_triples=blazegraph.count_triples()
        if self.debug:
            print(f"{count_triples} triples found")
