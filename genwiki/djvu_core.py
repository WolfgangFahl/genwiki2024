"""
Created on 2025-02-25

@author: wf
"""

from dataclasses import dataclass
from typing import Optional

import numpy
from ngwidgets.yamlable import lod_storable


@lod_storable
class DjVu:
    """Represents a DjVu main file e.g. bundled or indexed"""

    path: str
    page_count: int
    dir_pages: Optional[int] = None


@lod_storable
class DjVuPage:
    """Represents a single djvu page"""

    path: str
    page_index: int
    valid: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    dpi: Optional[int] = None
    djvu_path: Optional[str] = None
    page_key: Optional[str] = None

    def __post_init__(self):
        """Post-initialization logic for DjVuPage."""
        if self.page_key is None:
            # we expect no more than 9999 pages per document in the genwiki context that is proven
            self.page_key = f"{self.djvu_path}#{self.page_index:04d}"
        pass


@dataclass
class DjVuImage(DjVuPage):
    buffer: Optional[numpy.ndarray] = None
