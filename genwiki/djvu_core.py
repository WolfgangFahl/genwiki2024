"""
Created on 2025-02-25

@author: wf
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy
from ngwidgets.yamlable import lod_storable


@lod_storable
class DjVuPage:
    """Represents a single djvu page"""

    path: str
    page_index: int
    valid: bool = False
    iso_date: Optional[str] = None
    filesize: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    dpi: Optional[int] = None
    djvu_path: Optional[str] = None
    page_key: Optional[str] = None
    error_msg: Optional[str] = None

    def __post_init__(self):
        """Post-initialization logic for DjVuPage."""
        if self.page_key is None:
            # we expect no more than 9999 pages per document in the genwiki context that is proven
            self.page_key = f"{self.djvu_path}#{self.page_index:04d}"
        pass

    @property
    def png_file(self) -> str:
        """
        Returns the PNG file name derived from the DjVu file path and page index.
        """
        prefix = os.path.splitext(os.path.basename(self.djvu_path))[0]
        png_file = f"{prefix}_page_{self.page_index:04d}.png"
        return png_file


@dataclass
class DjVu:
    """Represents a DjVu main file e.g. bundled or indexed"""

    path: str
    page_count: int
    bundled: bool = False
    iso_date: Optional[str] = None
    filesize: Optional[int] = None
    tar_filesize: Optional[int] = None
    tar_iso_date: Optional[str] = None
    dir_pages: Optional[int] = None


@lod_storable
class DjVuFile(DjVu):
    """Represents a DjVu main file e.g. bundled or indexed"""

    pages: List[DjVuPage] = field(default_factory=list)

    def get_page_by_page_index(self, page_index: int) -> Optional[DjVuPage]:
        """
        Retrieve a page by its page index.

        Args:
            page_index (int): The index of the page to retrieve.

        Returns:
            Optional[DjVuPage]: The requested DjVuPage if found, otherwise None.
        """
        for page in self.pages:
            if page.page_index == page_index:
                return page
        return None


@dataclass
class DjVuViewPage:
    file: DjVuFile
    page: DjVuPage
    base_path: str

    @property
    def content_path(self) -> str:
        """Path for content retrieval"""
        return f"{Path(self.base_path).stem}/{self.page.png_file}"

    @property
    def image_url(self) -> str:
        """URL path for HTML display"""
        return f"/djvu/content/{self.content_path}"


@dataclass
class DjVuImage(DjVuPage):
    buffer: Optional[numpy.ndarray] = None
