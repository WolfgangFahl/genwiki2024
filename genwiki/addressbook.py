'''
Created on 19.08.2024

@author: wf
'''
from genwiki.template import TemplateMap, TemplateParam

class AddressBookConverter:
    """
    convert Adressbook pages
    """
    def __init__(self):
        self.template_map= TemplateMap(
            template_name="Info Adressbuch",
            topic_name="AddressBook",
            param_mapping={
                'Bild': TemplateParam(new_name='image'),
                'Titel': TemplateParam(new_name='title'),
                'Untertitel': TemplateParam(new_name='subtitle'),
                'Autor / Hrsg.': TemplateParam(new_name='author'),
                'Erscheinungsjahr': TemplateParam(new_name='year', to_int=True),
                'Seitenzahl': TemplateParam(new_name='pageCount', to_int=True),
                'Enthaltene Orte': TemplateParam(new_name='location', regex=r'\[\[GOV:(.*?)\|'),
                'Verlag': TemplateParam(new_name='publisher'),
                'GOV-Quelle': TemplateParam(new_name='govSource'),
                'Standort online': TemplateParam(new_name='onlineSource', regex=r'\{\{ThULB\|(.*?)\}\}'),
                'DES': TemplateParam(new_name='des')
            }
        )
        