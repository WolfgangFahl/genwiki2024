"""
Created on 2025-02-25

@author: wf
"""

import os
import sys
from dataclasses import dataclass

import cairo
import djvu.decode
import numpy

from genwiki.djvu_core import DjVuImage


@dataclass
class ImageJob:
    """
    Represents a processed DjVu page, including document, page, page job, and image data.
    """
    document: djvu.decode.Document
    page: djvu.decode.Page
    pagejob: djvu.decode.PageJob
    image: DjVuImage


class DjVuProcessor(djvu.decode.Context):
    """
    Processes DjVu files and converts pages to image buffers.

    see https://raw.githubusercontent.com/jwilk-archive/python-djvulibre/refs/heads/master/examples/djvu2png
    with Copyright © 2010-2021 Jakub Wilk <jwilk@jwilk.net> and GNU General Public License version 2

    """

    def __init__(self):
        super().__init__()
        self.cairo_pixel_format = cairo.FORMAT_ARGB32
        self.djvu_pixel_format = djvu.decode.PixelFormatRgbMask(
            0xFF0000, 0xFF00, 0xFF, bpp=32
        )
        self.djvu_pixel_format.rows_top_to_bottom = 1
        self.djvu_pixel_format.y_top_to_bottom = 0

    def handle_message(self, message):
        if isinstance(message, djvu.decode.ErrorMessage):
            print(message, file=sys.stderr)
            os._exit(1)

    def imagejob_from_pagejob(
        self, document, page,page_index:int,relurl:str, pagejob,
        mode=djvu.decode.RENDER_FOREGROUND
    ) -> ImageJob:
        """
        Converts a DjVu page job to an ImageJob instance.

        Args:
            document: The DjVu document containing the page.
            page: The specific page being processed.
            page_index: the page index
            relurl(str): the relative url
            page_job: The decoded DjVu page job.
            mode (int): Rendering mode, defaults to RENDER_COLOR.


        Returns:
            ImageJob: The processed image data.
        """
        width, height = pagejob.size
        rect = (0, 0, width, height)

        bytes_per_line = cairo.ImageSurface.format_stride_for_width(
            self.cairo_pixel_format, width
        )
        assert bytes_per_line % 4 == 0

        color_buffer = numpy.zeros((height, bytes_per_line // 4), dtype=numpy.uint32)
        pagejob.render(
            mode,
            rect,
            rect,
            self.djvu_pixel_format,
            row_alignment=bytes_per_line,
            buffer=color_buffer,
        )

        mask_buffer = numpy.zeros((height, bytes_per_line // 4), dtype=numpy.uint32)
        if mode == djvu.decode.RENDER_FOREGROUND:
            pagejob.render(
                djvu.decode.RENDER_MASK_ONLY,
                rect,
                rect,
                self.djvu_pixel_format,
                row_alignment=bytes_per_line,
                buffer=mask_buffer,
            )
            mask_buffer <<= 24
            color_buffer |= mask_buffer

        color_buffer ^= 0xFF000000

        image = DjVuImage(
            width=width,
            height=height,
            dpi=pagejob.dpi,
            page_index=page_index,
            djvu_path=relurl,
            path=page.file.name,
            buffer=color_buffer,
        )
        imagejob = ImageJob(document=document, page=page, pagejob=pagejob, image=image)
        return imagejob

    def yield_pages(self, djvu_path:str):
        """
        yield the pages for the given djvu_path
        """
        document = self.new_document(djvu.decode.FileURI(djvu_path))
        document.decoding_job.wait()
        for page in document.pages:
            yield document, page

    def process(self, djvu_path, relurl:str,mode=djvu.decode.RENDER_COLOR, wait: bool = True):
        """
        Converts a DjVu url to image buffers.

        Args:
            djvu_path (str): Path to the DjVu file.
            relurl(str): relative url
            mode (int): Rendering mode, defaults to RENDER_COLOR.
            wait(bool): if True wait for the decode job

        Yields:
            ImageJob: Processed page data.
        """
        page_index=0
        for document, page in self.yield_pages(djvu_path):
            page_index+=1
            pagejob = page.decode(wait=wait)
            imagejob=self.imagejob_from_pagejob(
                document=document,
                page=page,
                page_index=page_index,
                relurl=relurl,
                pagejob=pagejob,
                mode=mode)
            yield imagejob