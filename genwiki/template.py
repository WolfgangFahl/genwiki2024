"""
Created on 19.08.2024

@author: wf
"""

import re
from dataclasses import field
from typing import Any, Callable, Dict, Optional

import mwparserfromhell
from ngwidgets.yamlable import lod_storable


@lod_storable
class TemplateParam:
    new_name: str
    regex: Optional[str] = None
    to_int: bool = False


@lod_storable
class TemplateMap:
    template_name: str
    topic_name: str
    param_mapping: Dict[str, TemplateParam] = field(default_factory=dict)

    def as_template_dict(
        self, page_name: str, page_content: str, callback: Callable = None
    ) -> Dict[str, Any]:
        wikicode = mwparserfromhell.parse(page_content)
        templates = wikicode.filter_templates(matches=self.template_name)

        if not templates:
            return {}

        template = templates[0]
        result = {}

        for old_field, param in self.param_mapping.items():
            if template.has(old_field):
                value = str(template.get(old_field).value).strip()

                if param.regex:
                    match = re.search(param.regex, value)
                    value = match.group(1) if match else value

                if param.to_int:
                    try:
                        value = int(value)
                    except ValueError:
                        pass  # Keep the original value if it's not a valid integer

                result[param.new_name] = value
        if callback:
            callback(page_name, page_content, result)
        return result

    def as_topic_dict(self, page_content: str) -> Dict[str, Any]:
        """
        Extract template parameters based on the topic_name without conversions.

        Args:
            page_content (str): The content of the wiki page containing the template.

        Returns:
            Dict[str, Any]: Extracted parameters as a dictionary.
        """
        wikicode = mwparserfromhell.parse(page_content)
        templates = wikicode.filter_templates(matches=self.topic_name)

        if not templates:
            return {}

        template = templates[0]
        result = {}

        for param in template.params:
            name = str(param.name).strip()
            value = str(param.value).strip()
            result[name] = value

        return result

    def dict_to_sidif(self, data: Dict[str, Any]) -> str:
        sidif_lines = [f"{self.topic_name}1 isA {self.topic_name}"]
        for key, value in data.items():
            sidif_lines.append(f'"{value}" is {key} of {self.topic_name}1')
        return "\n".join(sidif_lines)

    def convert_template(self, page_name:str, page_content: str, output_format: str = "sidif") -> str:
        data = self.as_template_dict(page_name=page_name,page_content=page_content)
        if not data:
            return f"No '{self.template_name}' template found in the content."

        if output_format == "sidif":
            return self.dict_to_sidif(data)
        elif output_format == "markup":
            return self.dict_to_markup(data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    # Add dict_to_markup method if not already present
    def dict_to_markup(self, data: Dict[str, Any]) -> str:
        markup_lines = [f"{{{{{self.topic_name}"]
        for key, value in data.items():
            markup_lines.append(f"| {key} = {value}")
        markup_lines.append("}}")
        return "\n".join(markup_lines)
