"""
Created on 2025-05-25

@author: wf
"""

import os

from lodstorage.query import EndpointManager
from lodstorage.sparql import SPARQL
from ngwidgets.basetest import Basetest
from tabulate import tabulate

from genwiki.genwiki_paths import GenWikiPaths
from genwiki.multilang_querymanager import MultiLanguageQueryManager


class TestGovSparql(Basetest):
    """
    test SPARQL queries for GOV
    """

    def setUp(self, debug=True, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        # Get the examples path
        self.examples_path = GenWikiPaths.get_examples_path()

        # Initialize the query manager with GOV queries
        self.queries_yaml_path = os.path.join(self.examples_path, "gov-queries.yaml")
        self.endpoint_yaml_path = os.path.join(self.examples_path, "gov-ep.yaml")
        self.endpoints = EndpointManager.getEndpoints(self.endpoint_yaml_path)

        # Create MultiLanguageQueryManager with SPARQL support
        self.qm = MultiLanguageQueryManager(
            yaml_path=self.queries_yaml_path, languages=["sparql"], debug=self.debug
        )

        # Setup SPARQL connection
        self.endpoint_name = "gov"
        self.endpoint = self.endpoints.get(self.endpoint_name)
        self.sparql = None
        if self.endpoint:
            self.sparql = SPARQL(self.endpoint.endpoint, debug=self.debug)

    def get_query(self, query_name: str, param_dict: dict = None) -> str:
        """
        Get a SPARQL query with parameters applied

        Args:
            query_name (str): Name of the query
            param_dict (dict): Parameters to apply to the query

        Returns:
            str: The parameterized SPARQL query
        """
        query = self.qm.query4Name(query_name)
        if param_dict:
            sparql_query = query.params.apply_parameters_with_check(param_dict)
        else:
            sparql_query = query.apply_default_params()

        sparql_query = f"{self.endpoint.prefixes}\n{sparql_query}"
        if self.debug:
            print(f"Query {query_name}:")
            print(sparql_query)
        return sparql_query

    def test_endpoint(self):
        """
        test the endpoint availability by querying a single triple
        """
        exception = self.sparql.test_query()
        msg = f"{str(exception)}"
        self.assertIsNone(exception, msg)

    def testNamedParameterizedQueries(self):
        """
        test named parameterized queries
        """
        query_names = self.qm.query_names

        if self.debug:
            print(f"Found {len(query_names)} queries: {query_names}")
            limit = 20
        for qi, query_name in enumerate(self.qm.query_names):
            with self.subTest(query_name=query_name):
                try:
                    sparql_query = self.get_query(query_name)
                    results = self.sparql.queryAsListOfDicts(sparql_query)

                    if self.debug:
                        print(f"\nQuery {query_name}: {len(results)} results")
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
