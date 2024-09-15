"""
Created on 26.08.2024

@author: wf
"""

from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB
from ngwidgets.lod_grid import ListOfDictsGrid
from ngwidgets.widgets import Link
from nicegui import background_tasks, run, ui
from nicegui.events import ValueChangeEventArguments

from genwiki.multilang_querymanager import MultiLanguageQueryManager
from genwiki.params_view import ParamsView
from genwiki.wiki import Wiki
from genwiki.wikidata import Wikidata


class QueryView:
    """
    simplified version of the snapquery version snapquery_view
    """

    def __init__(
        self, solution, mlqm: MultiLanguageQueryManager, sql_db: SQLDB, wiki: Wiki
    ):
        self.solution = solution
        self.mlqm = mlqm
        self.wiki = wiki
        self.sql_db = sql_db
        self.load_task = None
        self.timeout = 5.0
        self.params_view = None

    def setup_ui(self):
        """
        setup the user interface
        """
        self.query_name = "Gesamtanzahl"
        with ui.row() as self.query_row:
            self.query_select = self.solution.add_select(
                "Abfrage",
                self.mlqm.query_names,
                on_change=self.on_update_query,
            ).bind_value(self, "query_name")
            self.refresh_button = ui.button(
                icon="refresh",
                on_click=self.on_update_query,
            ).tooltip("Parameter-Ansicht aktualisieren")
            self.quer_button = ui.button(
                icon="play_circle",
                on_click=self.run_query,
            ).tooltip("ausführen")
        with ui.row() as self.params_row:
            pass
        self.grid_row = ui.row()
        pass

    async def on_update_query(self, _vcae: ValueChangeEventArguments):
        """
        react on a changed query
        """
        self.query = self.mlqm.query4Name(self.query_name)
        if self.params_view:
            self.params_view.delete()
        if self.query.params.has_params:
            self.query.set_default_params(self.query.params.params_dict)
            self.params_view = ParamsView(
                solution=self.solution, params=self.query.params
            )
            self.params_view.setup()
            self.params_view.open()
        self.params_row.update()

    def get_query_lod(self):
        """
        run the query
        """
        query = self.query
        if query.lang == "sql":
            qlod = self.sql_db.query(query.query)
        elif query.lang == "sparql":
            sparql = Wikidata.get_sparql()
            qlod = sparql.queryAsListOfDicts(
                query.query, param_dict=query.params.params_dict
            )
        elif query.lang == "ask":
            qlod = self.wiki.query_as_list_of_dicts(query.query)
        else:
            raise ValueError(f"query language {query.lang} not supported")
        return qlod

    async def load_query_results(self):
        """
        (re) load the query results
        """
        try:
            if self.query.params.has_params:
                self.query.query = self.query.params.apply_parameters()
                self.params_view.close()
            lod = await run.io_bound(self.get_query_lod)
            if not lod:
                with self.solution.container:
                    ui.notify("query execution failure")
                return
            self.grid_row.clear()
            with self.query_row:
                record_count = len(lod) if lod is not None else 0
                # markup = f'<span style="color: green;">{record_count} records in {stats.duration:.2f} secs</span>'
            # tablefmt = "html"
            # self.query.preFormatWithCallBacks(lod, tablefmt=tablefmt)
            # self.query.formatWithValueFormatters(lod, tablefmt=tablefmt)
            for record in lod:
                for key, value in record.items():
                    if isinstance(value, str):
                        if value.startswith("http"):
                            record[key] = Link.create(value, value)
            with self.grid_row:
                self.lod_grid = ListOfDictsGrid()
                self.lod_grid.load_lod(lod)
            self.grid_row.update()
        except Exception as ex:
            self.solution.handle_exception(ex)

    async def run_query(self, _args):
        """
        run the current query
        """

        def cancel_running():
            if self.load_task:
                self.load_task.cancel()

        self.grid_row.clear()
        with self.grid_row:
            ui.spinner()
        self.grid_row.update()
        # cancel task still running
        cancel_running()
        # cancel task if it takes too long
        ui.timer(self.timeout, lambda: cancel_running(), once=True)
        # run task in background
        self.load_task = background_tasks.create(self.load_query_results())
