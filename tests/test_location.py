"""
Created on 2024-08-25

@author: wf
"""

import json

from ez_wikidata.wdsearch import WikidataSearch

from genwiki.gov_api import GOV_API
from genwiki.nominatim import NominatimWrapper
from tests.gbasetest import GenealogyBasetest


class TestLocations(GenealogyBasetest):
    """
    test location handling
    """

    def setUp(self, debug=False, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)

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
