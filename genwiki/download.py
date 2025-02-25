"""
Created on 25.02.2025

@author: wf
"""

import os
import time

import requests


class Download:
    @classmethod
    def download(cls, url: str, target_path: str, mkdir: bool = True):
        """
        Downloads a file if it does not exist, has zero size, or is older than the remote file.

        Args:
            url (str): The URL to download the file from.
            target_path (str): The path where the file should be saved.
            mkdir (bool): Whether to create the target directory if it does not exist. Default is False.
        """
        file_exists = os.path.exists(target_path)
        file_is_empty = file_exists and os.path.getsize(target_path) == 0
        local_mtime = os.path.getmtime(target_path) if file_exists else 0

        response = requests.head(url)
        response.raise_for_status()

        remote_mtime = response.headers.get("Last-Modified")
        if remote_mtime:
            remote_mtime = time.mktime(
                time.strptime(remote_mtime, "%a, %d %b %Y %H:%M:%S %Z")
            )
        else:
            remote_mtime = None

        needs_download = (
            not file_exists
            or file_is_empty
            or (remote_mtime and remote_mtime > local_mtime)
        )

        if needs_download:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            if mkdir:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if remote_mtime:
                os.utime(target_path, (remote_mtime, remote_mtime))
