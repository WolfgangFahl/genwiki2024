"""
Created on 2025-05-25

@author: wf
"""

import os
from typing import Optional

from lodstorage.multilang_querymanager import MultiLanguageQueryManager
from lodstorage.query import EndpointManager, PrefixConfigs
from lodstorage.sparql import SPARQL

from genwiki.genwiki_paths import GenWikiPaths


class GovQuery:
    """
    Named Parameterized Queries support for

    SPARQL endpoint https://gov-sparql.genealogy.net/

    see https://discourse.genealogy.net/t/gov-mit-sparql-abfragen/824147
    """

    def __init__(
        self,
        endpoint_name: str = "gov",
        prefixes_path: Optional[str] = None,
        debug: bool = False,
    ):
        self.debug = debug
        # Get the examples path
        self.examples_path = GenWikiPaths.get_examples_path()

        # Initialize the query manager with GOV queries
        self.queries_yaml_path = os.path.join(self.examples_path, "gov-queries.yaml")
        self.endpoint_yaml_path = os.path.join(self.examples_path, "gov-ep.yaml")

        # Create MultiLanguageQueryManager without endpoint (SPARQL support not yet in MLQM)
        self.qm = MultiLanguageQueryManager(
            yaml_path=self.queries_yaml_path,
            languages=["sparql"],
            debug=self.debug,
        )

        # Setup SPARQL connection
        self.endpoint_name = endpoint_name
        self.endpoints = EndpointManager.getEndpoints(self.endpoint_yaml_path)
        self.endpoint = self.endpoints.get(self.endpoint_name)
        self.sparql = None
        if self.endpoint:
            self.sparql = SPARQL(self.endpoint.endpoint, debug=self.debug)

        # Setup prefix configurations
        if prefixes_path:
            self.prefix_configs = PrefixConfigs.preload(prefixes_path)
        else:
            # Use default prefixes.yaml from pyLoDStorage
            self.prefix_configs = PrefixConfigs.get_instance()

    def get_query(
        self, query_name: str, param_dict: Optional[dict] = None
    ) -> Optional[str]:
        """
        Get a SPARQL query with parameters applied

        Args:
            query_name (str): Name of the query
            param_dict (dict): Parameters to apply to the query

        Returns:
            str: The parameterized SPARQL query or None if query not found
        """
        query = self.qm.query4Name(query_name)
        if query is None:
            return None

        # Add endpoint prefixes
        if self.endpoint is not None:
            query.add_endpoint_prefixes(self.endpoint, self.prefix_configs)

        # Apply parameters - use apply_parameters_with_check which handles both
        # custom params and default values from param_list
        if param_dict:
            sparql_query = query.params.apply_parameters_with_check(
                param_dict, param_list=query.param_list
            )
        else:
            sparql_query = query.params.apply_parameters_with_check(
                {}, param_list=query.param_list
            )

        # Prepend prefixes if they were added
        if query.prefixes:
            prefix_str = "".join(query.prefixes)
            sparql_query = f"{prefix_str}\n{sparql_query}"

        if self.debug:
            print(f"Query {query_name}:")
            print(sparql_query)
        return sparql_query
