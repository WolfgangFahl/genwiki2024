"""
Created on 2025-02-25

@author: wf
"""

import io
import mimetypes
import os
import tarfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from genwiki.djvu_core import DjVuFile


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

    def read_from_tar(self, tarball_path: Path, filename: str) -> bytes:
        """
        Reads a file directly from a tarball.

        Args:
            tarball_path (Path): Path to the tar archive.
            filename (str): Name of the file inside the archive.

        Returns:
            bytes: The file contents.
        """
        with tarfile.open(tarball_path, "r") as tar:
            try:
                member = tar.getmember(filename)
                with tar.extractfile(member) as file:
                    return file.read()
            except KeyError:
                raise HTTPException(
                    status_code=404, detail=f"File {filename} not found in tarball"
                )

    def get_content(self, file: str) -> Response:
        """
        Retrieves a content file (PNG, JPG, YAML, etc.) from the tarball and serves it as a response.

        Args:
            file (str): The full path in the format <DjVu name>/<file name>.

        Returns:
            Response: The requested content file with the correct media type.
        """
        try:
            djvu_name, filename = file.split("/", 1)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid file path format. Expected <DjVu name>/<file name>.",
            )

        tarball_path = Path(self.image_path) / f"{djvu_name}.tar"

        if not tarball_path.exists():
            raise HTTPException(status_code=404, detail="Tarball not found")

        file_content = self.read_from_tar(tarball_path, filename)
        file_stream = io.BytesIO(file_content)
        # Detect MIME type based on file extension
        media_type, _ = mimetypes.guess_type(filename)
        if media_type is None:
            media_type = "application/octet-stream"  # Default for unknown types

        content_response = Response(content=file_content, media_type=media_type)

        return content_response

    def get_page(self, path: str, page_index: int) -> HTMLResponse:
        """
        Fetches and renders an HTML page displaying the PNG image of the given DjVu file page from a tarball.
        """
        tarball_file = Path(self.image_path) / f"{Path(path).stem}.tar"
        yaml_file = f"{Path(path).stem}.yaml"

        if not tarball_file.exists():
            raise HTTPException(status_code=404, detail="Tarball not found")

        try:
            yaml_data = self.read_from_tar(tarball_file, yaml_file).decode("utf-8")
            djvu_file = DjVuFile.from_yaml(yaml_data)
        except HTTPException:
            raise HTTPException(
                status_code=404, detail="YAML metadata not found in tarball"
            )
        except Exception:
            raise HTTPException(
                status_code=500, detail="Error reading YAML from tarball"
            )

        page_count = len(djvu_file.pages)
        if page_index < 1 or page_index > page_count:
            raise HTTPException(status_code=404, detail=f"Page {page_index} not found")

        djvu_page = djvu_file.pages[page_index - 1]
        image_filename = djvu_page.png_file
        image_url = f"/djvu/content/{Path(path).stem}/{image_filename}"

        return HTMLResponse(
            content=self.get_markup(path, page_index, len(djvu_file.pages), image_url)
        )

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
                <span>{page_index} / {total_pages}</span>
                <a href="/djvu/{path}?page={next_page}" title="Next Page">⏵</a>
                <a href="/djvu/{path}?page={fast_forward}" title="Fast Forward (Jump +10 Pages)">⏩</a>
                <a href="/djvu/{path}?page={last_page}" title="Last Page ({total_pages}/{total_pages})">⏭</a>
            </div>
            <img src="{image_url}" alt="DjVu Page {page_index}">
        </body>
        </html>
        """
        return markup
