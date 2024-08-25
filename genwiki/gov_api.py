'''
Created on 25.08.2024

@author: wf
'''
import requests
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Position:
    lon: float
    lat: float
    height: int
    type: str

@dataclass
class ExternalReference:
    value: str

@dataclass
class Name:
    lang: str
    value: str

@dataclass
class Type:
    value: str

@dataclass
class Timespan:
    begin: dict
    end: dict

@dataclass
class Source:
    ref: Optional[str] = None
    note: Optional[str] = None

@dataclass
class Population:
    value: str
    timespan: Optional[Timespan] = None
    source: Optional[List[Source]] = None
    year: Optional[int] = None

@dataclass
class PostalCode:
    value: str
    timespan: Optional[Timespan] = None

@dataclass
class MunicipalId:
    value: str

@dataclass
class PartOf:
    ref: str
    timespan: Optional[Timespan] = None
    source: Optional[List[Source]] = None

@dataclass
class GOVObject:
    id: str
    lastModification: datetime
    position: Position
    externalReference: List[ExternalReference]
    name: List[Name]
    type: List[Type]
    population: List[Population]
    postalCode: List[PostalCode]
    municipalId: List[MunicipalId]
    partOf: List[PartOf]

class GOV_API():
    """
    access to Webservice
    https://wiki.genealogy.net/GOV/Webservice
    """

    def __init__(self):
        self.url= f"https://gov.genealogy.net/api/getObject"

    def get_raw_gov_object(self,gov_id: str):

        params = {"itemId": gov_id}
        response = requests.get(self.url, params=params)
        response.raise_for_status()
        data = response.json()
        return data

    def get_gov_object(self,gov_id:str)-> GOVObject:
        data=self.get_raw_gov_object(gov_id)
        # Convert lastModification to datetime
        data['lastModification'] = datetime.fromisoformat(data['lastModification'].replace('Z', '+00:00'))

        # Create GOVObject instance
        gov_object = GOVObject(**data)
        return gov_object

