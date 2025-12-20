"""
Created on 2025-05-25

@author: wf
"""

from ngwidgets.basetest import Basetest
from tabulate import tabulate

from genwiki.gov_query import GovQuery


class TestGovSparql(Basetest):
    """
    test SPARQL queries for GOV
    """

    def setUp(self, debug=True, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        endpoint_name = "gov"
        self.gq = GovQuery(endpoint_name=endpoint_name, debug=self.debug)

    def test_endpoint(self):
        """
        test the endpoint availability by querying a single triple
        """
        exception = self.gq.sparql.test_query()
        msg = f"{str(exception)}"
        self.assertIsNone(exception, msg)

    def testNamedParameterizedQueries(self):
        """
        test named parameterized queries
        """
        query_names = self.gq.qm.query_names

        if self.debug:
            print(f"Found {len(query_names)} queries: {query_names}")
            limit = 20
        for qi, query_name in enumerate(self.gq.qm.query_names):
            with self.subTest(query_name=query_name):
                try:
                    sparql_query = self.gq.get_query(query_name)
                    results = self.gq.sparql.queryAsListOfDicts(sparql_query)

                    if self.debug:
                        print(f"\nQuery #{qi}:{query_name}: {len(results)} results")
                        if results:
                            print(
                                tabulate(
                                    results[:limit], headers="keys", tablefmt="grid"
                                )
                            )
                except Exception as e:
                    if self.debug:
                        print(f"Query {query_name} failed: {e}")
                    self.fail(e)
