'''
Created on 2024-09-12

@author: wf
'''
from lodstorage.query import QueryManager, Query
class MultiLanguageQueryManager():
    """
    Query manager for multiple languages
    """
    def __init__(self,yaml_path:str,languages:list=["sql","sparql","ask"],debug:bool=False):
        self.languages=languages
        self.debug=debug
        self.qms={}
        for lang in languages:
            qm = QueryManager(
                lang=lang, queriesPath=yaml_path, with_default=False, debug=self.debug
            )
            self.qms[lang]=qm

        self.query_names=[]
        for qm in self.qms.values():
            self.query_names.extend(list(qm.queriesByName.keys()))

    def query4Name(self,name:str)->Query:
        result=None
        for qm in self.qms.values():
            if name in qm.queriesByName:
                result=qm.queriesByName[name]
                break
        return result