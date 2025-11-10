"""
Created on 2025-05-26

@author: __wf__
"""

from ngwidgets.basetest import Basetest
from owlapy

class TestGovOntology(Basetest):
    """
    test GOV Ontology using owlapy
    """

    def setUp(self, debug: bool = True, profile: bool = True) -> None:
        """
        setUp the test environment

        Args:
            debug: enable debug output
            profile: enable profiling
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.onto_url: str = "http://gov.genealogy.net/ontology.owl"
        self.onto= onto = SyncOntology(self.onto_url)


    def testGovOntology(self) -> None:
        """
        test loading the gov ontology
        """
        classes = list(self.onto.classes_in_signature())

        if self.debug:
            for owl_class in classes:
                class_name: str = owl_class.remainder
                print(class_name)

        classes_count: int = len(classes)
        self.assertTrue(classes_count > 0)

    def testProperties(self) -> None:
        """
        test loading the gov ontology and showing class properties
        """
        onto = SyncOntology(self.onto_url)

        object_props = list(onto.object_properties_in_signature())
        data_props = list(onto.data_properties_in_signature())

        if self.debug:
            for prop in object_props:
                prop_name: str = prop.remainder
                print(f"ObjectProperty: {prop_name}")
            for prop in data_props:
                prop_name: str = prop.remainder
                print(f"DataProperty: {prop_name}")