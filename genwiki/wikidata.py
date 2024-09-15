"""
Created on 15.09.2024

@author: wf
"""

from lodstorage.sparql import SPARQL


class Wikidata:
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
