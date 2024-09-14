"""
Created on 2024-08-15

@author: wf
"""

import os

from tqdm import tqdm

from genwiki.addressbook import AddressBookConverter
from genwiki.wiki import Wiki
from tests.gbasetest import GenealogyBasetest


class TestCategories(GenealogyBasetest):
    """
    test category handling

    you need to run

    wikibackup -s genealogy -q "[[Kategorie:Adressbuch_in_der_Online-Erfassung/fertig]]"

    """

    def setUp(self, debug=True, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)
        self.wiki_id = "genealogy"
        self.get_wiki_user(wikiId=self.wiki_id, save=self.inPublicCI())
        self.target_wiki_id = "gensmw"
        self.get_wiki_user(wikiId=self.target_wiki_id, save=self.inPublicCI())
        self.target_wiki = Wiki(wiki_id=self.target_wiki_id, debug=self.debug)
        self.target_wiki.wiki_push.toWiki = self.target_wiki.wiki_push.fromWiki
        self.ask_query = "[[Kategorie:Adressbuch_in_der_Online-Erfassung/fertig]]"
        self.backup_dir = "/tmp/genwiki"
        self.wiki = Wiki(
            wiki_id=self.wiki_id, debug=self.debug, backup_dir=self.backup_dir
        )
        self.wiki.wiki_push.fromWiki.is_smw_enabled = False

    def test_query(self):
        """
        test SMW Ask query access
        """
        ask_query = """{{#ask: [[Concept:AddressBook]]
    |mainlabel=AddressBook
    |?AddressBook id = id
    |?AddressBook title = title
    |?AddressBook subtitle = subtitle
    |?AddressBook year = year
    |?AddressBook pageCount = pageCount
    |?AddressBook location = location
    |limit=20
    }}"""
        qlod = self.target_wiki.query_as_list_of_dicts(ask_query)
        self.assertIsInstance(qlod, list)
        self.assertTrue(len(qlod) > 0)
        debug = self.debug
        # debug=True
        for record in qlod:
            self.assertIsInstance(record, dict)
            self.assertTrue("title" in record)
            if debug:
                print(record)
        pass

    def testCategories(self):
        """
        Test categories by processing all .wiki files in the backup directory.
        """
        with_backup = self.inPublicCI() or not os.path.exists(self.backup_dir)
        # with_backup=True
        if with_backup:
            self.wiki.backup(ask_query=self.ask_query)
        page_contents = self.wiki.get_all_content()
        self.assertTrue(len(page_contents) > 10)
        if self.debug:
            print(page_contents)

    def test_convert_addressbooks(self):
        force = not self.inPublicCI()
        # dry run?
        # force=False

        # Set up source and target wikis
        source_wiki = self.wiki

        # Create AddressBookConverter
        ac = AddressBookConverter(debug=self.debug)

        # Get page contents
        page_contents = source_wiki.get_all_content()

        limit = 5

        # Set up tqdm progress bar
        progress_bar = tqdm(total=limit, desc="Converting AddressBooks", unit="page")

        mode = "push"  # or 'push' if you want to test pushing to the wiki

        # Convert with limit of 10 pages
        target_pages = ac.convert(
            page_contents,
            target_wiki=self.target_wiki,
            mode=mode,
            limit=limit,
            force=force,
            progress_bar=progress_bar,
        )

        # Close the progress bar
        progress_bar.close()

        rcount = len(target_pages)
        # Assertions
        self.assertEqual(
            progress_bar.n, rcount, f"Expected {rcount} pages to be processed"
        )

        # Check if backup files were created (if mode is 'backup')
        if mode == "backup":
            ab_count = 0
            page_contents = self.target_wiki.get_all_content()
            for _page_name, page_content in page_contents.items():
                ab_dict = ac.template_map.as_topic_dict(page_content)
                if ab_dict:
                    ab_count += 1

            self.assertTrue(
                rcount - ab_count < 3,
                f"Expected {rcount} {ac.template_map.topic_name} backup files to be created -max 3 difference",
            )

        if self.debug:
            print(f"Converted {rcount} AddressBook pages")

    def test_convert_template(self):
        """
        Test the template conversion functionality for both SiDIF and markup formats.
        """
        ac = AddressBookConverter()
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

        dict_result = template_map.as_template_dict(page_content)
        if self.debug:
            print(dict_result)

        # Test SiDIF conversion
        sidif_result = template_map.convert_template(page_content, "sidif")
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
            '"weimarTH1851" is des of AddressBook1',
        ]

        if self.debug:
            print("SiDIF Conversion Result:")
            print(sidif_result)
            print("\nExpected SiDIF Result:")
            print("\n".join(expected_sidif_lines))

        for line in expected_sidif_lines:
            self.assertIn(
                line, sidif_result, f"Expected line not found in SiDIF result: {line}"
            )

        # Test markup conversion
        markup_result = template_map.convert_template(page_content, "markup")
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
            "}}",
        ]

        if self.debug:
            print("\nMarkup Conversion Result:")
            print(markup_result)
            print("\nExpected Markup Result:")
            print("\n".join(expected_markup_lines))

        for line in expected_markup_lines:
            self.assertIn(
                line, markup_result, f"Expected line not found in markup result: {line}"
            )

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
