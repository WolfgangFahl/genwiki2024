"""
Created on 2025-02-26

@author: wf
"""

import tarfile
from pathlib import Path


class Tarball:
    """
    tarball support
    """

    @staticmethod
    def read_from_tar(tarball_path: Path, filename: str) -> bytes:
        """
        Reads a file directly from a tarball.

        Args:
            tarball_path (Path): Path to the tar archive.
            filename (str): Name of the file inside the archive.

        Returns:
            bytes: The file contents.
        """
        with tarfile.open(tarball_path, "r") as tar:
            member = tar.getmember(filename)
            with tar.extractfile(member) as file:
                bytes_read = file.read()
                return bytes_read
