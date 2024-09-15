"""
Created on 15.09.2024

@author: wf
"""

import os


class GenWikiPaths:
    @classmethod
    def get_examples_path(cls) -> str:
        # the root directory (default: examples)
        path = os.path.join(os.path.dirname(__file__), "../genwiki_examples")
        path = os.path.abspath(path)
        return path
