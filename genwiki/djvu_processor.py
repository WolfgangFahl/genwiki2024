"""
Created on 2025-02-25

@author: wf
"""
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Generator
from concurrent.futures import ThreadPoolExecutor, Future

import cairo
import djvu.decode
import numpy
from ngwidgets.profiler import Profiler
from genwiki.djvu_core import DjVuImage


@dataclass
class ImageJob:
    """
    Represents a processed DjVu page, including document, page, page job, and image data.
    """
    document: djvu.decode.Document
    page: djvu.decode.Page
    page_index: int  # Added page_index to track position
    relurl: str      # Added relurl for context
    pagejob: Optional[djvu.decode.PageJob] = field(default=None)
    image: Optional[DjVuImage] = field(default=None)

    def __post_init__(self):
        """Initialize profiler if not provided"""
        self.profiler = Profiler(f"Image Job {self.relurl}#{self.page_index:04d}")
        self.profiler.start()

    def log(self,msg):
        self.profiler.time(msg)

    def get_size(self) -> Tuple[int, int]:
        """Get the width and height of the page if pagejob is available"""
        if self.pagejob:
            return self.pagejob.size
        return (0, 0)


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

    def save_image_to_png(self, image_job: ImageJob, output_path: str):
        """
        Saves the rendered DjVu page as a PNG file.

        Args:
            image_job (ImageJob): The processed image job containing buffer data
            output_path (str): The path where the PNG file should be saved.
        """
        if not image_job.image or image_job.image.buffer is None:
            raise ValueError("Image buffer not available in ImageJob")

        width, height = image_job.get_size()
        surface = cairo.ImageSurface.create_for_data(
            image_job.image.buffer, cairo.FORMAT_ARGB32, width, height
        )
        surface.write_to_png(output_path)

    def render_pagejob_to_buffer(self, image_job: ImageJob, mode: int) -> numpy.ndarray:
        """
        Renders a DjVu page job to a color buffer.

        Args:
            image_job (ImageJob): The job containing the pagejob to render
            mode (int): Rendering mode.

        Returns:
            numpy.ndarray: The rendered color buffer.
        """
        if not image_job.pagejob:
            raise ValueError("PageJob not available")

        width, height = image_job.get_size()
        rect = (0, 0, width, height)

        bytes_per_line = cairo.ImageSurface.format_stride_for_width(
            self.cairo_pixel_format, width
        )
        assert bytes_per_line % 4 == 0

        color_buffer = numpy.zeros((height, bytes_per_line // 4), dtype=numpy.uint32)
        image_job.pagejob.render(
            mode,
            rect,
            rect,
            self.djvu_pixel_format,
            row_alignment=bytes_per_line,
            buffer=color_buffer,
        )

        if mode == djvu.decode.RENDER_FOREGROUND:
            mask_buffer = numpy.zeros_like(color_buffer)
            image_job.pagejob.render(
                djvu.decode.RENDER_MASK_ONLY,
                rect,
                rect,
                self.djvu_pixel_format,
                row_alignment=bytes_per_line,
                buffer=mask_buffer,
            )
            color_buffer |= mask_buffer << 24

        color_buffer ^= 0xFF000000  # Apply transparency
        return color_buffer

    def create_image_jobs(self, djvu_path: str, relurl: str) -> List[ImageJob]:
        """
        Create initial image jobs for all pages in the document

        Args:
            djvu_path (str): Path to the DjVu file
            relurl (str): Relative URL

        Returns:
            List[ImageJob]: List of initialized image jobs
        """
        document = self.new_document(djvu.decode.FileURI(djvu_path))
        document.decoding_job.wait()

        image_jobs = []
        for page_index, page in enumerate(document.pages,start=1):
            job = ImageJob(
                document=document,
                page=page,
                page_index=page_index,
                relurl=relurl
            )
            image_jobs.append(job)

        return image_jobs

    def decode_page(self, image_job: ImageJob, wait: bool = False) -> ImageJob:
        """
        Decodes a single page and updates the ImageJob

        Args:
            image_job (ImageJob): The job to process
            wait (bool): Whether to wait for decoding to complete

        Returns:
            ImageJob: Updated image job with pagejob
        """
        image_job.log(" page.decode start")
        pagejob = image_job.page.decode(wait=wait)
        image_job.log(" page.decode done")
        # Update the image job with the decoded page job
        image_job.pagejob = pagejob
        return image_job

    def render_page(self, image_job: ImageJob, mode: int = djvu.decode.RENDER_COLOR) -> ImageJob:
        """
        Renders a page and updates the ImageJob with the rendered image

        Args:
            image_job (ImageJob): The job to process
            mode (int): Rendering mode

        Returns:
            ImageJob: Updated image job with rendered image
        """
        image_job.log(" render start")
        if not image_job.pagejob:
            raise ValueError(f"PageJob not available for page {image_job.page_index}")

        width, height = image_job.get_size()
        color_buffer = self.render_pagejob_to_buffer(image_job, mode)

        image = DjVuImage(
            width=width,
            height=height,
            dpi=image_job.pagejob.dpi,
            page_index=image_job.page_index,
            djvu_path=image_job.relurl,
            path=image_job.page.file.name,
            buffer=color_buffer,
        )

        # Update the image job with the rendered image
        image_job.image = image
        image_job.log(" render done")

        return image_job

    def process(self, djvu_path: str, relurl: str, mode: int = djvu.decode.RENDER_COLOR, wait: bool = True) -> Generator[ImageJob, None, None]:
        """
        Converts a DjVu URL to image buffers with fully parallel decoding and rendering.

        Args:
            djvu_path (str): Path to the DjVu file.
            relurl (str): Relative URL.
            mode (int): Rendering mode, defaults to RENDER_COLOR.
            wait (bool): If True, wait for the decode job.

        Yields:
            ImageJob: Fully processed image job.
        """
        profiler = Profiler("processing")

        # Step 1: Create image jobs for all pages
        image_jobs = self.create_image_jobs(djvu_path, relurl)
        profiler.time("create image jobs")

        # Step 2: Decode all pages in parallel
        with ThreadPoolExecutor() as executor:
            decode_futures = [executor.submit(self.decode_page, job, wait) for job in image_jobs]

        max_workers = os.cpu_count() * 4
        # Step 3: Render all pages in parallel as they become available
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            render_futures: List[Future] = []

            # Submit rendering jobs as decoding completes
            for future in decode_futures:
                decoded_job = future.result()
                render_futures.append(executor.submit(self.render_page, decoded_job, mode))

            # Yield results as they become available
            for future in render_futures:
                rendered_job = future.result()
                yield rendered_job


# Example usage:
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Test the processor
    processor = DjVuProcessor()
    djvu_path = "path/to/document.djvu"
    relurl = "document.djvu"

    # Process in parallel and save each page
    for job in processor.process(djvu_path, relurl):
        output_path = f"output_page_{job.page_index}.png"
        processor.save_image_to_png(job, output_path)
        print(f"Saved page {job.page_index} to {output_path}")