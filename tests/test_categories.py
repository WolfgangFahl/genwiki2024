"""
Created on 2024-08-15

@author: wf
"""
import unittest
from ngwidgets.basetest import Basetest
from genwiki.wiki import Wiki

class TestCategories(Basetest):
    """
    test category handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.wiki = Wiki(wiki_id="genealogy",debug=self.debug)

    @unittest.skipIf(Basetest.inPublicCI(), "wiki access needed")
    def testCategories(self):
        """
        Test categories by processing all .wiki files in the backup directory.
        """
        page_contents=self.wiki.get_all_content()
        self.assertTrue(len(page_contents)>10)
        if self.debug:
            print(page_contents)



