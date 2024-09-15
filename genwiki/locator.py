"""
Created on 15.09.2024

@author: wf
"""

import os

import geocoder
from ez_wikidata.wdsearch import WikidataSearch

from genwiki.genwiki_paths import GenWikiPaths
from genwiki.gov_api import GOV_API
from genwiki.multilang_querymanager import MultiLanguageQueryManager
from genwiki.nominatim import NominatimWrapper
from genwiki.wikidata import Wikidata
from typing import Tuple

class Locator:
    """
    find locations
    """

    def __init__(self):
        self.nominatim = NominatimWrapper(user_agent="GenWiki2024LocationTest")
        self.wds = WikidataSearch()
        self.gov_api = GOV_API()
        self.sparql = Wikidata.get_sparql()
        yaml_path = os.path.join(GenWikiPaths.get_examples_path(), "queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)
        self.lookup_query = self.mlqm.query4Name("WikidataLookup")
        self.limit = 11
        self.lang_map = {"deu": "de", "pol": "pl"}

    def lookup_wikidata_id_by_geonames(self, geonames_id: str, lang: str = "en") -> str:
        result=None
        query = self.mlqm.query4Name("WikidataLookupByGeoNamesID")
        param_dict={
            "geonames_id":geonames_id,
            "lang":lang
        }
        sparql_query=query.params.apply_parameters_with_check(param_dict)
        qlod=self.sparql.queryAsListOfDicts(queryString=sparql_query, param_dict=param_dict)
        if len(qlod)==1:
            record=qlod[0]
            item=record["item"]
            wikidataid = Wikidata.unprefix(item)
            result=wikidataid
        elif len(qlod)>1:
            ValueError(f"wikidata has multiple entries for geonames_id{geonames_id}")
        return result

    def locate_by_name(self,name:str,language:str="de",debug:bool=False):
        self.wds.language = language
        sr = self.wds.searchOptions(name, limit=self.limit)
        for j, q_record in enumerate(sr):
            qid, qlabel, desc = q_record
            if debug:
                print(f"{j:3}:{qlabel}({qid}):{desc}")
            if name in desc or name in qlabel:
                return qid
        return None

    def locate(self, gov_id: str, debug: bool = False) -> Tuple[str,str]:
        """
        locate the locaction described by the given gov_id
        """
        geonames_wikidata_id=None
        wds_wikidata_id=None
        try:
            gov_obj = self.gov_api.get_raw_gov_object(gov_id)
            for i,ref in enumerate(gov_obj["externalReference"]):
                val=ref["value"]
                if debug:
                    print(f"{i}:{val}")
                if val.startswith("geonames"):
                    geonames_id = val.split(":")[1]
                    geonames_wikidata_id = self.lookup_wikidata_id_by_geonames(geonames_id)
                for name_record in gov_obj["name"]:
                    lang = name_record["lang"]
                    name = name_record["value"]
                    if lang in self.lang_map:
                        language = self.lang_map[lang]
                    else:
                        language = "en"
                    wds_wikidata_id=self.locate_by_name(name, language, debug)
                    if wds_wikidata_id:
                        break

        except Exception as ex:
            if "404" in str(ex):
                wds_wikidata_id=self.nominatim.lookup_wikidata_id(gov_id)
                pass
            else:
                raise ex

        return geonames_wikidata_id,wds_wikidata_id
