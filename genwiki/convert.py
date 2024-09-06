'''
Created on 26.08.2024

@author: wf
'''
import os
from genwiki.parquet import Parquet
from lodstorage.sql import SQLDB

class ParquetAdressbokToSql():
    """
    convert parquet Addressbook files to Sql
    """
    def __init__(self,folder:str,column_mapping:dict=None,table_name:str="address",debug:bool=False):
        self.parquet_handler = Parquet(debug=debug)
        if not os.path.exists(folder):
            raise ValueError(f"Invalid folder {folder}")
        self.folder=folder
        self.table_name=table_name
        if column_mapping is None:
            column_mapping = {
                "id": "id",
                "page": "page",
                "lastname": "lastname",
                "firstname": "firstname",
                "Beruf o. ä.": "occupation",
                "Straße": "street",
                "Ortsname": "location",
                "Ortskennung": "location_code",
                "abw./zus. Ortsangabe": "location_extra",
                "Firmenname": "company_name",
                "Familienstand": "marital_status",
                "Vorname Bezugsperson": "reference_person_firstname",
                "Beruf Bezugsperson": "reference_person_occupation",
                "Eigentümer": "owner",
                "Funktionsträger": "official",
                "abweichender Wohnort": "alternate_residence",
                "Bezirk": "district",
                "source": "source",
                "jahr": "year"
            }
        self.year_mapping = {
            "weimarTH1851.parquet": 1851,
            "weimarTH1853.parquet": 1853
        }
        self.column_mapping=column_mapping

    def inject_year(self):
        # Add year to each row based on the year_mapping
        for _table_name, rows in self.parquet_data.items():
            for row in rows:
                source = row.get('source')
                if source in self.year_mapping:
                    row['jahr'] = self.year_mapping[source]
                else:
                    print(f"Warning: No year mapping found for source {source}")

    def read(self):
        # Read all parquet files
        self.parquet_data = self.parquet_handler.read_parquet_files(self.folder)
        return self.parquet_data

    def convert(self,db:SQLDB):
        # Convert to SQLite with the correct table name and column mapping
        self.parquet_handler.convert_parquet_to_sqlite(self.parquet_data, db=db, table_name=self.table_name, column_mapping=self.column_mapping)

    def to_db(self,db:SQLDB):
        self.read()
        self.inject_year()
        self.convert(db)