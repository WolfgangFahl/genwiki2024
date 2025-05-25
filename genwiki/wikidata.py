"""
Created on 2024-09-15

@author: wf
"""

from lodstorage.sparql import SPARQL


class Wikidata:
    """
    fixed Wikidata endpoint
    """
    @classmethod
    def get_sparql(cls):
        endpoint_uri = "https://query.wikidata.org/sparql"
        sparql = SPARQL(endpoint_uri)
        return sparql

    @classmethod
    def unprefix(self, qid: str):
        item_prefix = "http://www.wikidata.org/entity/"
        if qid.startswith(item_prefix):
            qid = qid.replace(item_prefix, "")
        return qid
