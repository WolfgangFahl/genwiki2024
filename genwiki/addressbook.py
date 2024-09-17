"""
Created on 19.08.2024

@author: wf
"""

import logging
import os
from typing import Any, Dict, List

from genwiki.locator import Locator
from genwiki.template import TemplateMap, TemplateParam
from genwiki.wikidata import Wikidata

class AddressBookConverter:
    """
    convert Adressbook pages
    """

    def __init__(self,force:bool=False,debug: bool = False):
        self.force=force
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
        self.locator = Locator(debug=self.debug)
        self.target_wiki=None

    def create_location_page(self,page_title:str,item:str,name:str,partOf:str,level:str="5",force:bool=False):
        """
        create a wiki page for the given location
        """
        if not self.target_wiki:
            raise ValueError("target wiki is not set")
        wiki = self.target_wiki.wiki_push.toWiki
        page = wiki.get_page(page_title)
        create = force or not page.exists
        kind_map={
            "3": "Country",
            "4": "Region",
            "5": "City"
        }
        location_kind=kind_map[level]
        if create:
            coords = self.locator.get_coordinates([item])
            if not item in coords:
                logging.warn(f"no coordinates for {item}")
                coord_markup=""
            else:
                lat, lon = coords[item]
                coord_markup=f"{lat},{lon}"
            markup = f"""{{{{Location
|path={page_title}
|name={name}
|coordinates={coord_markup}
|wikidataid={item}
|locationKind={location_kind}
|level={level}
|partOf={partOf}
}}}}
"""
            page.edit(markup, "created by genwiki2024 addressbook converter")

    def check_location(
        self,
        page_title: str,
        item,
        lookup_qlod: List[Dict[str, Any]],
        force: bool = False,
    ):
        """
        check the location page
        """
        if not page_title:
            msg=f"missing page title for item {item}"
            logging.error(msg)
            return
        parts = page_title.rsplit(
            "/", 1
        )  # Split from the right, limit to one split
        partOf = parts[0]  # PL/22
        name = parts[1]  # Miastko
        # PL/22/Miastko
        self.create_location_page(page_title=page_title, item=item, name=name,partOf=partOf,force=force)
        for record in lookup_qlod:
            level = record["level"]
            iso_code = record["iso_code"]
            item=record["intermediateAdmin"]
            item=Wikidata.unprefix(item)
            name=record["intermediateAdminLabel"]
            page_title=f"""{iso_code.replace("-","/")}"""
            parts = page_title.rsplit(
            "/", 1
            )  # Split from the right, limit to one split
            partOf = parts[0]  # PL/22
            self.create_location_page(page_title=page_title, item=item, name=name,partOf=partOf,level=level,force=force)


    def record_convert(self, page_name: str, page_content: str, record: Dict):
        """
        addressbook record conversion callback
        """
        gov_id = record["location"]
        page_title = page_name.replace(" ", "_")
        record["id"] = page_title
        record["genwikiurl"] = f"https://wiki.genealogy.net/{page_title}"
        if "image" in record and record["image"]:
            record["image"] = f"""File:{record["image"]}"""
        items_dict = self.locator.locate(gov_id)
        if len(items_dict) > 0:
            for key, item in items_dict.items():
                if not item:
                    continue
                lookup_qlod = self.locator.lookup_item(item)
                location_title = self.locator.to_path(lookup_qlod)
                if location_title:
                    record["at"] = location_title
                    self.check_location(location_title, item, lookup_qlod,force=self.force)
                    break


    def convert(
        self,
        page_contents,
        source_wiki=None,
        target_wiki=None,
        mode="backup",
        limit: int = None,
        dry_run:bool=False,
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
        self.target_wiki = target_wiki
        if not dry_run:
            target_wiki.wiki_push.toWiki.login()
        result = {}
        total = len(page_contents) if limit is None else min(limit, len(page_contents))
        if progress_bar:
            progress_bar.total = total
            progress_bar.set_description(f"Converting {total} pages")
        wiki=target_wiki.wiki_push.toWiki
        for i, (page_name, page_content) in enumerate(page_contents.items()):
            if limit and i >= limit:
                break
            # avoid effort for existing pages if not in force mode
            if mode == "push" and target_wiki:
                page=wiki.get_page(page_name)
                if page.exists and not force:
                    logging.info(f"page {page_name} exists")
                    continue

            ab_dict = self.template_map.as_template_dict(
                page_name, page_content, callback=self.record_convert
            )
            markup = self.template_map.dict_to_markup(ab_dict)
            result[page_name] = markup
            if mode == "push" and target_wiki:
                edit_status = target_wiki.wiki_push.edit_page_content(
                    page_title=page_name,
                    new_text=markup,
                    summary="Converted AddressBook template",
                    force=not dry_run,
                )
                logging.log(logging.INFO, edit_status)
                pass
                source_page = source_wiki.wiki_push.fromWiki.getPage(page_name)
                image = None
                for page_image in source_page.images():
                    base_name = page_image.base_name.replace("Datei:", "File:")
                    if "image" in ab_dict and base_name == ab_dict["image"]:
                        image = page_image
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
