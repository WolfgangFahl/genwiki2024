"""
Created on 19.08.2024

@author: wf
"""

import os

from genwiki.template import TemplateMap, TemplateParam


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

    def convert(
        self,
        page_contents,
        target_wiki=None,
        mode="backup",
        limit: int = None,
        progress_bar=None,
    ):
        """
        Convert the pages of the given page_contents dict.

        Args:
            page_contents (dict): Dictionary of page names and their content.
            target_wiki (Wiki): Target wiki object for pushing content (if mode is 'push').
            mode (str): 'push' to push to target wiki, 'backup' to store as backup files.
            limit (int): Limit the number of pages to process.
            progress_bar (Progressbar): Progress bar object to update during conversion.
        """
        total = len(page_contents) if limit is None else min(limit, len(page_contents))
        if progress_bar:
            progress_bar.total = total
            progress_bar.set_description(f"Converting {total} pages")

        for i, (page_name, page_content) in enumerate(page_contents.items()):
            if limit and i >= limit:
                break

            ab_dict = self.template_map.as_template_dict(page_content)
            markup = self.template_map.dict_to_markup(ab_dict)

            if mode == "push" and target_wiki:
                target_wiki.edit_page(
                    page_name, markup, summary="Converted AddressBook template"
                )
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
