"""
Created on 2024-08-15

@author: wf
"""

from genwiki.wiki import Wiki
from genwiki.addressbook import AddressBookConverter
from tests.gbasetest import GenealogyBasetest


class TestCategories(GenealogyBasetest):
    """
    test category handling

    you need to run

    wikibackup -s genealogy -q "[[Kategorie:Adressbuch_in_der_Online-Erfassung/fertig]]"

    """

    def setUp(self, debug=True, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)
        wiki_id="genealogy"
        self.get_wiki_user(wikiId=wiki_id, save=self.inPublicCI())
        self.ask_query = "[[Kategorie:Adressbuch_in_der_Online-Erfassung/fertig]]"
        self.wiki = Wiki(
            wiki_id=wiki_id, debug=self.debug, backup_dir="/tmp/genwiki"
        )
        self.wiki.is_smw_enabled=False

    def testCategories(self):
        """
        Test categories by processing all .wiki files in the backup directory.
        """
        with_backup = self.inPublicCI()
        if with_backup:
            self.wiki.backup(ask_query=self.ask_query)
        page_contents = self.wiki.get_all_content()
        self.assertTrue(len(page_contents) > 10)
        if self.debug:
            print(page_contents)
            
    

    def test_convert_template(self):
        """
        Test the template conversion functionality for both SiDIF and markup formats.
        """
        ac=AddressBookConverter()
        template_map = ac.template_map
        page_content = """
        {{Info Adressbuch
        | Bild = Weimar-AB-1851_Cover.jpg
        | Titel = Adreß-Buch der Residenz-Stadt Weimar
        | Untertitel = Ein Handbuch für Einheimische und Fremde
        | Autor / Hrsg. = C. G. Kästner
        | Erscheinungsjahr = 1851
        | Seitenzahl = 50
        | Enthaltene Orte = [[GOV:WEIMARJO50QX|Weimar]]
        | GOV-Quelle = source_1134489
        | Standort online = {{ThULB|http://zs.thulb.uni-jena.de/receive/jportal_jpvolume_00103933}}
        | DES = weimarTH1851
        }}
        """
        
        dict_result=template_map.as_template_dict(page_content)
        if self.debug:
            print(dict_result)
        
        # Test SiDIF conversion
        sidif_result = template_map.convert_template(page_content, 'sidif')
        expected_sidif_lines = [
            "AddressBook1 isA AddressBook",
            '"Weimar-AB-1851_Cover.jpg" is image of AddressBook1',
            '"Adreß-Buch der Residenz-Stadt Weimar" is title of AddressBook1',
            '"Ein Handbuch für Einheimische und Fremde" is subtitle of AddressBook1',
            '"C. G. Kästner" is author of AddressBook1',
            '"1851" is year of AddressBook1',
            '"50" is pageCount of AddressBook1',
            '"WEIMARJO50QX" is location of AddressBook1',
            '"source_1134489" is govSource of AddressBook1',
            '"http://zs.thulb.uni-jena.de/receive/jportal_jpvolume_00103933" is onlineSource of AddressBook1',
            '"weimarTH1851" is des of AddressBook1'
        ]
        
        if self.debug:
            print("SiDIF Conversion Result:")
            print(sidif_result)
            print("\nExpected SiDIF Result:")
            print("\n".join(expected_sidif_lines))
        
        for line in expected_sidif_lines:
            self.assertIn(line, sidif_result, f"Expected line not found in SiDIF result: {line}")
        
        # Test markup conversion
        markup_result = template_map.convert_template(page_content, 'markup')
        expected_markup_lines = [
            "{{Template:AddressBook",
            "| image = Weimar-AB-1851_Cover.jpg",
            "| title = Adreß-Buch der Residenz-Stadt Weimar",
            "| subtitle = Ein Handbuch für Einheimische und Fremde",
            "| author = C. G. Kästner",
            "| year = 1851",
            "| pageCount = 50",
            "| location = WEIMARJO50QX",
            "| govSource = source_1134489",
            "| onlineSource = http://zs.thulb.uni-jena.de/receive/jportal_jpvolume_00103933",
            "| des = weimarTH1851",
            "}}"
        ]
        
        if self.debug:
            print("\nMarkup Conversion Result:")
            print(markup_result)
            print("\nExpected Markup Result:")
            print("\n".join(expected_markup_lines))
        
        for line in expected_markup_lines:
            self.assertIn(line, markup_result, f"Expected line not found in markup result: {line}")
        
        # Test that integer conversion worked
        self.assertIn('"1851" is year of AddressBook1', sidif_result)
        self.assertIn('"50" is pageCount of AddressBook1', sidif_result)
        self.assertIn("| year = 1851", markup_result)
        self.assertIn("| pageCount = 50", markup_result)
        
        # Test that regex extraction worked
        self.assertIn('"WEIMARJO50QX" is location of AddressBook1', sidif_result)
        self.assertIn("| location = WEIMARJO50QX", markup_result)
        
        if self.debug:
            print("\nAll assertions passed successfully.")

