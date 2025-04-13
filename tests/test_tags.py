"""
Created on 2025-04-13

@author: wf
"""
import os
from genwiki.tagana import TagAnalyzer, WikiPage
from tests.gbasetest import GenealogyBasetest
from lodstorage.mysql import MySqlQuery
from lodstorage.query import EndpointManager
from genwiki.genwiki_paths import GenWikiPaths
from genwiki.multilang_querymanager import MultiLanguageQueryManager

class TestTags(GenealogyBasetest):
    """
    """

    def setUp(self, debug=False, profile=True):
        GenealogyBasetest.setUp(self, debug=debug, profile=profile)
        endpoint_path = os.path.expanduser("~/.pylodstorage/endpoints.yaml")
        self.endpoints = EndpointManager.getEndpoints(endpoint_path)
        self.wiki_id="genwiki"
        self.endpoint=self.endpoints.get(self.wiki_id)
        self.mysql=None
        if self.endpoint:
            self.mysql=MySqlQuery(endpoint=self.endpoint)
        yaml_path = os.path.join(GenWikiPaths.get_examples_path(), "wiki_queries.yaml")
        self.mlqm = MultiLanguageQueryManager(yaml_path=yaml_path)

    def get_query(self,query_name,param_dict=None):
        query=self.mlqm.query4Name(query_name)
        #print(query)
        if param_dict:
            sql_query=query.params.apply_parameters_with_check(param_dict)
        else:
            sql_query=query.apply_default_params()
        print(sql_query)
        return sql_query

    def testQueries(self):
        """
        test the wiki queries
        """
        if not self.mysql:
            print ("no mysql connection ")
            return

        for qi,query_name in enumerate(self.mlqm.query_names):
            sql_query=self.get_query(query_name)
            index=0
            limit=10
            for record in self.mysql.query_generator(sql_query):
                index+=1
                print(f"{qi}/{index:2}:{record}")
                if index>limit:
                    break

    def testTagAnalyzer(self):
        """
        test the tag analyzer
        """
        def page_generator():
            for record in self.mysql.query_generator(sql_query):
                wiki_page=WikiPage(title=record['old_title'],text=record['old_text'],timestamp=record['old_timestamp'])
                yield wiki_page

        ta = TagAnalyzer(wiki_id=self.wiki_id,endpoint=self.endpoint)
        sql_query=self.get_query("user_content",{"user_id":112275})
        ta.parse_pages(page_generator)
        pass
