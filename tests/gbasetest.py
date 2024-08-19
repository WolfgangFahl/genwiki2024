'''
Created on 2024-08-19

Basetests for Genealogy Wiki
@author: wf
'''
from ngwidgets.basetest import Basetest
import os
from wikibot3rd.wikiuser import WikiUser

class GenealogyBasetest(Basetest):
    
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        
    def get_wiki_user(self, wikiId="or", save=False) -> WikiUser:
        """
        get wiki users for given wikiId
        """
        iniFile = WikiUser.iniFilePath(wikiId)
        wikiUser = None
        if not os.path.isfile(iniFile):
            wikiDict = None
            if wikiId == "cr":
                wikiDict = {
                    "wikiId": wikiId,
                    "email": "noreply@nouser.com",
                    "url": "http://cr.bitplan.com",
                    "scriptPath": "",
                    "version": "MediaWiki 1.35.5",
                }
            elif wikiId == "genealogy":
                wikiDict = {
                    "wikiId": wikiId,
                    "email": "noreply@nouser.com",
                    "url": "https://wiki.genealogy.net",
                    "scriptPath": "/",
                    "version": "MediaWiki 1.35.11",
                }
            elif wikiId == "smwcopy":
                wikiDict = {
                    "wikiId": wikiId,
                    "email": "noreply@nouser.com",
                    "url": "https://smw.bitplan.com/",
                    "scriptPath": "",
                    "version": "MediaWiki 1.35.5",
                }
            if wikiDict is None:
                raise Exception(f"wikiId {wikiId} is not known")
            else:
                wikiUser = WikiUser.ofDict(wikiDict, lenient=True)
                if save:
                    wikiUser.save()
        else:
            wikiUser = WikiUser.ofWikiId(wikiId, lenient=True)
        return wikiUser
