"""
Created on 2025-02-25

@author: wf
"""
import os
from pathlib import Path
from fastapi import HTTPException, FastAPI
from fastapi.staticfiles import StaticFiles
from genwiki.djvu_core import DjVuFile
from starlette.responses import HTMLResponse

class DjVuViewer:
    """
    Handles loading and retrieving DjVu page metadata from YAML files and sets up static file serving.
    """

    _static_mounted = False  # Ensures mount is only done once

    def __init__(self, app: FastAPI, base_path: str = None):
        if base_path is None:
            base_path = os.getenv("GENWIKI_PATH", "/Users/wf/hd/wf-fur.bitplan.com/genwiki")
        self.image_path = os.path.join(base_path, "djvu_images")

        if not DjVuViewer._static_mounted:
            app.mount("/static/djvu", StaticFiles(directory=self.image_path), name="djvu_images")
            DjVuViewer._static_mounted = True


    """
Created on 2025-02-25

@author: wf
"""

import os
from pathlib import Path
import yaml
from fastapi import HTTPException, FastAPI
from fastapi.staticfiles import StaticFiles
from genwiki.djvu_core import DjVuFile

class DjVuViewer:
    """
    Handles loading and retrieving DjVu page metadata from YAML files and sets up static file serving.
    """

    _static_mounted = False  # Ensures mount is only done once

    def __init__(self, app: FastAPI, base_path: str = None):
        if base_path is None:
            base_path = os.getenv("GENWIKI_PATH", "/Users/wf/hd/wf-fur.bitplan.com/genwiki")
        self.image_path = os.path.join(base_path, "djvu_images")

        if not DjVuViewer._static_mounted:
            app.mount("/static/djvu", StaticFiles(directory=self.image_path), name="djvu_images")
            DjVuViewer._static_mounted = True

    def get_page(self, path: str, page_index: int)->HTMLResponse:
        """
        Fetches and renders an HTML page displaying the PNG image of the given DjVu file page.
        """
        yaml_file = Path(self.image_path) / f"{Path(path).stem}.yaml"

        if not yaml_file.exists():
            raise HTTPException(status_code=404, detail="YAML metadata not found")

        djvu_file = DjVuFile.load_from_yaml_file(yaml_file)
        djvu_page = djvu_file.get_page_by_page_index(page_index)

        if not djvu_page:
            raise HTTPException(status_code=404, detail=f"Page {page_index} not found")

        image_filename = Path(djvu_page.path).name
        image_url = f"/static/djvu/{image_filename}"
"""
Created on 2025-02-25

@author: wf
"""

import os
from pathlib import Path
import yaml
from fastapi import HTTPException, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from genwiki.djvu_core import DjVuFile

class DjVuViewer:
    """
    Handles loading and retrieving DjVu page metadata from YAML files and sets up static file serving.
    """

    _static_mounted = False  # Ensures mount is only done once

    def __init__(self, app: FastAPI, base_path: str = None):
        if base_path is None:
            base_path = os.getenv("GENWIKI_PATH", "/Users/wf/hd/wf-fur.bitplan.com/genwiki")
        self.image_path = os.path.join(base_path, "djvu_images")

        if not DjVuViewer._static_mounted:
            app.mount("/static/djvu", StaticFiles(directory=self.image_path), name="djvu_images")
            DjVuViewer._static_mounted = True

    def get_page(self, path: str, page_index: int) -> HTMLResponse:
        """
        Fetches and renders an HTML page displaying the PNG image of the given DjVu file page.
        """
        yaml_file = Path(self.image_path) / f"{Path(path).stem}.yaml"

        if not yaml_file.exists():
            raise HTTPException(status_code=404, detail="YAML metadata not found")

        djvu_file = DjVuFile.load_from_yaml_file(yaml_file)
        djvu_page = djvu_file.get_page_by_page_index(page_index)

        if not djvu_page:
            raise HTTPException(status_code=404, detail=f"Page {page_index} not found")

        image_filename = djvu_page.png_file
        image_url = f"/static/djvu/{image_filename}"
        html_markup=self.get_markup(path, page_index, image_url)
        return HTMLResponse(content=html_markup)

        return self.get_markup(path, page_index, image_url)

    def get_markup(self, path: str, page_index: int, image_url: str) -> str:
        """
        Returns the HTML markup for displaying the DjVu page.
        """
        return f"""
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
                .nav a {{ margin: 0 10px; text-decoration: none; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>DjVu Viewer</h1>
            <img src="{image_url}" alt="DjVu Page {page_index}">
            <div class="nav">
                <a href="/djvu/{path}?page={page_index-1}">Previous</a>
                <a href="/djvu/{path}?page={page_index+1}">Next</a>
            </div>
        </body>
        </html>
        """
