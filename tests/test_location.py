"""
Created on 2024-08-25

@author: wf
"""

import json

from ez_wikidata.wdsearch import WikidataSearch

from genwiki.gov_api import GOV_API
from genwiki.locator import Locator
from genwiki.nominatim import NominatimWrapper
from tests.gbasetest import GenealogyBasetest


class TestLocations(GenealogyBasetest):
    """
    test location handling
    """

    def setUp(self, debug=False, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)
        self.locator = Locator(debug=True)

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

    def testLocator(self):
        """
        test the locator
        """
        geo_names_id = "3092080"
        qid = self.locator.lookup_wikidata_id_by_geonames(geo_names_id, lang="de")
        self.assertEqual("Q255385", qid)

        debug = True
        for gov_id, expected in [
            ("RUMURGJO84LA", {"gov-Miastko@pl": "Q255385"}),
            ("WEIMARJO50QX", {"gov-Weimar@de": "Q3955"}),
            ("Vaihingen auf den Fildern", {}),
        ]:
            items = self.locator.locate(gov_id)
            if debug:
                print(f"{gov_id}:{items}")
            # self.assertEqual(ex_geo_qid,geo_qid)
            # self.assertEqual(ex_wds_qid,wds_qid)

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
