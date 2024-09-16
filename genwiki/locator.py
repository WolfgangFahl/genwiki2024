"""
Created on 15.09.2024

@author: wf
"""
import logging
import os
from geopy.distance import geodesic
import geocoder
from ez_wikidata.wdsearch import WikidataSearch

from genwiki.genwiki_paths import GenWikiPaths
from genwiki.gov_api import GOV_API
from genwiki.multilang_querymanager import MultiLanguageQueryManager
from genwiki.nominatim import NominatimWrapper
from genwiki.wikidata import Wikidata
from typing import Dict, List

class Locator:
    """
    find locations
    """

    def __init__(self,debug:bool=False):
        self.nominatim = NominatimWrapper(user_agent="GenWiki2024LocationTest")
        self.wds = WikidataSearch()
        self.gov_api = GOV_API()
        self.sparql = Wikidata.get_sparql()
        yaml_path = os.path.join(GenWikiPaths.get_examples_path(), "queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)
        self.lookup_query = self.mlqm.query4Name("WikidataLookup")
        self.limit = 11
        self.lang_map = {"deu": "de", "pol": "pl"}
        self.debug=debug

    def get_coordinates(self, items: List[str]) -> Dict[str, tuple]:
        """
        Get coordinates for multiple Wikidata items
        """
        query = self.mlqm.query4Name("WikidataItemsCoordinates")
        items_str = " ".join([f"wd:{item}" for item in items if item])
        param_dict = {"items": items_str}
        sparql_query = query.params.apply_parameters_with_check(param_dict)
        qlod = self.sparql.queryAsListOfDicts(queryString=sparql_query, param_dict=param_dict)

        coordinates = {}
        for record in qlod:
            item = Wikidata.unprefix(record["item"])
            coord_str = record["coordinates"]
            lon,lat = map(float, coord_str.strip("Point()").split())
            coordinates[item] = (lat, lon)
        return coordinates

    def lookup_path_for_item(self,item:str,lang:str="de"):
        """
        lookup the path for the given item wikidata Q-Identifier
        """
        path=None
        param_dict={
            "item": item,
            "lang": lang
        }
        query=self.lookup_query
        sparql_query=query.params.apply_parameters_with_check(param_dict)
        qlod=self.sparql.queryAsListOfDicts(queryString=sparql_query, param_dict=param_dict)
        for record in qlod:
            level=record["level"]
            if level=="4":
                iso_code=record["iso_code"]
                label=record["itemLabel"]
                path=f"""{iso_code.replace("-","/")}/{label}"""
        return path

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

    def locate_by_name(self,name:str,language:str="de"):
        self.wds.language = language
        sr = self.wds.searchOptions(name, limit=self.limit)
        for j, q_record in enumerate(sr):
            qid, qlabel, desc = q_record
            if self.debug:
                print(f"{j:3}:{qlabel}({qid}):{desc}")
            if name in desc or name in qlabel:
                return qid
        return None

    def validate(self,gov_obj,items: Dict[str,str],max_distance_km: float = 3.0):
        """
        validate the list of wikidata items against the given gov_obj
        """
        if not gov_obj:
            return
        gov_position = gov_obj.get("position", {})
        gov_lat, gov_lon = gov_position.get("lat"), gov_position.get("lon")

        if not gov_lat or not gov_lon:
            msg="Gov object does not have valid coordinates"
            logging.error(msg)
            return

        gov_coords = (gov_lat, gov_lon)
        wikidata_items = [item for item in items.values() if item]
        wikidata_coords = self.get_coordinates(wikidata_items)
        items_to_remove = []
        for key, item in items.items():
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

    def locate(self, gov_id: str) -> Dict[str,str]:
        """
        locate the locaction described by the given gov_id
        """
        items={}
        gov_obj=None
        try:
            gov_obj = self.gov_api.get_raw_gov_object(gov_id)
            if "externalReference" in gov_obj:
                for i,ref in enumerate(gov_obj["externalReference"]):
                    val=ref["value"]
                    if self.debug:
                        print(f"{i}:{val}")
                    if val.startswith("geonames"):
                        geonames_id = val.split(":")[1]
                        items[val] = self.lookup_wikidata_id_by_geonames(geonames_id)
                    for name_record in gov_obj["name"]:
                        lang = name_record["lang"]
                        name = name_record["value"]
                        if lang in self.lang_map:
                            language = self.lang_map[lang]
                        else:
                            language = "en"
                        item=self.locate_by_name(name, language)
                        items[f"gov-{name}@{language}"]=item

        except Exception as ex:
            if "404" in str(ex):
                item=self.nominatim.lookup_wikidata_id(gov_id)
                if item:
                    items["nominatim"]=item
                pass
            else:
                raise ex
        self.validate(gov_obj, items)
        return items
