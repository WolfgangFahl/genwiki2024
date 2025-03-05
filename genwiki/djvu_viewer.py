"""
Created on 2025-02-25

@author: wf
"""

import mimetypes
import os
from pathlib import Path
from typing import Optional,Tuple
import traceback
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from genwiki.djvu_core import DjVuFile, DjVuViewPage
from genwiki.tarball import Tarball
from genwiki.image_convert import ImageConverter

class DjVuViewer:
    """
    Handles loading and retrieving DjVu page metadata from YAML files and sets up static file serving.
    """

    _static_mounted = False  # Ensures mount is only done once

    def __init__(self, app: FastAPI, base_path: str = None):
        if base_path is None:
            base_path = os.getenv(
                "GENWIKI_PATH", "/Users/wf/hd/wf-fur.bitplan.com/genwiki"
            )
        self.image_path = os.path.join(base_path, "djvu_images")

        if not DjVuViewer._static_mounted:
            app.mount(
                "/static/djvu",
                StaticFiles(directory=self.image_path),
                name="djvu_images",
            )
            DjVuViewer._static_mounted = True

    def handle_exception(self, e: BaseException, trace: Optional[bool] = None):
        """Handles an exception by creating an error message.

        Args:
            e (BaseException): The exception to handle.
            trace (bool, optional): Whether to include the traceback in the error message. Default is False.
        """
        if trace:
            self.error_msg = str(e) + "\n" + traceback.format_exc()
        else:
            self.error_msg = str(e)
        logging.error(self.error_msg)

    def get_file_content(self, file: str) -> Tuple[str, bytes]:
        """
        Retrieves a content file (PNG, JPG, YAML, etc.) from the tarball

        Args:
            file (str): The full path in the format <DjVu name>/<file name>.

        """
        djvu_name, filename = file.split("/", 1)
        tarball_path = Path(self.image_path) / f"{djvu_name}.tar"
        file_content = Tarball.read_from_tar(tarball_path, filename)
        return filename, file_content

    def create_content_response(self, filename: str, file_content: bytes) -> Response:
        # Detect MIME type based on file extension
        media_type, _ = mimetypes.guess_type(filename)
        if media_type is None:
            media_type = "application/octet-stream"  # Default for unknown types

        content_response = Response(content=file_content, media_type=media_type)

        return content_response

    def get_content(self, file: str) -> Response:
        """
        Retrieves a content file (PNG, JPG, YAML, etc.) from the tarball and serves it as a response.

        Args:
            file (str): The full path in the format <DjVu name>/<file name>.

        Returns:
            Response: The requested content file with the correct media type.
        """
        try:
            filename, file_content = self.get_file_content(file)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid file path format. Expected <DjVu name>/<file name>.",
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Tarball not found")
        except KeyError:
            djvu_name, filename = file.split("/", 1)
            raise HTTPException(
                status_code=404,
                detail=f"File {filename} of DjVu {djvu_name} not found in tarball",
            )
        content_response = self.create_content_response(filename, file_content)
        return content_response

    def get_djvu_view_page(self, path: str, page_index: int) -> DjVuViewPage:
        """
        Helper function to fetch DjVu page data.

        Args:
            path (str): Path to the DjVu file (without page notation).
            page_index (int): Page number to display (1-based).

        Returns:
            DjVuViewPage: dataclass instance with file,page and image_url
        """
        tarball_file = Path(self.image_path) / f"{Path(path).stem}.tar"
        yaml_file = f"{Path(path).stem}.yaml"

        if not tarball_file.exists():
            raise HTTPException(status_code=404, detail="Tarball not found")

        try:
            yaml_data = Tarball.read_from_tar(tarball_file, yaml_file).decode("utf-8")
            djvu_file = DjVuFile.from_yaml(yaml_data)
        except Exception as ex:
            self.handle_exception(ex)
            raise HTTPException(
                status_code=500, detail=f"Error reading {yaml_file} from tarball"
            )

        page_count = len(djvu_file.pages)
        if page_index < 1 or page_index > page_count:
            raise HTTPException(status_code=404, detail=f"Page {page_index} not found")

        djvu_page = djvu_file.pages[page_index - 1]
        djvu_view_page = DjVuViewPage(file=djvu_file, page=djvu_page, base_path=path)
        return djvu_view_page

    def get_page4path(
        self,
        path: str,
        pageno: int,
        ext: str,
        scale: float = 1.0,
        quality: int = 85
    ) -> Response:
        """
        Fetches and displays a specific page of a DjVu file in the desired format.

        Args:
            path (str): The path to the DjVu document.
            pageno (int): The page number within the DjVu document.
            ext (str): The desired file extension for the page (e.g., "png", "jpg").
            scale (float, optional): The scale factor to apply to the image (0.0-1.0). Defaults to 1.0.
            quality (int, optional): The JPEG quality (1-100). Defaults to 85.

        Returns:
            Response: Response with the page content in the requested format.

        Raises:
            HTTPException: With status code 501 if the specified file extension is unsupported.
            HTTPException: With status code 500 if an error occurs while retrieving the page content.
        """
        # Check if the file extension is supported
        exts = ["png", "jpg"]
        if ext not in exts:
            msg = f"Unsupported file extension: {ext}. Must be one of {', '.join(exts)}."
            raise HTTPException(status_code=501, detail=msg)

        try:
            # Get the DjVu view page
            djvu_view_page = self.get_djvu_view_page(path, pageno)
            content_path = djvu_view_page.content_path

            # Get the original file content (PNG format)
            filename, file_content = self.get_file_content(content_path)

            # If JPG is requested, convert the PNG data to JPG
            if ext == "jpg":
                # Extract the DPI from the page metadata (assuming it's available)
                # If not available, you might need to add a parameter or use a default value
                dpi = getattr(djvu_view_page.page, 'dpi', 300)  # Default to 300 if not specified

                # Use ImageConverter to convert PNG to JPG
                converter = ImageConverter(file_content, dpi)
                file_content = converter.convert_to_jpg(scale=scale, quality=quality)

                # Update filename to reflect the JPG extension
                filename = filename.replace('.png', '.jpg')

            # Create and return the response with the appropriate content
            file_response= self.create_content_response(filename, file_content)
            return file_response
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving page content: {str(e)}"
            )

    def get_page(self, path: str, page_index: int) -> HTMLResponse:
        """
        Fetches and renders an HTML page displaying the PNG image of the given DjVu file page from a tarball.
        """
        djvu_view_page = self.get_djvu_view_page(path, page_index)
        djvu_file = djvu_view_page.file
        image_url = djvu_view_page.image_url
        html_response = HTMLResponse(
            content=self.get_markup(path, page_index, len(djvu_file.pages), image_url)
        )
        return html_response

    def create_page_dropdown(self, path, current_page, total_pages):
        """
        Create an HTML select dropdown for page navigation

        Args:
            path: Path of the DjVu file
            current_page: Currently displayed page number
            total_pages: Total number of pages in the document

        Returns:
            HTML select element with page options
        """
        options = []
        for page_num in range(1, total_pages + 1):
            selected = " selected" if page_num == current_page else ""
            options.append(f'<option value="{page_num}"{selected}>{page_num}</option>')

        options_html = "\n".join(options)

        select_html = f"""<select onchange="window.location.href='/djvu/{path}?page='+this.value">
        {options_html}
    </select>"""

        return select_html

    def get_markup(
        self, path: str, page_index: int, total_pages: int, image_url: str
    ) -> str:
        """
        Returns the HTML markup for displaying the DjVu page with navigation.

        Args:
            path (str): DjVu file path.
            page_index (int): Current page index.
            total_pages (int): Total number of pages in the DjVu document.
            image_url (str): URL to the PNG file.

        Returns:
            str: HTML markup.
        """
        first_page = 1  # Fix: Pages start from 1
        last_page = total_pages  # Fix: Last page is total_pages, not total_pages - 1
        prev_page = max(first_page, page_index - 1)
        next_page = min(last_page, page_index + 1)
        fast_backward = max(first_page, page_index - 10)
        fast_forward = min(last_page, page_index + 10)
        select_markup = self.create_page_dropdown(path, page_index, total_pages)

        markup = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DjVu Viewer</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; }}
                img {{ max-width: 100%; height: auto; }}
                .nav {{ margin-top: 20px; }}
                .nav a {{ margin: 0 10px; text-decoration: none; font-weight: bold; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/djvu/{path}?page={first_page}" title="First Page (1/{total_pages})">⏮</a>
                <a href="/djvu/{path}?page={fast_backward}" title="Fast Backward (Jump -10 Pages)">⏪</a>
                <a href="/djvu/{path}?page={prev_page}" title="Previous Page">⏴</a>
                <span>{select_markup} / {total_pages}</span>
                <a href="/djvu/{path}?page={next_page}" title="Next Page">⏵</a>
                <a href="/djvu/{path}?page={fast_forward}" title="Fast Forward (Jump +10 Pages)">⏩</a>
                <a href="/djvu/{path}?page={last_page}" title="Last Page ({total_pages}/{total_pages})">⏭</a>
            </div>
            <img src="{image_url}" alt="DjVu Page {page_index}">
        </body>
        </html>
        """
        return markup
