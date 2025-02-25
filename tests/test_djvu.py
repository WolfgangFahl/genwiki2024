"""
Created on 2025-02-24

@author: wf
"""

import json
import os
import time
from dataclasses import asdict

import djvu.decode
from ngwidgets.basetest import Basetest
from tqdm import tqdm

from genwiki.djvu_core import DjVu, DjVuPage
from genwiki.djvu_manager import DjVuManager
from genwiki.djvu_processor import DjVuProcessor
from genwiki.download import Download


class TestDjVu(Basetest):
    """
    Test djvu handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        current_folder = os.path.dirname(__file__)
        self.genwiki_examples_folder = os.path.join(
            current_folder, "..", "genwiki_examples"
        )
        self.basepath = "/Users/wf/hd/wf-fur.bitplan.com/genwiki"
        self.baseurl = "https://wiki.genealogy.net/"
        self.limit = 10000000
        # self.limit=50
        self.local = True
        if not os.path.isdir(self.basepath):
            self.local = False
            self.basepath = "/tmp/genwiki/image"
            self.limit = 50

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
        for relurl in [
            "/images/9/96/Elberfeld-AB-1896-97-Stadtplan.djvu",
            "/images/9/96/vz1890-neuenhausen-zb04.djvu",
            "/images/0/08/Deutsches-Kirchliches-AB-1927.djvu",
        ]:
            djvu_path = self.get_djvu(relurl)
            url = djvu.decode.FileURI(djvu_path)
            # url=f"{baseurl}/{relurl}"
            dproc = DjVuProcessor()
            print(f"processing {url}")
            document = dproc.new_document(url)
            document.decoding_job.wait()
            print(len(document.files))
        pass

    def add_page(self, page_lod, path: str, page_index: int, page):
        """
        Adds a DjVuPage to the given list of pages.

        Args:
            page_lod (list): List to which the page dictionary is appended.
            path (str): Path to the DjVu file.
            page_index (int): Index of the page.
            page: Page object containing metadata.

        Returns:
            DjVuPage: The created DjVuPage instance.
        """
        try:
            filename = page.file.name
            if "gesperrtes" in filename:
                filename = "?"
                valid = False
            else:
                valid = True
        except Exception as _ex:
            filename = "?"
            valid = False
        dpage = DjVuPage(
            # height=page.height,
            # width=page.width,
            # dpi=page.dpi,
            path=filename,
            page_index=page_index,
            valid=valid,
            djvu_path=path,
        )
        row = asdict(dpage)
        page_lod.append(row)
        return dpage

    def test_all_djvu(self):
        """
        test all djvu pages
        """
        dvm = DjVuManager()
        dvm_target = DjVuManager(db_path="/tmp/genwiki_djvu.db")
        dproc = DjVuProcessor()
        lod = dvm.query("all_djvu")
        total = 0
        start_time = time.time()
        debug = self.debug
        debug = False
        errors = 0
        djvu_lod = []
        page_lod = []
        for index, r in enumerate(lod, start=1):
            path = r.get("path").replace("./", "/")
            djvu_path = self.get_djvu(path)
            if not djvu_path:
                errors += 1
                continue
            page_index = 0
            for document, page in dproc.yield_pages(djvu_path):
                page_count = len(document.pages)
                page_index += 1
                dpage = self.add_page(page_lod, path, page_index, page)
                # if debug:
                #    print(f"    {page_index:4d}/{page_count:4d}:{filename}")
            djvu = DjVu(path=path, page_count=page_count)
            djvu_row = asdict(djvu)
            djvu_lod.append(djvu_row)
            total += page_index
            if total > self.limit:
                break
            elapsed = time.time() - start_time
            pages_per_sec = total / elapsed if elapsed > 0 else 0
            print(
                f"{index:4d} {page_count:4d} {total:7d} {pages_per_sec:7.0f} pages/s: {path}"
            )
        expected_errors = 0 if self.local else 2
        self.assertTrue(errors <= expected_errors)
        dvm_target.store(lod=page_lod, entity_name="Page", primary_key="page_key")
        dvm_target.store(lod=djvu_lod, entity_name="DjVu", primary_key="path")

    def test_issue49(self):
        """
        Test loading DjVu file with python-djvu and storing relevant metadata.
        """
        output_dir = "/tmp/djvu_pngs"
        os.makedirs(output_dir, exist_ok=True)
        for url, page_count in [
            # ("./images/9/96/Elberfeld-AB-1896-97-Stadtplan.djvu", 1),
            #("./images/0/08/Deutsches-Kirchliches-AB-1927.djvu", 1188),
            ("/images/9/96/vz1890-neuenhausen-zb04.djvu", 3)
        ]:
            with self.subTest(url=url, expected_pages=page_count):
                if not self.local and page_count > 1:
                    return
                relurl = url.lstrip(".")
                djvu_path = self.get_djvu(relurl)
                dproc = DjVuProcessor()
                if self.debug:
                    print(f"processing {relurl}")
                #for document, page in dproc.yield_pages(djvu_path):
                #    pass
                for image_job in dproc.process(djvu_path, relurl=relurl):
                    image = image_job.image
                    output_prefix = os.path.splitext(os.path.basename(djvu_path))[0]
                    output_path = os.path.join(
                        output_dir,
                        f"{output_prefix}_page_{image.page_index:04d}.png",
                    )
                    dproc.save_image_to_png(
                        image_job=image_job, output_path=output_path
                    )

    def testDjVuManager(self):
        """
        test the DjVu Manager
        """
        dvm = DjVuManager()
        lod = dvm.query("total")
        if self.debug:
            print(json.dumps(lod, indent=2))
        self.assertEqual(lod, [{"files": 4288, "pages": 1028225}])
