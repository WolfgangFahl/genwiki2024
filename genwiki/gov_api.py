"""
Created on 25.08.2024

@author: wf
"""
import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import requests


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


class GOV_API:
    """
    Access to Webservice https://wiki.genealogy.net/GOV/Webservice
    with local caching
    """

    def __init__(self):
        self.url = "https://gov.genealogy.net/api/getObject"
        self.cache_dir = os.path.expanduser("~/.govapi")
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_cache_path(self, gov_id: str) -> str:
        return os.path.join(self.cache_dir, f"{gov_id}.json")

    def get_from_cache(self, gov_id: str) -> Optional[dict]:
        cache_path = self.get_cache_path(gov_id)
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None

    def save_to_cache(self, gov_id: str, data: dict):
        cache_path = self.get_cache_path(gov_id)
        with open(cache_path, 'w') as f:
            json.dump(data, f)

    def get_raw_gov_object(self, gov_id: str):
        # Check cache first
        cached_data = self.get_from_cache(gov_id)
        if cached_data:
            return cached_data

        # If not in cache, fetch from API
        params = {"itemId": gov_id}
        response = requests.get(self.url, params=params)
        response.raise_for_status()
        data = response.json()

        # Save to cache
        self.save_to_cache(gov_id, data)

        return data

    def get_gov_object(self, gov_id: str) -> GOVObject:
        data = self.get_raw_gov_object(gov_id)
        # Convert lastModification to datetime
        data["lastModification"] = datetime.fromisoformat(
            data["lastModification"].replace("Z", "+00:00")
        )

        # Create GOVObject instance
        gov_object = GOVObject(**data)
        return gov_object
