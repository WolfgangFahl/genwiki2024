"""
Created on 19.08.2024

@author: wf
"""

import logging
import os
from typing import Dict

from genwiki.template import TemplateMap, TemplateParam
from genwiki.locator import Locator

class AddressBookConverter:
    """
    convert Adressbook pages
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.template_map = TemplateMap(
            template_name="Info Adressbuch",
            topic_name="AddressBook",
            param_mapping={
                "Bild": TemplateParam(new_name="image"),
                "Titel": TemplateParam(new_name="title"),
                "Untertitel": TemplateParam(new_name="subtitle"),
                "Autor / Hrsg.": TemplateParam(new_name="author"),
                "Erscheinungsjahr": TemplateParam(new_name="year", to_int=True),
                "Seitenzahl": TemplateParam(new_name="pageCount", to_int=True),
                "Enthaltene Orte": TemplateParam(
                    new_name="location", regex=r"\[\[GOV:(.*?)\|"
                ),
                "Verlag": TemplateParam(new_name="publisher"),
                "GOV-Quelle": TemplateParam(new_name="govSource"),
                "Standort online": TemplateParam(
                    new_name="onlineSource", regex=r"\{\{ThULB\|(.*?)\}\}"
                ),
                "DES": TemplateParam(new_name="des"),
            },
        )
        self.year_mapping = {"weimarTH1851.parquet": 1851, "weimarTH1853.parquet": 1853}
        self.locator=Locator(debug=self.debug)

    def check_location(self,page_title:str,item,force:bool=True):
        """
        check the location page
        """
        wiki=self.target_wiki.wiki_push.toWiki
        page=wiki.get_page(page_title)
        create=force or not page.exists
        if create:
            coords=self.locator.get_coordinates([item])
            lat,lon=coords[item]
            parts = page_title.rsplit("/", 1)  # Split from the right, limit to one split
            partOf = parts[0]  # PL/22
            name = parts[1]  # Miastko
            # PL/22/Miastko
            markup=f"""{{{{Location
|path={page_title}
|name={name}
|coordinates={lat},{lon}
|wikidataid={item}
|locationKind=City
|level=5
|partOf={partOf}
}}}}
"""
            page.edit(markup,"created by genwiki2024 addressbook converter")
            pass

    def record_convert(self, page_name:str, page_content:str, record: Dict):
        """
        addressbook record conversion callback
        """
        gov_id = record["location"]
        page_title=page_name.replace(" ","_")
        record["id"]=page_title
        record["genwikiurl"]=f"https://wiki.genealogy.net/{page_title}"
        if "image" in record and record["image"]:
            record["image"]=f"""File:{record["image"]}"""
        items_dict=self.locator.locate(gov_id)
        if len(items_dict)>0:
            for key,item in items_dict.items():
                if not item:
                    continue
                page_title=self.locator.lookup_path_for_item(item)
                record["at"]=page_title
                self.check_location(page_title, item)
                break
                pass

    def convert(
        self,
        page_contents,
        source_wiki=None,
        target_wiki=None,
        mode="backup",
        limit: int = None,
        force: bool = False,
        progress_bar=None,
    ):
        """
        Convert the pages of the given page_contents dict.

        Args:
            page_contents (dict): Dictionary of page names and their content.
            target_wiki (Wiki): Target wiki object for pushing content (if mode is 'push').
            mode (str): 'push' to push to target wiki, 'backup' to store as backup files.
            limit (int): Limit the number of pages to process.
            force (bool): if not True only do a dry run
            progress_bar (Progressbar): Progress bar object to update during conversion.
        """
        self.target_wiki=target_wiki
        if force:
            target_wiki.wiki_push.toWiki.login()
        result = {}
        total = len(page_contents) if limit is None else min(limit, len(page_contents))
        if progress_bar:
            progress_bar.total = total
            progress_bar.set_description(f"Converting {total} pages")

        for i, (page_name, page_content) in enumerate(page_contents.items()):
            if limit and i >= limit:
                break

            ab_dict = self.template_map.as_template_dict(
                page_name,page_content, callback=self.record_convert
            )
            markup = self.template_map.dict_to_markup(ab_dict)
            result[page_name] = markup
            if mode == "push" and target_wiki:
                edit_status = target_wiki.wiki_push.edit_page_content(
                    page_title=page_name,
                    new_text=markup,
                    summary="Converted AddressBook template",
                    force=force,
                )
                logging.log(logging.INFO, edit_status)
                pass
                source_page = source_wiki.wiki_push.fromWiki.getPage(page_name)
                image=None
                for page_image in source_page.images():
                    base_name=page_image.base_name.replace("Datei:","File:")
                    if base_name==ab_dict["image"]:
                        image=page_image
                    pass
                if image:
                    source_wiki.wiki_push.pushImages([image], ignore=True)

            elif mode == "backup":
                backup_path = os.path.join(
                    target_wiki.wiki_backup_dir, f"{page_name}.wiki"
                )
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(markup)

            if progress_bar:
                progress_bar.update(1)

            if self.debug:
                print(f"Processed page: {page_name}")

        if progress_bar:
            progress_bar.set_description("Conversion complete")
        return result
