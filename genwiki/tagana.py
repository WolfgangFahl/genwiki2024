#!/usr/bin/env python3
"""
MediaWiki Tag Analyzer

Created on 2025-04-13

@author: wf
"""
import re
from dataclasses import field
from wikibot3rd.wikiclient import WikiClient
#import mwparserfromhell
#from lodstorage.sql import SQLDB
from lodstorage.mysql import MySqlQuery
from lodstorage.query import Endpoint
from lodstorage.yamlable import lod_storable
from tqdm import tqdm
from typing import Dict,List

@lod_storable
class WikiPage:
    title: str
    text: str
    timestamp: str
    templates: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    tags: Dict[str, int] = field(default_factory=dict)

    def parse(self):
        # Extract templates using regex
        template_pattern = re.compile(r'{{([^|{}]+)')
        for match in template_pattern.finditer(self.text):
            template_name = match.group(1).strip()
            self.templates.append(template_name)

        # Extract categories using regex
        for prefix in ["Category", "Kategorie"]:
            category_pattern = re.compile(r'\[\[' + prefix + r':([^\]|]+)')
            for match in category_pattern.finditer(self.text):
                category_name = match.group(1).strip()
                self.categories.append(category_name)

        # Extract HTML tags using regex
        tag_pattern = re.compile(r'<([a-zA-Z0-9]+)[^>]*>')
        for match in tag_pattern.finditer(self.text):
            tag_name = match.group(1).lower()
            self.tags[tag_name] = self.tags.get(tag_name, 0) + 1




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
        #self.sqldb=SQLDB(sqldb_path)

    def parse_pages(self,page_generator):
        self.page_index=0
        if self.client.needs_login():
            self.client.login()
        statistics = self.client.get_site_statistics()
        self.page_count=statistics["pages"]
        pbar = tqdm(total=self.page_count, desc="Parsing pages")
        for wiki_page in page_generator():
            self.analyze_page(wiki_page)
            pbar.update(1)
        pbar.close()

    def analyze_page(self,wiki_page):
        self.page_index+=1
        wiki_page.parse()
