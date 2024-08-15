"""
Created on 2024-08-15

@author: wf
"""

import os

from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.webserver import WebserverConfig
from nicegui import Client, app, ui

from genwiki.version import Version


class GenWikiWebServer(InputWebserver):
    """WebServer class that manages the server and handles Sprinkler operations."""

    @classmethod
    def get_config(cls) -> WebserverConfig:
        copy_right = "(c)2024 Wolfgang Fahl"
        config = WebserverConfig(
            copy_right=copy_right,
            version=Version(),
            default_port=9852,
            short_name="genwiki2024",
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = GenWikiSolution
        return server_config

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=GenWikiWebServer.get_config())
        self.simulation = None


class GenWikiSolution(InputWebSolution):
    """
    the NiceSprinkler solution
    """

    def __init__(self, webserver: GenWikiWebServer, client: Client):
        """
        Initialize the solution

        Args:
            webserver (GenWikiWebServer): The webserver instance associated with this solution.
            client (Client): The client instance this context is associated with.
        """
        super().__init__(webserver, client)
