"""
Created on 2024-08-25

@author: wf
"""

import json

from ez_wikidata.wdsearch import WikidataSearch

from genwiki.gov_api import GOV_API
from genwiki.locator import Locator
from genwiki.nominatim import NominatimWrapper
from genwiki.wikidata import Wikidata
from tests.gbasetest import GenealogyBasetest


class TestLocations(GenealogyBasetest):
    """
    test location handling
    """

    def setUp(self, debug=False, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)
        self.locator = Locator(debug=debug)

    def get_parts(self, items):
        parts = {}
        qlod = self.locator.multi_item_query(
            query_name="WikidataItemHasParts", items=items, lang="de"
        )
        for record in qlod:
            part = record["part"]
            part = Wikidata.unprefix(part)
            parts[part] = record
        return parts

    def test_location_hierarchy(self):
        """
        get a lookup of european locations
        """
        europe = "Q46"
        parts = self.get_parts([europe])
        sub_parts = self.get_parts(list(parts.keys()))
        countries_to_regions = {}
        for qid, record in sub_parts.items():
            record["item"] = Wikidata.unprefix(record["item"])
            record["part"] = Wikidata.unprefix(record["part"])
            print(f"{qid}:{record}")
            region_label = record["itemLabel"]
            country_label = record["partLabel"]

            # If the country is not already in the mapping, add it
            if country_label not in countries_to_regions:
                countries_to_regions[country_label] = region_label
            else:
                print(
                    f"Duplicate assignment found for country {country_label}. Keeping the first region: {countries_to_regions[country_label]}."
                )

        # Export the mapping to a JSON file
        with open("/tmp/countries_to_regions.json", "w", encoding="utf-8") as f:
            json.dump(countries_to_regions, f, ensure_ascii=False, indent=4)

    def test_coords(self):
        """
        test getting coordinates for items
        """
        items = ["Q1729", "Q7070"]
        coords = self.locator.get_coordinates(items)
        expected = {
            "Q1729": (50.978055555, 11.028888888),  # Erfurt
            "Q7070": (50.974722222, 10.324444444),  # Eisenach
        }
        self.assertEqual(expected, coords)

    def test_path(self):
        """
        test getting a path
        """
        item = "Q3955"
        page_title = self.locator.lookup_path_for_item(item)
        self.assertEqual("DE/TH/Weimar", page_title)

    def test_sort_items(self):
        """
        test sorting items
        """
        items = {"a": "Q20", "b": "Q20", "c": "Q20", "d": "Q300", "e": "Q200"}
        expected = {"a": "Q20", "b": "Q20", "c": "Q20", "e": "Q200", "d": "Q300"}
        self.locator.sort_items(items)
        self.assertEqual(expected, items)

    def testLocator(self):
        """
        test the locator
        """
        geo_names_id = "3092080"
        qid = self.locator.lookup_wikidata_id_by_geoid(
            geoid_kind="geonames", geo_id=geo_names_id, lang="de"
        )
        self.assertEqual("Q255385", qid)

        debug = True
        for gov_id, expected in [
            ("adm_136611", {}),
            ("RUMURGJO84LA", {"gov-Miastko@pl": "Q255385"}),
            ("WEIMARJO50QX", {"gov-Weimar@de": "Q3955"}),
            ("Vaihingen auf den Fildern", {}),
        ]:
            items = self.locator.locate(gov_id)
            if debug:
                print(f"{gov_id}:{items}")
            self.assertEqual(expected, items)

    def testWikidataSearch(self):
        """ """
        examples = [("Q57993", "Thalheim", "Erzgebirgskreis")]
        wds = WikidataSearch()
        limit = 10
        debug = self.debug
        debug = True
        found_location = None
        for i, (expected_qid, location, located_in) in enumerate(examples):
            wds.language = "de"
            sr = wds.searchOptions(location, limit=limit)
            if debug:
                print(f"{i:2}:{location}:{len(sr)}")
                print(json.dumps(sr, indent=2))
            for _j, record in enumerate(sr):
                qid, qlabel, desc = record
                if located_in in desc or located_in in qlabel:
                    found_location = record
        if found_location:
            qid, qlabel, desc = found_location
            if debug:
                print(f"found: {qid} {qlabel}-{desc}")
                self.assertEqual(expected_qid, qid)
        self.assertIsNotNone(found_location)

    def testGOV(self):
        """
        test gov api access
        """
        # Example usage
        gov_id = "WEIMARJO50QX"
        gov_api = GOV_API()
        obj = gov_api.get_raw_gov_object(gov_id)
        debug = self.debug
        debug = True
        if debug:
            print(json.dumps(obj, indent=2))

    def testNominatim(self):
        """
        test Nominatim functionality
        """
        nominatim = NominatimWrapper(user_agent="GenWiki2024LocationTest")
        examples = [
            ("Q57993", "Thalheim (Erzgebirge)"),
        ]
        debug = self.debug
        debug = True
        for expected_qid, location in examples:
            wikidata_id = nominatim.lookup_wikidata_id(location)
            self.assertIsNotNone(wikidata_id, f"Wikidata ID not found for {location}")
            self.assertEqual(
                expected_qid, wikidata_id, f"Unexpected Wikidata ID for {location}"
            )
            if debug:
                print(f"Wikidata ID for {location}: {wikidata_id}")
