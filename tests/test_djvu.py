"""
Created on 2025-02-24

@author: wf
"""

import argparse
import json
import os

import djvu.decode
from ngwidgets.basetest import Basetest

from genwiki.djvu_cmd import DjVuCmd
from genwiki.djvu_manager import DjVuManager
from genwiki.djvu_processor import DjVuProcessor
from genwiki.download import Download


class TestDjVu(Basetest):
    """
    Test djvu handling
    """

    def setUp(self, debug=True, profile=True):

        Basetest.setUp(self, debug=debug, profile=profile)
        self.basepath = DjVuCmd.default_base_path
        self.output_dir = os.path.join(self.basepath, "djvu_images")
        self.baseurl = "https://wiki.genealogy.net/"
        self.limit = 10000000
        # self.limit=50
        self.local = True
        if not os.path.isdir(self.basepath):
            self.local = False
            self.basepath = "/tmp/genwiki/images"
            self.output_dir = "/tmp/genwiki/djvu_images"
            self.limit = 50
        os.makedirs(self.output_dir, exist_ok=True)

    def get_djvu(self, relurl):
        """
        get the djvu file for the relative url
        """
        djvu_path = self.basepath + relurl
        url = self.baseurl + relurl
        if not self.local:
            try:
                Download.download(url, djvu_path)
            except Exception as _ex:
                print(f"invalid {djvu_path}")
                return None
        self.assertTrue(os.path.isfile(djvu_path), djvu_path)
        return djvu_path

    def test_djvu_processor(self):
        """
        test the DjVu processor
        """
        for relurl,elen in [
            ("/images/2/2f/Sorau-AB-1913.djvu",255),
            ("/images/9/96/Elberfeld-AB-1896-97-Stadtplan.djvu",1),
            ("/images/9/96/vz1890-neuenhausen-zb04.djvu",3),
            ("/images/0/08/Deutsches-Kirchliches-AB-1927.djvu",1188)
        ]:
            djvu_path = self.get_djvu(relurl)
            url = djvu.decode.FileURI(djvu_path)
            # url=f"{baseurl}/{relurl}"
            dproc = DjVuProcessor()
            if self.debug:
                print(f"processing {url}")
            document = dproc.context.new_document(url)
            document.decoding_job.wait()
            if self.debug:
                page_count=len(document.files)
                print(f"{page_count} pages")
            self.assertEqual(elen,page_count)
        pass

    def test_all_djvu(self):
        """
        test all djvu pages
        """
        if self.inPublicCI():
            return
        args = argparse.Namespace(
            command="catalog",
            db_path="/tmp/test_genwiki_djvu.db",
            base_path=DjVuCmd.default_base_path,
            limit=10000000,
            sort="asc",
            force=False,
            output_path=self.output_dir,
            parallel=False,
            debug=True,
            verbose=False,
            serial=False
        )
        djvu_cmd = DjVuCmd(args=args)
        djvu_cmd.handle_args()
        expected_errors = 0 if self.local else 2
        self.assertTrue(djvu_cmd.errors <= expected_errors)

    def test_convert(self):
        """
        test the conversion
        """
        args = argparse.Namespace(
            command="convert",
            db_path="/tmp/test_genwiki_djvu.db",
            base_path=self.basepath,
            limit=50,
            force=True,
            sort="asc",
            output_path=self.output_dir,
            parallel=True,
            url="/images/2/2f/Sorau-AB-1913.djvu",
            #url="/images/9/96/vz1890-neuenhausen-zb04.djvu",
            debug=True,
            serial=False,
            verbose=True,
        )
        djvu_cmd = DjVuCmd(args=args)
        djvu_cmd.handle_args()

    def test_issue49(self):
        """
        Test loading DjVu file with python-djvu and storing relevant metadata.
        """
        output_dir = "/tmp/djvu_pngs"
        os.makedirs(output_dir, exist_ok=True)
        for url, page_count in [
            ("/images/9/96/vz1890-neuenhausen-zb04.djvu", 3),
            ("./images/f/fc/Siegkreis-AB-1905-06_Honnef.djvu", 35),
            # ("./images/9/96/Elberfeld-AB-1896-97-Stadtplan.djvu", 1),
            # ("./images/0/08/Deutsches-Kirchliches-AB-1927.djvu", 1188),
        ]:
            with self.subTest(url=url, expected_pages=page_count):
                if not self.local and page_count > 1:
                    return
                relurl = url.lstrip(".")
                djvu_path = self.get_djvu(relurl)
                dproc = DjVuProcessor()
                if self.debug:
                    print(f"processing {relurl}")
                # for document, page in dproc.yield_pages(djvu_path):
                #    pass
                count = 0
                for _image_job in dproc.process_parallel(
                    djvu_path, relurl=relurl, save_png=True, output_path=output_dir
                ):
                    count += 1

                if self.debug:
                    print(f"Processed {count} pages")

    def testDjVuManager(self):
        """
        test the DjVu Manager
        """
        dvm = DjVuManager()
        lod = dvm.query("total")
        if self.debug:
            print(json.dumps(lod, indent=2))
        self.assertEqual(lod, [{"files": 4288, "pages": 1028225}])
