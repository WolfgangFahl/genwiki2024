"""
Created on 2024-08-15

@author: wf
"""

import logging
import os
from typing import Callable, Dict

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

    def backup(self, ask_query: str):
        """
        backup the pages for the given query
        """
        page_lod = self.wiki_push.queryPages(ask_query)
        page_titles = list(page_lod.keys())
        self.wiki_push.backup(pageTitles=page_titles, backupPath=self.wiki_backup_dir)

    def process_all_wiki_files(self, callback: Callable[[str], None] = None):
        """
        Recursively loop over all .wiki files in the backup directory and process them using the provided callback.

        Args:
            callback (Callable[[str], None], optional): A function to call for each .wiki file found.
                                                        Defaults to reading the file content.
        Raises:
            ValueError: If the backup directory does not exist.
        """
        if callback is None:
            callback = self.read_file_content

        if os.path.isdir(self.wiki_backup_dir):
            for root, _dirs, files in os.walk(self.wiki_backup_dir):
                for file_name in files:
                    if file_name.endswith(".wiki"):
                        file_path = os.path.join(root, file_name)
                        self.log(f"Processing file: {file_path}", logging.DEBUG)
                        callback(file_path)
        else:
            err_msg = f"Directory {self.wiki_backup_dir} does not exist."
            self.log(err_msg, logging.ERROR)
            raise ValueError(err_msg)

    def get_all_content(self) -> Dict[str, str]:
        """
        Gather the content of all .wiki files in the backup directory.

        Returns:
            Dict[str, str]: A dictionary where keys are file paths and values are the content of the .wiki files.
        """
        content_dict = {}

        def add_content(file_path: str):
            content_dict[file_path] = self.read_file_content(file_path)

        self.process_all_wiki_files(callback=add_content)
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
        
