"""
MediaWiki Tag Analyzer

Created on 2025-04-13

@author: wf
"""
import os
from collections import Counter
import re
from dataclasses import dataclass,field
from wikibot3rd.wikiclient import WikiClient
#import mwparserfromhell
from lodstorage.sql import SQLDB
from lodstorage.mysql import MySqlQuery
from lodstorage.query import Endpoint
from tqdm import tqdm

@dataclass
class WikiPage:
    page_id: int
    title: str
    text: str
    timestamp: str
    parse_items:list =field(default_factory=list)
    page_index:int=0

    def add_parse_item(self, kind: str, name: str, count: int = None):
        self.page_index += 1
        pi = {
            "page_key":f"{self.page_id}:{self.page_index}",
            "page_id": self.page_id,
            "page_index": self.page_index,
            "kind": kind,
            "name": name,
            "count": count
        }
        self.parse_items.append(pi)

    def add_parser_counter(self, counter: Counter, kind: str):
        """Add items from a counter to parse_items with sequential indices"""
        for name, count in counter.items():
            self.add_parse_item(kind=kind, name=name, count=count)

    def parse(self):
        # Create local counters for tracking occurrences
        template_counter = Counter()
        category_counter = Counter()
        tag_counter = Counter()

        # Extract templates using regex
        template_pattern = re.compile(r'{{([^|{}]+)')
        for match in template_pattern.finditer(self.text):
            template_name = match.group(1).strip()
            template_counter[template_name] += 1

        # Extract categories using regex
        for prefix in ["Category", "Kategorie"]:
            category_pattern = re.compile(r'\[\[' + prefix + r':([^\]|]+)')
            for match in category_pattern.finditer(self.text):
                category_name = match.group(1).strip()
                category_counter[category_name] += 1

        # Extract HTML tags using regex
        tag_pattern = re.compile(r'<([a-zA-Z0-9]+)[^>]*>')
        for match in tag_pattern.finditer(self.text):
            tag_name = match.group(1).lower()
            tag_counter[tag_name] += 1

        # Add all counter items to parse_items
        self.add_parser_counter(template_counter, "template")
        self.add_parser_counter(category_counter, "category")
        self.add_parser_counter(tag_counter, "tag")

class TagAnalyzer:
    """
    Analyzes mediawiki markup tag usage in MediaWiki pages
    """

    def __init__(self, wiki_id: str,endpoint:Endpoint=None):
        """
        Initialize with wiki ID and optional and endpoint_conf
        """
        self.client = WikiClient.of_wiki_id(wiki_id)
        self.endpoint=endpoint
        self.mysql=None
        if endpoint:
            self.mysql=MySqlQuery(endpoint=self.endpoint)
        sqldb_path=os.path.expanduser("~/.genwiki/parse_items.db")
        self.sqldb=SQLDB(sqldb_path)

    def parse_pages(self,page_generator):
        """
        parse all pages for the given page generator
        """
        self.page_index=0
        if self.client.needs_login():
            self.client.login()
        statistics = self.client.get_site_statistics()
        self.page_count=statistics["pages"]
        pbar = tqdm(total=self.page_count, desc="Parsing pages")
        records=0
        created=False
        for wiki_page in page_generator():
            self.analyze_page(wiki_page)
            parse_count=len(wiki_page.parse_items)
            records+=parse_count
            if parse_count>0:
                if not created:
                    entityInfo=self.sqldb.createTable(
                        wiki_page.parse_items,
                        "pageparse", "page_key",
                        withCreate=True, withDrop=True)
                    created=True
                self.sqldb.store(wiki_page.parse_items, entityInfo, executeMany=True, fixNone=False, replace=False)
            pbar.update(1)
        pbar.close()
        print(f"created {records} parse_items")

    def analyze_page(self,wiki_page):
        self.page_index+=1
        wiki_page.parse()
