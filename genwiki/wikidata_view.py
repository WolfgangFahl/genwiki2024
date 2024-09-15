"""
Created on 14.09.2024

@author: wf
"""

from nicegui import ui
import re
from genwiki.multilang_querymanager import MultiLanguageQueryManager
from genwiki.wiki import Wiki
from lodstorage.sparql import SPARQL

class WikidataItemView:
    """
    show a wikidata item
    """

    def __init__(self, solution, mlqm: MultiLanguageQueryManager, qid: str):
        self.solution = solution
        self.mlqm = mlqm

        self.qid = self.unprefix(qid)
        self.item_query=self.mlqm.query4Name("WikidataItemNameAndCoordinates")

    def unprefix(self,qid:str):
        item_prefix="http://www.wikidata.org/entity/"
        if qid.startswith(item_prefix):
            qid=qid.replace(item_prefix, "")
        return qid

    def convert_point_to_latlon(self,point_str:str):
        # Define the pattern to match the "Point(x y)" format
        pattern = r"Point\(([-\d.]+)\s+([-\d.]+)\)"

        # Define the replacement pattern
        replacement = r"\1°, \2°"

        # Use re.sub to replace the match
        return re.sub(pattern, replacement, point_str)

    def setup_ui(self):
        """
        setup the user interface
        """
        ui.label(self.qid)
        query=self.item_query
        query.params.params_dict["item"]=self.qid
        query.endpoint = "https://query.wikidata.org/sparql"
        endpoint = SPARQL(query.endpoint)
        qlod = endpoint.queryAsListOfDicts(
                query.query, param_dict=query.params.params_dict
        )
        if len(qlod)==1:
            record=qlod[0]
            wikidataid=record["item"]
            wikidataid=self.unprefix(wikidataid)
            if "coordinates" in record:
                point_str=record["coordinates"]
                latlon=self.convert_point_to_latlon(point_str)
                coord=f"\n|coordinates={latlon}"
            else:
                coord=""
                pass
            # convert to -32.715°, -77.03201°
            wiki_markup=f"""{{{{Location
|name={record["itemLabel"]}
|wikidataid={wikidataid}{coord}
}}}}"""
            html_markup=f"<pre>{wiki_markup}</pre>"
            ui.html(html_markup)
        else:
            ui.notify(f"Could not retrieve details for {self.qid}")
        pass

