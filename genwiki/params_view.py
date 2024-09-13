"""
Created on 06.05.2024

@author: wf
"""

from lodstorage.params import Params
from ngwidgets.dict_edit import DictEdit, FieldUiDef, FormUiDef


class ParamsView:
    """
    a view for Query Parameters
    """

    def __init__(self, solution, params: Params,title:str="Params",icon:str="tune"):
        """
        construct me with the given solution and params
        """
        self.solution = solution
        self.params=params
        self.dict_edit=None
        self.title=title
        self.icon=icon

    def open(self):
        """
        show the details of the dict edit
        """
        self.dict_edit.open()

    def close(self):
        """
        hide the details of the dict edit
        """
        self.dict_edit.close()

    def delete(self):
        self.dict_edit.card.delete()
        self.dict_edit=None

    def setup(self):
        """
        Update the params and refresh the dict_edit
        """
        if self.dict_edit:
            self.dict_edit.card.delete()
        self.dict_edit=self.get_dict_edit()

    def get_dict_edit(self) -> DictEdit:
        """
        Return a DictEdit instance for editing parameters.
        """
        # Define a custom form definition for the title "Params"
        form_ui_def = FormUiDef(
            title=self.title,
            icon=self.icon,
            ui_fields={
                key: FieldUiDef.from_key_value(key, value)
                for key, value in self.params.params_dict.items()
            },
        )
        self.dict_edit = DictEdit(
            data_to_edit=self.params.params_dict, form_ui_def=form_ui_def
        )
        return self.dict_edit
