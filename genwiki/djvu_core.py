"""
Created on 2025-02-25

@author: wf
"""

from typing import Optional

import numpy
from ngwidgets.yamlable import lod_storable


@lod_storable
class DjVu:
    """Represents a DjVu main file e.g. bundled or indexed"""

    path: str
    dir_pages: int
    page_count: int


@lod_storable
class Page:
    """Represents a single djvu page"""

    path: str
    width: int
    height: int
    dpi: int
    djvu_path: Optional[str] = None


class DjVuImage(Page):
    buffer: Optional[numpy.ndarray] = None
