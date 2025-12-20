"""
Created on 2025-05-26

@author: wf
"""

from ngwidgets.basetest import Basetest
from owlready2 import default_world, get_ontology


class TestGovOntology(Basetest):
    """
    test GOV Ontology
    """

    def setUp(self, debug=True, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.onto_url = "https://gov.genealogy.net/ontology.owl"

    def testGovOntology(self):
        """
        test loading the gov ontology
        """
        onto = get_ontology(self.onto_url)
        onto.load()
        classes = list(
            default_world.sparql(
                """
           SELECT ?x
           WHERE { ?x a owl:Class . }
        """
            )
        )
        if self.debug:
            for (cls,) in classes:
                print(cls)
        self.assertTrue(len(classes) > 0)

    def testProperties(self):
        """
        test loading the gov ontology and showing class properties
        """

        def safe_name(entity):
            return getattr(entity, "name", str(entity))

        onto = get_ontology(self.onto_url)
        onto.load()
        if self.debug:
            for prop in onto.properties():
                domain = [safe_name(c) for c in prop.domain]
                range_ = [safe_name(c) for c in prop.range]
                print(f"{prop.name}: domain={domain} range={range_}")
