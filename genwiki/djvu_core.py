'''
Created on 2025-02-25

@author: wf
'''
from ngwidgets.yamlable import lod_storable
from typing import Optional
import numpy

@lod_storable
class DjVu:
    """Represents a record from the djvu table."""

    path: str
    dir_pages: int
    page_count: int


@lod_storable
class Image:
    """Represents a record from the image table."""
    path: str
    width: int
    height: int
    dpi: int
    djvu_path: Optional[str] = None
    buffer: Optional[numpy.ndarray]=None
