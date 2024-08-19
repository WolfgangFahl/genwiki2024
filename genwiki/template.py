'''
Created on 19.08.2024

@author: wf
'''
from dataclasses import field
from ngwidgets.yamlable import lod_storable
from typing import Optional, Dict, Any
import mwparserfromhell
import re

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

    def as_template_dict(self, page_content: str) -> Dict[str, Any]:
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

        return result

    def dict_to_sidif(self, data: Dict[str, Any]) -> str:
        sidif_lines = [f"{self.topic_name}1 isA {self.topic_name}"]
        for key, value in data.items():
            sidif_lines.append(f'"{value}" is {key} of {self.topic_name}1')
        return '\n'.join(sidif_lines)

    def convert_template(self, page_content: str, output_format: str = 'sidif') -> str:
        data = self.as_template_dict(page_content)
        if not data:
            return f"No '{self.template_name}' template found in the content."

        if output_format == 'sidif':
            return self.dict_to_sidif(data)
        elif output_format == 'markup':
            return self.dict_to_markup(data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    # Add dict_to_markup method if not already present
    def dict_to_markup(self, data: Dict[str, Any]) -> str:
        markup_lines = [f"{{{{Template:{self.topic_name}"]
        for key, value in data.items():
            markup_lines.append(f"| {key} = {value}")
        markup_lines.append("}}")
        return '\n'.join(markup_lines)