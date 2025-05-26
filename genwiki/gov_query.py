"""
Created on 2025-05-25

@author: wf
"""

import os

from lodstorage.query import EndpointManager
from lodstorage.sparql import SPARQL

from genwiki.genwiki_paths import GenWikiPaths
from genwiki.multilang_querymanager import MultiLanguageQueryManager


class GovQuery:
    """
    Named Parameterized Queries support for

    SPARQL endpoint https://gov-sparql.genealogy.net/

    see https://discourse.genealogy.net/t/gov-mit-sparql-abfragen/824147
    """

    def __init__(self, endpoint_name:str='gov',debug: bool = False):
        self.debug = debug
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
        self.endpoint_name = endpoint_name
        self.endpoint = self.endpoints.get(self.endpoint_name)
        self.sparql = None
        if self.endpoint:
            self.sparql = SPARQL(self.endpoint.endpoint, debug=self.debug)

    def add_prefixes(self, sparql_query: str) -> str:
        prefixed_query = f"{self.endpoint.prefixes}\n{sparql_query}"
        return prefixed_query

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

        sparql_query = self.add_prefixes(sparql_query)
        if self.debug:
            print(f"Query {query_name}:")
            print(sparql_query)
        return sparql_query
