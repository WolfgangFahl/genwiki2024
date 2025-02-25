"""
Created on 2025-02-24

@author: wf
"""

import json
import os
import time
import djvu.decode
from ngwidgets.basetest import Basetest
from genwiki.download import Download
from genwiki.djvu_manager import DjVuManager
from genwiki.djvu_processor import DjVuProcessor


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
        self.basepath="/Users/wf/hd/wf-fur.bitplan.com/genwik"
        self.baseurl="https://wiki.genealogy.net/"
        self.limit=10000000
        self.local=True
        if not os.path.isdir(self.basepath):
            self.local=False
            self.basepath="/tmp/genwiki/image"
            self.limit=50

    def test_djvu_processor(self):
        """
        test the DjVu processor
        """
        for relurl in [
            "/images/9/96/Elberfeld-AB-1896-97-Stadtplan.djvu",
            "/images/9/96/vz1890-neuenhausen-zb04.djvu",
            "/images/0/08/Deutsches-Kirchliches-AB-1927.djvu"
        ]:
            djvu_path=self.basepath+relurl
            url=self.baseurl+relurl
            if not self.local:
                Download.download(url, djvu_path)
            self.assertTrue(os.path.isfile(djvu_path))
            url=djvu.decode.FileURI(djvu_path)
            #url=f"{baseurl}/{relurl}"
            dproc=DjVuProcessor()
            print(f"processing {url}")
            document = dproc.new_document(url)
            document.decoding_job.wait()
            print(len(document.files))
        pass


    def test_all_djvu(self):
        """
        test all djvu pages
        """
        dvm = DjVuManager()
        dproc = DjVuProcessor()
        lod = dvm.query("all_djvu")
        total = 0
        start_time = time.time()
        debug=self.debug
        debug=False
        errors=0
        for index,r in enumerate(lod,start=1):
            path = r.get("path").replace("./", "/")
            djvu_path = self.basepath + path
            url=self.baseurl+path
            if not self.local:
                try:
                    Download.download(url, djvu_path)
                except Exception as ex:
                    print(f"invalid {djvu_path}")
                    errors+=1
                    continue
            page_index=0
            for document,page in dproc.yield_pages(djvu_path):
                page_count=len(document.pages)
                page_index+=1
                try:
                    filename=page.file.name
                except Exception as _ex:
                    filename="?"
                if debug:
                    print(f"    {page_index:4d}/{page_count:4d}:{filename}")
            total += page_index
            if total>self.limit:
                break
            elapsed = time.time() - start_time
            pages_per_sec = total / elapsed if elapsed > 0 else 0
            print(f"{index:4d} {page_count:4d} {total:7d} {pages_per_sec:7.0f} pages/s: {path}")
        print(errors)


    def test_issue49(self):
        """
        Test loading DjVu file with python-djvu and storing relevant metadata.
        """
        cachedir="/tmp/images"
        for image_url, page_count in [
            ("./images/9/96/Elberfeld-AB-1896-97-Stadtplan.djvu", 1),
            ("./images/0/08/Deutsches-Kirchliches-AB-1927.djvu", 1188)
        ]:
            with self.subTest(image_url=image_url, expected_pages=page_count):
                filename = os.path.basename(image_url)
                relurl = os.path.dirname(image_url).lstrip("./")
                url = f"https://wiki.genealogy.net/{relurl}/{filename}"
                target_path = f"{cachedir}/{relurl}/{filename}"
                Download.download(url, target_path)
                dproc=DjVuProcessor()
                for document, page in dproc.yield_pages(target_path):
                    pass
                for imagejob in dproc.process(target_path):
                    pass

    def testDjVuManager(self):
        """
        test the DjVu Manager
        """
        dvm = DjVuManager()
        lod = dvm.query("total")
        if self.debug:
            print(json.dumps(lod, indent=2))
        self.assertEqual(lod,[
  {
    "files": 4288,
    "pages": 1028225
  }
])
