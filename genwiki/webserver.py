"""
Created on 2024-08-15

@author: wf
"""

import os

from lodstorage.multilang_querymanager import MultiLanguageQueryManager
from lodstorage.sql import SQLDB
from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.login import Login
from ngwidgets.profiler import Profiler
from ngwidgets.users import Users
from ngwidgets.webserver import WebserverConfig
from ngwidgets.widgets import Link
from nicegui import Client, app, ui
from starlette.responses import FileResponse, HTMLResponse, RedirectResponse
from wd.wditem_search import WikidataItemSearch

from genwiki.convert import ParquetAdressbokToSql
from genwiki.genwiki_paths import GenWikiPaths
from genwiki.gov_query import GovQuery
from genwiki.query_view import QueryView
from genwiki.version import Version
from genwiki.wiki import Wiki
from genwiki.wikidata import Wikidata
from genwiki.wikidata_view import WikidataItemView


class GenWikiWebServer(InputWebserver):
    """WebServer class that manages the server and handles GenWiki operations."""

    @classmethod
    def get_config(cls) -> WebserverConfig:
        copy_right = "(c)2024-2025 Wolfgang Fahl"
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
        path = GenWikiPaths.get_examples_path()
        return path

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=GenWikiWebServer.get_config())
        users = Users(self.config.base_path)
        self.login = Login(self, users)

        address_db_path = os.path.join(self.config.storage_path, "address.db")
        if os.path.isfile(address_db_path) and os.path.getsize(address_db_path) > 0:
            self.sql_db = SQLDB(address_db_path, check_same_thread=False)
        else:
            profiler = Profiler("convert parquet files", profile=True)
            pats = ParquetAdressbokToSql(folder=self.examples_path())
            self.sql_db = SQLDB(address_db_path, check_same_thread=False)
            pats.to_db(self.sql_db)
            profiler.time()

        @ui.page("/")
        async def home(client: Client):
            return await self.page(client, GenWikiSolution.home)

        @ui.page("/gov")
        async def show_gov_query(client: Client):
            return await self.page(client, GenWikiSolution.show_gov_query)

        @ui.page("/wd/{qid}")
        async def wikidata_item(client: Client, qid: str):
            """
            show the wikidata item for the given Wikidata QID
            """
            await self.page(client, GenWikiSolution.wikidata_item, qid)

        @ui.page("/wd")
        async def wikidata(client: Client):
            return await self.page(client, GenWikiSolution.wikidata)

        @ui.page("/login")
        async def login(client: Client):
            return await self.page(client, GenWikiSolution.login_ui)

        @ui.page("/logout")
        async def logout(client: Client) -> RedirectResponse:
            if not client:
                pass
            if self.login.authenticated():
                await self.login.logout()
            return RedirectResponse("/")

    def configure_run(self):
        """
        configure me
        """
        super().configure_run()
        self.url_prefix = self.args.url_prefix
        self.wiki_id = "gensmw"
        self.wiki = Wiki(wiki_id=self.wiki_id, debug=self.args.debug)

        yaml_path = os.path.join(self.examples_path(), "queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)

        # Add GOV query manager
        self.gov_query = GovQuery(debug=self.args.debug)


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
        self.mlqm = webserver.mlqm
        self.gov_query = webserver.gov_query
        self.wiki = webserver.wiki
        self.sql_db = self.webserver.sql_db

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
        with self.header:
            self.link_button("GOV Query", "/gov", "account_tree")
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
            """ """
            self.query_view = QueryView(
                self,
                mlqm=self.mlqm,
                sql_db=self.sql_db,
                wiki=self.wiki,
                sparql=Wikidata.get_sparql(),
            )
            self.query_view.setup_ui()

        await self.setup_content_div(setup_home)

    async def show_gov_query(self):
        """
        provide the GOV Named Parameterized Queries page
        """

        def show():
            self.query_view = QueryView(
                self,
                mlqm=self.gov_query.qm,
                sql_db=self.sql_db,
                wiki=self.wiki,
                sparql=self.gov_query.sparql,
                add_prefixes=self.gov_query.add_prefixes,
            )
            self.query_view.setup_ui()

        await self.setup_content_div(show)

    async def wikidata_item(self, qid: str):
        """
        show a wikidata item with the given Wikidata id

        Args:
            qid(str): the Wikidata id of the item to show
        """

        def show():
            self.wdv = WikidataItemView(self, mlqm=self.mlqm, qid=qid)
            self.wdv.setup_ui()

        await self.setup_content_div(show)

    async def wikidata(self):
        """
        provide the location page
        """

        def record_filter(qid: str, record: dict):
            if "label" and "desc" in record:
                text = f"""{record["label"]}({qid})☞{record["desc"]}"""
                wd_link = Link.create(f"/wd/{qid}", text)
                # getting the link to be at second position
                # is a bit tricky
                temp_items = list(record.items())
                # Add the new item in the second position
                temp_items.insert(1, ("wikidata item", wd_link))

                # Clear the original dictionary and update it with the new order of items
                record.clear()
                record.update(temp_items)

        def show():
            self.wd_item_search = WikidataItemSearch(
                self, record_filter=record_filter, lang="de"
            )

        await self.setup_content_div(show)
