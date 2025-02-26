"""
Created on 2025-02-25

@author: wf
"""

import logging
import os
import shutil
import sys
import tarfile
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Optional, Tuple

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
    djvu_path: str# fully qualifying path of the container DjVu document
    document: djvu.decode.Document
    page: djvu.decode.Page
    page_index: int  # Added page_index to track position
    relurl: str  # Added relurl for context
    pagejob: Optional[djvu.decode.PageJob] = field(default=None)
    image: Optional[DjVuImage] = field(default=None)
    verbose: bool = False
    debug: bool = False
    # keep track of any errors
    error: Optional[Exception] = field(default=None)

    def __post_init__(self):
        """Initialize profiler if not provided"""
        self.profiler = Profiler(
            f"Image Job {self.relurl}#{self.page_index:04d}",
            profile=self.verbose or self.debug,
        )
        self.profiler.start()

    def log(self, msg):
        if self.verbose or self.debug:
            self.profiler.time(" " + msg)

    def get_size(self) -> Tuple[int, int]:
        """Get the width and height of the page if pagejob is available"""
        if self.pagejob:
            return self.pagejob.size
        return (0, 0)

    @staticmethod
    def get_prefix(relurl: str):
        prefix = os.path.splitext(os.path.basename(relurl))[0]
        return prefix

    @property
    def prefix(self) -> str:
        prefix = ImageJob.get_prefix(relurl=self.relurl)
        return prefix

    @property
    def filename(self) -> str:
        try:
            # Attempt to safely decode the file name
            filename = self.page.file.name.encode(
                "utf-8", errors="replace"
            ).decode("utf-8")
        except Exception as e:
            if self.debug:
                logging.warn(
                    f"Failed to decode filename for page {self.page_index}: {e}"
                )
            filename = f"page_{self.page_index:04d}.djvu"
        return filename

    @property
    def dirname(self)->str:
        dirname=os.path.dirname(self.djvu_path)
        return dirname

    @property
    def filepath(self)->str:
        filepath=os.path.join(self.dirname,self.filename)
        return filepath

class DjVuContext(djvu.decode.Context):
    """
    A lightweight wrapper around djvu.decode.Context to handle messages.
    """

    def __init__(self):
        super().__init__()
        self.message_handler = None

    def handle_message(self, message):
        """
        Handles messages from the DjVu decoding context.
        """
        if self.message_handler:
            self.message_handler(message)


class DjVuProcessor:
    """
    Processes DjVu files and converts pages to image buffers.

    see https://raw.githubusercontent.com/jwilk-archive/python-djvulibre/refs/heads/master/examples/djvu2png
    with Copyright © 2010-2021 Jakub Wilk <jwilk@jwilk.net> and GNU General Public License version 2
    """

    def __init__(self, tar: bool = True, verbose: bool = False, debug: bool = False):
        """
        Initializes the DjVuProcessor.

        Args:
            tar(bool,optional): Enable tarball creation (default: True).
            verbose (bool, optional): Enable verbose output (default: False).
            debug (bool, optional): Enable debug logging (default: False).
        """
        self.tar = tar
        self.verbose = verbose
        self.debug = debug
        self.context = DjVuContext()  # delegate context instance
        self.context.message_handler = self.handle_message
        self.cairo_pixel_format = cairo.FORMAT_ARGB32
        self.djvu_pixel_format = djvu.decode.PixelFormatRgbMask(
            0xFF0000, 0xFF00, 0xFF, bpp=32
        )
        self.djvu_pixel_format.rows_top_to_bottom = 1
        self.djvu_pixel_format.y_top_to_bottom = 0

    def create_tarball(
        self, source_dir: str, output_tar: str, include_ext: Optional[List[str]] = None
    ):
        """
        Creates a tar archive from the given source directory, including only specific file types.

        Args:
            source_dir (str): Directory containing files to archive.
            output_tar (str): Path to the output tar file.
            include_ext (Optional[List[str]]): List of file extensions to include.
                - "yaml": Includes metadata files.
                - "png": Includes lossless original images.
                - "jpg": Includes compressed thumbnails.
                Defaults to ["yaml", "png", "jpg"].
        """
        if include_ext is None:
            include_ext = [
                "yaml",
                "png",
                "jpg",
            ]  # yaml metadata, png lossless original, jpg thumbnails
        with tarfile.open(output_tar, "w") as tar:
            for file in os.listdir(source_dir):
                if any(file.lower().endswith(ext) for ext in include_ext):
                    tar.add(os.path.join(source_dir, file), arcname=file)

    def handle_message(self, message):
        if isinstance(message, djvu.decode.ErrorMessage):
            raise Exception(message)

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

    def save_as_png(self, image_job: ImageJob, output_dir: str) -> str:
        """
        Save an image job as PNG in the specified directory

        Args:
            image_job: The image job to save
            output_dir: Directory to save to

        Returns:
            Path to the saved PNG file
        """
        output_path = os.path.join(
            output_dir, f"{image_job.prefix}_page_{image_job.page_index:04d}.png"
        )
        image_job.log("save png start")
        # Save PNG
        self.save_image_to_png(image_job, output_path)
        return output_path
        image_job.log("save png done")

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

    def ensure_file_exists(self,path:str):
        if not os.path.isfile(path):
            msg=f"file {path} not found"
            raise ValueError(msg)

    def yield_pages(self, djvu_path: str):
        """
        yield the pages for the given djvu_path
        """
        self.ensure_file_exists(djvu_path)
        document = self.context.new_document(djvu.decode.FileURI(djvu_path))
        document.decoding_job.wait()
        for page in document.pages:
            yield document, page

    def create_image_jobs(self, djvu_path: str, relurl: str) -> List[ImageJob]:
        """
        Create initial image jobs for all pages in the document

        Args:
            djvu_path (str): Path to the DjVu file
            relurl (str): Relative URL

        Returns:
            List[ImageJob]: List of initialized image jobs
        """
        image_jobs = []
        page_index = 0
        for document, page in self.yield_pages(djvu_path):
            page_index += 1
            job = ImageJob(
                djvu_path=djvu_path,
                document=document,
                page=page,
                page_index=page_index,
                relurl=relurl,
                debug=self.debug,
                verbose=self.verbose
            )
            image_jobs.append(job)

        return image_jobs

    def decode_page(self, image_job: ImageJob, wait: bool = True) -> ImageJob:
        """
        Decodes a single page and updates the ImageJob

        Args:
            image_job (ImageJob): The job to process
            wait (bool): Whether to wait for decoding to complete

        Returns:
            ImageJob: Updated image job with pagejob
        """
        try:
            file_size_msg=""
            filepath=image_job.filepath
            # check whether the document is bundled or not
            if image_job.document.type!=2:
                # we need to check the file is external
                self.ensure_file_exists(filepath)
                file_size = os.path.getsize(filepath)
                file_size_msg=(f"{filepath}:{file_size} bytes ")
            image_job.log(f" page.decode {file_size_msg}start")
            pagejob = image_job.page.decode(wait=wait)
            image_job.log(" page.decode done")
            # Update the image job with the decoded page job
            image_job.pagejob = pagejob
        except Exception as e:
            # Store exception but don't raise
            image_job.error = e
        return image_job

    def render_page(
        self, image_job: ImageJob, mode: int = djvu.decode.RENDER_COLOR
    ) -> ImageJob:
        """
        Renders a page and updates the ImageJob with the rendered image

        Args:
            image_job (ImageJob): The job to process
            mode (int): Rendering mode

        Returns:
            ImageJob: Updated image job with rendered image
        """
        try:
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
                path=image_job.filename,
                buffer=color_buffer,
            )

            # Update the image job with the rendered image
            image_job.image = image
            image_job.log(" render done")
        except Exception as e:
            # Store exception but don't raise
            image_job.error = e
        return image_job

    def prepare(self, output_path: str,relurl:str):
        """
        Prepares the output directory and sets up temporary storage if tarball creation is enabled.

        Args:
            output_path (str): The final destination path for output files.
            relurl(str): the relative url to process

        Attributes:
            final_output_path (str): The actual output path where the final files will be stored.
            temp_dir (Optional[str]): A temporary directory for intermediate storage if tarball creation is enabled.
            output_path (str): The working output path (either temporary or final).
            profiler (Profiler): Profiler instance for tracking processing time.
        """
        self.final_output_path = output_path
        if self.tar:
            # Use a temporary directory for intermediate PNG storage
            self.temp_dir = tempfile.mkdtemp()
            self.output_path = self.temp_dir
        else:
            self.output_path = output_path
        self.profiler = Profiler(f"processing {relurl}", profile=self.verbose or self.debug)
        # Prepare output directory if needed
        os.makedirs(self.final_output_path, exist_ok=True)

    def wrap_as_tarball(self, djvu_path: str):
        """
        Wraps processed output files into a tarball

        Args:
            djvu_path (str): The path to the original DjVu file.

        """
        tarball_path = os.path.join(
            self.final_output_path, f"{Path(djvu_path).stem}.tar"
        )
        self.create_tarball(self.output_path, tarball_path)
        shutil.rmtree(self.temp_dir)

    def process(
        self,
        djvu_path: str,
        relurl: str,
        mode: int = djvu.decode.RENDER_COLOR,
        wait: bool = True,
        save_png: bool = False,
        output_path: str = None,
    ) -> Generator[ImageJob, None, None]:
        """
        Converts a DjVu URL to image buffers with sequential decoding and rendering.
        """
        self.prepare(output_path=output_path,relurl=relurl)
        # Step 1: Create image jobs for all pages
        image_jobs = self.create_image_jobs(djvu_path, relurl)
        self.profiler.time(f" create image jobs")

        # Process each page sequentially
        for job in image_jobs:
            # Step 2: Decode the page
            decoded_job = self.decode_page(job, wait)

            # Step 3: Render the page
            rendered_job = self.render_page(decoded_job, mode)
            self.profiler.time(f" process page {rendered_job.page_index:4d}")

            # Step 4: Optionally save to PNG
            if save_png:
                self.save_as_png(rendered_job, self.output_path)

            yield rendered_job

    def process_parallel(
        self,
        djvu_path: str,
        relurl: str,
        mode: int = djvu.decode.RENDER_COLOR,
        wait: bool = True,
        save_png: bool = False,
        output_path: str = None,
    ) -> Generator[ImageJob, None, None]:
        """
        Converts a DjVu URL to image buffers with fully parallel decoding and rendering.

        Args:
            djvu_path (str): Path to the DjVu file.
            relurl (str): Relative URL for referencing the file.
            mode (int, optional): Rendering mode (default: djvu.decode.RENDER_COLOR).
            wait (bool, optional): Whether to wait for processing to complete (default: True).
            save_png (bool, optional): Whether to save output as PNG files (default: False).
            output_path (str, optional): Directory path to save PNG files (default: None).

        Yields:
            Generator[ImageJob, None, None]: A generator yielding image jobs.
        """
        self.prepare(output_path=output_path,relurl=relurl)

        # Step 1: Create image jobs for all pages
        image_jobs = self.create_image_jobs(djvu_path, relurl)
        self.profiler.time(" create image jobs")

        # Step 2: Decode all pages in parallel
        with ThreadPoolExecutor() as executor:
            decode_futures = [
                executor.submit(self.decode_page, job, wait) for job in image_jobs
            ]

        # Step 3 & 4: Render and save all pages in parallel
        max_workers = os.cpu_count() * 4
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            render_futures: List[Future] = []

            # Submit rendering jobs as decoding completes
            for future in decode_futures:
                decoded_job = future.result()
                render_futures.append(
                    executor.submit(self.render_page, decoded_job, mode)
                )

            # Process rendered jobs as they become available
            for future in render_futures:
                rendered_job = future.result()
                self.profiler.time(f" process page {rendered_job.page_index:4d}")

                # Optionally save to PNG in parallel (submit to executor)
                if save_png:
                    executor.submit(self.save_as_png, rendered_job, self.output_path)

                yield rendered_job
