"""
Created on 15.09.2024

@author: wf
"""

import logging
import os
from collections import Counter
from typing import Any, Dict, List

import geocoder
from ez_wikidata.wdsearch import WikidataSearch
from geopy.distance import geodesic

from genwiki.genwiki_paths import GenWikiPaths
from genwiki.gov_api import GOV_API
from genwiki.multilang_querymanager import MultiLanguageQueryManager
from genwiki.nominatim import NominatimWrapper
from genwiki.wikidata import Wikidata


class Locator:
    """
    find locations
    """

    def __init__(self, debug: bool = False):
        self.nominatim = NominatimWrapper(user_agent="GenWiki2024LocationTest")
        self.wds = WikidataSearch()
        self.gov_api = GOV_API()
        self.sparql = Wikidata.get_sparql()
        yaml_path = os.path.join(GenWikiPaths.get_examples_path(), "queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)
        self.lookup_query = self.mlqm.query4Name("WikidataLookup")
        self.limit = 11
        self.lang_map = {"deu": "de", "pol": "pl"}
        self.debug = debug

    def multi_item_query(
        self, query_name, items: List[str], lang: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        perform a multi item query for the given query_name with
        """
        query = self.mlqm.query4Name(query_name)
        items_str = " ".join([f"wd:{item}" for item in items if item])
        param_dict = {"items": items_str, "lang": lang}
        sparql_query = query.params.apply_parameters_with_check(param_dict)
        qlod = self.sparql.queryAsListOfDicts(
            queryString=sparql_query, param_dict=param_dict
        )
        return qlod

    def get_coordinates(self, items: List[str]) -> Dict[str, tuple]:
        """
        Get coordinates for multiple Wikidata items
        """
        qlod = self.multi_item_query(query_name="WikidataItemsCoordinates", items=items)

        coordinates = {}
        for record in qlod:
            item = Wikidata.unprefix(record["item"])
            coord_str = record["coordinates"]
            lon, lat = map(float, coord_str.strip("Point()").split())
            coordinates[item] = (lat, lon)
        return coordinates

    def lookup_item(self, item: str, lang: str = "de"):
        param_dict = {"item": item, "lang": lang}
        query = self.lookup_query
        sparql_query = query.params.apply_parameters_with_check(param_dict)
        qlod = self.sparql.queryAsListOfDicts(
            queryString=sparql_query, param_dict=param_dict
        )
        return qlod

    def to_path(self, qlod) -> str:
        path = None
        for record in qlod:
            level = record["level"]
            if level == "4":
                iso_code = record["iso_code"]
                label = record["itemLabel"]
                path = f"""{iso_code.replace("-","/")}/{label}"""
        return path

    def lookup_path_for_item(self, item: str, lang: str = "de") -> str:
        """
        lookup the path for the given item wikidata Q-Identifier
        """
        qlod = self.lookup_item(item, lang)
        path = self.to_path(qlod)
        return path

    def lookup_wikidata_id_by_geoid(
        self, geoid_kind: str, geo_id: str, lang: str = "en"
    ) -> str:
        result = None
        if geoid_kind == "NUTS2003" or geoid_kind == "NUTS1999":
            query_name = "WikidataLookupByNutsCode"
            param_name = "nuts_code"
        elif geoid_kind == "geonames":
            query_name = "WikidataLookupByGeoNamesID"
            param_name = "geonames_id"
        else:
            raise ValueError(f"invalid geo_id_kind {geoid_kind}")
        query = self.mlqm.query4Name(query_name)
        param_dict = {param_name: geo_id, "lang": lang}
        sparql_query = query.params.apply_parameters_with_check(param_dict)
        qlod = self.sparql.queryAsListOfDicts(
            queryString=sparql_query, param_dict=param_dict
        )
        if len(qlod) == 1:
            record = qlod[0]
            item = record["item"]
            wikidataid = Wikidata.unprefix(item)
            result = wikidataid
        elif len(qlod) > 1:
            raise ValueError(f"wikidata has multiple entries for {param_name}:{geo_id}")
        return result

    def locate_by_name(self, name: str, language: str = "de"):
        self.wds.language = language
        sr = self.wds.searchOptions(name, limit=self.limit)
        for j, q_record in enumerate(sr):
            qid, qlabel, desc = q_record
            if self.debug:
                print(f"{j:3}:{qlabel}({qid}):{desc}")
            if name in desc or name in qlabel:
                return qid
        return None

    def validate(self, gov_obj, items: Dict[str, str], max_distance_km: float = 3.0):
        """
        validate the list of wikidata items against the given gov_obj
        """
        if not gov_obj:
            return
        gov_position = gov_obj.get("position", {})
        gov_lat, gov_lon = gov_position.get("lat"), gov_position.get("lon")
        items_to_remove = []
        wikidata_coords = {}
        if not gov_lat or not gov_lon:
            msg = "Gov object does not have valid coordinates"
            logging.warn(msg)
            gov_coords = None
        else:
            gov_coords = (gov_lat, gov_lon)
            wikidata_items = [item for item in items.values() if item]
            wikidata_coords = self.get_coordinates(wikidata_items)

        for key, item in items.items():
            ok = item is not None
            if item in wikidata_coords:
                item_coords = wikidata_coords[item]
                distance = geodesic(gov_coords, item_coords).kilometers
                ok = distance <= max_distance_km
                if self.debug:
                    check_mark = "✓" if ok else "✗"
                    print(f"{key}: {distance:.1f} km {check_mark}")
            if not ok:
                items_to_remove.append(key)

        for key in items_to_remove:
            items.pop(key)

    def sort_items(self, items):
        # Count occurrences of each value
        value_counts = Counter(items.values())

        # Sort items by value, then by frequency of value
        sorted_items = sorted(items.items(), key=lambda x: (x[1], -value_counts[x[1]]))

        # Clear and update the original dictionary
        items.clear()
        items.update(sorted_items)

        return items

    def locate(self, gov_id: str) -> Dict[str, str]:
        """
        locate the locaction described by the given gov_id
        """
        items = {}
        gov_obj = None
        try:
            gov_obj = self.gov_api.get_raw_gov_object(gov_id)
            if "externalReference" in gov_obj:
                for i, ref in enumerate(gov_obj["externalReference"]):
                    val = ref["value"]
                    if self.debug:
                        print(f"{i}:{val}")
                    for geoid_kind in ["geonames", "NUTS2003", "NUTS1999"]:
                        if val.startswith(geoid_kind):
                            geo_id = val.split(":")[1]
                            item = self.lookup_wikidata_id_by_geoid(geoid_kind, geo_id)
                            if item:
                                items[val] = item
                    for name_record in gov_obj["name"]:
                        lang = name_record["lang"]
                        name = name_record["value"]
                        if lang in self.lang_map:
                            language = self.lang_map[lang]
                        else:
                            language = "en"
                        item = self.locate_by_name(name, language)
                        items[f"gov-{name}@{language}"] = item

        except Exception as ex:
            if "404" in str(ex) or "501" in str(ex):
                item = self.nominatim.lookup_wikidata_id(gov_id)
                if item:
                    items["nominatim"] = item
                pass
            else:
                raise ex
        self.validate(gov_obj, items)
        self.sort_items(items)
        return items
