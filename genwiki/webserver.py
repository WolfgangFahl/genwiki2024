"""
Created on 2024-08-15

@author: wf
"""
import os
from genwiki.convert import ParquetAdressbokToSql

from genwiki.query_view import QueryView
from lodstorage.sql import SQLDB
from lodstorage.query import QueryManager
from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.login import Login
from ngwidgets.users import Users
from ngwidgets.profiler import Profiler
from ngwidgets.webserver import WebserverConfig
from nicegui import Client, ui
from starlette.responses import RedirectResponse

from genwiki.version import Version


class GenWikiWebServer(InputWebserver):
    """WebServer class that manages the server and handles GenWiki operations."""

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

    def examples_path(self) -> str:
        # the root directory (default: examples)
        path = os.path.join(os.path.dirname(__file__), "../genwiki_examples")
        path = os.path.abspath(path)
        return path

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=GenWikiWebServer.get_config())
        users = Users(self.config.base_path)
        self.login = Login(self, users)
        address_db_path=os.path.join(self.config.storage_path,"address.db")
        if os.path.isfile(address_db_path) and os.path.getsize(address_db_path) > 0:
            self.sql_db=SQLDB(address_db_path,check_same_thread=False)
        else:
            profiler = Profiler("convert parquet files", profile=True)
            pats=ParquetAdressbokToSql(folder=self.examples_path())
            self.sql_db=SQLDB(address_db_path)
            pats.to_db(self.sql_db)
            profiler.time()

        yaml_path = os.path.join(self.examples_path(), "queries.yaml")
        self.qm = QueryManager(lang="sql", queriesPath=yaml_path, with_default=False,debug=self.debug)


        @ui.page("/")
        async def home(client: Client):
            return await self.page(client, GenWikiSolution.home)

        @ui.page("/login")
        async def login(client: Client):
            return await self.page(client, GenWikiSolution.login_ui)

        @ui.page("/logout")
        async def logout(client: Client) -> RedirectResponse:
            if self.login.authenticated():
                await self.login.logout()
            return RedirectResponse("/")


class GenWikiSolution(InputWebSolution):
    """
    the GenWiki solution
    """

    def __init__(self, webserver: GenWikiWebServer, client: Client):
        """
        Initialize the solution

        Args:
            webserver (GenWikiWebServer): The webserver instance associated with this solution.
            client (Client): The client instance this context is associated with.
        """
        super().__init__(webserver, client)
        self.qm=self.webserver.qm
        self.sql_db =self.webserver.sql_db

    def authenticated(self) -> bool:
        """
        Check if the user is authenticated.
        Returns:
            True if the user is authenticated, False otherwise.
        """
        return self.webserver.login.authenticated()

    def setup_menu(self, detailed: bool = True):
        """
        setup the menu
        """
        super().setup_menu(detailed=detailed)
        ui.button(icon="menu", on_click=lambda: self.header.toggle())
        with self.header:
            if self.authenticated():
                self.link_button("logout", "/logout", "logout", new_tab=False)
            else:
                self.link_button("login", "/login", "login", new_tab=False)

    async def login_ui(self):
        """
        login ui
        """
        await self.webserver.login.login(self)

    async def home(self):
        """Provide the main content page"""

        def setup_home():
            """
            """
            self.query_view=QueryView(self,qm=self.qm,sql_db=self.sql_db)
            self.query_view.setup_ui()


        await self.setup_content_div(setup_home)
