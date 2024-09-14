"""
Created on 2024-08-15

@author: wf
"""

import logging
import os
from typing import Any, Dict, Generator, List, Tuple

from wikibot3rd.wikipush import WikiPush


class Wiki:
    """
    Access to a Mediawiki.

    Attributes:
        wiki_id (str): The ID of the wiki to access.
        wiki_backup_dir (str): The directory where the backup files are stored.
        debug (bool): Indicates if debugging is enabled.
    """

    def __init__(self, wiki_id: str, backup_dir: str = None, debug: bool = False):
        """
        Initialize the Wiki object.

        Args:
            wiki_id (str): The ID of the wiki to access.
            backup_dir(str): the backup directory to use
            debug (bool): If True, enable debug logging.
        """
        self.wiki_id = wiki_id
        self.wiki_push = WikiPush(fromWikiId=wiki_id, debug=debug)
        self.debug = debug
        if backup_dir is None:
            backup_dir = os.path.expanduser(f"~/wikibackup/{self.wiki_id}")
        self.wiki_backup_dir = backup_dir

        # Set up logging
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def log(self, message: str, level: int = logging.INFO):
        """
        Log a message based on the debug setting.

        Args:
            message (str): The message to log.
            level (int): The logging level, default is INFO.
        """
        if self.debug:
            logging.log(level, message)
        else:
            logging.log(logging.DEBUG, message)

    def query_as_dict_of_dicts(self,ask_query:str)->Dict[str,Dict[str,Any]]:
        """
        run the given SMW ask query against my wiki
        """
        qdict=self.wiki_push.queryPages(askQuery=ask_query)
        return qdict

    def query_as_list_of_dicts(self,ask_query:str)->List[Dict[str,Any]]:
        qdict=self.query_as_dict_of_dicts(ask_query)
        qlod=list(qdict.values())
        return qlod

    def backup(self, ask_query: str):
        """
        backup the pages for the given query
        """
        page_lod = self.wiki_push.queryPages(ask_query)
        page_titles = list(page_lod.keys())
        self.wiki_push.backup(pageTitles=page_titles, backupPath=self.wiki_backup_dir)

    def get_all_wiki_files(self) -> Generator[Tuple[str, str], None, None]:
        """
        Generator that yields tuples of (file_path, page_name)
        for all .wiki files in the backup directory.
        """
        if not os.path.isdir(self.wiki_backup_dir):
            err_msg = f"Directory {self.wiki_backup_dir} does not exist."
            self.log(err_msg, logging.ERROR)
            raise ValueError(err_msg)

        for root, _, files in os.walk(self.wiki_backup_dir):
            for file_name in files:
                if file_name.endswith(".wiki"):
                    file_path = os.path.join(root, file_name)
                    page_name = file_name[:-5]  # Remove .wiki extension
                    relative_path = os.path.relpath(file_path, self.wiki_backup_dir)
                    page_name = os.path.splitext(relative_path)[
                        0
                    ]  # Remove extension and use relative path
                    self.log(f"Processing file: {file_path}", logging.DEBUG)
                    yield file_path, page_name

    def get_all_content(self) -> Dict[str, str]:
        """
        Gather the content of all .wiki files in the backup directory.

        Returns:
            Dict[str, str]: A dictionary where keys are page names and values are the content of the .wiki files.
        """
        content_dict = {}
        for file_path, page_name in self.get_all_wiki_files():
            content_dict[page_name] = self.read_file_content(file_path)
        return content_dict

    def read_file_content(self, file_path: str) -> str:
        """
        Read the content of a .wiki file.

        Args:
            file_path (str): The path to the .wiki file.

        Returns:
            str: The content of the file.
        """
        self.log(f"Attempting to read file: {file_path}", logging.DEBUG)
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            self.log(f"Read content from {file_path}", logging.DEBUG)
            return content
