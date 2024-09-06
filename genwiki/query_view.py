"""
Created on 26.08.2024

@author: wf
"""

from lodstorage.params import Params
from lodstorage.query import QueryManager
from lodstorage.sql import SQLDB
from ngwidgets.lod_grid import ListOfDictsGrid
from ngwidgets.widgets import Link
from nicegui import background_tasks, run, ui
from nicegui.events import ValueChangeEventArguments

from genwiki.params_view import ParamsView


class QueryView:
    """
    simplified version of the snapquery version snapquery_view
    """

    def __init__(self, solution, qm: QueryManager, sql_db: SQLDB):
        self.solution = solution
        self.qm = qm
        self.sql_db = sql_db
        self.load_task = None
        self.timeout = 5.0
        self.params_view=None
        self.params_edit=None

    def setup_ui(self):
        """
        setup the user interface
        """
        self.query_name = "Gesamtanzahl"
        with ui.row() as self.query_row:
            self.query_select = self.solution.add_select(
                "Abfrage",
                list(self.qm.queriesByName.keys()),
                on_change=self.on_update_query,
            ).bind_value(self, "query_name")
            self.quer_button = ui.button(
                icon="play_circle",
                on_click=self.run_query,
            ).tooltip("ausführen")
        with ui.row() as self.params_row:
            pass
        self.grid_row = ui.row()
        pass

    async def on_update_query(self, _vcae: ValueChangeEventArguments):
        self.query = self.qm.queriesByName[self.query_name]
        self.params = Params(self.query.query)
        if self.params.has_params:
            if self.params_view:
                self.params_view.delete()
            if self.params_edit:
                self.params_edit.delete()
            self.params_row.clear()
            with self.params_row:
                self.params_view = ParamsView(self, self.params)
                self.params_edit = self.params_view.get_dict_edit()
        pass

    def get_query_lod(self):
        lod = self.sql_db.query(self.query.query)
        return lod

    async def load_query_results(self):
        """
        (re) load the query results
        """
        try:
            if self.params.has_params:
                self.query.query = self.params.apply_parameters()
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
