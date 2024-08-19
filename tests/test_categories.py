"""
Created on 2024-08-15

@author: wf
"""
from tests.gbasetest import GenealogyBasetest
from genwiki.wiki import Wiki

class TestCategories(GenealogyBasetest):
    """
    test category handling
    
    you need to run 
    
    wikibackup -s genealogy -q "[[Kategorie:Adressbuch_in_der_Online-Erfassung/fertig]]"
    
    """

    def setUp(self, debug=True, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)
        self.ask_query="[[Kategorie:Adressbuch_in_der_Online-Erfassung/fertig]]"
        self.wiki = Wiki(wiki_id="genealogy",debug=self.debug,backup_dir="/tmp/genwiki")

    def testCategories(self):
        """
        Test categories by processing all .wiki files in the backup directory.
        """
        with_backup=self.inPublicCI()
        if with_backup:
            self.wiki.backup(ask_query=self.ask_query)
        page_contents=self.wiki.get_all_content()
        self.assertTrue(len(page_contents)>10)
        if self.debug:
            print(page_contents)



